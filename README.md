# Omega Protocol v2.6.5

Meta-Scrutiny and Scrutiny Protocol Implementation for AI reasoning systems. Provides structured frameworks for multi-agent scrutiny, meta-reasoning, and collaborative problem-solving.

## Overview

The Omega Protocol implements a hierarchical reasoning architecture:

- **Scrutiny Protocol v1.3**: Base layer for structured reasoning and critique
- **Meta-Scrutiny Protocol v1.3**: Higher-order reasoning about reasoning processes
- **PINN/TOE Workers**: Physics-informed neural network and Theory of Everything workers

## Components

```
OmegaProtocol_V2.6.5/
├── scrutiny-v1.3/          # Scrutiny protocol implementation
├── meta-scrutiny-v1.3/     # Meta-scrutiny protocol implementation
├── omega/                  # Core Omega protocol modules
├── docs/                   # Documentation
├── examples/               # Usage examples
├── pinn_worker.py          # Physics-informed neural network worker
├── toe_worker.py           # Theory of Everything worker
└── build.sh                # Build script
```

## Quick Start

```bash
# Install dependencies
pip install -e .[dev]

# Run build
./build.sh

# Run tests
pytest -v
```

## Configuration

See `.env.example` for required environment variables.

## Development

```bash
# Install dev dependencies
pip install -e .[dev]

# Lint
ruff check .
mypy .

# Test
pytest -v
```

## License

MIT License - see [LICENSE](LICENSE) for details.