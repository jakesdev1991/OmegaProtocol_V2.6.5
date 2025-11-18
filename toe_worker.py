#!/usr/bin/env python3
import argparse
import time
import math
import traceback
import numpy as np

def worker_callable(params: dict) -> float:
    start_time = time.time()
    try:
        c1 = params.get("const_G_eff", 0.5)
        c2 = params.get("lambda_vac", 5.0)
        c3 = params.get("q_phi_decay", 0.1)
        x = (c1 - 0.5) * 10
        y = (c2 - 5.0)
        a = 20
        b = 0.2
        c = 2 * math.pi
        term1 = -a * math.exp(-b * math.sqrt(0.5 * (x**2 + y**2)))
        term2 = -math.exp(0.5 * (math.cos(c * x) + math.cos(c * y)))
        term3 = math.exp(c3)
        loss = term1 + term2 + a + math.exp(1) + term3
        time.sleep(0.01)
        if not np.isfinite(loss):
            loss = float('inf')
    except Exception as e:
        print(f"[toe_worker] FAILED: {e}\n{traceback.format_exc()}")
        loss = float('inf')
    end_time = time.time()
    print(f"  [toe_worker] Trial finished. Loss: {loss:.6f} [Time: {end_time - start_time:.2f}s]")
    return loss

def main():
    parser = argparse.ArgumentParser(description="Omega ToE Worker")
    parser.add_argument("--n-iters", type=int, default=20)
    parser.add_argument("--n-candidates", type=int, default=10)
    args = parser.parse_args()
    search_space = {
        "const_G_eff": type("P", (), {"param_type": "float", "low": 0.0, "high": 1.0})(),
        "lambda_vac": type("P", (), {"param_type": "float", "low": 0.0, "high": 10.0})(),
        "q_phi_decay": type("P", (), {"param_type": "float", "low": 0.0, "high": 1.0})()
    }
    from omega.universal import UniversalOptimizer
    optimizer = UniversalOptimizer(optimizer="quantum_phi", log_path="scrutiny-v1.2/toe_optimization_log.json.gz")
    result = optimizer.optimize(worker_callable=worker_callable, search_space=search_space, n_iters=args.n_iters, n_candidates_per_iter=args.n_candidates)
    print("=== ToE Optimization Complete ===")
    print(result)

if __name__ == "__main__":
    main()