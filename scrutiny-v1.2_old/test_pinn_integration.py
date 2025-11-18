import pytest
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
import pinn_worker

import torch

TEST_PARAMS = {
    "width": 10,
    "depth": 2,
    "lr": 1e-4,
    "gamma": 0.9
}
TEST_ADAM_STEPS = 5
DEVICE = torch.device("cpu")

@pytest.fixture(scope="module")
def setup_worker():
    pinn_worker.WORKER_GLOBALS["device"] = DEVICE
    pinn_worker.WORKER_GLOBALS["n_adam_steps"] = TEST_ADAM_STEPS

def test_pinn_train_model(setup_worker):
    loss = pinn_worker.train_model(
        params=TEST_PARAMS,
        device=DEVICE,
        n_adam_steps=TEST_ADAM_STEPS
    )
    assert loss is not None
    assert loss != float('inf')
    assert loss > 0.0

def test_pinn_worker_callable(setup_worker):
    loss = pinn_worker.worker_callable(TEST_PARAMS)
    assert loss is not None
    assert loss != float('inf')
    assert loss > 0.0

def test_pinn_optimizer_integration(setup_worker):
    from omega.types import FloatParameter, IntParameter
    search_space = {
        "width": type("P", (), {"param_type": "int", "low": 10, "high": 10})(),
        "depth": type("P", (), {"param_type": "int", "low": 2, "high": 2})(),
        "lr": type("P", (), {"param_type": "float", "low": 1e-4, "high": 1e-4})(),
        "gamma": type("P", (), {"param_type": "float", "low": 0.9, "high": 0.9})()
    }
    from omega.universal import UniversalOptimizer
    optimizer = UniversalOptimizer(optimizer="optuna")
    result = optimizer.optimize(worker_callable=pinn_worker.worker_callable, search_space=search_space, n_iters=1, n_candidates_per_iter=1)
    assert result["best_value"] is not None