# Quick Start

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

# Measurement collapses the qubit state to the measured outcome
q = Qubit.plus() # Qubit in superposition
print(f"Qubit state before measurement: {q.state}")
measurement_result = q.measure("hadamard") # Collapses the internal state
print(f"Measurement result: {measurement_result}")
print(f"Qubit state after measurement (collapsed): {q.state}")

# Example of applying a gate
q_zero = Qubit.zero()
print(f"Qubit state before X gate: {q_zero.state}")
q_zero.apply_gate(PauliX().matrix) # Apply Pauli-X gate
print(f"Qubit state after X gate: {q_zero.state}")
```

## Density Matrix & Circuit

```python
# Density matrix: mixed state simulation
from qkdpy.core.density_matrix import DensityMatrix, depolarizing_channel

# Create a maximally mixed state
rho = DensityMatrix.maximally_mixed(2)
print(f"Purity: {rho.purity():.4f}")          # 0.5 for maximally mixed
print(f"Entropy: {rho.entropy():.4f}")        # 1.0 for maximally mixed

# Apply a depolarizing channel
depolarized = rho.apply_channel(depolarizing_channel(p=0.1))

# Compute fidelity with an ideal state
fidelity = DensityMatrix.fidelity(depolarized, rho)

# Circuit composition
from qkdpy.core.circuit import Circuit

qc = Circuit(2)
qc.h(0).cx(0, 1)  # Create Bell state
qc.measure_all()
state = qc.simulate()  # statevector before measurement; measurements are skipped
print(f"State: {state}")
print(f"Circuit depth: {qc.depth()}")
print(f"Gate count: {qc.count_ops()}")
```

For High-Dimensional QKD:

```python
from qkdpy import HDQKD, QuantumChannel

# Create a quantum channel with some noise
channel = QuantumChannel(loss=0.1, noise_model='depolarizing', noise_level=0.05)

# Create an HD-QKD protocol instance with 5-dimensional qudits.
# Full mutually-unbiased-basis security holds for prime dimensions.
hd_qkd = HDQKD(channel, key_length=100, dimension=5)

# Execute the protocol
results = hd_qkd.execute()

# Print the results
print(f"Generated key: {results['final_key']}")
print(f"QBER: {results['qber']:.4f}")
print(f"Is secure: {results['is_secure']}")

# The execution is automatically instrumented with:
# - OperationSpan tracing (duration, success/failure)
# - QBER diagnostics (warning if QBER approaches threshold)
# - Protocol execution event recording
```

## Enterprise Quick Start

To use enterprise features:

```bash
pip install "qkdpy[enterprise]"
```

```python
from qkdpy.enterprise import ConfigAudit, ComplianceStandard

# Run a config audit against industry standards
checker = ConfigAudit(
    [ComplianceStandard.ETSI_GS_QKD_014, ComplianceStandard.NIST_SP_800_57]
)
report = checker.check_compliance()

print(report.export_markdown())

# Check overall compliance status
if report.overall_compliant:
    print("All checks passed!")
else:
    print(f"Failed checks: {report.failed_checks}")
    for check in report.get_failed_checks():
        print(f"  - [{check.severity}] {check.requirement}")
        print(f"    Recommendation: {check.recommendation}")
```

See the [examples](examples.md) page for more advanced usage including the quantum-safe migration toolkit and observability features.
