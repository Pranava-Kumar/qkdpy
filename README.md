# QKDpy: Quantum Key Distribution Library

<div align="center">

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Documentation](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://qkdpy.readthedocs.io/)

**A production-grade Python library for Quantum Key Distribution at the intersection of Space Technology, Quantum Computing, AI/ML, and Enterprise Compliance**

[Features](#-features) • [Satellite QKD](#-satellite-qkd) • [ML Integration](#-ml-integration) • [Observability](#-observability--instrumentation) • [Product Tiers](#-product-tiers) • [Quantum-Safe Migration](#-quantum-safe-migration-toolkit) • [Quick Start](#-quick-start)

</div>

---

## 🌟 Highlights

| Domain                   | Capabilities                                                                               |
| ------------------------ | ------------------------------------------------------------------------------------------ |
| **🚀 Space Technology**  | Satellite-ground QKD, free-space optical channels, orbital mechanics, atmospheric modeling |
| **⚛️ Quantum Computing** | 10+ QKD protocols (BB84, E91, CV-QKD, HD-QKD), qubit/qudit simulation, entanglement        |
| **🤖 AI/ML**             | Bayesian optimization, neural network predictors, anomaly detection, adaptive protocols    |

---

## 🛰️ Satellite QKD

QKDpy includes a comprehensive **Satellite Quantum Key Distribution** module for simulating space-ground quantum links:

```python
from qkdpy.network import SatelliteQKD, AtmosphericProfile, OrbitType

# Create a LEO satellite QKD system
sat_qkd = SatelliteQKD(
    orbit_type=OrbitType.LEO,
    altitude_km=500,
    ground_station_lat=28.5,   # Cape Canaveral
    ground_station_lon=-80.6,
)

# Simulate a satellite pass with atmospheric effects
atmosphere = AtmosphericProfile(
    visibility_km=23.0,
    turbulence_cn2=1e-14,
    aerosol_optical_depth=0.1,
)

results = sat_qkd.simulate_pass(
    duration_seconds=300,
    atmosphere=atmosphere,
)

print(f"Total key bits: {results['total_key_bits']:,.0f}")
print(f"Peak elevation: {max(results['elevation_angles']):.1f}°")
```

**Features:**

- 🌍 **Orbital Mechanics**: LEO/MEO/GEO orbit simulation with realistic slant range
- 🌫️ **Atmospheric Effects**: Rayleigh/Mie scattering, turbulence (Fried parameter), clouds
- 📡 **Free-Space Optical Channel**: Geometric spreading, pointing loss, beam wandering
- 🧠 **ML Channel Prediction**: Train models to predict optimal transmission windows

---

## 🤖 ML Integration

Optimize QKD performance with built-in machine learning:

```python
from qkdpy import QKDOptimizer, EfficientQKDPredictor

# Bayesian optimization for protocol parameters
optimizer = QKDOptimizer("BB84")
results = optimizer.optimize_channel_parameters(
    {"loss": (0.0, 0.5), "noise_level": (0.0, 0.1)},
    objective_function,
    method="bayesian",  # or "genetic", "neural"
)

# Resource-efficient predictor for edge deployment
predictor = EfficientQKDPredictor(
    input_dim=5,
    max_memory_mb=128,  # Constrained for embedded systems
    enable_quantization=True,
    enable_pruning=True,
)
```

---

## 🔍 Observability & Instrumentation

QKDpy includes built-in structured observability for debugging, performance analysis, and operations telemetry:

```python
from qkdpy.utils import OperationSpan, instrument, record_protocol_execution

# Context manager for timing any block
with OperationSpan("protocol.execute", protocol="BB84") as span:
    result = protocol.run()
    span.set_metadata(qber=result.qber)

# Decorator for automatic instrumentation
@instrument("ml.train")
def train_model(self, data):
    ...

# One-shot event recording
record_protocol_execution(
    protocol_name="BB84",
    key_length=256,
    qber=0.025,
    final_key_size=192,
    is_secure=True,
    duration_ms=145.2,
)
```

**Features:**
- **OperationSpan** — Context manager with automatic duration tracking and structured start/complete/failure events
- **@instrument decorator** — One-line function instrumentation with argument metadata capture
- **record_* helpers** — Domain-specific events for protocol execution, ML training, and QBER diagnostics
- **structlog backend** — JSON output for log aggregation (ELK, Datadog) or pretty-printed console

---

## 🏷️ Product Tiers

QKDpy uses a cumulative three-tier licensing model. Each tier includes everything in the tiers below it.

### Tier Comparison

| Feature | FREE | ENTERPRISE | PREMIUM |
|---------|:----:|:----------:|:-------:|
| All QKD Protocols | ✅ | ✅ | ✅ |
| Satellite QKD Simulation | ✅ | ✅ | ✅ |
| ML Integration & Optimization | ✅ | ✅ | ✅ |
| Advanced Visualization | ✅ | ✅ | ✅ |
| **Compliance Reporting** (ETSI, NIST, FIPS, ISO) | — | ✅ | ✅ |
| **HSM Integration** (PKCS#11) | — | ✅ | ✅ |
| **Audit Logging** | — | ✅ | ✅ |
| **ML-Based Attack Detection** | — | ✅ | ✅ |
| **Key Escrow** | — | ✅ | ✅ |
| **Compliance HTML Export** | — | ✅ | ✅ |
| **Quantum-Safe Migration Toolkit** | — | — | ✅ |
| **Crypto Inventory Assessment** | — | — | ✅ |
| **Priority Support** | — | — | ✅ |

### Enterprise Suite

```python
from qkdpy.enterprise import (
    HSMInterface,
    AuditLogger,
    ComplianceChecker,
    ComplianceStandard,
)

# Hardware Security Module integration
hsm = get_hsm(provider=HSMProvider.SOFTWARE)  # or PKCS11
key_handle = hsm.generate_key("session_key", key_length=256)

# Tamper-evident audit logging
audit = AuditLogger(storage_path="audit.log")
audit.log_key_event(AuditEventType.KEY_GENERATED, "session_key")

# Compliance checking (NIST, FIPS, ISO, ETSI)
checker = ComplianceChecker([ComplianceStandard.NIST_SP_800_57])
report = checker.check_compliance()
print(report.export_markdown())
print(report.export_html())  # Enterprise-gated feature
```

Set your product tier via environment or config:

```python
import os
os.environ["QKDPY_PRODUCT_TIER"] = "enterprise"

from qkdpy import set_config
set_config(product_tier="enterprise")
```

### Compliance Standards Supported

| Standard | Description |
|----------|-------------|
| **ETSI GS QKD 014** | KME-SA Interface (key delivery, authentication, status) |
| **ETSI GS QKD 016** | Common Criteria Protection Profile (security target, audit) |
| **ISO/IEC 23837-1/2** | QKD Security Requirements (key length, QBER thresholds) |
| **NIST SP 800-57** | Key Management (key length, algorithm lifetime) |
| **FIPS 140-2/140-3** | Cryptographic Module (approved algorithms, module integrity) |
| **ISO 27001** | Information Security (access control, logging, crypto policy) |

---

## 🔐 Quantum-Safe Migration Toolkit

**PREMIUM-tier** toolkit for assessing and planning migration to quantum-resistant cryptography:

```python
from qkdpy.enterprise.quantum_safe import (
    classic_enterprise_profile,
    generate_roadmap,
    QuantumSafeAssessment,
)

# Generate a crypto inventory from a classic enterprise profile
inventory = classic_enterprise_profile()
print(f"Total assets: {inventory.total_assets}")
print(f"Risk score: {inventory.risk_score:.0%}")

# Generate a phased migration roadmap
roadmap = generate_roadmap(inventory)
summary = roadmap.get_summary()
print(f"Target completion: {summary['target_completion']}")
print(f"Total steps: {summary['total_steps']}")

# Full assessment with recommendations
assessment = QuantumSafeAssessment(
    inventory=inventory,
    roadmap=roadmap,
)
report = assessment.to_dict()
for rec in report["recommendations"]:
    print(f"- {rec}")
```

**Migration phases:** Assess → Plan → Pilot → Migrate → Verify

---

## 📦 Features

### Protocols

- **BB84** (Standard + Decoy-State)
- **E91** (Entanglement-based)
- **B92**, **SARG04**
- **CV-QKD** (Continuous-Variable)
- **Device-Independent QKD**
- **HD-QKD** (High-Dimensional)

### Enterprise

- **Product Tier Licensing** — FREE/ENTERPRISE/PREMIUM with cumulative features
- **Compliance Checking** — ETSI GS QKD 014/016, ISO/IEC 23837, NIST SP 800-57, FIPS 140-2, ISO 27001
- **HSM Integration** — PKCS#11 interface with software fallback
- **Audit Logging** — Tamper-evident, structured event logging
- **Quantum-Safe Migration** — Crypto inventory, risk assessment, phased migration roadmap
- **Key Escrow** — Secure key recovery for enterprise deployments

### Observability

- **OperationSpan** — Context manager for timed, structured operation tracking
- **@instrument decorator** — One-line function instrumentation
- **Domain-specific events** — Protocol execution, ML training, QBER diagnostics
- **structlog backend** — JSON or console output
- **Correlation IDs** — Trace operations across components

### Infrastructure

- Structured exception hierarchy (`QKDException`)
- Centralized configuration management
- Structured logging with `structlog`
- Input validation decorators
- Type-safe (strict `mypy`)

---

## 🚀 Quick Start

```bash
# Install with uv (recommended)
pip install uv
uv pip install qkdpy

# Or with optional features
uv pip install qkdpy[ml]           # ML optimization
uv pip install qkdpy[enterprise]   # Enterprise features
uv pip install qkdpy[all]          # Everything
```

```python
from qkdpy import BB84, QuantumChannel

# Create channel and protocol
channel = QuantumChannel(loss=0.1, noise_model='depolarizing', noise_level=0.02)
bb84 = BB84(channel, key_length=256)

# Execute protocol
results = bb84.execute()
print(f"Key: {results['final_key'][:32]}...")
print(f"QBER: {results['qber']:.2%}")
print(f"Secure: {results['is_secure']}")
```

---

## 📐 Architecture Decisions

Key technical decisions are captured as Architecture Decision Records (ADRs):

| ADR | Decision |
|-----|----------|
| [ADR-001](docs/decisions/ADR-001-product-tier-licensing.md) | Product Tier Licensing Model (FREE/ENTERPRISE/PREMIUM) |
| [ADR-002](docs/decisions/ADR-002-observability-and-instrumentation.md) | Observability via structlog + OperationSpan |
| [ADR-003](docs/decisions/ADR-003-compliance-architecture.md) | Pluggable Compliance Checker Architecture |

---

## 🎯 Career Relevance

This library demonstrates expertise at the intersection of:

| Space Technology             | Quantum Computing            | AI/ML                     |
| ---------------------------- | ---------------------------- | ------------------------- |
| Satellite orbital mechanics  | Qubit/qudit state simulation | Bayesian optimization     |
| Free-space optical links     | QKD protocol implementation  | Neural network prediction |
| Atmospheric channel modeling | Entanglement distribution    | Anomaly detection         |
| Ground station networks      | Error correction codes       | Adaptive parameter tuning |

**Real-world applications:**

- 🛰️ Quantum satellite missions (like China's Micius)
- 🏦 Enterprise quantum-safe communications
- 🔬 Research in quantum networks

---

## 📄 License

Apache License 2.0 - See [LICENSE](LICENSE)

## 👤 Author

**Pranava Kumar** - Quantum Computing & Space Technology Enthusiast

---

<div align="center">

_Building the future of secure space communications through quantum technology_

</div>
