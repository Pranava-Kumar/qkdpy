# Open-Core Layout & Repository Audit

This document (1) defines what stays FREE vs. what's gated behind ENTERPRISE/PREMIUM for the open-core distribution, and (2) tracks a manual audit of the repository's content so we know exactly what's shipped, what's internal, and what's planned for the next phase.

---

## 1. Open-core layout

The library is intentionally split into a permissive-licensed free core and a commercial enterprise/premium tier. The split is governed by code at `src/qkdpy/enterprise/licensing.py` (`ProductTier`, `Feature`, `set_active_tier`).

### 1.1 Tier model — `ProductTier`

| Tier | Audience | Distribution |
|------|----------|--------------|
| **FREE** | Open-source community, researchers, students, teachers | Apache-2.0 (`LICENSE`) |
| **ENTERPRISE** | Companies running internal QKD modeling, compliance teams, labs | Commercial license (contact) |
| **PREMIUM** | Vendors, large-scale research consortia | Commercial license + service-level agreement |

The default tier when the library is imported is `FREE`. Activation of non-FREE tiers is purely a *runtime demo gate* by default; opt-in key verification is available via `QKDPY_LICENSE_ENFORCEMENT=1` + `QKDPY_LICENSE_SECRET` (see v0.6.6 changelog).

### 1.2 What lands where — feature matrix

Based on the `Feature` enum and the modules in `src/qkdpy/`:

#### Always FREE (Apache-2.0)
- **Core quantum stack** (`qkdpy.core`)
  - `Qubit`, `Qudit`, `MultiQubitState`, `QuantumGate`, `Measurement`
  - `QuantumChannel` (loss, depolarizing / bit-flip / phase-flip / amplitude-damping / dephasing noise, eavesdropper hook)
  - Atmospheric / satellite helpers (`hufnagel_valley_cn2`, `von_karman_spectrum`, `fried_parameter`, `rytov_variance`, `scintillation_index`, `modtran_band_transmittance`, `background_stray_count_rate`, `link_direction_factor`)
  - PNS attack simulator (`core/attacks/pns_attack.py`)
- **All 11 QKD protocols** (`qkdpy.protocols`)
  - `BB84`, `B92`, `E91`, `SARG04`, `DecoyStateBB84`, `MDIQKD`, `CVQKD`, `EnhancedCVQKD`, `HDQKD`, `DIQKD`, `TwistedPair`
- **Crypto** (`qkdpy.crypto`)
  - `QuantumRandomNumberGenerator`, `OneTimePad`, `QuantumAuth`, `QuantumSideChannelProtection`, `QuantumHash`, `ZeroKnowledgeProof`
- **Key management** (`qkdpy.key_management`)
  - `ErrorCorrection` (Cascade, Winnow, LDPC, BCH, Reed-Solomon, LDPC blind, blind fallback chain)
  - `PrivacyAmplification` (Universal hashing seedable, Toeplitz, cryptographic hash, Bennett-Brassard, AES)
  - `KeyDistillation`, `QuantumKeyManager`
- **Network** (`qkdpy.network`)
  - `SatelliteQKD` with LEO/MEO/GEO orbits, atmospheric profile, pass simulation, link budget helpers
  - `NetworkNode`, `MultiPartyNetwork`, `QuantumRouter` — routing and multi-party relay primitives
  - `AtmosphericChannel` (visibility, turbulence, aerosols)
- **Visualization** (`qkdpy.utils.visualization`) — Bloch sphere, key-rate/QBER curves, network topology, satellite pass plots
- **Framework integrations** (`qkdpy.integrations`)
  - **Qiskit** — circuit transpilation, `AerSimulator` noise models
  - **Cirq** — protocol conversion (including E91)
  - **PennyLane** — QML with noisy mixed-state simulation
  - **QpiAI** — QpiAI Quantum SDK statevector sampling
- **Utilities** (`qkdpy.utils`)
  - `OperationSpan`, `@instrument`, `record_protocol_execution`, `record_ml_training`, `record_qber_diagnostic`
  - structlog backend (JSON / pretty), correlation IDs
- **ML optimizer & predictor** (`qkdpy.ml`)
  - `QKDOptimizer` (Bayesian + genetic)
  - `EfficientQKDPredictor` (quantization, pruning, edge deployment)
- **Attack simulators** (`qkdpy.core.attacks`)
  - Intercept-resend, PNS, Trojan-horse, beam-splitting — research/educational only
- **Exceptions, config, validation, logging** (`qkdpy.exceptions`, `qkdpy.config`)

#### ENTERPRISE-gated (commercial license required)

These capabilities ship in the same wheel but are gated behind `ProductTier.ENTERPRISE` (see `qkdpy/enterprise/licensing.py`):

- `qkdpy.enterprise.HSMInterface` — PKCS#11 software / hardware HSM key generation and storage
- `qkdpy.enterprise.AuditLogger` — tamper-evident audit trail
- `qkdpy.enterprise.ComplianceChecker` — automated checks against **ETSI GS QKD 014**, **ETSI GS QKD 016**, **ISO/IEC 23837-1/2**, **NIST SP 800-57**, **FIPS 140-2/140-3**, **ISO 27001**
- Compliance **markdown export** of reports
- ML-based attack detection over protocol traces

#### PREMIUM-gated (commercial license + SLA)

Beyond ENTERPRISE:

- `qkdpy.enterprise.quantum_safe` toolkit
  - `classic_enterprise_profile()` — generate a crypto inventory from a standard enterprise footprint
  - `generate_roadmap()` — phased migration plan (Assess → Plan → Pilot → Migrate → Verify)
  - `QuantumSafeAssessment` — full report with risk scoring and recommendations
- **Compliance HTML export** (the polish layer enterprises need for auditors)
- **Crypto Inventory Assessment** — deeper asset / algorithm review
- **Key Escrow** — opt-in recovery flows for regulated deployments
- **Priority Support** — SLA-backed response windows

### 1.3 Distribution mechanics

| Audience | What they install | What they get |
|----------|-------------------|--------------|
| Open-source community | `pip install qkdpy` (Apache-2.0) | Everything in **Always FREE** above. Default tier is `FREE`. |
| ENTERPRISE customer | Same wheel + commercial license file/key | ENTERPRISE features unlocked after license verification. |
| PREMIUM customer | Same wheel + commercial license + SLA token | PREMIUM features unlocked + support escalation path. |

Default tier is `FREE` on import. By default, tier activation above `FREE` is a **runtime demo gate** (the API works but logs that you're in demo mode). Opt-in license enforcement is available:

```bash
export QKDPY_LICENSE_ENFORCEMENT=1
export QKDPY_LICENSE_SECRET="<your-commercial-license-key>"
```

When enforcement is on, gated features raise a `LicenseError` if no valid key is found. This is **not** a full license server — see the [Status & Scope section in the README](https://github.com/Pranava-Kumar/qkdpy#-status--scope) for caveats.

---

## 2. Manual repository audit

This section records what the repository *actually contains* today, what is being deleted in the OPEN_CORE cleanup, and what still lives in the planning docs but is **not** shipped as part of v0.6.x. Sections 1 (above) and this audit are kept in sync: anything listed here as "kept" should map to a tier in §1, and anything listed as "deferred" should appear in [`docs/NEXT_STEPS.md`](NEXT_STEPS.md).

### 2.1 Methodology
- Walked `src/qkdpy/` top-down to enumerate shipped modules
- Grepped for `Feature.` references to confirm tier gating reach
- Read `qkdpy/enterprise/licensing.py` for the authoritative `ProductTier` / `Feature` enum
- Cross-checked README claims (protocol count, channel model coverage, integrations) against the actual class list
- Reviewed the `scripts/`, `projects/`, and root-level `.md` files for material that should not ship in the public repo

### 2.2 What ships in the public open-core repo

| Path | Purpose | Tier |
|------|---------|------|
| `src/qkdpy/` | Library source (see §1.2) | mixed |
| `tests/` | pytest suite (~610 tests) | FREE-only behavior, ENTERPRISE-gated behavior is gated but exercised in CI |
| `docs/` | Architecture diagrams, ADRs, this `OPEN_CORE.md`, `NEXT_STEPS.md` | n/a |
| `benchmarks/` | Throughput / latency benchmark scripts | FREE (allows reproducing reported numbers) |
| `examples/` | Runnable examples per protocol tier | FREE |
| `pyproject.toml`, `README.md`, `LICENSE`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md` | Packaging + governance | n/a |
| `.github/` | CI workflows (lint, tests, mypy, black) | n/a |
| `.pre-commit-config.yaml`, `pyproject.toml [tool.*]` | Local/CI linting | n/a |

### 2.3 What is being removed (and why)

| Removed path | Reason |
|--------------|--------|
| `scripts/blackbox/` | Diagnostic / scratch scripts, not part of the public test suite. Replaced earlier debugging noise. |
| `projects/qkdpy-commercial/01-brainstorm/` | Pre-monetization internal brainstorm. Belongs in private planning, not in the public repo. |
| `projects/qkdpy-commercial/02-research/` | Commercial / market research notes. Not Apache-2.0 appropriate. |
| `projects/qkdpy-commercial/ENHANCEMENT_PLAN.md` | Internal forward-looking file that overlaps with `docs/NEXT_STEPS.md`. |
| Audit / stress-test PDFs in the root or `docs/` | Comparative audit output — kept locally for the maintainer's records, not appropriate for the public repo. |

The replacement for the deleted forward-looking material is `docs/NEXT_STEPS.md`, the production-grade simulator roadmap, which **stays in the repo but is gitignored from published wheels** — it documents intent, not shipped code.

### 2.4 Known limitations (carried over by design)

These are *intentional* in v0.6.x and **not** bugs to be fixed quietly. They are tracked here so maintainers can defend scope decisions:

- **Phenomenological channel models.** Atmospheric / satellite / depolarizing channels are approximated, not quantum-optics solvers.
- **LDPC error correction.** Belief-propagation path is simplified; the BCH / Reed-Solomon and "blind fallback" chains are there to keep QBER recovery alive in adversarial CI but are not a hardened codec.
- **Demo-grade licensing.** Enterprise / Premium enforcement is a demo gate by default; opt-in HMAC verification is fine for *proof-of-commercial-deployment* but is not a license server.
- **PNS / intercept-resend attack simulators** are research / educational, not a "blue team" toolkit.
- **Compliance exports** are templates, not a certified auditor report. They map the algorithmic concepts of the standards listed, not specific legal obligations.

### 2.5 Deferred to `docs/NEXT_STEPS.md`

The following are **not** in scope for v0.6.x. Each has a section in `NEXT_STEPS.md` so it doesn't get lost:

- Photon-number-resolving (PNR) detector simulation
- Decoy-state finite-key analysis with composable security bounds
- Network-layer simulation under realistic stochastic loss, not just mean-field
- Hardware-in-the-loop hooks (real detector counts, real LDPC encodes)
- Production-grade secrets handling (HSM-backed key material lifecycle)
- Side-channel resistance validation (detector blinding, MDI-QKD at scale)
- Multi-protocol network router simulating arbitrary topologies

---

## 3. References

- `docs/NEXT_STEPS.md` — production-grade simulator roadmap
- `CHANGELOG.md` — version history
- `docs/decisions/ADR-001-product-tier-licensing.md` — why this split exists
- `docs/decisions/ADR-002-observability-and-instrumentation.md` — observability stance
- `docs/decisions/ADR-003-compliance-architecture.md` — compliance checker design
