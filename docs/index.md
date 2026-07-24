# QKDpy Documentation

Welcome to the documentation for **QKDpy**, a Python library for **Quantum Key Distribution simulation** at the intersection of **Space Technology, Quantum Computing, AI/ML, and Enterprise Compliance**.

> **Status & Scope.** QKDpy is a *research / educational simulator*. It
> models QKD protocols, channels, and attacks with phenomenological
> approximations. It is **not** validated for securing real key material
> and **not** a hardened, standards-compliant codec. See the
> [Status & Scope section in the README](https://github.com/Pranava-Kumar/qkdpy#-status--scope)
> for the precise maturity level.

## Key Capabilities

| Domain | Features |
|--------|----------|
| **Satellite QKD** | Satellite-ground links, free-space optical channels, orbital mechanics, atmospheric modeling |
| **QKD Protocols** | 10+ protocols (BB84, E91, CV-QKD, HD-QKD, B92, SARG04, SixState, DI-QKD) |
| **Density Matrix** | Mixed-state simulation, partial trace, fidelity, entropy, purity, CPTP channels (depolarizing, amplitude damping, Kraus channel composition) |
| **Circuit Composer** | Quantum circuit construction, gate composition, Bell state preparation, OpenQASM 2.0 export, simulation |
| **Secret Key Rate** | Asymptotic and finite-size secret key rate computation for BB84 and other protocols |
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
adr_public/ADR-Public-01-product-tiers
adr_public/ADR-Public-02-observability
adr_public/ROADMAP-Public
```

## Architecture Decision Records

Design rationale for major architectural choices is captured in
[Architecture Decision Records](decisions/). Internal ADRs (not
compiled into the public site) document decisions that are primarily
relevant to maintainers and contributors.

| ADR | Subject |
|-----|---------|
| [ADR-001](decisions/ADR-001-product-tier-licensing.md) | Product tier licensing model |
| [ADR-002](decisions/ADR-002-observability-and-instrumentation.md) | Observability and instrumentation |
| [ADR-003](decisions/ADR-003-compliance-architecture.md) | Enterprise config audit architecture |
| [ADR-004](decisions/ADR-004-enterprise-hsm-is-software-simulation.md) | HSM is a software simulation |
| [ADR-005](decisions/ADR-005-core-quantum-simulation-stack.md) | Core quantum simulation stack |
| [ADR-006](decisions/ADR-006-protocol-execution-model.md) | Protocol execution model (template method) |

## Architecture & Diagrams

The diagrams below summarize how the library is organized — from the
high-level module breakdown through the protocol execution flow, the
core quantum stack, key management, network / satellite links, framework
integrations, the crypto & enterprise surface, the ML optimization
pipeline, and the end-to-end data flow.

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
