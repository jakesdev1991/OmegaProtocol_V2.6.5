#!/usr/bin/env python3
from __future__ import annotations
import argparse
import sys
import traceback
from pathlib import Path
from typing import Dict, Any
import numpy as np
import torch
import torch.nn as nn
from torch.optim.lr_scheduler import ExponentialLR
import time

# PINN model (compact)
class PINN(nn.Module):
    def __init__(self, width: int = 20, depth: int = 4, noise: float = 0.0):
        super().__init__()
        layers = [nn.Linear(2, width), nn.Tanh()]
        for _ in range(depth - 1):
            layers.extend([nn.Linear(width, width), nn.Tanh()])
        layers.append(nn.Linear(width, 1))
        self.net = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor, t: torch.Tensor) -> torch.Tensor:
        return self.net(torch.cat([x, t], dim=1))

NU = 0.01 / np.pi

def f(pinn: PINN, x: torch.Tensor, t: torch.Tensor) -> torch.Tensor:
    u = pinn(x, t)
    u_t = torch.autograd.grad(u, t, torch.ones_like(u), create_graph=True)[0]
    u_x = torch.autograd.grad(u, x, torch.ones_like(u), create_graph=True)[0]
    u_xx = torch.autograd.grad(u_x, x, torch.ones_like(u_x), create_graph=True)[0]
    return u_t + u * u_x - NU * u_xx

def train_model(params: dict, device: torch.device, n_adam_steps: int) -> float:
    width = params.get("width", 20)
    depth = params.get("depth", 4)
    lr = params.get("lr", 1e-3)
    gamma = params.get("gamma", 0.99)
    noise = params.get("noise", 0.0)
    pinn = PINN(width=width, depth=depth, noise=noise).to(device)
    optimizer = torch.optim.Adam(pinn.parameters(), lr=lr)
    scheduler = ExponentialLR(optimizer, gamma=gamma)
    x_ic = torch.linspace(-1, 1, 100).view(-1, 1).to(device)
    t_ic = torch.zeros_like(x_ic).to(device)
    u_ic = -torch.sin(np.pi * x_ic).to(device)
    t_bc = torch.linspace(0, 1, 100).view(-1, 1).to(device)
    x_bc_left = -torch.ones_like(t_bc).to(device)
    x_bc_right = torch.ones_like(t_bc).to(device)
    u_bc = torch.zeros_like(t_bc).to(device)
    x_col = (torch.rand(1000, 1) * 2 - 1).to(device).requires_grad_(True)
    t_col = torch.rand(1000, 1).to(device).requires_grad_(True)
    final_loss = float('inf')
    for step in range(n_adam_steps):
        optimizer.zero_grad()
        u_pred_ic = pinn(x_ic, t_ic)
        loss_ic = torch.mean((u_pred_ic - u_ic) ** 2)
        u_pred_bc_left = pinn(x_bc_left, t_bc)
        u_pred_bc_right = pinn(x_bc_right, t_bc)
        loss_bc = torch.mean((u_pred_bc_left - u_bc) ** 2) + \
                  torch.mean((u_pred_bc_right - u_bc) ** 2)
        f_pred = f(pinn, x_col, t_col)
        loss_f = torch.mean(f_pred ** 2)
        loss = loss_ic + loss_bc + loss_f
        loss.backward()
        optimizer.step()
        if step % 100 == 0:
            scheduler.step()
        if step == n_adam_steps - 1:
            final_loss = loss.item()
    return final_loss

WORKER_GLOBALS = {
    "device": torch.device("cpu"),
    "n_adam_steps": 2000
}

def worker_callable(params: Dict[str, Any]) -> float:
    global WORKER_GLOBALS
    start_time = time.time()
    print(f"  [pinn_worker] Trial starting. Params: {params}")
    try:
        final_loss = train_model(
            params=params,
            device=WORKER_GLOBALS["device"],
            n_adam_steps=WORKER_GLOBALS["n_adam_steps"]
        )
        if final_loss is None or not np.isfinite(final_loss):
            final_loss = float('inf')
    except Exception as e:
        print(f"  [pinn_worker] Trial FAILED with exception: {e}")
        traceback.print_exc(file=sys.stdout)
        final_loss = float('inf')
    end_time = time.time()
    print(f"  [pinn_worker] Trial finished. Loss: {final_loss:.6f} [Time: {end_time - start_time:.2f}s]")
    return final_loss

def main():
    parser = argparse.ArgumentParser(description="Omega PINN Worker Launcher")
    parser.add_argument("--n-iters", type=int, default=10, help="Number of optimization iterations")
    parser.add_argument("--n-candidates", type=int, default=8, help="Number of candidates per iteration")
    parser.add_argument("--adam-steps", type=int, default=2000, help="Number of Adam steps per trial")
    parser.add_argument("--cpu", action="store_true", help="Force use CPU")
    args = parser.parse_args()
    global WORKER_GLOBALS
    WORKER_GLOBALS["n_adam_steps"] = args.adam_steps
    if args.cpu or not torch.cuda.is_available():
        WORKER_GLOBALS["device"] = torch.device("cpu")
        print("=== Omega PINN Worker (CPU) ===")
    else:
        WORKER_GLOBALS["device"] = torch.device("cuda")
        print("=== Omega PINN Worker (CUDA) ===")
    search_space = {
        "width": type("P", (), {"param_type": "int", "low": 10, "high": 80})(),
        "depth": type("P", (), {"param_type": "int", "low": 2, "high": 10})(),
        "lr": type("P", (), {"param_type": "float", "low": 1e-5, "high": 1e-2, "log": True})(),
        "gamma": type("P", (), {"param_type": "float", "low": 0.9, "high": 0.999})()
    }
    from omega.universal import UniversalOptimizer
    optimizer = UniversalOptimizer(optimizer="optuna", log_path="scrutiny-v1.2/pinn_optimization_log.json.gz")
    result = optimizer.optimize(worker_callable=worker_callable, search_space=search_space, n_iters=args.n_iters, n_candidates_per_iter=args.n_candidates)
    print("=== Optimization Complete ===")
    print(result)

if __name__ == "__main__":
    main()