# Examples

## Advanced Protocol Usage

QKDpy supports advanced protocols and features:

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
```

## Density Matrix & Circuit

QKDpy provides a full density matrix simulation stack and quantum circuit composer for mixed-state simulations:

```python
from qkdpy.core.density_matrix import DensityMatrix, CPTPChannel

# Create a maximally mixed state of 2 qubits
rho = DensityMatrix.maximally_mixed(2)
print(f"Purity: {rho.purity():.4f}")          # 0.5 for maximally mixed
print(f"Entropy: {rho.entropy():.4f}")        # 1.0 for maximally mixed

# Partial trace: trace out the second qubit
reduced = DensityMatrix.partial_trace(rho, keep=[0], dims=[2, 2])
print(f"Reduced density matrix shape: {reduced.shape}")

# Apply a depolarizing channel
depolarized = DensityMatrix.depolarizing(rho, p=0.1)

# Apply an amplitude damping channel
amp_damped = DensityMatrix.amplitude_damping(rho, gamma=0.2)

# Fidelity comparison between two density matrices
fidelity = DensityMatrix.fidelity(depolarized, amp_damped)
print(f"Fidelity: {fidelity:.4f}")

# CPTP channel creation and composition
from qkdpy.core.cptp import KrausChannel

# Create a depolarizing channel via Kraus operators
kraus_ops = [
    [[1, 0], [0, 1]],    # Identity (probability 1-p)
    [[0, 1], [1, 0]],    # Pauli X
    [[0, -1j], [1j, 0]], # Pauli Y
    [[1, 0], [0, -1]],   # Pauli Z
]
channel = KrausChannel(kraus_ops)

# Compose channels: depolarizing then amplitude damping
composed = channel.compose(KrausChannel.from_kraus(...))

# Circuit composition and simulation
from qkdpy.core.circuit import Circuit

qc = Circuit(2)
qc.h(0).cx(0, 1)  # Create Bell state |00⟩ + |11⟩
qc.measure_all()
state = qc.simulate()
print(f"Circuit depth: {qc.depth()}")
print(f"Gate count: {qc.count_ops()}")

# Export circuit to OpenQASM 2.0
qasm_str = qc.to_qasm()
print(qasm_str)
```

## Secret Key Rate Computation

```python
from qkdpy.core.key_rate import SecretKeyRate

# Compute asymptotic secret key rate for BB84
skr = SecretKeyRate.bb84_asymptotic(qber=0.025)
print(f"Secret key rate: {skr:.4f} bits per signal")

# Compute with finite-size corrections
skr_finite = SecretKeyRate.bb84_finite_key(
    qber=0.025,
    n_signals=1_000_000,
    epsilon_sec=1e-9,
    epsilon_cor=1e-15,
)
print(f"Finite-key rate: {skr_finite:.4f} bits per signal")
```

## Observability & Instrumentation

Protocol executions are automatically instrumented with structured telemetry. You can also add custom instrumentation:

```python
from qkdpy.utils import OperationSpan, instrument

# Track execution time and emit structured events
with OperationSpan("custom.operation", protocol="BB84") as span:
    # ... your code ...
    span.set_metadata(qber=0.025, key_size=256)

# Decorate any function for automatic instrumentation
@instrument("ml.train")
def train_model(self, data):
    # Function is automatically wrapped in OperationSpan
    ...

# Record domain-specific events
from qkdpy.utils import record_protocol_execution, record_ml_training

record_protocol_execution(
    protocol_name="BB84",
    key_length=256,
    qber=0.025,
    final_key_size=192,
    is_secure=True,
    duration_ms=145.2,
)

record_ml_training(
    model_name="QKDPredictor",
    protocol="BB84",
    input_dim=10,
    training_samples=5000,
    training_time_ms=3200.5,
    final_loss=0.023,
    convergence_iterations=42,
)
```

## Enterprise Compliance Checking

Requires ENTERPRISE tier:

```python
import os
os.environ["QKDPY_PRODUCT_TIER"] = "enterprise"

from qkdpy.enterprise import (
    ConfigAudit,
    ComplianceStandard,
)

# Initialize config audit
checker = ConfigAudit()

# Run checks against multiple standards
report = checker.check_compliance([
    ComplianceStandard.ETSI_GS_QKD_014,
    ComplianceStandard.NIST_SP_800_57,
    ComplianceStandard.FIPS_140_2,
])

# Export reports in multiple formats
print(report.export_markdown())
html = report.export_html()  # Enterprise-gated feature

# Analyze results
print(f"Overall compliant: {report.overall_compliant}")
print(f"Passed: {report.passed_checks}/{report.passed_checks + report.failed_checks}")

for check in report.get_failed_checks():
    print(f"[{check.severity.upper()}] {check.check_id}: {check.requirement}")
    print(f"  → {check.recommendation}")
```

## Quantum-Safe Migration Toolkit

Requires PREMIUM tier:

```python
import os
os.environ["QKDPY_PRODUCT_TIER"] = "premium"

from qkdpy.enterprise.quantum_safe import (
    classic_enterprise_profile,
    generate_roadmap,
    QuantumSafeAssessment,
    CryptoAsset,
    CryptoAlgorithmType,
    QuantumResistance,
)

# Use the preset classic enterprise profile
inventory = classic_enterprise_profile()
print(f"Total cryptographic assets: {inventory.total_assets}")
print(f"Vulnerable to quantum attacks: {inventory.vulnerable_count}")
print(f"Overall risk score: {inventory.risk_score:.0%}")

# Generate a phased migration roadmap
roadmap = generate_roadmap(inventory)
summary = roadmap.get_summary()
print(f"Target completion: {summary['target_completion']}")
print(f"Migration steps: {summary['total_steps']}")

for step in roadmap.steps:
    print(f"  [{step.phase.value}] {step.title} - {step.estimated_effort}")

# Create a full assessment with recommendations
assessment = QuantumSafeAssessment(
    inventory=inventory,
    roadmap=roadmap,
)
assessment_dict = assessment.to_dict()
for rec in assessment_dict["recommendations"]:
    print(f"- {rec}")

# Build a custom inventory
from datetime import datetime, UTC

custom_inventory = CryptoInventoryReport(
    scanned_at=datetime.now(UTC),
    system_description="My Custom System",
    assets=[
        CryptoAsset(
            name="RSA-2048",
            algorithm_type=CryptoAlgorithmType.ASYMMETRIC,
            key_size_bits=2048,
            resistance=QuantumResistance.VULNERABLE,
            location="tls-certificates",
        ),
        CryptoAsset(
            name="AES-256",
            algorithm_type=CryptoAlgorithmType.SYMMETRIC,
            key_size_bits=256,
            resistance=QuantumResistance.SAFE,
            location="storage-encryption",
        ),
    ],
)
```

## Product Tier Gating

The licensing system gates features at runtime. Each tier is cumulative:

```python
from qkdpy.enterprise import (
    ProductTier,
    Feature,
    get_active_tier,
    set_active_tier,
    feature_available,
)

# Check current tier
print(f"Active tier: {get_active_tier().value}")

# Check feature availability
if feature_available(Feature.COMPLIANCE_REPORTING):
    print("Compliance reporting is available")

# Features raise LicenseError when called without the right tier
from qkdpy.enterprise import require_feature, LicenseError

@require_feature(Feature.QUANTUM_SAFE_MIGRATION)
def run_migration_assessment():
    ...

try:
    run_migration_assessment()
except LicenseError as e:
    print(f"License error: {e}")
```
