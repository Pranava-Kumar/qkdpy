# qkdpy vs QpiAI Quantum SDK: Core Quantum Logic Comparison

**Date:** 2026-07-14
**Scope:** Mathematical/physical correctness audit comparing qkdpy's implementations against QpiAI's hardware-verified, cloud-tested implementations.
**Note:** This is NOT a code-change request. Pure analysis only.

---

## Table of Contents

1. [State Vector Representation](#1-state-vector-representation)
2. [Density Matrix Support](#2-density-matrix-support)
3. [Noise Channels](#3-noise-channels)
4. [Entanglement Measures](#4-entanglement-measures)
5. [Gate Implementations](#5-gate-implementations)
6. [Measurement Statistics](#6-measurement-statistics)
7. [Protocol Completeness](#7-protocol-completeness)
8. [Integration Layer Bugs](#8-integration-layer-bugs)
9. [Summary Table](#9-summary-table)

---

## 1. State Vector Representation

### What qkdpy does

Two separate classes for state vectors:

- **`Qubit`** (`src/qkdpy/core/qubit.py`, line 10-201): Single-qubit only. Stores a 2-element complex numpy array `[alpha, beta]` representing `alpha|0> + beta|1>`. Normalization is enforced in `__init__` (line 30-34). Factory methods: `zero()`, `one()`, `plus()`, `minus()`.

- **`MultiQubitState`** (`src/qkdpy/core/multiqubit.py`, line 13-371): Multi-qubit state vector, dimension must be a power of 2. Factory methods: `from_qubits()`, `zeros()`, `ghz()`, `w_state()`. Supports `apply_gate()` with arbitrary qubit targeting and `measure()` with collapse. Has `entanglement_entropy()` stub (returns 0.0).

### What QpiAI validates

- **`Statevector`** (`qpiai_quantum/quantum_info/statevector.py`): Unified class for 1 to n qubits. Constructor accepts list, ndarray, Circuit (simulates), or copy. Factory: `from_label()`, `from_circuit_object()`. Properties: `probabilities()`, `probabilities_dict()`, `purity()`, `is_valid()`. Methods: `to_density_matrix()`, `evolve()`, `copy()`. Arithmetic: `__add__`, `__sub__`, `__mul__`, `__truediv__`, `__getitem__`.

- Cloud-tested with `QpiAI-QSV-Simulator` and `QpiAI-Indus-1` (real QPU).

### Discrepancies

| Issue | qkdpy | QpiAI | Severity |
|-------|-------|-------|----------|
| Single vs multi-qubit unified API | Separate classes | Unified `Statevector` for all qubit counts | MINOR |
| State evolution | `evolve()` via `apply_gate()` method | `evolve(other)` method | NONE (design choice) |
| Probabilities dict | Only `probabilities` tuple property | `probabilities_dict(decimals)` with basis labels | MINOR |
| Arithmetic operators | `__eq__` only | Full arithmetic + `__getitem__` + `__array__` | MINOR |
| Circuit-based construction | Manual | `Statevector(circuit)` auto-simulates | MINOR |

**Discrepancy Level: MINOR.** qkdpy's separation is a valid design choice for a protocol-specialized library. The main gap is the lack of a unified statevector API that could simplify cross-class operations.

---

## 2. Density Matrix Support

### What qkdpy does

**`Qubit.density_matrix()`** (`src/qkdpy/core/qubit.py`, lines 160-167):
```python
def density_matrix(self) -> np.ndarray:
    return np.outer(self._state, np.conjugate(self._state))
```

**`MultiQubitState.density_matrix()`** (`src/qkdpy/core/multiqubit.py`, lines 312-318):
```python
def density_matrix(self) -> np.ndarray:
    return np.outer(self._state, np.conjugate(self._state))
```

Both compute the outer product of a state vector with its conjugate -- this produces a **pure state density matrix only**. There is no mechanism to create or manipulate mixed states anywhere in qkdpy. The `Measurement` class provides:

- `measure_purity()` (line 159-172): Always returns 1.0 for any reachable state (all states are pure).
- `measure_von_neumann_entropy()` (line 174-193): Always returns 0.0 for any reachable state.
- `measure_observable()` (line 196-215): Works correctly on pure states.
- `quantum_state_tomography()` (line 254-328): Reconstructs density matrix but state must be pure.

### What QpiAI validates

**Two layers of density matrix support:**

1. **`quantum_info.DensityMatrix`** (`qpiai_quantum/quantum_info/density_matrix.py`): User-facing, circuit-integrated. Methods: `purity()`, `von_neumann_entropy()`, `trace()`, `is_valid()`, `is_pure()`, `fidelity()`, `partial_trace()`, `probabilities()`, `probabilities_dict()`. Arithmetic operators. Convertible to/from `formalism.DensityMatrix`.

2. **`formalism.DensityMatrix`** (`qpiai_quantum/formalism/density_matrix/density_matrix.py`): Advanced operations:
   - **Noise channels**: `ADC(param)`, `depol(param)`, `kraus(operator_list)` -- all density-matrix-based
   - **Entropy**: `reyni(alpha)` -- Renyi entropy
   - **Entanglement**: `concurrence()`, `eof()` (entanglement of formation), `schmidt_rank()`
   - **Partial transpose**: `partial_transpose(dims, axis)`
   - **Bell/CHSH**: `max_bell_value()`, `teleportation_fidelity()`
   - **Coherence**: `relative_entropy_coherence()`
   - **Distinguishability**: `distinguishability(X, ...)` -- state discrimination

All validated against cloud simulator and QPU backends.

### Discrepancies

| Issue | qkdpy | QpiAI | Severity |
|-------|-------|-------|----------|
| Mixed state support | **None** -- all states are pure | Full mixed state via density matrix + Kraus noise | **MAJOR** |
| Noise channel integration | State-vector-based (quantum trajectory) | Density-matrix-based (Kraus operators) | **MAJOR** |
| Entanglement measures | Not available | concurrence(), eof(), schmidt_rank() | **MAJOR** |
| Partial trace | Not implemented | `partial_trace(qubits_to_keep, dims)` | **MAJOR** |
| Purity function | Always 1.0 (dead code) | Correct for mixed states | **MEDIUM** |
| von Neumann entropy | Always 0.0 (dead code) | Correct for mixed states | **MEDIUM** |
| Fidelity | Only for pure state vectors | `fidelity(other, validate)` with density matrices | MINOR |

**Discrepancy Level: MAJOR.** qkdpy has NO mixed state support. The density_matrix() method is always pure state only. Key functions like `purity()`, `von_neumann_entropy()`, and `entanglement_entropy()` are technically correct in their formulas but always return trivial values (1.0, 0.0, 0.0 respectively) because mixed states cannot be created. These are effectively dead code that will mislead users into thinking mixed state analysis is supported.

**Specific file/line references:**
- `src/qkdpy/core/qubit.py:160-167` -- density_matrix() pure-state-only
- `src/qkdpy/core/multiqubit.py:312-318` -- density_matrix() pure-state-only
- `src/qkdpy/core/multiqubit.py:320-339` -- entanglement_entropy() returns 0.0 (stub)
- `src/qkdpy/core/measurements.py:159-172` -- measure_purity() always computes Tr(rho^2) = Tr(rho) = 1
- `src/qkdpy/core/measurements.py:174-193` -- measure_von_neumann_entropy() always computes -sum(1*log2(1)) = 0

---

## 3. Noise Channels

### What qkdpy does

All defined in `src/qkdpy/core/channels.py`. Five noise models using **state vector evolution** (quantum trajectory / Monte Carlo approach):

#### 3.1 Depolarizing Noise (`_depolarizing_noise`, lines 202-217)

```python
def _depolarizing_noise(self, qubit: Qubit) -> Qubit:
    if np.random.random() < self.noise_level:
        gate = random.choice([Identity, PauliX, PauliY, PauliZ])
        qubit.apply_gate(gate)
    return qubit
```

**Mathematical analysis:** The effective channel is:
```
rho -> (1 - noise_level) * rho + noise_level/4 * (I*rho*I + X*rho*X + Y*rho*Y + Z*rho*Z)
     = (1 - 3*noise_level/4) * rho + noise_level/4 * (X*rho*X + Y*rho*Y + Z*rho*Z)
```

**Issue 1: Identity in the random choice.** The Identity gate should NOT be in the random choice set. The standard depolarizing channel applies:
```
rho -> (1 - p) * rho + p/3 * (X*rho*X + Y*rho*Y + Z*rho*Z)
```

With Identity in the choice, the identity is applied with probability noise_level/4, reducing the effective error rate from `noise_level` to `3*noise_level/4`. If a user sets `noise_level=0.1`, they expect 10% error rate but get 7.5%.

**Issue 2: State vector approach cannot model mixed states.** Depolarizing noise maps pure states to mixed states, but qkdpy's state vector approach only ever produces another pure state (one of the four Pauli-evolved states). This is equivalent to the quantum trajectory method but requires many runs to converge to the correct mixed state statistics.

#### 3.2 Bit Flip Noise (`_bit_flip_noise`, lines 219-224)

```python
def _bit_flip_noise(self, qubit: Qubit) -> Qubit:
    if np.random.random() < self.noise_level:
        qubit.apply_gate(PauliX().matrix)
        self.error_count += 1
    return qubit
```

**Analysis:** Mathematically correct. Applies X with probability `noise_level`. Same state-vector limitation applies (can't represent mixed states).

#### 3.3 Phase Flip Noise (`_phase_flip_noise`, lines 226-231)

```python
def _phase_flip_noise(self, qubit: Qubit) -> Qubit:
    if np.random.random() < self.noise_level:
        qubit.apply_gate(PauliZ().matrix)
        self.error_count += 1
    return qubit
```

**Analysis:** Mathematically correct. Same state-vector limitation applies.

#### 3.4 Amplitude Damping Noise (`_amplitude_damping_noise`, lines 233-241)

```python
def _amplitude_damping_noise(self, qubit: Qubit) -> Qubit:
    if np.random.random() < self.noise_level:
        gamma = self.noise_level
        if qubit.probabilities[1] > 0 and np.random.random() < gamma:
            qubit._state = np.array([1, 0], dtype=complex)
            self.error_count += 1
    return qubit
```

**Issue 1: Nested probability.** The outer check `random() < noise_level` AND the inner check `random() < gamma` (where gamma = noise_level) are nested. The effective damping probability is `noise_level^2`, not `noise_level`. If a user sets `noise_level=0.1`, the effective damping rate is 1%, not 10%.

**Issue 2: Incorrect physics.** The amplitude damping channel Kraus operators are:
```
K0 = [[1, 0], [0, sqrt(1-gamma)]]
K1 = [[0, sqrt(gamma)], [0, 0]]
```

The evolution is: `rho -> K0*rho*K0^dag + K1*rho*K1^dag`

For a pure state `a|0> + b|1>`, the correct amplitude damping produces the mixed state:
```
rho = |a|^2 |0><0| + a*b*conj(sqrt(1-gamma)) |0><1| + conj(a)*b*sqrt(1-gamma) |1><0| + |b|^2*(1-gamma) |1><1| + |b|^2*gamma |0><0|
```

But qkdpy's implementation collapses `|1>` to `|0>` deterministically, which:
- Destroys coherence (the off-diagonal elements are lost)
- Always produces `|0>` regardless of the original superposition
- Does not correctly model the partial loss of amplitude + partial coherence

**Issue 3: State vector approach fundamentally insufficient.** The correct density matrix cannot even be represented as a pure state vector.

#### 3.5 Other Channel Effects

- `_apply_polarization_drift()` (lines 359-385): Applies `[[cos(theta), -sin(theta)], [sin(theta), cos(theta)]]` -- this is a rotation in the X-Y plane, not a polarization drift. A correct polarization drift should be a unitary rotation around the appropriate axis on the Bloch sphere.

- `_apply_thermal_noise()` (lines 429-455): Same issue as depolarizing (includes Identity in random choice).

### What QpiAI validates

**`formalism.DensityMatrix`** methods:
- `depol(param)`: Correct depolarizing channel using Kraus operators on density matrix
- `ADC(param)`: Correct amplitude damping channel using Kraus operators
- `kraus(operator_list)`: Custom Kraus operator application
- All operate on density matrices, correctly tracking coherences in mixed states

Additionally, the **`quantum_info.DensityMatrix`** class provides:
- `partial_trace()`: For computing reduced density matrices of subsystems
- `fidelity()`: For comparing states under noise

Wall-clock tested via cloud simulator and QPU backends.

### Discrepancies

| Issue | qkdpy | QpiAI | Severity |
|-------|-------|-------|----------|
| Depolarizing includes Identity | YES (line 207) | NO -- standard X,Y,Z only | **MAJOR** |
| Depolarizing probability ratio | Uniform 1/4 each I,X,Y,Z | p: 1-p do nothing, p/3 each X,Y,Z | **MAJOR** |
| Amplitude damping probability | noise_level^2 (nested) | gamma (single parameter) | **MAJOR** |
| Amplitude damping coherence | Destroys all coherence | Preserves via Kraus operators | **MAJOR** |
| State representation under noise | Pure state only (quantum trajectory) | Mixed state (density matrix) | **MAJOR** |
| Kraus operator extensibility | None | `kraus(operator_list)` | **MAJOR** |
| Polarization drift | X-Y rotation (line 376-382) | N/A (different abstraction level) | MINOR |
| Bit flip noise | Correct PA=noise_level | N/A | NONE |
| Phase flip noise | Correct PZ=noise_level | N/A | NONE |

**Discrepancy Level: MAJOR.** Three of the five noise channels have mathematical errors. All noise channels use a state-vector approach that cannot represent mixed states, which is fundamentally insufficient for modeling noisy quantum channels. The correct approach requires density matrix evolution with Kraus operators.

---

## 4. Entanglement Measures

### What qkdpy does

**`MultiQubitState.entanglement_entropy()`** (`src/qkdpy/core/multiqubit.py`, lines 320-339):

```python
def entanglement_entropy(self, subsystem_qubits: list[int]) -> float:
    # ... validation ...
    # This is a complex calculation that would require partial trace computation
    # For now, we'll return a placeholder
    return 0.0
```

- **This is a stub that returns 0.0 unconditionally.**
- There is NO partial trace implementation (required for computing reduced density matrices).
- There is NO concurrence, EOF (entanglement of formation), or Schmidt rank.
- The only entanglement-adjacent function is `fidelity()` (line 341-358), which computes `|<psi|phi>|^2` for two pure states.

### What QpiAI validates

**`formalism.DensityMatrix`** provides:

| Method | Description |
|--------|-------------|
| `concurrence()` | Wootters concurrence for 2-qubit states (hardware-tested) |
| `eof()` | Entanglement of Formation |
| `schmidt_rank()` | Schmidt rank decomposition |
| `max_bell_value()` | Maximum Bell inequality violation |
| `partial_trace()` | For reduced density matrices |
| `partial_transpose()` | For Peres-Horodecki criterion |
| `teleportation_fidelity()` | Fidelity for quantum teleportation |

### Discrepancies

| Issue | qkdpy | QpiAI | Severity |
|-------|-------|-------|----------|
| entanglement_entropy | Returns 0.0 (stub) | Full concurrence + EOF | **MAJOR** |
| Partial trace | Not implemented | `partial_trace(qubits_to_keep, dims)` | **MAJOR** |
| Concurrence | Not available | `concurrence()` -- hardware-verified | **MAJOR** |
| EOF | Not available | `eof()` | MAJOR |
| Schmidt rank | Not available | `schmidt_rank()` | MAJOR |
| Bell value | Manual computation in E91 | `max_bell_value()` | MINOR |
| Fidelity | Pure-state only | Pure and mixed states | MEDIUM |

**Discrepancy Level: MAJOR.** `entanglement_entropy()` is a documented stub. Without partial trace, no entanglement measure can be computed for subsystems. For a QKD-focused library that implements E91, this is a critical gap since E91 fundamentally depends on entanglement verification.

---

## 5. Gate Implementations

### What qkdpy does

**`src/qkdpy/core/gates.py`** (lines 1-163): Defines 17 gate classes.

| Gate | qkdpy Matrix | Standard Matrix | Status |
|------|-------------|-----------------|--------|
| Identity | [[1,0],[0,1]] | [[1,0],[0,1]] | CORRECT |
| PauliX | [[0,1],[1,0]] | [[0,1],[1,0]] | CORRECT |
| PauliY | [[0,-i],[i,0]] | [[0,-i],[i,0]] | CORRECT |
| PauliZ | [[1,0],[0,-1]] | [[1,0],[0,-1]] | CORRECT |
| Hadamard | [[1,1],[1,-1]]/sqrt(2) | [[1,1],[1,-1]]/sqrt(2) | CORRECT |
| S | [[1,0],[0,i]] | [[1,0],[0,i]] | CORRECT |
| SDag | [[1,0],[0,-i]] | [[1,0],[0,-i]] | CORRECT |
| T | [[1,0],[0,exp(i*pi/4)]] | [[1,0],[0,exp(i*pi/4)]] | CORRECT |
| TDag | [[1,0],[0,exp(-i*pi/4)]] | [[1,0],[0,exp(-i*pi/4)]] | CORRECT |
| Rx(theta) | [[cos(theta/2), -i sin(theta/2)], [-i sin(theta/2), cos(theta/2)]] | Standard Rx | CORRECT |
| Ry(theta) | [[cos(theta/2), -sin(theta/2)], [sin(theta/2), cos(theta/2)]] | Standard Ry | CORRECT |
| Rz(theta) | [[exp(-i*theta/2), 0], [0, exp(i*theta/2)]] | Standard Rz | CORRECT |
| CNOT | [[1,0,0,0],[0,1,0,0],[0,0,0,1],[0,0,1,0]] | Standard CNOT | CORRECT |
| CZ | [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,-1]] | Standard CZ | CORRECT |
| SWAP | [[1,0,0,0],[0,0,1,0],[0,1,0,0],[0,0,0,1]] | Standard SWAP | CORRECT |

**All existing gate matrices are mathematically correct** -- no phase errors, sign errors, or normalization issues found.

### What QpiAI validates

QpiAI provides a significantly larger gate set (40+ gate names, audit lines 162-166):
- Additional single-qubit: SX, SXDG
- Additional two-qubit: CY, ISWAP, CP(theta), RZZ(theta), RXX(theta), RYY(theta)
- Additional three-qubit: CCX (Toffoli), CSWAP (Fredkin)
- Multi-controlled: MCX (arbitrary controls)
- Additional: Barrier, CH, CS, DCX, ECR, CRX, CRY, CRZ
- Parametric: U3, CU1, CU3, CU

### Discrepancies

| Issue | qkdpy | QpiAI | Severity |
|-------|-------|-------|----------|
| Existing gate correctness | All verified correct | Reference standard | **NONE** |
| Gate coverage | 17 gates | 40+ gates | MINOR (scope difference) |
| SX / sqrt-X | Missing | Available | MINOR |
| CY | Missing | Available | MINOR |
| CP (controlled phase) | Missing | Available | MINOR |
| Toffoli (CCX) | Missing | Available | MINOR |
| ISWAP | Missing | Available | MINOR |
| MCX | Missing | Available | MINOR |

**Discrepancy Level: NONE (for mathematical correctness of existing gates).** All of qkdpy's gate matrices are correct. The missing gates are a completeness gap but not a correctness issue.

---

## 6. Measurement Statistics

### What qkdpy does

**`Qubit.measure()`** (`src/qkdpy/core/qubit.py`, lines 93-133):
- Computational basis: Computes `|alpha|^2` and `|beta|^2`, uses `secure_random()` for probabilistic outcome. **CORRECT.**
- Hadamard basis: Applies H gate to rotate to computational basis, measures. **CORRECT.** (H maps X-eigenstates to Z-eigenstates.)
- Circular basis: Applies `[[1,-i],[1,i]]/sqrt(2)` gate to rotate to computational basis. **CORRECT.** (This is the S-dagger-H transformation that maps Y-eigenstates to Z-eigenstates.)

**`MultiQubitState.measure()`** (`src/qkdpy/core/multiqubit.py`, lines 245-310):
- Correctly computes marginal probabilities for a single qubit in a multi-qubit state.
- Correctly collapses and renormalizes the state after measurement.

**`Measurement.quantum_state_tomography()`** (`src/qkdpy/core/measurements.py`, lines 254-328):
- Measures in X, Y, Z bases by applying H (for X) and S-dagger-H (for Y) before computational measurement.
- Resets state to original before each measurement (assumes reproducible state preparation).
- Reconstructs density matrix from expectation values: `rho = (I + <X>X + <Y>Y + <Z>Z) / 2`. **CORRECT.**
- **Limitation:** Only works for pure states or identically prepared copies (the `_state = original.copy()` approach).

**`Measurement.measure_bell_state()`** (`src/qkdpy/core/measurements.py`, lines 218-252):
- Computes fidelities of a 2-qubit state against all 4 Bell states. **CORRECT.**

### What QpiAI validates

- Standard measurement via `circuit.measure(qubit, clbit)` and `circuit.measure_all()`
- Results returned via `JobResult.counts` (dict of bitstring to count)
- Statevector simulation provides direct probability access
- No dedicated tomography utility (user must build measurement circuits manually)
- Formalism level: `distinguishability()` for state discrimination

### Discrepancies

| Issue | qkdpy | QpiAI | Severity |
|-------|-------|-------|----------|
| Projective measurement | Correct | Standard | **NONE** |
| Basis rotation | H for X, Sdag-H for Y | Building blocks only | NONE |
| State collapse | Correctly implemented | Via measurement | NONE |
| Multi-qubit measurement | Correct marginal + collapse | Via circuit.measure() | NONE |
| Tomography (pure states) | Correct | Not provided | NONE |
| Tomography (mixed states) | **Not supported** (always resets) | Via DensityMatrix | **MEDIUM** |
| POVM support | None | None | LOW |

**Discrepancy Level: MINOR.** qkdpy's measurement implementations are mathematically correct. The main gap is that quantum state tomography only works for pure states because it resets the state to the original before each basis rotation.

---

## 7. Protocol Completeness

### What qkdpy implements

**BB84** (`src/qkdpy/protocols/bb84.py`):
- Implements the full BB84 protocol: state preparation, transmission, measurement, basis sifting, QBER estimation.
- Uses `secure_randint()` and `secure_choice()` for cryptographically secure randomness.
- Sending 5x more qubits than needed (line 40) to account for sifting.
- QBER estimation (line 152-181) compares full sifted key -- acceptable for simulation, though real QKD would sacrifice a subset.

**E91** (`src/qkdpy/protocols/e91.py`):
- Uses `MultiQubitState.ghz(2)` for Bell pair creation (line 90).
- Alice angles: [0, pi/4, pi/2]; Bob angles: [pi/4, pi/2, 3*pi/4].
- `measure_states()` (lines 70-136): Valid approach of combining preparation + measurement in one step since both parties act locally.
- `sift_keys()` (lines 138-164): Correctly filters for matching angles (pi/4 and pi/2 pairs).
- `test_bell_inequality()` (lines 177-239):
  - Correlation computed as `E = 2*P(match) - 1` -- **CORRECT** for Bell state |Phi+>.
  - The theoretical S-value = 4/sqrt(2) ≈ 2.828 for ideal statistics.
  - CHSH formula `S = E(A1,B1) - E(A1,B3) + E(A3,B1) + E(A3,B3)` -- **CORRECT**.
  - QBER estimation from Bell value: `0.5 * (1 - |S|/(2*sqrt(2)))` (line 237) -- **CORRECT**.

### What QpiAI provides

QpiAI provides general-purpose quantum algorithms:
- QRNG (most directly QKD-relevant): `QRNG(n_bits=256)` for key generation
- QFT, Grover, Shor, Simon, Bernstein-Vazirani, Deutsch-Jozsa, QPE, Amplitude Estimation, VQE, QAOA
- **No dedicated QKD protocol modules** (BB84, E91, B92, etc.)
- **No sifting/post-processing utilities**
- **No quantum channel model** with configurable noise parameters
- **No key distillation workflow**

### Discrepancies

| Aspect | qkdpy | QpiAI | Severity |
|--------|-------|-------|----------|
| BB84 implementation | Complete | Not available | NONE (different focus) |
| E91 implementation | Complete with CHSH test | Not available | NONE |
| Key generation | Protocol-based | QRNG algorithm | NONE |
| Channel simulation | Full with noise models | Basic (depol/ADC only) | NONE |
| Protocol completeness | QKD-focused | General-purpose | NONE |

**E91-specific math verification:**
- Correlation function for |Phi+> with Ry(-a) rotation: E(a,b) = cos(a-b). Mathematically verified.
- For matching angles (a=b): E = 1, perfect correlation. **CORRECT.**
- For CHSH test: S = 0.707 - (-0.707) + 0.707 + 0.707 = 2.828 (ideal). **CORRECT.**
- Bell violation threshold (|S| > 2): **CORRECT.**

**Discrepancy Level: NONE.** The protocols are a different domain focus, not directly comparable. qkdpy's BB84 and E91 implementations are mathematically sound for their purpose.

---

## 8. Integration Layer Bugs

**File:** `src/qkdpy/integrations/qpiai_integration.py`

### 8.1 `qpiai_to_qubit()` -- Phase Information Loss

**Lines 64-74:**
```python
def qpiai_to_qubit(self, qpiai_state: Statevector) -> Qubit:
    state = qpiai_state.data
    return Qubit(float(np.real(state[0])), float(np.real(state[1])))
```

**Bug:** This discards the imaginary components of the state vector. The `np.real()` calls strip all phase information.

- A state like `|+i> = (|0> + i|1>)/sqrt(2)` would be converted to `(1/sqrt(2), 0)` instead of `(1/sqrt(2), i/sqrt(2))`.
- The resulting Qubit would not be normalized (since |Im(state[1])|^2 is lost).
- Any quantum state with non-real amplitudes is silently corrupted.

**Correct implementation:**
```python
return Qubit(state[0], state[1])
```

**Discrepancy Level: MAJOR.** This is a correctness bug that corrupts any state with complex amplitudes during conversion.

### 8.2 `create_bb84_circuit()` -- Separate Qubit Registers

**Lines 127-169:**
```python
circuit = Circuit(num_qubits * 2, num_qubits * 2)
# Alice prepares and encodes qubits on wires 0..num_qubits-1
# Bob measures on wires num_qubits..2*num_qubits-1
```

**Issue:** Alice prepares qubits on one set of wires and Bob measures on a completely independent set of wires. There is **no quantum channel** connecting them. The operations on Alice's wires and Bob's wires are independent. This simulates separate random preparations and measurements, not the BB84 protocol.

In a correct BB84 simulation, Bob should measure the **same** qubits that Alice prepared (after channel effects). The circuit should use `num_qubits` qubits (not `2*num_qubits`), with Alice's preparation gates followed by Bob's measurement gates on the same qubits.

**Correct circuit structure:**
```python
circuit = Circuit(num_qubits, num_qubits)
# Alice prepares
for i in range(num_qubits):
    if alice_bit[i] == 1:
        circuit.X(i)
    if alice_bases[i] == "X":
        circuit.H(i)
# Channel effects would go here
# Bob measures
for i in range(num_qubits):
    if bob_bases[i] == "X":
        circuit.H(i)
# Measure all
for i in range(num_qubits):
    circuit.MEASURE(i, i)
```

**But note:** This still doesn't model channel loss, noise, or eavesdropping -- those would need to be added.

**Discrepancy Level: MAJOR.** The circuit structure is physically incorrect for BB84 simulation.

---

## 9. Summary Table

| # | Area | Discrepancy Level | Key Finding | Priority |
|---|------|-------------------|-------------|----------|
| 1 | State vector | MINOR | No unified Statevector; separate Qubit/MultiQubitState | LOW |
| 2 | Density matrix | **MAJOR** | Pure-state only; no mixed state support; purity/entropy functions return trivial values | **HIGH** |
| 3a | Depolarizing noise | **MAJOR** | Identity included in random choice; error rate is 3/4 of intended value | **HIGH** |
| 3b | Amplitude damping | **MAJOR** | Nested probability gives gamma^2 effect; all coherence destroyed | **HIGH** |
| 3c | Noise representation | **MAJOR** | State vector approach cannot represent mixed states; needs density matrix + Kraus | **HIGH** |
| 4 | Entanglement measures | **MAJOR** | entanglement_entropy() is a stub returning 0.0; no partial trace | **HIGH** |
| 5 | Gate correctness | NONE | All 17 gate matrices verified correct | NONE |
| 6 | Measurement | MINOR | Correct for projective measurement; tomography limited to pure states | MEDIUM |
| 7 | Protocol completeness | NONE | BB84/E91 logic sound; CHSH math verified correct | NONE |
| 8a | qpiai_to_qubit() | **MAJOR** | Imaginary components stripped via np.real(); corrupts complex states | **HIGH** |
| 8b | BB84 circuit integration | **MAJOR** | Separate qubit registers; no quantum channel between Alice and Bob | **HIGH** |

### Executive Summary

**Mathematical correctness audit of qkdpy against QpiAI Quantum SDK reveals:**

1. **Gate matrices are fully correct** (17/17 verified against standard definitions). No phase, sign, or normalization errors.

2. **BB84 and E91 protocol logic is sound.** CHSH inequality calculation in E91 is mathematically verified with E(a,b) = cos(a-b) correlation for |Phi+> Bell state.

3. **Four critical issues requiring attention (HIGH priority):**
   - **Noise channels have mathematical errors** -- depolarizing includes Identity in Pauli set, amplitude damping has nested-probability bug, and all use state-vector approach that cannot model mixed states.
   - **No mixed state density matrix support** -- purity, entropy, and entanglement functions are effectively dead code.
   - **Integration conversion corrupts complex amplitudes** -- `qpiai_to_qubit()` uses `np.real()` on both components, discarding phase information.
   - **BB84 integration circuit has no quantum channel** -- Alice and Bob operate on separate, unconnected qubit registers.

4. **Architectural limitation:** The state-vector-only approach in qkdpy's noise channels is fundamentally insufficient for modeling noisy quantum channels. The correct approach requires density matrix evolution with Kraus operators (as demonstrated by QpiAI's `formalism.DensityMatrix`).
