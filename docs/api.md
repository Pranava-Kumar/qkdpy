# API Reference

This page describes the **public API surface** of QKDpy — the objects
and entry points you interact with. It is intentionally a usage
reference, not a source dump; full source lives on
[GitHub](https://github.com/Pranava-Kumar/qkdpy) where you can
read, fork, and contribute.

All examples assume a quantum channel has been constructed first:

```python
from qkdpy import QuantumChannel

channel = QuantumChannel(
    loss=0.1,
    noise_model="depolarizing",
    noise_level=0.02,
)
```

## Protocols

QKDpy ships 10+ QKD protocols under `qkdpy` top-level imports:

| Protocol | Import | Typical use |
|----------|---------|--------------|
| BB84 | `from qkdpy import BB84` | Standard prepare-and-measure over a channel |
| Decoy-State BB84 | `from qkdpy.protocols import DecoyStateBB84` | Photon-number-splitting resistant variant |
| B92 | `from qkdpy.protocols import B92` | Two-state minimal protocol |
| SARG04 | `from qkdpy.protocols import SARG04` | Four-state variant with stronger basis guarantee |
| E91 | `from qkdpy.protocols import E91` | Entanglement-based (Bell-pair) protocol |
| Six-State | `from qkdpy.protocols import SixState` | Three-basis protocol, tighter QBER bound |
| CV-QKD | `from qkdpy.protocols import CVQKD` | Continuous-variable Gaussian protocol |
| Enhanced CV-QKD | `from qkdpy.protocols import EnhancedCVQKD` | Reconciliation-enhanced CV variant |
| HD-QKD | `from qkdpy.protocols import HDQKD` | High-dimensional qudit protocol |
| MDI-QKD | `from qkdpy.protocols import MDIQKD` | Measurement-device-independent |
| DI-QKD | `from qkdpy.protocols import DIQKD` | Device-independent (self-testing) |

### Running a protocol

Every protocol follows the same template:

```python
from qkdpy import BB84

bb84 = BB84(channel, key_length=256)
result = bb84.execute()

print(result["final_key"][:32])   # shared key (hex string)
print(f"QBER: {result['qber']:.2%}")  # quantum bit error rate
print(f"Secure: {result['is_secure']}")  # boolean abort decision
```

The result mapping always contains at least: `final_key`,
`qber`, `is_secure`, `sifted_key`, and protocol-specific
extras (e.g. `secret_key_rate` for CV-QKD).

## Core Quantum Stack

`qkdpy.core` provides the simulation primitives:

- `Qubit` / `Qudit` — statevector containers with gate application,
  measurement, and partial trace.
- `MultiQubitState` — n-qubit registers with entanglement
  entropy and GHZ / W preparation.
- `QuantumGate` — the standard gate set (Pauli, Hadamard,
  rotation, CNOT, CZ, SWAP, ...).
- `QuantumChannel` — loss, depolarizing / bit-flip / phase-flip /
  amplitude-damping / dephasing noise, plus an eavesdropper hook.
- `Measurement` — basis measurement, tomography, fidelity, purity,
  entanglement-witness helpers.

## Key Management

`qkdpy.key_management` turns sifted key material into a
shared secret:

- `ErrorCorrection` — Cascade, Winnow, LDPC, BCH, Reed-Solomon
  reconciliation (matching the documented backend set).
- `PrivacyAmplification` — universal hashing, Toeplitz, cryptographic
  hash, Bennett-Brassard, AES.
- `KeyDistillation` / `QuantumKeyManager` — orchestration of the
  sift → correct → amplify pipeline.

```python
from qkdpy.key_management import QuantumKeyManager

manager = QuantumKeyManager()
secure_key = manager.distill(sifted_key, qber=result["qber"])
```

## Crypto

`qkdpy.crypto` provides algorithm building blocks (one-time pad,
quantum-grade random, authentication, side-channel protection, quantum
hash, zero-knowledge proof) used by the key-management and
protocol layers. These are research-grade implementations, not a
substitute for a validated cryptographic module.

## Network & Satellite QKD

`qkdpy.network` covers multi-party routing and satellite-ground
simulation:

```python
from qkdpy.network import SatelliteQKD, AtmosphericProfile, OrbitType

sat = SatelliteQKD(orbit_type=OrbitType.LEO, altitude_km=500)
atmosphere = AtmosphericProfile(visibility_km=23.0, turbulence_cn2=1e-14)
report = sat.simulate_pass(duration_seconds=300, atmosphere=atmosphere)
```

`hufnagel_valley_cn2`, `von_karman_spectrum`, `fried_parameter`,
`rytov_variance`, `scintillation_index`, `modtran_band_transmittance`,
and `background_stray_count_rate` expose the atmospheric helpers.

## ML Optimization

`qkdpy.ml` tunes protocol / channel parameters:

```python
from qkdpy import QKDOptimizer, EfficientQKDPredictor

optimizer = QKDOptimizer("BB84")
study = optimizer.optimize_channel_parameters(
    {"loss": (0.0, 0.5), "noise_level": (0.0, 0.1)},
    objective_fn,
    method="bayesian",
)
```

`EfficientQKDPredictor` offers quantization / pruning for edge
deployment.

## Enterprise Features

A subset of capabilities is gated behind the ENTERPRISE and
PREMIUM product tiers. With a valid license, `qkdpy.enterprise`
exposes:

- `HSMInterface` — PKCS#11 key generation / storage (software or
  hardware HSM).
- `AuditLogger` — tamper-evident event log.
- `ComplianceChecker` / `ComplianceStandard` — automated checks
  against ETSI GS QKD 014 / 016, ISO/IEC 23837-1/2, NIST
  SP 800-57, FIPS 140-2/140-3, ISO 27001.
- `quantum_safe` toolkit — `classic_enterprise_profile()`,
  `generate_roadmap()`, `QuantumSafeAssessment` for phased
  post-quantum migration planning.

See the README's Product Tiers section for the full matrix and how
to activate a tier at runtime.

## Observability

`qkdpy.utils` instruments the library without changing your code:

```python
from qkdpy.utils import OperationSpan, instrument, record_protocol_execution

with OperationSpan("protocol.execute", protocol="BB84") as span:
    result = bb84.execute()
    span.set_metadata(qber=result["qber"])
```

`OperationSpan`, the `@instrument` decorator, and the
`record_*` helpers emit structured events through a `structlog`
backend (JSON for aggregation, or pretty console output).
