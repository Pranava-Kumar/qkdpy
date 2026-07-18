# Next Steps — Production-Grade QKD Simulator Roadmap

> **Status:** Planning document. **Not** in scope for the current v0.6.x
> release. The deployed library is a research / educational simulator and is
> explicitly not production-grade (see [`OPEN_CORE.md`](OPEN_CORE.md) § 2.4 and
> the README's *Status & Scope* section).
>
> This roadmap tracks what would have to change — model fidelity, noise
> models, error correction, security proofs, hardware hooks, secrets
> lifecycle, deployment signals — to take QKDpy from "qualitative simulator"
> to "production-grade simulator / digital twin." It exists so the work
> doesn't get lost between release cycles, not as a commitment on dates.

---

## 0. Guiding principles

1. **Production-grade** means *defensible*: every result the simulator
   produces should be traceable to a published algorithm or a measured
   detector characteristic, not a phenomenological approximation.
2. **Composable security proofs first, throughput second.** Decoy-state
   finite-key analysis, MDI-QKD proof plumbing, and DI-QKD Bell-inequality
   testing replace the current QBER-only abort heuristic.
3. **Hardware-in-the-loop is a feature, not an optional extra.** The
   simulator should be able to consume real detector counts and real LDPC
   encodes, not only its own internal RNG.
4. **Secrets lifecycle is owned end-to-end.** No ephemeral paper-keys,
   no "user passes a string of bits in manually." HSM-backed key material
   lifecycle becomes the default for any PREMIUM-tier deployment.
5. **No silently weakened guarantees.** Every change that affects channel
   models, noise, measurement, privacy amplification, or error correction
   must ship with a regression test that demonstrates the physical /
   security behavior (existing CONTRIBUTING.md § AI policy § 5).

---

## 1. Model fidelity

### 1.1 Photon-number-resolving detectors
- Move from "click / no-click" Bernoulli sampling to a Poisson-conditional
  detector model with realistic dark counts, after-pulsing, and dead time.
- Replace `QuantumChannel` loss application with a photon-number
  distribution (`P(n)`) sampled per pulse, not a per-pulse survival
  probability.
- Acceptance criteria: detector count histograms against published WSI /
  SNSPD characterization papers, not against an arbitrary baseline.

### 1.2 Composable decoy-state analysis
- Implement finite-key composable-secure bounds (Tomamichel-Leverrier-
  Renner style) for `DecoyStateBB84` so that `is_secure` is no longer a
  QBER threshold but an actual ε-secure yes/no.
- Surface the ε parameters (`ε_sec`, ε_cor`, ε_ro`) in the protocol
  result schema.
- Acceptance criteria: results reproduce published decoy-state numerics
  on a reference scenario within published bounds.

### 1.3 Atmospheric / free-space optical channels
- Replace `hufnagel_valley_cn2`-only turbulence with a state-vector
  simulator that handles weak + strong scintillation regimes, with
  justified regime-switching.
- MODTRAN integration becomes optional (`modtran-bundle` extra),
  defaulting to a parametric MODTRAN-equivalent (not just `Cn2`).
- Acceptance criteria: a published pass scenario produces a key rate
  within an order of magnitude of the published experimental value.

### 1.4 Loss + error correction realism
- LDPC: replace the simplified belief-propagation path with a proper
  rate-compatible LDPC family (rate ~0.5–0.9), with a lifted check matrix
  and a worked throughput / QBER sensitivity plot.
- Cascade: keep Cascade as the low-QBER reference path; add a benchmark
  mode so the BCH / RS / LDPC selection is data-driven, not hard-coded.
- Acceptance criteria: documented reference codec with published FER
  curves.

---

## 2. Security proofs & analyzed protocols

### 2.1 MDI-QKD at scale
- The current MDI-QKD simulator stops at two trusted nodes and a Charlie
  relay. Promote it to a network-scale model with multiple Charlies,
  detector misalignment, and composable ε security.
- Acceptance criteria: an extension to ≥4 trusted nodes with
  composable-security assertions across the chain.

### 2.2 DI-QKD self-testing
- The DI-QKD module currently reports a CHSH value; upgrade it to a full
  self-testing extraction (e.g., the Acín-Massar-Pironio /
  Yang-Navascués protocols) so the output key rate carries an explicit
  ε-security bound, not a CHSH threshold.

### 2.3 Side-channel resistance validation
- Add detector-blinding, wavelength-dependent attack, and Trojan-horse
  test harnesses in `qkdpy.core.attacks` (already a FREE area), but with
  per-attack *detection yield* metrics that map to the relevant ETSI /
  ISO / NIST requirement IDs.

### 2.4 CV-QKD noise realism
- Replace the additive-Gaussian channel with the canonical
  pure-loss + Gaussian-noise model used in the literature, with explicit
  reconciliation-efficiency scaling and a public reconciliation
  benchmark.

---

## 3. Hardware-in-the-loop

| Capability | Target |
|------------|--------|
| Real detector ingestion | Consume `.csv` / `.h5` timeseries from ID Quantique, QuantumCTek, or generic SNSPD arrays; plug them in via a `DetectorSource` interface so simulations are *hybrid*. |
| Real LDPC ingestion | Accept a ParityCheckMatrix in alist / QC sparse format and have the simulator reuse the existing belief-propagation decoder. |
| Time-tagging | Replace wall-clock simulation with a synced time-tag pipeline (ns resolution) so timing side-channels can be modeled. |
| QKD hardware emulation | A "device-under-test" abstraction with a published interface; a vendor adapter even for one device is enough to prove the abstraction is right. |

---

## 4. Network scale

- Topology graph (`networkx.DiGraph` already used internally) becomes the
  authoritative model: routers, repeater chains, multi-protocol gateways
  are topology-aware, not hard-wired.
- Stochastic-loss channels replace mean-field loss: rain / cloud / fog
  ingest time-series, not a single number.
- A scheduling layer that can answer "what is the maximum key rate
  achievable across this topology under this weather forecast end-to-end"
  — not just per-link.

---

## 5. Secrets lifecycle & deployment

- **HSM-backed key material.** Move from
  `QuantumKeyManager.generate_key(...)` returning a Python string to a
  handle-based model where the HSM keeps the actual bytes.
- **KME-SA interoperability.** Implement the ETSI GS QKD 014
  key-deliver / status interface on top of the simulator so it can be
  exercised by an external KME test harness.
- **Audit log forgery resistance.** The current `AuditLogger`
  (ENTERPRISE-gated) ships with HMAC chaining; promote it to a Merkle-
  anchored log with periodic checkpoints.
- **Compliance export authenticity.** Generated reports gain a verifiable
  signature bound to the audit log, so an external auditor can detect
  post-hoc edits.

---

## 6. Distribution / lifecycle

- Tier-gated features remain gated, but the **license verification
  path** moves from a demo-gate by default to **Moshi-policy** style
  signed-license files with revocation lists. The opt-in HMAC path
  introduced in v0.6.6 stays for low-friction deployments.
- Each tier's runtime error semantics change: a missing license raises
  `LicenseError` with a remediation hint (`contact@qkdpy.org`), not a
  silent demo.
- **Long-term support branches.** A production-grade distribution
  needs `0.7.x` LTS, not just the rolling `main`. Plan an LTS branch
  alongside the feature branch.

---

## 7. Validation, tests, and continuous assurance

- **Reference scenarios** library: ~20 published experiments (BB84 over
  fiber, MDI across cities, satellite pass, Micius) with their published
  results vendored as `.expected.json`. Every change that touches
  physics-related code must reproduce the expected numbers within a
  documented tolerance.
- **Regression-sensitivity diffs**: CI compares the simulator's
  throughput / QBER / key-rate-vs-distance curves against a frozen
  reference; violations block merge.
- **Mutation tests** for the security-sensitive paths (privacy
  amplification, error correction, key distillation) per `mutmut`.
- **Property-based tests** (Hypothesis) for the utility primitives
  (basis sifting, integrity check bits).

---

## 8. Documentation / governance

- Each step advances one of the ADRs in
  `docs/decisions/`. New ADRs write down the *why* of a model swap, not
  just the *what*.
- The "Status & Scope" section in the README is **only** rewritten
  *downward* (i.e., we add more legitimate-engineering-use cases
  gradually, never quietly widen the production-suitability claim).
- Threat model document published alongside the simulator, with the
  assumption list and out-of-scope list side by side.

---

## 9. Out of scope (intentionally)

Even "production-grade" does **not** mean certifying QKDpy as a
cryptographic module. The following are explicitly out:

- Replacing a certified HSM.
- Generating or protecting real production key material.
- Acting as an auditor for an actual QKD deployment.
- Legal or regulatory attestation. Compliance templates help engineers
  reason; they do not replace auditors.

See `OPEN_CORE.md § 2.4` for the current v0.6.x version of this caveat.

---

## 10. Sequencing (proposed, not committed)

| Phase | Bucket | Rough dependency |
|-------|--------|-------------------|
| **0** | Refactor & cleanup | Public-repo cleanup (this commit), `pyproject.toml` maturity, CI signals |
| **1** | Composable decoy-state + LDPC hardening | § 1.1, § 1.2 |
| **2** | Detector PNR + atmospheric realism | § 1.1, § 1.3 |
| **3** | Hardware-in-the-loop + KME-SA | § 3, § 5 |
| **4** | Network scale + scheduling | § 4 |
| **5** | License enforcement + audit anchors | § 5, § 6 |

Each phase is a separate release train. *No* item on this roadmap ships
until it has tests, documentation, ADRs, and an updated "Status & Scope"
caveat.

---

## 11. References

- `OPEN_CORE.md` — current open-core layout and known limitations
- `CHANGELOG.md` — what's already shipped
- `docs/decisions/ADR-001-product-tier-licensing.md` — monetization model
- `docs/decisions/ADR-002-observability-and-instrumentation.md` —
  observability stance
- `docs/decisions/ADR-003-compliance-architecture.md` — compliance shape
