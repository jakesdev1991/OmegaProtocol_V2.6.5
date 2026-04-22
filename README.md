# Omega Protocol v2.6.5

Omega Protocol now includes an explicit **semiclassical RCOD toy model** matching the
paper in `docs/quantum_vacuum_engineering.tex`.

## What's included

- AQFT-inspired RCOD flux operator utilities in `omega/physics/rcod.py`.
- 1-loop derivative-coupling momentum-space helpers (`one_loop_vertex_factor`).
- Semiclassical negative-energy pulse helpers with QEI lower-bound accounting.
- Legacy optimizer + scrutiny suites.

## Quick start (CPU)

1. `python3 -m venv venv`
2. `source venv/bin/activate`
3. `pip install -e .[dev]`
4. `pytest scrutiny-v1.3 meta-scrutiny-v1.3 -q`

## RCOD mini example

```python
import numpy as np
from omega.physics.rcod import (
    QEIBound,
    induced_energy_density_from_pulse,
    qei_saturation_ratio,
    sampled_negative_energy,
)

t = np.linspace(-2.0, 2.0, 2001)
dt = t[1] - t[0]
tau0 = 0.25
B = np.exp(-(t**2) / (2*tau0**2))
rho = induced_energy_density_from_pulse(B, dt, coupling=1.0)
neg = sampled_negative_energy(t, rho, tau0=tau0)
ratio = qei_saturation_ratio(neg, QEIBound(C=1.0, tau0=tau0))
print("QEI saturation ratio:", ratio)
```
