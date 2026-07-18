# Product Tier Model — Public Overview

**Date:** 2026-07-18
**Status:** Active

## Context

QKDpy is distributed as a permissively-licensed open-source library
(Apache-2.0) so the research and education community can use,
study, and extend it freely. At the same time, organizations that
need compliance tooling, audit trails, and migration planning require
capabilities that go beyond what an open-source release is meant to
carry.

## Decision

The library ships with a single, cumulative three-tier model:

| Tier | Audience | Distribution |
|------|----------|--------------|
| **FREE** | Researchers, students, educators, open-source users | Apache-2.0 |
| **ENTERPRISE** | Companies running internal QKD modeling, compliance & audit teams, labs | Commercial license |
| **PREMIUM** | Vendors, large research consortia | Commercial license + support agreement |

- The default experience on import is **FREE**.
- Each higher tier **includes** everything in the tiers below it.
- Enterprise / Premium activation is a **runtime** switch; the same
  wheel serves all tiers.
- Opt-in license verification is available for deployments that want
  to enforce entitlement; without it the gate remains informational.

## Consequences

- Open-source users get the full simulation core, all protocols,
  satellite modeling, ML optimization, and visualizations at no cost.
- Enterprise customers gain compliance automation, HSM integration,
  and audit logging under a separate commercial agreement.
- Premium customers additionally receive the quantum-safe migration
  toolkit and priority support.

## Public capabilities by tier

| Capability | FREE | ENTERPRISE | PREMIUM |
|------------|:----:|:----------:|:-------:|
| All QKD protocols | Yes | Yes | Yes |
| Satellite QKD simulation | Yes | Yes | Yes |
| ML optimization | Yes | Yes | Yes |
| Compliance reporting (ETSI / NIST / FIPS / ISO) | — | Yes | Yes |
| HSM integration (PKCS#11) | — | Yes | Yes |
| Audit logging | — | Yes | Yes |
| ML-based attack detection | — | Yes | Yes |
| Key escrow | — | Yes | Yes |
| Quantum-safe migration toolkit | — | — | Yes |
| Crypto inventory assessment | — | — | Yes |
| Priority support | — | — | Yes |

See the README's Product Tiers section for the authoritative matrix and
runtime activation instructions.
