# Omega Protocol v2.6.5

This repository contains the Omega Protocol v2.6.5 core library,
two worker modules (PINN and ToE), and test/analysis suites.

Quick start (CPU):
1. python3 build_from_dump.py
2. ./build.sh install-cpu
3. source venv/bin/activate
4. ./build.sh run-pinn --n-iters 2 --n-candidates 2 --adam-steps 100

Tests:
- ./build.sh test