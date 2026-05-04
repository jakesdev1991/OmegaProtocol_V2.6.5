# Omega Protocol Scaling & Fidelity

This document outlines known scaling properties and **fidelity limits** for the
RCOD semiclassical toy model and optimizer framework.

## Semiclassical RCOD constraints

- **Derivative-only backreaction:** static (`q -> 0`) RCOD sourcing has vanishing
  response kernel prefactor in the toy 1-loop model.
- **Pulse requirement:** negative-energy excursions require time-localized pulses
  in the external field `B(t)`.
- **QEI bound tracking:** sampled negative energy is constrained by
  `-C / tau0^4`; code paths expose this through `QEIBound` and
  `qei_saturation_ratio`.

## Compute-side scaling

- **Sparse graphs:** for graphs exceeding 10M nodes with < 0.001% density,
  the engine switches to a bounded approximation (Rule SD-1).
- **Time budgets:** optimization runs remain budget-constrained (Rule SD-4).
