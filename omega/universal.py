# =====================================================================
# Ω Universal Optimizer - v4.2.0-optuna
# =====================================================================
# This file is now upgraded to use a real Bayesian Optimizer
# via 'optuna' instead of the SurrogateModel stub.
# =====================================================================

# stdlib
import os, sys, json, gzip, pickle, hashlib, time, atexit, signal, tempfile, logging, random, argparse, ast
from collections import OrderedDict, defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Callable, Dict, Any, List, Tuple, Union, Optional
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed, wait, FIRST_COMPLETED, Future
import threading

# dependencies
import numpy as np

try:
    import ray
except ImportError:
    print("[omega.universal] warning: 'ray' not installed. 'ray' scheduler unavailable.")
    ray = None

try:
    import torch
except ImportError:
    print("[omega.universal] warning: 'torch' not installed. 'sobol' sampler unavailable.")
    torch = None

try:
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)
except ImportError:
    print("[omega.universal] warning: 'optuna' not installed. 'bayesian' strategy unavailable.")
    optuna = None

# ----------------------------------------------------------------------
# Import your real Omega analysis module
# ----------------------------------------------------------------------
try:
    from . import analysis as omega_analysis
except ImportError:
    print("[omega.universal] warning: 'omega.analysis' module not found.")
    omega_analysis = None
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------
logger = logging.getLogger("omega_optimizer")
logger.setLevel(logging.INFO)
if not logger.hasHandlers():
    sh = logging.StreamHandler(sys.stdout)
    fmt = logging.Formatter("[%(name)s] %(levelname)s: %(message)s")
    sh.setFormatter(fmt)
    logger.addHandler(sh)

# ----------------------------------------------------------------------
# Dataclasses (from v4.1.0)
# ----------------------------------------------------------------------
@dataclass
class Trial:
    trial_id: str
    params_norm: np.ndarray # Normalized parameters [0, 1]
    status: str = "PENDING"
    checkpoints: List[Tuple[int, float]] = field(default_factory=list)
    last_loss: float = np.inf
    last_checkpoint: Optional[str] = None
    optuna_trial_id: Optional[int] = None # For linking to Optuna

    @property
    def current_budget(self) -> int:
        return self.checkpoints[-1][0] if self.checkpoints else 0

    @property
    def best_loss(self) -> float:
        return min(loss for _, loss in self.checkpoints) if self.checkpoints else np.inf

@dataclass
class OptResult:
    """Standardized result object returned by optimizer."""
    params: np.ndarray             # Natural (de-normalized) parameters
    objective_value: float       # The raw loss (e.g., L2 Error)
    cod: float                   # Chain Overlap Density (COD)
    cri_score: float             # Causal Rate of Influence (CRI)
    metadata: Dict[str, Any] = field(default_factory=dict)

# ----------------------------------------------------------------------
# Worker Invoker (from v4.1.0)
# ----------------------------------------------------------------------
def _worker_invoker(
    trial: Trial,
    budget: int,
    checkpoint_path: Optional[Path],
    cfg: "Config",
    dim: int,
    lows: np.ndarray,
    param_scale: np.ndarray) -> Tuple[str, int, float, Optional[str]]:
    """
    Static top-level function to invoke the user's objective.
    This is what ProcessPoolExecutor/Ray can pickle.
    """
    try:
        # 1. De-normalize parameters
        params_natural = lows + trial.params_norm * param_scale

        # 2. Handle integer casting
        for i in cfg.int_indices:
            params_natural[i] = int(round(params_natural[i]))

        # 3. Call the user's actual worker function
        loss = cfg.objective(
            params_natural=params_natural,
            budget=budget,
            trial_id=trial.trial_id,
            checkpoint_dir=cfg.checkpoint_dir
        )

        # 4. Handle failed trials
        if loss is None or not np.isfinite(loss):
            loss = np.inf

        # 5. Return result tuple
        return trial.trial_id, budget, float(loss), None

    except Exception as e:
        logger.warning(f"Trial {trial.trial_id} failed with error: {e}")
        return trial.trial_id, budget, np.inf, None

# ----------------------------------------------------------------------
# Config (from v4.1.0)
# ----------------------------------------------------------------------
@dataclass
class Config:
    objective: Callable[..., float]
    search_space: Dict[str, Tuple[float, float]]
    checkpoint_path: Path
    checkpoint_dir: Path
    worker_budget: int

    # --- Optional RC params ---
    budgets: List[int] = field(default_factory=lambda: [1, 5, 10])
    promotion_fraction: float = 0.33
    min_surrogate_points: int = 10
    task_scheduler: str = "ray"

    # --- Derived params (set in __post_init__) ---
    int_indices: List[int] = field(default_factory=list)
    search_space_keys: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.checkpoint_path = Path(self.checkpoint_path)
        self.checkpoint_dir = Path(self.checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        self.search_space_keys = list(self.search_space.keys())
        for i, (name, bounds) in enumerate(self.search_space.items()):
            if isinstance(bounds[0], int) and isinstance(bounds[1], int):
                self.int_indices.append(i)

# ----------------------------------------------------------------------
# Optimizer (v4.2.0) - Upgraded with Optuna
# ----------------------------------------------------------------------
class UniversalOptimizer:
    """
    This class now uses Optuna for real Bayesian Optimization (TPE sampler).
    It replaces the SurrogateModel stub.
    """
    def __init__(
        self, 
        objective: Callable[..., float],
        search_space: Dict[str, Tuple[float, float]],
        rc: Dict[str, Any],
        n_workers: int = 4
    ):
        logger.info("Initializing Omega Universal Optimizer (v4.2.0-optuna)")

        # 1. Config
        self.cfg = Config(objective=objective, search_space=search_space, **rc)

        # 2. Search Space
        self.dim = len(self.cfg.search_space)
        self.lows = np.array([v[0] for v in self.cfg.search_space.values()])
        self.highs = np.array([v[1] for v in self.cfg.search_space.values()])
        self.param_scale = self.highs - self.lows

        # 3. State
        self.trials: Dict[str, Trial] = {}
        self.best_trial: Optional[Trial] = None
        self.launched_new_trials = 0
        self.pending_jobs = 0
        self.completed_trials_count = 0

        # 4. Components
        if torch:
            self.sobol = torch.quasirandom.SobolEngine(dimension=self.dim)
        else:
            self.sobol = None
            logger.warning("Torch not found. Sobol sampler disabled. Falling back to np.random.")
        
        # --- NEW: Optuna Integration ---
        self.optuna_study: Optional[optuna.Study] = None
        if optuna:
            # We use an in-memory study. The checkpoint file is our source of truth.
            self.optuna_study = optuna.create_study(
                sampler=optuna.samplers.TPEsampler(),
                direction="minimize"
            )
        else:
            logger.warning("Optuna not found. 'bayesian' strategy will fall back to 'random'.")
        # --- End Optuna ---

        # 5. Parallelism
        self.n_workers = n_workers
        self.task_scheduler = self.cfg.task_scheduler
        self._pool = None

        if self.task_scheduler == "ray":
            if ray is None:
                logger.warning("Ray scheduler requested but 'ray' not installed. Falling back to 'process' scheduler.")
                self.task_scheduler = "process"
            elif not ray.is_initialized():
                ray.init(num_cpus=n_workers, logging_level=logging.ERROR)
        
        if self.task_scheduler == "process":
            self._pool = ProcessPoolExecutor(max_workers=self.n_workers)

        logger.info(f"Using scheduler: '{self.task_scheduler}' with {self.n_workers} workers.")

        # 6. Load Checkpoint
        self._load_checkpoint()

        # 7. Register shutdown hooks
        atexit.register(self.close)
        signal.signal(signal.SIGTERM, self._shutdown_handler)
        signal.signal(signal.SIGINT, self._shutdown_handler)

    def _shutdown_handler(self, sig, frame):
        logger.warning(f"Shutdown signal ({sig}) received. Closing pool...")
        self.close()
        sys.exit(1)

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        logger.info("Shutting down optimizer pool...")
        if self._pool:
            self._pool.shutdown(wait=True)
            self._pool = None
        if self.task_scheduler == "ray" and ray and ray.is_initialized():
            ray.shutdown()
        logger.info("Shutdown complete.")

    def _save_checkpoint(self):
        try:
            state = {
                "trials": self.trials,
                "best_trial_id": self.best_trial.trial_id if self.best_trial else None
            }
            with gzip.open(self.cfg.checkpoint_path, 'wb') as f:
                pickle.dump(state, f)
        except Exception as e:
            logger.warning(f"Failed to save checkpoint: {e}")

    def _load_checkpoint(self):
        if not self.cfg.checkpoint_path.exists():
            logger.info("No checkpoint found, starting new run.")
            return
        
        try:
            with gzip.open(self.cfg.checkpoint_path, 'rb') as f:
                state = pickle.load(f)
            self.trials = state["trials"]
            best_id = state.get("best_trial_id")
            if best_id and best_id in self.trials:
                self.best_trial = self.trials[best_id]
            
            logger.info(f"Loaded {len(self.trials)} trials from checkpoint.")
            
            # --- NEW: Re-populate Optuna study from history ---
            if self.optuna_study:
                logger.info("Re-populating Optuna study from checkpoint...")
                for trial in self.trials.values():
                    if trial.status == "COMPLETED":
                        # We must re-create the trial for Optuna
                        optuna_trial = self._create_optuna_trial_from_params(trial.params_norm)
                        # Tell Optuna the result
                        self.optuna_study.tell(optuna_trial, trial.best_loss)
                        trial.optuna_trial_id = optuna_trial.number # Link it
                        self.completed_trials_count += 1
                logger.info(f"Re-populated Optuna with {self.completed_trials_count} trials.")
            # --- End Optuna ---
            
        except Exception as e:
            logger.warning(f"Failed to load checkpoint: {e}. Starting new run.")
            self.trials = {}
            self.best_trial = None

    def _create_optuna_trial_from_params(self, params_norm: np.ndarray) -> optuna.Trial:
        """Helper to create a new optuna trial from normalized params."""
        # De-normalize
        params_natural = self.lows + params_norm * self.param_scale
        
        # Optuna needs a "distribution" map to create a trial
        distributions = {}
        for i, key in enumerate(self.cfg.search_space_keys):
            bounds = self.cfg.search_space[key]
            if i in self.cfg.int_indices:
                distributions[key] = optuna.distributions.IntDistribution(bounds[0], bounds[1])
            else:
                # Check for log scale (as defined in pinn_worker.py)
                is_log = key == "lr" 
                distributions[key] = optuna.distributions.FloatDistribution(bounds[0], bounds[1], log=is_log)
        
        # Create a "frozen" (static) trial with our parameters
        optuna_trial = optuna.trial.create_trial(
            params=dict(zip(self.cfg.search_space_keys, params_natural)),
            distributions=distributions,
            value=None # We will .tell() this later
        )
        return self.optuna_study.ask(fixed_params=optuna_trial.params)


    def _get_next_candidates_optuna(self, n: int) -> List[Tuple[np.ndarray, optuna.Trial]]:
        """Gets n candidate points [0, 1] from Optuna."""
        candidates = []
        for _ in range(n):
            # Ask Optuna for the next best parameters
            optuna_trial = self.optuna_study.ask()
            
            # Extract the natural parameters
            params_natural_list = [optuna_trial.params[key] for key in self.cfg.search_space_keys]
            params_natural = np.array(params_natural_list)
            
            # Re-normalize them to [0, 1] for storage
            params_norm = (params_natural - self.lows) / self.param_scale
            candidates.append((params_norm, optuna_trial))
        return candidates

    def _get_next_candidates_random(self, n: int) -> List[Tuple[np.ndarray, None]]:
        """Gets n random candidate points [0, 1]."""
        if self.sobol:
            points_norm = self.sobol.draw(n).float().numpy()
        else:
            points_norm = np.random.rand(n, self.dim)
        return [(p, None) for p in list(points_norm)]

    def _propose_trial(self, params_norm: np.ndarray, optuna_trial: Optional[optuna.Trial]) -> Trial:
        trial_id = hashlib.md5(params_norm.tobytes()).hexdigest()[:10]
        if trial_id not in self.trials:
            self.trials[trial_id] = Trial(
                trial_id=trial_id, 
                params_norm=params_norm,
                optuna_trial_id=optuna_trial.number if optuna_trial else None
            )
        return self.trials[trial_id]

    def _submit_job(
        self, 
        trial: Trial, 
        budget: int, 
        ckpt_path: Optional[Path] = None
    ) -> Union[Future, "ray.ObjectRef"]:
        """Submits a job to the configured scheduler."""
        target_callable = _worker_invoker
        kwargs = dict(
            trial=trial,
            budget=budget,
            checkpoint_path=ckpt_path,
            cfg=self.cfg,
            dim=self.dim,
            lows=self.lows,
            param_scale=self.param_scale
        )
        if self.task_scheduler == "ray":
            remote_callable = ray.remote(target_callable)
            return remote_callable.remote(**kwargs)
        else:
            if self._pool is None:
                raise RuntimeError("Process pool is not initialized.")
            return self._pool.submit(target_callable, **kwargs)

    def optimize(
        self, 
        n_iters: int, 
        n_candidates: int, 
        strategy: str = "bayesian"
    ) -> OptResult:
        """
        Main optimization loop.
        """
        logger.info(f"Starting optimization: {n_iters} iterations, {n_candidates} candidates/iter.")

        # --- Check if Optuna is available ---
        use_bayesian = strategy == "bayesian" and self.optuna_study is not None
        if strategy == "bayesian" and not use_bayesian:
            logger.warning("'bayesian' strategy requested, but Optuna is not available. Falling back to 'random'.")
            strategy = "random"
        # ---
        
        for it in range(n_iters):
            logger.info(f"--- Iteration {it+1} / {n_iters} ---")

            # 1. Get candidate parameters
            # Use random sampling for warm-up, then switch to Optuna
            is_warmup = (self.completed_trials_count < self.cfg.min_surrogate_points)
            
            if strategy == "random" or is_warmup:
                if is_warmup:
                    logger.info(f"Warm-up sampling (need {self.cfg.min_surrogate_points - self.completed_trials_count} more trials).")
                candidates = self._get_next_candidates_random(n_candidates)
            else:
                logger.info("Using 'bayesian' strategy (Optuna TPE).")
                candidates = self._get_next_candidates_optuna(n_candidates)

            # 2. Submit jobs
            futures = set()
            for params_norm, optuna_trial in candidates:
                trial = self._propose_trial(params_norm, optuna_trial)
                
                if trial.status == "COMPLETED":
                    logger.debug(f"Skipping completed trial {trial.trial_id}")
                    continue
                if trial.status == "RUNNING":
                    logger.debug(f"Skipping running trial {trial.trial_id}")
                    continue
                
                trial.status = "RUNNING"
                self.launched_new_trials += 1
                fut = self._submit_job(trial, self.cfg.worker_budget)
                futures.add(fut)
                self.pending_jobs += 1
            
            if not futures:
                logger.warning("No new jobs submitted in this iteration.")
                continue
            
            # 3. Collect results
            try:
                if self.task_scheduler == "ray":
                    while futures:
                        done_refs, futures = ray.wait(list(futures), num_returns=1)
                        result = ray.get(done_refs[0])
                        self._process_result(result, use_bayesian)
                else:
                    for fut in as_completed(futures):
                        result = fut.result()
                        self._process_result(result, use_bayesian)
            
            except KeyboardInterrupt:
                logger.warning("Iteration interrupted by user.")
                self.close()
                break
            except Exception as e:
                logger.error(f"Error in job collection: {e}", exc_info=True)
                self.close()
                break

            # 4. Save checkpoint
            self._save_checkpoint()

            if self.best_trial:
                logger.info(f"Iter {it+1} complete. Best loss so far: {self.best_trial.best_loss:.4e}")
            else:
                logger.info(f"Iter {it+1} complete. No results yet.")

        # --- End of optimization ---
        logger.info("Optimization run finished.")
        if not self.best_trial:
            raise RuntimeError("Optimization failed to find any valid result.")

        # De-normalize best parameters
        best_params_natural = self.lows + self.best_trial.params_norm * self.param_scale
        for i in self.cfg.int_indices:
            best_params_natural[i] = int(round(best_params_natural[i]))

        # ==========================================================
        # Real Omega Metrics
        # ==========================================================
        
        logger.info("Running Omega Protocol post-run analysis...")
        all_trials = list(self.trials.values())
        
        if omega_analysis:
            real_cod = omega_analysis.calculate_cod(all_trials)
            real_cri = omega_analysis.calculate_cri(all_trials)
            logger.info(f"Analysis complete: COD={real_cod:.4f}, CRI={real_cri:.4f}")
        else:
            logger.warning("omega.analysis module not found. Returning 0.0 for metrics.")
            real_cod = 0.0
            real_cri = 0.0

        return OptResult(
            params=best_params_natural,
            objective_value=self.best_trial.best_loss,
            cod=real_cod,
            cri_score=real_cri,
            metadata={"trial_id": self.best_trial.trial_id}
        )
        # ==========================================================

    def _process_result(self, result: Tuple[str, int, float, Optional[str]], use_bayesian: bool):
        """Callback to handle a completed job."""
        self.pending_jobs -= 1
        try:
            trial_id, budget, loss, ckpt_path = result
            
            if trial_id not in self.trials:
                logger.warning(f"Received result for unknown trial {trial_id}")
                return
            
            trial = self.trials[trial_id]
            trial.status = "COMPLETED"
            trial.checkpoints.append((budget, loss))
            trial.last_loss = loss
            if ckpt_path:
                trial.last_checkpoint = ckpt_path

            # --- NEW: Report result to Optuna ---
            if use_bayesian and self.optuna_study:
                try:
                    self.optuna_study.tell(trial.optuna_trial_id, loss)
                except Exception as e:
                    logger.warning(f"Failed to .tell() Optuna for trial {trial_id}: {e}")
            # --- End Optuna ---
            
            if loss < np.inf:
                self.completed_trials_count += 1
                if self.best_trial is None or loss < self.best_trial.best_loss:
                    self.best_trial = trial
                    logger.info(f"New best trial: {trial_id} Loss: {loss:.4e}")
            else:
                logger.debug(f"Trial {trial_id} failed (loss=inf).")

        except Exception as e:
            logger.error(f"Error processing result: {e}", exc_info=True)
