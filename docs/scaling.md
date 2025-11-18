# Omega Protocol Scaling & Fidelity

This document outlines the known scaling properties and **fidelity limits** of the Omega Engine v2.3.

- **Sparse Graphs:** For graphs exceeding 10M nodes with < 0.001% density, the engine will switch to a bounded approximation (see Rule SD-1).
- **Time Budgets:** Optimization runs are subject to budgets (see Rule SD-4).
