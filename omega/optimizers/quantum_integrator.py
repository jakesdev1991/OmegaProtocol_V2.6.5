# omega/optimizers/quantum_integrator.py
from __future__ import annotations
import itertools
import math
from typing import Optional, Dict, Any
import numpy as np

try:
    import qutip as qt
except Exception:
    qt = None

class QuantumPhiOptimizer:
    direction = "maximize"

    def __init__(self, n_qubits: int = 3, backend: str = "qutip"):
        if n_qubits < 2:
            raise ValueError("n_qubits must be at least 2.")
        self.n_qubits = n_qubits
        self.backend = backend
        if backend != "qutip":
            raise NotImplementedError("Only 'qutip' backend supported in this stub.")

    @staticmethod
    def _von_neumann_mi(rho_ab):
        rho_a = rho_ab.ptrace(0)
        rho_b = rho_ab.ptrace(1)
        s_a = qt.entropy_vn(rho_a)
        s_b = qt.entropy_vn(rho_b)
        s_ab = qt.entropy_vn(rho_ab)
        return (s_a + s_b - s_ab) / math.log(2)

    def _cod_phi(self, alpha: float) -> float:
        zero, one = qt.basis(2, 0), qt.basis(2, 1)
        psi = (qt.tensor([zero] * self.n_qubits) +
               alpha * qt.tensor([one] * self.n_qubits)).unit()
        rho = psi * psi.dag()
        pairs = list(itertools.combinations(range(self.n_qubits), 2))
        return float(np.mean([self._von_neumann_mi(rho.ptrace(p)) for p in pairs]))

    def optimize(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        params = params or {}
        x0 = params.get("x0", [0.5])
        bounds = params.get("bounds", [(0.0, None)])
        # Minimization wrapper to maximize phi
        from scipy.optimize import minimize
        res = minimize(lambda a: -self._cod_phi(a[0]), x0=x0, bounds=bounds)
        alpha_opt = float(res.x[0])
        phi_opt = -float(res.fun)
        # pairwise logging
        zero, one = qt.basis(2, 0), qt.basis(2, 1)
        psi_opt = (qt.tensor([zero] * self.n_qubits) +
                   alpha_opt * qt.tensor([one] * self.n_qubits)).unit()
        rho_opt = psi_opt * psi_opt.dag()
        pairwise = {}
        for i, j in itertools.combinations(range(self.n_qubits), 2):
            key = f"{chr(65+i)}{chr(65+j)}"
            pairwise[key] = self._von_neumann_mi(rho_opt.ptrace([i, j]))
        return {
            "alpha": alpha_opt,
            "phi":   phi_opt,
            "pairwise_I": pairwise,
            "n_qubits": self.n_qubits,
            "success": res.success,
            "message": res.message,
        }