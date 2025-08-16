# QKDpy: Quantum Key Distribution Library

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/yourusername/qkdpy/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/qkdpy/actions/workflows/ci.yml)
[![Release](https://github.com/yourusername/qkdpy/actions/workflows/release.yml/badge.svg)](https://github.com/yourusername/qkdpy/actions/workflows/release.yml)
[![Documentation](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://qkdpy.readthedocs.io/)

QKDpy is a comprehensive Python library for Quantum Key Distribution (QKD) simulations, implementing various QKD protocols, quantum simulators, and cryptographic tools. It provides an intuitive API similar to NumPy, TensorFlow, and scikit-learn, making quantum cryptography accessible to developers and researchers.

## Features

- **Quantum Simulation**: Simulate qubits, quantum gates (now with individual gate classes for better modularity), multi-qubit states, and measurements (with flexible state collapse for research and visualization)
- **QKD Protocols**: Implementations of BB84, E92, E91, SARG04, CV-QKD, Device-Independent QKD, HD-QKD, and more
- **High-Dimensional QKD**: Support for qudit-based protocols with enhanced security and key rates
- **Key Management**: Advanced error correction and privacy amplification algorithms
- **Quantum Cryptography**: Quantum authentication, key exchange, and random number generation
- **Enhanced Security**: Message authentication, key validation, and side-channel protection
- **Machine Learning Integration**: Optimization and anomaly detection for QKD systems
- **Quantum Networks**: Multi-party QKD and network simulation capabilities
- **Visualization**: Advanced tools to visualize quantum states and protocol execution
- **Quantum Network Analysis**: Tools for analyzing quantum networks and multi-party QKD
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

## Quick Start

Here's a simple example of using the BB84 protocol to generate a secure key:

```python
from qkdpy import BB84, QuantumChannel, Qubit
from qkdpy.core import PauliX, Hadamard # Import individual gate classes

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

# Example of flexible qubit measurement and collapse
q = Qubit.plus() # Qubit in superposition
print(f"Qubit state before measurement: {q.state}")
measurement_result = q.measure("hadamard") # Measure without collapsing internal state
print(f"Measurement result: {measurement_result}")
print(f"Qubit state after measurement (still in superposition): {q.state}")
q.collapse_state(measurement_result, "hadamard") # Explicitly collapse the state
print(f"Qubit state after explicit collapse: {q.state}")

# Example of applying a gate
q_zero = Qubit.zero()
print(f"Qubit state before X gate: {q_zero.state}")
q_zero.apply_gate(PauliX().matrix) # Apply Pauli-X gate
print(f"Qubit state after X gate: {q_zero.state}")
```

For High-Dimensional QKD:

```python
from qkdpy import HDQKD, QuantumChannel

# Create a quantum channel with some noise
channel = QuantumChannel(loss=0.1, noise_model='depolarizing', noise_level=0.05)

# Create an HD-QKD protocol instance with 4-dimensional qudits
hd_qkd = HDQKD(channel, key_length=100, dimension=4)

# Execute the protocol
results = hd_qkd.execute()

# Print the results
print(f"Generated key: {results['final_key']}")
print(f"QBER: {results['qber']:.4f}")
print(f"Is secure: {results['is_secure']}")
print(f"Dimensional efficiency gain: {hd_qkd.get_dimension_efficiency():.2f}x")
```

For more examples, see the examples directory.

## Advanced Usage

QKDpy also supports advanced protocols and features:

```python
from qkdpy import (
    DeviceIndependentQKD,
    QuantumKeyManager,
    QuantumRandomNumberGenerator,
    QuantumNetwork,
    HDQKD,
    QKDOptimizer
)

# Device-independent QKD
di_qkd = DeviceIndependentQKD(channel, key_length=100)
results = di_qkd.execute()

# Quantum key management
key_manager = QuantumKeyManager(channel)
key_id = key_manager.generate_key("secure_session", key_length=128)

# Quantum random number generation
qrng = QuantumRandomNumberGenerator(channel)
random_bits = qrng.generate_random_bits(100)

# Quantum network simulation
network = QuantumNetwork("Research Network")
network.add_node("Alice")
network.add_node("Bob")
network.add_connection("Alice", "Bob", channel)
key = network.establish_key_between_nodes("Alice", "Bob", 128)

# High-dimensional QKD
hd_qkd = HDQKD(channel, key_length=100, dimension=4)
hd_results = hd_qkd.execute()

# ML-based QKD optimization
optimizer = QKDOptimizer("BB84")
parameter_space = {
    "loss": (0.0, 0.5),
    "noise_level": (0.0, 0.1)
}
# optimization_results = optimizer.optimize_channel_parameters(
#     parameter_space,
#     lambda params: simulate_protocol_performance(params),
#     num_iterations=50
# )
```

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
