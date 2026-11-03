# Installation

To install QKDpy, you can use pip or uv.

## Using uv (recommended)

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone https://github.com/Pranava-Kumar/qkdpy.git
cd qkdpy

# Create a virtual environment
uv venv

# Install in development mode
uv pip install -e .
```

## Using pip

```bash
# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e .
```

## Optional Extras

QKDpy provides several optional dependency groups for extended functionality:

```bash
# Development tools (testing, linting, documentation)
pip install qkdpy[dev]

# Machine learning components (scikit-learn, pandas)
pip install qkdpy[ml]

# Documentation dependencies
pip install qkdpy[docs]

# Visualization extras (seaborn)
pip install qkdpy[viz]

# Enterprise features (compliance, audit, software-simulation HSM)
pip install "qkdpy[enterprise]"

# Cirq quantum computing framework integration
pip install "qkdpy[cirq]"

# PennyLane quantum computing framework integration
pip install "qkdpy[pennylane]"

# Qiskit integration (noise models, transpilation)
pip install "qkdpy[qiskit]"

# QpiAI Quantum SDK integration
pip install "qkdpy[qpiai]"

# Common optional features (no external quantum SDKs)
pip install "qkdpy[ml,viz,enterprise]"
```

## Product Tiers

QKDpy uses a cumulative three-tier licensing model. By default, the FREE tier is active, which includes all QKD protocols, satellite simulation, ML integration, and advanced visualization.

To activate higher tiers, provide a license key (any non-empty string in demo
mode; signed keys are required when `QKDPY_LICENSE_ENFORCEMENT=1`):

```python
from qkdpy import QKDConfig, set_config

config = QKDConfig()
config.enterprise.product_tier = "enterprise"  # or "premium"
config.enterprise.license_key = "demo-key"
set_config(config)
```

You can also set `QKDPY_PRODUCT_TIER` / `QKDPY_LICENSE_KEY` in the environment
and then call `set_config(get_config())` to apply them.

See the [Product Tiers section in the README](https://github.com/Pranava-Kumar/qkdpy#-product-tiers) for a full feature comparison.

## Verify Installation

```bash
python -c "import qkdpy; print(qkdpy.__version__)"
```
