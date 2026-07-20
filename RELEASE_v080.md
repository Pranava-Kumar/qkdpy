# QKDpy v0.8.0 Release Notes

## Major Features

### 1. Density Matrix Module (`qkdpy.core.density_matrix`)

The density matrix module enables realistic simulation of mixed quantum states and noise processes.

**Key Features:**
- `DensityMatrix` class for representing mixed quantum states
- CPTP (Completely Positive Trace-Preserving) channel implementation
- Standard noise channels: depolarizing, amplitude damping, phase damping, bit flip, phase flip
- Quantum state metrics: purity, von Neumann entropy, fidelity, trace distance
- Partial trace for analyzing entangled subsystems

**Example Usage:**
```python
from qkdpy import DensityMatrix, Qubit
from qkdpy.core import depolarizing_channel

# Create a pure state
rho = DensityMatrix.from_pure(Qubit.plus())
print(f"Purity: {rho.purity():.4f}")  # 1.0

# Apply noise
kraus = depolarizing_channel(p=0.2)
rho_noisy = rho.apply_channel(kraus)
print(f"Noisy purity: {rho_noisy.purity():.4f}")  # < 1.0

# Compute fidelity
fid = rho.fidelity(rho_noisy)
print(f"Fidelity: {fid:.4f}")
```

**Use Cases:**
- Simulate realistic noise in quantum channels
- Analyze decoherence effects on QKD protocols
- Compute entanglement measures for multi-qubit systems
- Model thermal and dissipative processes

---

### 2. Quantum Circuit Model (`qkdpy.core.circuit`)

The circuit module provides a high-level interface for composing quantum operations.

**Key Features:**
- `Circuit` class for building quantum circuits
- Standard gates: H, X, Y, Z, S, T, Rx, Ry, Rz, CNOT, CZ, SWAP
- Custom gate support via unitary matrices
- Circuit composition and concatenation
- OpenQASM 2.0 export for interoperability
- Circuit analysis: depth, gate count, operation statistics

**Example Usage:**
```python
from qkdpy import Circuit

# Create a Bell state circuit
circuit = Circuit(2)
circuit.h(0)
circuit.cx(0, 1)

# Simulate
state = circuit.simulate()
print(f"Bell state: {state}")

# Analyze
print(f"Depth: {circuit.depth()}")
print(f"Operations: {circuit.count_ops()}")

# Export to QASM
qasm = circuit.to_qasm()
```

**Use Cases:**
- Intuitive quantum state preparation
- Compose complex quantum operations
- Interface with other quantum frameworks via QASM
- Analyze circuit complexity and depth

---

### 3. Secret Key Rate Calculator (`qkdpy.protocols.key_rate`)

The key rate calculator computes secure key rates for QKD protocols under various channel conditions.

**Key Features:**
- `SecretKeyRate` class with protocol-specific methods
- Supported protocols: BB84, Decoy-State BB84, E91, SARG04
- `ChannelParameters` and `DecoyStateParameters` dataclasses
- Automatic QBER estimation from physical parameters
- Maximum secure distance calculation
- Protocol comparison and optimization

**Example Usage:**
```python
from qkdpy import SecretKeyRate, ChannelParameters

# Define channel parameters
params = ChannelParameters(
    distance_km=50,
    channel_loss_db_km=0.2,
    detector_efficiency=0.6,
    dark_count_prob=1e-6,
    misalignment_error=0.02
)

# Calculate key rate
rate = SecretKeyRate.bb84(params)
print(f"BB84 key rate: {rate:.6f} bits/pulse")

# Compare protocols
rate_e91 = SecretKeyRate.e91(params)
rate_sarg04 = SecretKeyRate.sarg04(params)

# Find maximum distance
max_dist = SecretKeyRate.max_distance(
    protocol='bb84',
    channel_loss_db_km=0.2,
    detector_efficiency=0.6,
    dark_count_prob=1e-6,
    threshold_rate=1e-6
)
print(f"Max distance: {max_dist:.1f} km")
```

**Use Cases:**
- Protocol selection for specific channel conditions
- System parameter optimization
- Performance benchmarking
- Feasibility analysis for QKD deployments

---

## Integration Examples

### Noisy Circuit Simulation

```python
from qkdpy import Circuit, DensityMatrix
from qkdpy.core import depolarizing_channel

# Create circuit
circuit = Circuit(1)
circuit.h(0)

# Get statevector
state = circuit.simulate()

# Convert to density matrix
rho = DensityMatrix.from_pure(state)

# Apply noise
kraus = depolarizing_channel(0.1)
rho_noisy = rho.apply_channel(kraus)

# Analyze
print(f"Fidelity: {rho.fidelity(rho_noisy):.4f}")
```

### QKD Protocol Analysis

```python
from qkdpy import SecretKeyRate, DecoyStateParameters

# Optimize decoy-state parameters
best_rate = 0
best_mu = 0

for mu in [0.1, 0.3, 0.5, 0.7, 1.0]:
    params = DecoyStateParameters(
        distance_km=100,
        mean_photon_number=mu,
        # ... other parameters
    )
    rate = SecretKeyRate.decoy_bb84(params)
    if rate > best_rate:
        best_rate = rate
        best_mu = mu

print(f"Optimal μ: {best_mu}, Rate: {best_rate:.6f}")
```

---

## Migration Guide from v0.7.x

### New Imports

The following classes and functions are now available at the top level:

```python
from qkdpy import (
    Circuit,
    DensityMatrix,
    SecretKeyRate,
    ChannelParameters,
    DecoyStateParameters,
)

# CPTP channels
from qkdpy.core import (
    depolarizing_channel,
    amplitude_damping_channel,
    phase_damping_channel,
    bit_flip_channel,
    phase_flip_channel,
)
```

### API Changes

- **No breaking changes**: All v0.7.x APIs remain compatible
- **New modules**: All features are additive
- **Enhanced protocols**: Existing protocol classes can now use `Circuit` for state preparation

---

## Performance Characteristics

### Density Matrix Operations

- **Memory**: O(d²) where d is Hilbert space dimension
- **Time**: O(d³) for most operations (matrix multiplication)
- **Scalability**: Suitable for systems up to ~10 qubits

### Circuit Simulation

- **Memory**: O(2ⁿ) for n-qubit statevector
- **Time**: O(g × 2ⁿ) where g is number of gates
- **Scalability**: Suitable for circuits up to ~20 qubits

### Key Rate Calculation

- **Time**: O(1) for single calculation
- **Distance search**: O(log(d_max/tolerance))
- **Scalability**: Real-time computation for protocol optimization

---

## Testing

All new features include comprehensive test coverage:

```bash
# Run tests for new modules
pytest tests/test_density_matrix.py -v
pytest tests/test_circuit.py -v
pytest tests/test_secret_key_rate.py -v

# Run all tests
pytest tests/ -v
```

**Test Coverage:**
- 33 tests for density matrix operations
- 32 tests for circuit functionality
- 23 tests for key rate calculations
- **Total: 88 new tests, all passing**

---

## Documentation

- **API Reference**: See docstrings in source code
- **Examples**: `examples/v080_features_showcase.py`
- **Theory**: Inline comments explain quantum information concepts

---

## Future Work (v0.9.0)

Planned features for the next release:

1. **Finite-Key Security Analysis**: Composable security with finite block sizes
2. **Vectorized Protocol Execution**: 10-100× speedup for large simulations
3. **Enhanced LDPC Codes**: Standardized code constructions
4. **Interactive Jupyter Notebooks**: Educational materials
5. **Benchmarking Suite**: Standardized performance comparisons

---

## Contributors

Thanks to all contributors who made v0.8.0 possible!

---

## License

Apache License 2.0 - See LICENSE file for details.