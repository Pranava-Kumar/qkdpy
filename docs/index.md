# QKDpy Documentation

Welcome to the documentation for **QKDpy**, a Python library for **Quantum Key Distribution simulation** at the intersection of **Space Technology, Quantum Computing, AI/ML, and Enterprise Compliance**.

> **Status & Scope.** QKDpy is a *research / educational simulator*. It
> models QKD protocols, channels, and attacks with phenomenological
> approximations. It is **not** validated for securing real key material
> and **not** a hardened, standards-compliant codec. See the
> [Status & Scope section in the README](https://github.com/Pranava-Kumar/qkdpy#-status--scope)
> for the precise maturity level and [](OPEN_CORE.md) for what ships
> FREE vs what is gated.

## Key Capabilities

| Domain | Features |
|--------|----------|
| **Satellite QKD** | Satellite-ground links, free-space optical channels, orbital mechanics, atmospheric modeling |
| **QKD Protocols** | 10+ protocols (BB84, E91, CV-QKD, HD-QKD, B92, SARG04, SixState, DI-QKD) |
| **AI/ML** | Bayesian optimization, neural network predictors, anomaly detection, adaptive protocols |
| **Enterprise** | Three-tier licensing (FREE/ENTERPRISE/PREMIUM), compliance checking, HSM integration, audit logging |
| **Observability** | Structured instrumentation via `OperationSpan`, `@instrument` decorator, domain-specific events |
| **Quantum-Safe** | Crypto inventory assessment, risk scoring, phased migration roadmap (PREMIUM) |

## Contents

```{toctree}
:maxdepth: 2
:caption: Contents:

installation
quickstart
api
examples
OPEN_CORE
NEXT_STEPS
```

## Architecture Decisions

```{toctree}
:maxdepth: 1
:caption: Architecture Decision Records:

decisions/ADR-001-product-tier-licensing
decisions/ADR-002-observability-and-instrumentation
decisions/ADR-003-compliance-architecture
decisions/ADR-004-enterprise-hsm-is-software-simulation
```

## Architecture & Diagrams

```{toctree}
:maxdepth: 1
:caption: Diagrams:

diagrams/01-high-level-architecture
diagrams/02-protocol-execution-flow
diagrams/03-core-quantum-stack
diagrams/04-key-management-pipeline
diagrams/05-network-satellite-qkd
diagrams/06-integration-layer
diagrams/07-crypto-enterprise
diagrams/08-ml-optimization
diagrams/09-data-flow
diagrams/10-api-surface
```

## Indices and tables

* {ref}`genindex`
* {ref}`modindex`
* {ref}`search`
