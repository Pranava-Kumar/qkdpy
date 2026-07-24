# ADR-005: Core Quantum Simulation Stack

## Status
Accepted

## Date
2026-07-24

## Context

QKDpy started with a pure-state simulation model — `Qubit` and `Qudit` state
vectors evolved unitarily through gates, with noise approximated at the
channel level. As the library grew toward v0.8.0, three requirements made
this model insufficient:

1. **Realistic noise modeling.** Real QKD hardware deals with decoherence,
   thermal noise, amplitude damping, and other non-unitary processes. A
   pure-state simulator cannot represent these without either (a) Monte
   Carlo trajectory sampling, which is approximate and converges slowly,
   or (b) the density-matrix formalism, which is exact for any CPTP map.

2. **Entanglement distillation and state tomography.** Protocols that use
   entanglement (E91, DI-QKD, MDI-QKD) need to compute reduced density
   matrices via partial trace. Partial trace on a pure state vector of a
   composite system is possible but awkward — it requires writing the
   state as a matrix and tracing, which is exactly the density-matrix
   operation but with extra steps.

3. **A composable circuit abstraction.** Before v0.8.0, every protocol
   built its operations manually — creating `Qubit` objects, applying
   gates one at a time, tracking the state in procedural code. There was
   no way to represent a reusable sequence of operations, export it, or
   simulate it on different backends.

## Decision

We add two complementary abstractions as the core simulation stack:

### DensityMatrix (low-level state representation)

A `DensityMatrix` class represents mixed quantum states as positive
semidefinite, trace-1 complex matrices. It provides:

- **Constructors:** `from_pure()`, `maximally_mixed()`, `from_probabilities()`
- **Operations:** `apply_channel()` (via Kraus operators), `partial_trace()`
- **Metrics:** `purity()`, `entropy()` (von Neumann), `fidelity()` (Uhlmann),
  `trace_distance()`
- **Standard channels:** Depolarizing, amplitude damping, phase damping,
  bit-flip, phase-flip — all as Kraus-operator CPTP maps

The density matrix is the **single source of truth** for state representation.
Pure states (`Qubit`, `Qudit`) are convenience wrappers that can be converted
to `DensityMatrix` when needed (e.g., for partial trace or channel application).

### Circuit (high-level operation composition)

A `Circuit` class provides a method-chaining API for composing quantum
programs:

- **Standard gates:** `h()`, `x()`, `y()`, `z()`, `s()`, `t()`, `rx()`, `ry()`,
  `rz()`, `cx()`, `cz()`, `swap()`
- **Composition:** `compose()`, `custom_gate()`
- **Simulation:** `simulate()` — executes the circuit on the density-matrix
  engine
- **Export:** `to_qasm()` — OpenQASM 2.0 output
- **Analysis:** `depth()`, `count_ops()`

The `Circuit` does NOT own a new simulation engine — it delegates to
`DensityMatrix` for state evolution. This keeps the physics in one place
(the density-matrix kernel) and the composition API in another.

### Relationship between the two

```
Circuit (gates + measurements)
   │
   ▼ simulates via
DensityMatrix (state + CPTP evolution)
   │
   ├── Standard channels (noise models)
   ├── Partial trace (entanglement)
   └── Metrics (fidelity, entropy, purity)
```

All `Qubit`/`Qudit` operations remain available and unchanged. The density
matrix layer is strictly additive — it does not replace the pure-state
model but sits alongside it, with conversion methods between the two.

### CPTPChannel framework

Building on `DensityMatrix`, a `CPTPChannel` class formalizes quantum
channels via Kraus operators:

- **Composition:** `compose()` — sequential channel composition
- **Choi matrix:** `choi_matrix()` — for channel-state duality
- **Diamond norm:** `diamond_distance()` — for channel distinguishability
- **Standard channels:** Depolarizing, amplitude damping, phase damping as
  `CPTPChannel` instances

## Alternatives Considered

### Continue with pure states only (Monte Carlo noise)
- **Pros:** No new data structure, lower memory per sample
- **Cons:** Simulating mixed states requires many trajectories for
  convergence. Every noise operation becomes approximate. Partial trace
  of entangled states requires manual Schmidt decomposition.
- **Rejected:** The density matrix is the correct formalism for mixed
  states. Monte Carlo is an approximation technique, not a state
  representation.

### Adopt QuTiP as a dependency
- **Pros:** Battle-tested density-matrix library, full-featured
- **Cons:** Heavy dependency (180 MB install) for a library that needs
  only core linear algebra. Version coupling risk. Hinders the
  educational goal of showing the math in code.
- **Rejected:** A ~450 LOC self-contained module is simpler to maintain
  and inspect than an external dependency. Users who need QuTiP can
  convert via the `.matrix` attribute.

### Adopt Qiskit/Cirq as the sole circuit interface
- **Pros:** Full-featured circuit optimizers, rich gate sets
- **Cons:** Requires the integration extra (`qkdpy[qiskit]`). Every
  user would need to install Qiskit just to run a basic protocol.
  Defeats the "zero-install-overhead" simulation goal.
- **Rejected:** Our `Circuit` is a lightweight internal DSL. Users who
  want Qiskit/Cirq backends can use the integration layer.

### Make Circuit own its simulation engine
- **Pros:** Cleaner separation, could swap engines
- **Cons:** Duplicates state-evolution logic already in `DensityMatrix`.
  Every engine would need to replicate the CPTP-channel code.
- **Rejected:** Circuit delegates to DensityMatrix. This keeps the
  physics kernel singular and the circuit layer as pure composition.

## Consequences

- Density-matrix simulation is exact for any CPTP map — no Monte Carlo
  convergence worries.
- Memory scales as O(d²) instead of O(d) for pure states. For the
  single-qubit and few-qubit simulations QKDpy targets (d ≤ 8 for qudits),
  this is negligible.
- Users can mix pure-state and density-matrix code freely — conversion
  goes both ways.
- `Circuit` provides a familiar API for users coming from Qiskit/Cirq
  while keeping the library self-contained.
- New protocols can express noise directly via `DensityMatrix.apply_channel()`
  instead of relying solely on `QuantumChannel` transmission noise.
- The CPTP channel framework enables channel tomography and process
  fidelity calculations that were previously impossible.
