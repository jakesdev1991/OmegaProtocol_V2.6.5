#!/usr/bin/env python3
"""
sim1.py - Example using UniversalOptimizer
"""
import sys
from pathlib import Path
try:
    import omega
except ImportError:
    project_root = Path(__file__).resolve().parent.parent
    sys.path.append(str(project_root))
    import omega

from omega.universal import UniversalOptimizer

def quadratic_worker(params: dict) -> float:
    x = params.get("x", 0.0)
    y = params.get("y", 0.0)
    import random
    val = (x - 3)**2 + (y + 2)**2 + random.uniform(-0.01, 0.01)
    return val

search_space = {
    "x": ( -10.0, 10.0 ),
    "y": ( -10.0, 10.0 )
}

def run_simulation():
    optimizer = UniversalOptimizer(optimizer="optuna", log_path="examples/sim1_log.json.gz")
    result = optimizer.optimize(worker_callable=quadratic_worker, search_space=search_space, n_iters=10, n_candidates_per_iter=10)
    print("Result:", result)

if __name__ == "__main__":
    run_simulation()