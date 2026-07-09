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

# The execution is automatically instrumented with:
# - OperationSpan tracing (duration, success/failure)
# - QBER diagnostics (warning if QBER approaches threshold)
# - Protocol execution event recording
```

## Enterprise Quick Start

To use enterprise features (requires ENTERPRISE or PREMIUM tier):

```bash
pip install qkdpy[enterprise]
export QKDPY_PRODUCT_TIER=enterprise
```

```python
from qkdpy.enterprise import ComplianceChecker, ComplianceStandard

# Run compliance checks against industry standards
checker = ComplianceChecker()
report = checker.check_compliance(
    [ComplianceStandard.ETSI_GS_QKD_014,
     ComplianceStandard.NIST_SP_800_57]
)

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
