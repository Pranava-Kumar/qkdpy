# QKDpy: Quantum Key Distribution Library

<div align="center">

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Documentation](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://qkdpy.readthedocs.io/)

**A production-grade Python library for Quantum Key Distribution at the intersection of Space Technology, Quantum Computing, and AI/ML**

[Features](#-features) • [Satellite QKD](#-satellite-qkd) • [ML Integration](#-ml-integration) • [Enterprise](#-enterprise-features) • [Quick Start](#-quick-start)

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

## 🔐 Enterprise Features

Production-ready security for enterprise deployments:

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

# Compliance checking (NIST, FIPS, ISO)
checker = ComplianceChecker([ComplianceStandard.NIST_SP_800_57])
report = checker.check_compliance()
print(report.export_markdown())
```

---

## 📦 Features

### Protocols

- **BB84** (Standard + Decoy-State)
- **E91** (Entanglement-based)
- **B92**, **SARG04**
- **CV-QKD** (Continuous-Variable)
- **Device-Independent QKD**
- **HD-QKD** (High-Dimensional)

### Infrastructure

- Structured exception hierarchy
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
uv pip install qkdpy[ml,enterprise]
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
