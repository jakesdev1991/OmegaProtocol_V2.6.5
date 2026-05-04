"""RCOD toy-model operators for semiclassical vacuum response.

This module mirrors the AQFT-inspired construction documented in
`docs/quantum_vacuum_engineering.tex` and provides numerically tractable
helpers for experimentation in the Omega Protocol codebase.
"""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class QEIBound:
    """Ford-Roman style QEI lower bound model.

    Attributes:
        C: Positive model constant.
        tau0: Characteristic sampling timescale.
    """

    C: float
    tau0: float

    def lower_bound(self) -> float:
        if self.C <= 0 or self.tau0 <= 0:
            raise ValueError("C and tau0 must be strictly positive.")
        return -self.C / (self.tau0**4)


def rcod_flux(grad_phi: np.ndarray, grad_phi_dagger: np.ndarray) -> np.ndarray:
    """Compute sigma_{mu nu} = i : d_[mu]phi^† d_[nu]phi : as an antisymmetric tensor.

    Inputs are 1D arrays representing gradient components in a local frame.
    """

    g1 = np.asarray(grad_phi, dtype=np.complex128)
    g2 = np.asarray(grad_phi_dagger, dtype=np.complex128)
    if g1.ndim != 1 or g2.ndim != 1 or g1.shape != g2.shape:
        raise ValueError("grad_phi and grad_phi_dagger must be equal-length 1D arrays.")

    outer = np.outer(g2, g1)
    antisym = 0.5 * (outer - outer.T)
    return 1j * antisym


def one_loop_vertex_factor(k: np.ndarray, q: np.ndarray) -> np.ndarray:
    """Return antisymmetric RCOD vertex k_[a](k+q)_[b] = 1/2(k_a q_b - k_b q_a)."""

    k = np.asarray(k, dtype=float)
    q = np.asarray(q, dtype=float)
    if k.shape != q.shape:
        raise ValueError("k and q must have the same shape.")
    return 0.5 * (np.outer(k, q) - np.outer(q, k))


def response_prefactor_norm(k: np.ndarray, q: np.ndarray) -> float:
    """A compact momentum-space proxy showing derivative coupling.

    The norm vanishes as q -> 0, encoding the no-DC-backreaction statement.
    """

    vertex = one_loop_vertex_factor(k, q)
    return float(np.linalg.norm(vertex, ord="fro"))


def induced_energy_density_from_pulse(
    b_t: np.ndarray,
    dt: float,
    coupling: float = 1.0,
) -> np.ndarray:
    """Compute a derivative-coupled toy response delta<T_00> proportional to d_t^2 B."""

    b_t = np.asarray(b_t, dtype=float)
    if b_t.ndim != 1 or b_t.size < 3:
        raise ValueError("b_t must be a 1D array with at least 3 samples.")
    if dt <= 0:
        raise ValueError("dt must be positive.")

    second = np.gradient(np.gradient(b_t, dt), dt)
    return coupling * second


def sampled_negative_energy(
    t: np.ndarray,
    energy_density: np.ndarray,
    tau0: float,
) -> float:
    """Integrate negative sampled energy with Gaussian sampling width tau0."""

    t = np.asarray(t, dtype=float)
    rho = np.asarray(energy_density, dtype=float)
    if t.shape != rho.shape:
        raise ValueError("t and energy_density must have matching shapes.")
    if tau0 <= 0:
        raise ValueError("tau0 must be positive.")

    f = np.exp(-(t**2) / (2.0 * tau0**2))
    f = f / np.sqrt(np.trapz(f**2, t))
    sampled = np.trapz(rho * f**2, t)
    return float(min(sampled, 0.0))


def qei_saturation_ratio(sampled_negative: float, bound: QEIBound) -> float:
    """Return ratio between magnitude of sampled negative energy and QEI limit.

    1.0 means exact saturation, <1.0 means below limit, >1.0 means violation.
    """

    lower = bound.lower_bound()
    if sampled_negative > 0:
        return 0.0
    return float(abs(sampled_negative) / abs(lower))
