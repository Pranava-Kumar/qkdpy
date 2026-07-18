# Roadmap — What's Next for QKDpy

**Last updated:** 2026-07-18

QKDpy today is a **research and educational simulator** of Quantum Key
Distribution. It lets you model protocols, channels, satellite links, and
attacks with phenomenological approximations, and it ships the full
open-source core plus enterprise/compliance and quantum-safe migration
add-ons.

This page describes the **developer's near- and medium-term plans**
for the project — what capabilities are intended next, and how the
library is expected to mature. It is a statement of direction, not a
commitment on dates or on any specific release.

## Themes we're investing in

1. **Higher-fidelity physics.** Moving from approximate channel models
   toward per-pulse photon statistics, regime-aware atmospheric
   turbulence, and reference-scenario validation against published
   experimental key rates.
2. **Stronger security reasoning.** Composable, finite-key
   security statements for decoy-state and device-independent
   protocols, so a result can report an explicit security margin
   instead of a single QBER threshold.
3. **Closer to real hardware.** The ability to feed real detector
   counts and real error-correction matrices into the simulator, and
   to interoperate with external key-management interfaces.
4. **Operability at scale.** Topology-aware multi-node networks,
   stochastic (not just mean-field) loss, and scheduling that can
   answer end-to-end key-rate questions under realistic conditions.
5. **Lifecycle hardening.** Secrets handling that keeps key material
   in an HSM-backed lifecycle, plus tamper-evident audit trails
   and verifiable compliance exports.

## How we sequence the work

The developer plans to advance the work in phases rather than all at
once:

- **Phase 1 — Core fidelity.** Better decoy-state analysis and
  error-correction backends.
- **Phase 2 — Realistic channels.** Photon-number-resolving
  detectors and atmospheric realism.
- **Phase 3 — Hardware hooks.** Ingesting real detector and
  codec data, plus key-management interoperability.
- **Phase 4 — Network scale.** Topology-aware routing and
  scheduling under stochastic loss.
- **Phase 5 — Lifecycle & enforcement.** HSM-backed secrets,
  anchored audit logs, and license enforcement.

Each phase is treated as its own release train, and the project's
**Status & Scope** stance is only ever widened deliberately —
never by quietly implying production-readiness.

## What QKDpy is *not* claiming

Even as it matures, QKDpy is not positioned as a certified
cryptographic module. It does not replace a certified HSM, it
does not generate or protect production key material on its own, and
its compliance templates support engineering reasoning rather than
substituting for an auditor's sign-off.

For the current maturity level and the precise list of what is and
is not in scope, see the **Status & Scope** section of the
[README](https://github.com/Pranava-Kumar/qkdpy#-status--scope).
