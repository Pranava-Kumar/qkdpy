# QKDpy: Quantum Key Distribution Library

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/yourusername/qkdpy/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/qkdpy/actions/workflows/ci.yml)
[![Release](https://github.com/yourusername/qkdpy/actions/workflows/release.yml/badge.svg)](https://github.com/yourusername/qkdpy/actions/workflows/release.yml)
[![Documentation](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://qkdpy.readthedocs.io/)

QKDpy is a comprehensive Python library for Quantum Key Distribution (QKD) simulations, implementing various QKD protocols, quantum simulators, and cryptographic tools. It provides an intuitive API similar to NumPy, TensorFlow, and scikit-learn, making quantum cryptography accessible to developers and researchers.

## Features

- **Quantum Simulation**: Simulate qubits, quantum gates, and measurements
- **QKD Protocols**: Implementations of BB84, E91, SARG04, and more
- **Key Management**: Error correction and privacy amplification algorithms
- **Cryptographic Tools**: One-time pad encryption and authentication using quantum keys
- **Visualization**: Tools to visualize quantum states and protocol execution
- **Extensible Design**: Easy to add new protocols and features
- **Performance**: Efficient implementations for simulations

## Installation

QKDpy requires Python 3.10 or higher. We recommend using [uv](https://github.com/astral-sh/uv) for package management:

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone https://github.com/yourusername/qkdpy.git
cd qkdpy

# Install in development mode
uv pip install -e .

```
# Quick Start

Here's a simple example of using the BB84 protocol to generate a secure key:

```python
from qkdpy import BB84, QuantumChannel

# Create a quantum channel with some noise
channel = QuantumChannel(loss=0.1, noise_model='depolarizing', noise_level=0.05)

# Create a BB84 protocol instance
bb84 = BB84(channel, key_length=100)

# Execute the protocol
results = bb84.execute()

# Print the results
print(f"Generated key: {results['final_key']}")
print(f"QBER: {results['qber']:.4f}")
print(f"Is secure: {results['is_secure']}")
```
For more examples, see the examples directory.

## Contributing
We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License
QKDpy is licensed under the Apache License 2.0. See [LICENSE](LICENSE) for the full license text.

## Citation
If you use QKDpy in your research, please cite it as described in [CITATION.cff](CITATION.cff).

## Code of Conduct
This project adheres to the Contributor Covenant [code of conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Contact
For questions, suggestions, or issues, please open an [issue](https://github.com/yourusername/qkdpy/issues) on GitHub.
