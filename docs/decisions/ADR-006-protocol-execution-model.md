# ADR-006: Protocol Execution Model

## Status
Accepted

## Date
2026-07-24

## Context

QKDpy implements 12+ QKD protocols (BB84, E91, CV-QKD, decoy-state BB84,
DI-QKD, HD-QKD, MDI-QKD, SARG04, B92, Six-State, twisted-pair, enhanced CV-QKD).
These protocols share a common high-level flow but differ in every detail:

| Phase | BB84 | E91 | CV-QKD |
|-------|------|-----|--------|
| State preparation | 4 polarisation states | Entangled Bell pairs | Coherent states with modulation |
| Measurement | Random basis measurement | Bell measurement | Homodyne/heterodyne detection |
| Sifting | Basis comparison | Basis comparison | Reconciliation |
| Security parameter | QBER threshold | CHSH violation | Excess noise |

If every protocol re-implements the orchestration loop, we get:
- Duplicated phase-ordering logic in every protocol class
- Inconsistent error handling and statistics collection
- No single place to add cross-cutting concerns (instrumentation, logging)
- Hard to add new protocols (copy-paste-modify from an existing one)
- Hard to audit the execute flow for correctness

The question is not *whether* to share code, but *how* to structure the
sharing — what pattern to use, and what each protocol must vs. may override.

## Decision

Use the **Template Method** pattern: `BaseProtocol.execute()` defines the
fixed phase sequence, and each protocol overrides individual phases.

### Architecture

```python
class BaseProtocol(ABC):
    def execute(self) -> ProtocolResult:
        self.reset()
        qubits = self.prepare_states()          # Step 1 — abstract
        received = self.channel.transmit_batch(qubits)  # Step 2 — fixed
        results = self.measure_states(received) # Step 3 — abstract
        alice_sifted, bob_sifted = self.sift_keys()     # Step 4 — abstract
        qber, alice_sifted, bob_sifted = \
            self._estimate_qber_with_sampling(...)       # Step 5 — fixed impl
        alice_corrected, bob_corrected = \
            self.error_correction(...)          # Step 6 — concrete (delegates)
        final_key = self.privacy_amplification(...)     # Step 7 — concrete (delegates)
        # ... evaluate security, return result
```

### What is abstract (protocol-specific)

- `prepare_states()` — Each protocol creates its own quantum states
- `measure_states()` — Each protocol measures in its own basis/frame
- `sift_keys()` — Each protocol has its own sifting rule

### What is concrete (shared by all protocols)

- `execute()` — The orchestration loop (the template method)
- `error_correction()` — Delegates to `ErrorCorrection` by method name
- `privacy_amplification()` — Delegates to `PrivacyAmplification` by method name
- `reset()` — Clears per-run state

### What has a default but can be overridden

- `estimate_qber()` — Default for discrete-variable protocols; CV-QKD
  overrides with excess-noise estimation
- `_estimate_eve_information()` — Different leakage models per protocol
  family

### Strategy-like delegation for pluggable steps

Error correction and privacy amplification use a **strategy** sub-pattern —
the base class holds a method name string (`"cascade"`, `"universal_hashing"`)
and dispatches to the corresponding function in the library module. This
lets protocols swap algorithms without overriding methods.

```python
def error_correction(self, alice_key, bob_key):
    if self.error_correction_method == "cascade":
        return self._cascade_error_correction(alice_key, bob_key)
    elif self.error_correction_method == "winnow":
        return self._winnow_error_correction(alice_key, bob_key)
```

## Alternatives Considered

### Composable pipeline (chain of phases as objects)
- **Pros:** Phases can be reordered, injected, or skipped at runtime.
  New phases don't require subclassing.
- **Cons:** Every protocol has the same phase order — runtime
  reconfigurability is not a requirement. The pipeline abstraction
  adds interface boilerplate (Phase base class, input/output types,
  wiring code) without benefit. Harder to follow the execution flow
  than a linear method.
- **Rejected:** The phase order is invariant across all protocols.
  Template method is simpler and more readable.

### Strategy-only (no base class, each protocol is standalone)
- **Pros:** Zero coupling between protocols. Each can evolve independently.
- **Cons:** Massive duplication of the execute loop, instrumentation,
  stats collection, and result packaging. Adding a cross-cutting
  feature (e.g., observability in v0.7.1) requires touching every
  protocol class.
- **Rejected:** The common flow is too large to duplicate 12 times.

### Mixin-based (phases as mixin classes combined via multiple inheritance)
- **Pros:** Fine-grained reuse — pick which phases you want
- **Cons:** MRO complications. Protocols inherit behavior from
  unpredictable locations. Adding a new phase requires creating a new
  mixin and updating every protocol's class line. Python MRO bugs are
  hard to debug.
- **Rejected:** Multiple inheritance for code sharing is fragile and
  hard to reason about.

### Decorator-based (phases registered as decorated functions)
- **Pros:** Very flexible, easy to reorder
- **Cons:** Phase ordering becomes implicit (depends on decorator
  application order in the source file). IDE navigation breaks.
  No type-checking of the phase interface.
- **Rejected:** Implicit ordering is dangerous for a multi-step
  process where each step depends on the previous one's output.

## Consequences

- Adding a new protocol requires implementing exactly 3 abstract methods
  (`prepare_states`, `measure_states`, `sift_keys`). Everything else comes
  from the base class.
- The `execute()` method is the single point of control for instrumentation,
  timing, logging, and security evaluation — adding `OperationSpan` in
  v0.7.1 required changing one file (`base.py`) instead of 12 protocol files.
- Protocol classes are self-contained and testable in isolation — each phase
  method can be tested directly.
- The fixed phase sequence means protocols with fundamentally different
  structures (e.g., measurement-device-independent protocols that need
  an additional public announcement phase) must work within the existing
  phases or override `execute()` entirely.
- Strategy delegation for error correction / privacy amplification means
  adding a new algorithm requires only a new method on the base class
  (or a function in the library module) — no protocol changes.
