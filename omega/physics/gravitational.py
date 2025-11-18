import numpy as np

def gw_chirp(t, f0=35, chirp_mass=30, distance=100, tc_offset=0.01):
    tc = t[-1] + tc_offset
    tau = tc - t
    if t.shape[0] < 2:
        tau0 = tc - t[0]
    else:
        tau0 = tc - t[0]
    tau = np.clip(tau, 1e-9, None)
    f = f0 * (tau0 / tau)**(3/8.0)
    const_phase = 2 * np.pi * f0 * tau0**(5/8.0) * (8.0/5.0)
    phi = - const_phase * (tau / tau0)**(5/8.0)
    amp = (chirp_mass / distance) * (f / f0)**(2/3.0)
    h_plus = amp * np.cos(phi)
    return t, h_plus, f
