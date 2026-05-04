import numpy as np

from omega.physics.rcod import (
    QEIBound,
    one_loop_vertex_factor,
    qei_saturation_ratio,
    rcod_flux,
    response_prefactor_norm,
)


def test_rcod_flux_is_antisymmetric():
    g = np.array([1 + 0.2j, -0.5 + 0.1j, 0.3 - 0.7j, 0.4 + 0.9j])
    sigma = rcod_flux(g, np.conj(g))
    np.testing.assert_allclose(sigma + sigma.T, 0.0, atol=1e-12)


def test_vertex_vanishes_for_zero_momentum_transfer():
    k = np.array([0.8, -0.1, 0.3, 1.2])
    q = np.zeros(4)
    vertex = one_loop_vertex_factor(k, q)
    np.testing.assert_allclose(vertex, 0.0)
    assert response_prefactor_norm(k, q) == 0.0


def test_qei_ratio_is_unity_at_saturation():
    bound = QEIBound(C=2.0, tau0=0.5)
    sampled = bound.lower_bound()
    ratio = qei_saturation_ratio(sampled_negative=sampled, bound=bound)
    assert np.isclose(ratio, 1.0)
