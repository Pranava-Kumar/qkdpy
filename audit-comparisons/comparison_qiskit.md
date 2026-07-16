# QKDpy vs Qiskit: Core Quantum Logic Comparison

**Date:** 2026-07-14
**Scope:** qkdpy core quantum logic vs Qiskit 1.x hardware-verified implementations
**Source files audited:** `qubit.py`, `gates.py`, `gate_utils.py`, `measurements.py`, `channels.py`, `multiqubit.py`, `bb84.py`, `e91.py`, `security_analysis.py`, `base.py`
**Qiskit reference:** `audit_qiskit.md` and qiskit source tree

---

## Table of Contents

1. [Qubit State Evolution](#1-qubit-state-evolution)
2. [Measurement](#2-measurement)
3. [Density Matrix](#3-density-matrix)
4. [Channel Noise Models](#4-channel-noise-models)
5. [BB84 Protocol Logic](#5-bb84-protocol-logic)
6. [E91 Protocol Logic](#6-e91-protocol-logic)
7. [QBER Calculation](#7-qber-calculation)
8. [Security Analysis](#8-security-analysis)
9. [Additional Issues Found](#9-additional-issues-found)

---

## 1. Qubit State Evolution

### What qkdpy does

**File:** `E:/opensource/qkdpy/src/qkdpy/core/qubit.py`, lines 73-91

`Qubit.apply_gate(gate)` applies a 2x2 unitary matrix to a single-qubit statevector:
```python
self._state = gate @ self._state
```
It validates unitarity via `np.allclose(gate @ gate.conj().T, I, atol=1e-10)` and rejects non-2x2 matrices.

**File:** `E:/opensource/qkdpy/src/qkdpy/core/multiqubit.py`, lines 145-243

`MultiQubitState.apply_gate(gate, target_qubits)` supports multi-qubit gates through two strategies:
- **Single target qubit:** builds I x I x ... x gate x ... x I via tensor product, then applies
- **Multiple target qubits:** custom bit-manipulation loop that iterates over all basis states and applies the gate submatrix

### What Qiskit does

**File:** `E:/opensource/qiskit/qiskit/quantum_info/states/statevector.py`

`Statevector.evolve(other, qargs=None)` applies an operator/channel/instruction to a subsystem. It:
- Accepts `Operator`, `QuantumCircuit`, `Instruction`, or `Channel` objects
- Tracks subsystem dimensions via `dims()` tuple
- Handles global phase naturally (statevector is defined up to global phase)
- Supports partial application (specify which qubits via `qargs`)

Qiskit gates are defined as `Gate` subclass instances with `_define()` methods that build circuit definitions, not just raw matrices.

### Discrepancies

| Issue | Detail | Severity |
|-------|--------|----------|
| **Single-qubit only** | qkdpy's `Qubit` class only handles 1-qubit gates. Multi-qubit operations require `MultiQubitState`. Qiskit unifies both via `Statevector.evolve()`. | MINOR |
| **Global phase tracking** | qkdpy does not explicitly track global phase. `__eq__` uses `np.allclose` which is sensitive to global phase, so two physically equivalent states differing by e^(iθ) will NOT compare equal. Qiskit's `Statevector.__eq__` also compares directly, but Qiskit explicitly documents this. | MINOR |
| **Gate validation** | qkdpy validates unitarity but NOT that the matrix is exactly 2x2 for qubit gates (beyond shape). Shape check on line 83 ensures (2,2) so this is fine. Qiskit's `Operator` constructor validates that the input is a valid quantum operation. | NONE |
| **Multi-qubit gate algorithm** | The general multi-qubit gate algorithm (multiqubit.py lines 192-239) uses a custom bit-manipulation loop. This is mathematically correct but O(4^n) in the worst case. Qiskit builds the full operator via tensor products. | MINOR |
| **Endianness** | qkdpy uses MSB-0 convention (qubit 0 is most significant bit). Qiskit uses LSB-0 convention (qubit 0 is least significant bit). Consistent within each system, but incompatible without conversion. | MINOR |

### Verdict

**Discrepancy level: MINOR.** Statevector evolution is mathematically correct. The endianness convention difference is the most practically significant issue for cross-framework comparisons. No logical errors in the evolution math.

---

## 2. Measurement

### What qkdpy does

**File:** `E:/opensource/qkdpy/src/qkdpy/core/qubit.py`, lines 93-133

`Qubit.measure(basis)` uses a **temp qubit approach**:
1. Copies the state into a temporary `Qubit`
2. Applies basis-rotation gate to temp qubit
3. Samples a result from temp qubit's computational-basis probabilities
4. Returns the result -- **the original qubit is NOT collapsed**

Basis rotation matrices:
- Computational (Z): identity (measure directly)
- Hadamard (X): `[[1, 1], [1, -1]] / sqrt(2)` -- correct
- Circular (Y): `[[1, -1j], [1, 1j]] / sqrt(2)` -- correct (maps Y eigenstates to Z)

**File:** `E:/opensource/qkdpy/src/qkdpy/core/qubit.py`, lines 135-158

`Qubit.collapse_state(result, basis)` is a **separate method** that sets the state to the appropriate eigenstate:
- Computational 0/1: |0> or |1>
- Hadamard 0/1: |+> or |->
- Circular 0/1: (|0> + i|1>)/sqrt(2) or (|0> - i|1>)/sqrt(2)

**File:** `E:/opensource/qkdpy/src/qkdpy/core/measurements.py`, lines 21-49

`Measurement.measure_in_basis(qubit, basis)` delegates to `Qubit.measure()` for qubits.

### What Qiskit does

**File:** `E:/opensource/qiskit/qiskit/quantum_info/states/statevector.py`

`Statevector.measure(qargs=None)` performs projective measurement and returns `(outcome, Statevector)` where the returned `Statevector` IS the collapsed state. The original statevector is not modified (immutable pattern). Qiskit also provides `sample_counts()` and `sample_memory()` for efficient sampling.

For circuit-based measurement:
```python
qc.measure(qubit, cbit)  # irreversible measurement in circuit model
```

Qiskit's circuit measurement is a fundamentally different paradigm -- it records outcomes to classical registers and the measurement is part of the circuit execution, not a statevector manipulation.

### Discrepancies

| Issue | Detail | Severity |
|-------|--------|----------|
| **Measure doesn't collapse** | qkdpy's `measure()` does NOT collapse the qubit state. The temp qubit is discarded. This means calling `measure()` twice without `collapse_state()` gives two independent samples -- a physically impossible scenario for projective measurements (second measurement must yield the same result). | **MAJOR** |
| **Disjoint API** | `measure()` and `collapse_state()` are separate calls, allowing callers to get a measurement result but then continue evolving the uncollapsed state -- also unphysical. Qiskit's `Statevector.measure()` returns the collapsed state as a new object, enforcing correct physics. | **MAJOR** |
| **collapse_state is forceful** | `collapse_state()` always sets the qubit to the exact eigenstate, regardless of what the state actually was. If a caller passes an incorrect `result`, the state is forced to an outcome inconsistent with the previous measurement. No validation. | MINOR |

### Root Cause

The temp-qubit pattern suggests the author was aware that measurement should collapse the state but wanted to avoid modifying the original qubit. The correct approach is either:
- Return a NEW qubit (collapsed) from `measure()`, leaving the original unchanged (Qiskit pattern)
- Modify the qubit in-place during `measure()` (simpler but less flexible)

The current implementation splits the operation across two methods, creating an API that permits physically impossible sequences.

### Verdict

**Discrepancy level: MAJOR.** The measurement API permits unphysical operations (multiple independent measurements without collapse, evolving an already-measured state). Fix requires redesigning the measure/collapse contract.

---

## 3. Density Matrix

### What qkdpy does

**File:** `E:/opensource/qkdpy/src/qkdpy/core/qubit.py`, lines 160-167

```python
def density_matrix(self) -> np.ndarray:
    return np.outer(self._state, np.conjugate(self._state))
```

This computes |psi><psi|, which is correct ONLY for pure states.

**File:** `E:/opensource/qkdpy/src/qkdpy/core/multiqubit.py`, lines 312-318

Same pure-state-only implementation for multi-qubit states.

**File:** `E:/opensource/qkdpy/src/qkdpy/core/measurements.py`, lines 147-172

`Measurement.measure_purity()` and `Measurement.measure_von_neumann_entropy()` operate on the pure-state density matrix. `purity()` will always return 1.0 (since the density matrix is always pure), and `measure_von_neumann_entropy()` will always return 0.0 for the same reason.

### What Qiskit does

**File:** `E:/opensource/qiskit/qiskit/quantum_info/states/densitymatrix.py`

`DensityMatrix` is a first-class object that:
- Accepts statevectors (auto-converts to |psi><psi|)
- Accepts mixed states directly (e.g., p*|0><0| + (1-p)*|1><1|)
- Supports `evolve()` with channels (Kraus operators), enabling correct noise simulation
- Has `purity()` method that returns meaningful values for mixed states
- Has `to_statevector()` for pure states
- Has `probabilities()`, `probabilities_dict()`, `measure()` methods

**File:** `E:/opensource/qiskit/qiskit/quantum_info/states/measures.py`

Entropy, purity, and fidelity functions accept both `Statevector` and `DensityMatrix`.

### Discrepancies

| Issue | Detail | Severity |
|-------|--------|----------|
| **Pure states only** | qkdpy's density_matrix() is always a rank-1 projector. No mixed state representation exists anywhere in the codebase. | **MAJOR** |
| **Purity always 1.0** | `Measurement.measure_purity()` (measurements.py line 170) will always return 1.0 regardless of noise or decoherence, since rho is always pure. Misleading for analysis. | **MAJOR** |
| **Entropy always 0** | `Measurement.measure_von_neumann_entropy()` (measurements.py line 175) will always return 0.0 for the same reason. | MAJOR |
| **Noise simulation limited** | Since channels.py noise models operate on statevectors (unraveling), the ensemble-averaged mixed state can never be computed. Analysis of decoherence effects is impossible. | MAJOR |

### Impact

The absence of mixed state support means:
- All noise models produce pure states (single noise trajectory)
- Statistical analysis of noise requires external Monte Carlo
- Critical QKD metrics (entropy, Holevo bound, etc.) cannot be computed from the internal state

### Verdict

**Discrepancy level: MAJOR.** The lack of mixed state support is a fundamental limitation. Fix requires introducing a `DensityMatrix` class alongside `Qubit`/`MultiQubitState`, and implementing Kraus operator evolution.

---

## 4. Channel Noise Models

### What qkdpy does

**File:** `E:/opensource/qkdpy/src/qkdpy/core/channels.py`

All noise models operate on **pure statevectors via the statevector unraveling** -- each application randomly picks a Kraus operator and applies it to the pure state, which is valid for individual trajectories but cannot represent the ensemble-averaged mixed state.

#### 4a. Depolarizing Noise (lines 202-217)

```python
if np.random.random() < self.noise_level:
    gate = random.choice([I, X, Y, Z])
    qubit.apply_gate(gate)
```

This applies a random Pauli with probability `p = noise_level`. The effective channel is:
- With prob (1-p): identity (no change)
- With prob p/4: X, Y, Z, or I

This gives: rho -> (1-p+p/4)rho + p/4 (X rho X + Y rho Y + Z rho Z) = (1-3p/4)rho + p/4 (X rho X + Y rho Y + Z rho Z)

This matches the standard depolarizing channel definition. **Mathematically correct.**

#### 4b. Bit Flip Noise (lines 219-224)

```python
if np.random.random() < self.noise_level:
    qubit.apply_gate(PauliX().matrix)
```

This gives: rho -> (1-p)rho + p X rho X. **Correct.**

#### 4c. Phase Flip Noise (lines 226-231)

```python
if np.random.random() < self.noise_level:
    qubit.apply_gate(PauliZ().matrix)
```

This gives: rho -> (1-p)rho + p Z rho Z. **Correct.**

#### 4d. Amplitude Damping Noise (lines 233-241) -- BUG

```python
if np.random.random() < self.noise_level:
    gamma = self.noise_level
    if qubit.probabilities[1] > 0 and np.random.random() < gamma:
        qubit._state = np.array([1, 0], dtype=complex)
```

**Two bugs:**
1. **Double probability factor:** The outer check uses `noise_level` and the inner check also uses `noise_level` (= gamma). The effective damping rate is `noise_level^2 * P(|1>)`, which is wrong. The correct rate should be just `noise_level * P(|1>)`.

2. **Incorrect operation:** When damping occurs, the state is collapsed to |0> regardless of the original state's |0> amplitude. The correct Kraus operators for amplitude damping are:
   - K0 = [[1, 0], [0, sqrt(1-gamma)]]
   - K1 = [[0, sqrt(gamma)], [0, 0]]

   So the non-jump evolution (K0) preserves the |0> component: K0|psi> = alpha|0> + sqrt(1-gamma)*beta|1>, NOT |0>.

### What Qiskit does

**File:** `E:/opensource/qiskit/qiskit/quantum_info/operators/channel/kraus.py`
**File:** `E:/opensource/qiskit/qiskit/quantum_info/operators/channel/superop.py`

Qiskit's quantum_info module provides:
- `Kraus` class -- represents a quantum channel via Kraus operators
- `SuperOp` class -- superoperator (Choi-Jamiolkowski) representation
- `Stinespring` -- Stinespring dilation representation
- `Chi` -- chi matrix representation
- `Operator` -- can be applied as a channel via `evolve()`

Kraus operators can be applied to `DensityMatrix` via `density_matrix.evolve(kraus_channel)`, giving the correct ensemble-averaged mixed state.

The correct amplitude damping channel:
```python
K0 = np.array([[1, 0], [0, np.sqrt(1-gamma)]])
K1 = np.array([[0, np.sqrt(gamma)], [0, 0]])
channel = Kraus([K0, K1])
```

### Discrepancies

| Noise Model | qkdpy | Qiskit | Severity |
|-------------|-------|--------|----------|
| **Depolarizing** | Statevector unraveling with Pauli selection (correct math) | `Kraus`/`SuperOp` + `DensityMatrix.evolve()` | MINOR |
| **Bit flip** | Statevector unraveling (correct) | Kraus operators | MINOR |
| **Phase flip** | Statevector unraveling (correct) | Kraus operators | MINOR |
| **Amplitude damping** | **DOUBLE PROBABILITY BUG:** rate = p^2 instead of p. **WRONG COLLAPSE:** collapses to |0> instead of applying K0/K1. | **MAJOR** |
| **Density matrix evolution** | NOT SUPPORTED -- all noise produces pure states | Full mixed-state evolution via Kraus operators | **MAJOR** |
| **Multi-qubit noise** | Skipped for qudits, partial support for qubits | Full tensor-product noise | MINOR |

### Mathematical Fix for Amplitude Damping

Replace the current implementation with:

```python
def _amplitude_damping_noise(self, qubit: Qubit) -> Qubit:
    gamma = self.noise_level
    alpha, beta = qubit.state

    # Roll the dice for a quantum jump
    jump_prob = min(1.0, gamma * abs(beta)**2)

    if np.random.random() < jump_prob:
        # Quantum jump: K1|psi> / norm -> |0>
        qubit._state = np.array([1.0 + 0j, 0.0 + 0j])
        self.error_count += 1
    else:
        # No jump: K0|psi> / norm
        new_alpha = alpha
        new_beta = np.sqrt(1 - gamma) * beta
        norm = np.sqrt(abs(new_alpha)**2 + abs(new_beta)**2)
        qubit._state = np.array([new_alpha / norm, new_beta / norm])

    return qubit
```

### Verdict

**Discrepancy level: MAJOR** (for amplitude damping and the absence of mixed-state density matrix evolution). The other noise models are statevector unravelings that are mathematically correct but limited to pure-state trajectories.

---

## 5. BB84 Protocol Logic

### What qkdpy does

**File:** `E:/opensource/qkdpy/src/qkdpy/protocols/bb84.py`

The protocol flow (from `base.py` `execute()` at lines 130-219):
1. Alice prepares random bits in random bases (Z or X), encoding |0>, |1>, |+>, |->
2. Qubits transmitted through `QuantumChannel` with optional noise/loss/eavesdropping
3. Bob measures in random bases (Z or X)
4. Bases are compared publicly; matching-basis bits form the sifted key
5. QBER is estimated from the full sifted key
6. Cascade error correction is applied
7. Privacy amplification via Toeplitz hashing

**State preparation (lines 50-83):**
- Computational basis: `Qubit.zero()` for bit 0, `Qubit.one()` for bit 1
- Hadamard basis: `Qubit.plus()` for bit 0, `Qubit.minus()` for bit 1
- This correctly implements the four BB84 states

**Basis reconciliation check (lines 119-150):**
- Keeps bits where Alice's basis == Bob's basis
- Bob's measurement result (in matching basis) should equal Alice's original bit
- Correct sifting logic

**QBER estimation (lines 152-181):**
- Uses ALL sifted bits for estimation
- No sacrificial subset (acceptable for simulation)
- Formula: errors / total_bits -- correct

### What Qiskit verifies

**From audit section 6.1-6.2:**

Qiskit implements BB84 via circuit-based simulation:
- |0>: default after reset
- |1>: `qc.x(0)`
- |+>: `qc.h(0)` applied to |0>
- |->: `qc.h(0); qc.z(0)` or `qc.h(0); qc.x(0)`

X-basis measurement: `qc.h(qubit); qc.measure(qubit, cbit)`

Qiskit's approach uses `Statevector.from_label()` for state preparation and circuit-based simulation for measurement.

### Discrepancies

| Issue | Detail | Severity |
|-------|--------|----------|
| **QBER estimation consumes full key** | qkdpy uses ALL sifted bits for QBER estimation. In real BB84, only a randomly chosen subset is sacrificed. qkdpy's approach is valid for simulation (gives more accurate QBER) but doesn't model the key-length reduction. | MINOR |
| **parallel measurement model** | qkdpy simulates sequential prepare-transmit-measure. Qiskit uses circuit-based simulation where prepare and measure are in one circuit. Both are valid models at different abstraction levels. | NONE |
| **Basis choice randomness** | qkdpy uses `secure_choice` (CSPRNG). Qiskit uses `np.random` or quantum randomness. Acceptable for simulation. | NONE |
| **BB84 state set** | qkdpy encodes |0>, |1>, |+>, |-> correctly. Gates match Qiskit's canonical representation. | NONE |
| **Intercept-resend QBER** | qkdpy should produce 25% QBER under intercept-resend (Eve guesses wrong basis 50%, causes error 50% of those = 25%). Channel implementation supports this correctly. | NONE |
| **Security threshold** | 11% is the correct theoretical threshold for BB84 with one-way classical post-processing. | NONE |

### Verdict

**Discrepancy level: MINOR.** The BB84 protocol implementation is logically sound and matches the standard specification. The minor issue is using the full sifted key for QBER estimation rather than a sacrificial subset, which is acceptable for simulation purposes.

---

## 6. E91 Protocol Logic

### What qkdpy does

**File:** `E:/opensource/qkdpy/src/qkdpy/protocols/e91.py`

Protocol flow:
1. Generate Bell pairs: `MultiQubitState.ghz(2)` = (|00> + |11>)/sqrt(2) = |Phi+>
2. Alice and Bob randomly choose measurement settings
3. Alice measures qubit 0 (applies Ry(-angle) then computational measurement)
4. Bob measures qubit 1 from the collapsed state (applies Ry(-angle) then computation measurement)
5. Key sifting: keep bits where Alice and Bob used the same angle (pi/4 and pi/2)
6. Bell test on mismatched settings for CHSH inequality

**Measurement angles:**
- Alice: {0, pi/4, pi/2}
- Bob: {pi/4, pi/2, 3pi/4}
- Matching for key: pi/4 and pi/2

**CHSH calculation (lines 177-239):**
```
S = E(A1, B1) - E(A1, B3) + E(A3, B1) + E(A3, B3)
```
where A1=0, A3=pi/2, B1=pi/4, B3=3pi/4. Expects S = 2*sqrt(2) for ideal Bell state. This matches the standard Ekert91 CHSH test.

### What Qiskit verifies

**From audit section 6.4-6.6:**

Qiskit E91 approach:
```python
qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)  # Bell state |Phi+>
# Alice H then measurement on qubit 0
# Bob H then measurement on qubit 1
```

Qiskit uses Hadamard-based measurement in the X basis, while qkdpy uses Ry rotations. Both are valid -- Ry gives continuous angle control while H gives the specific X-basis rotation.

### Discrepancies

| Issue | Detail | Severity |
|-------|--------|----------|
| **Sequential vs simultaneous measurement** | qkdpy measures Alice THEN Bob on the collapsed state. This gives the correct correlation statistics for Bell states but is physically different from simultaneous measurement. | MINOR |
| **Bell state preparation** | qkdpy uses `MultiQubitState.ghz(2)` = (|00> + |11>)/sqrt(2). Qiskit uses H + CX = (|00> + |11>)/sqrt(2). Both produce the same |Phi+> state. | NONE |
| **Key generation angles** | qkdpy keeps matches at pi/4 and pi/2. For |Phi+> at matching angles, P(same) = cos^2(0) = 1. Perfect correlation expected. Correct. | NONE |
| **CHSH formula** | S = E(A1,B1) - E(A1,B3) + E(A3,B1) + E(A3,B3). For the chosen angles, this gives S = 4/sqrt(2) = 2.828. Calculation matches comments. | NONE |
| **E correlation calculation** | `E = 2 * match_prob - 1` is the correct formula for the correlation coefficient E = P(same) - P(diff). | NONE |
| **Bell test uses full data** | The CHSH value is computed from all available (non-sifted) data. This is correct -- the Bell test and key generation use disjoint measurement settings. | NONE |
| **Loss handling** | If a qubit is lost, results are set to -1 and skipped in analysis. Correct. | NONE |

### Verdict

**Discrepancy level: MINOR.** The E91 protocol is mathematically sound. The sequential measurement approach is an implementation detail that produces identical correlation statistics. The CHSH calculation and key sifting logic are correct.

---

## 7. QBER Calculation

### What qkdpy does

**BB84** (bb84.py lines 152-181):
```python
qber = errors / sample_size
```
where `errors = count of mismatched bits` and `sample_size = len(sifted_key)`.

**E91** (e91.py lines 166-175):
```python
errors = sum(1 for a, b in zip(alice_sifted, bob_sifted, strict=False) if a != b)
return errors / len(alice_sifted)
```

Both compute QBER = (number of mismatched bits) / (total compared bits).

### What Qiskit validates

The audit mentions `calculate_qber(counts, alice_bases, bob_bases)` in the existing integration, which computes QBER from measurement outcome counts. The formula is equivalent: QBER = P(bit mismatch | same basis).

### Discrepancies

| Issue | Detail | Severity |
|-------|--------|----------|
| **QBER formula** | qkdpy's formula QBER = mismatches / total is the standard and physically correct formula for QBER. | NONE |
| **Statistical approach** | qkdpy uses the full sifted key (or full data in E91). This gives maximum statistical accuracy for simulation. | NONE |

### Verdict

**Discrepancy level: NONE.** The QBER formula is physically correct and matches the standard definition.

---

## 8. Security Analysis

### What qkdpy does

**File:** `E:/opensource/qkdpy/src/qkdpy/core/security_analysis.py`

**SecurityAnalyzer.perform_security_analysis** (lines 28-89):
- Compares QBER against protocol-specific threshold
- Computes key rate after correction: `R = R_raw * max(0, I_AB - I_AE) * efficiency`
- where `I_AB = 1 - h2(QBER)` and `I_AE = h2(QBER)` (for BB84)
- Estimates security parameters (visibility, multi-photon probability, etc.)
- Analyzes vulnerabilities to various attack types

**Key rate formula details (lines 112-157):**
```python
mutual_ab = 1 - h2(qber)
mutual_ae = h2(qber)
corrected_rate = raw_rate * max(0, mutual_ab - mutual_ae)
# Then multiplied by protocol efficiency factor
```

**Eve information estimation** (base.py lines 329-344):
```python
return min(1.0, qber * 2)
```

**Security thresholds** (security_analysis.py lines 91-110):
- BB84: 0.11 (11%)
- E91: 0.071 (7.1%)
- SARG04: 0.146
- six-state: 0.127

### What Qiskit does

**File:** `E:/opensource/qiskit/qiskit/quantum_info/states/measures.py`
**File:** `E:/opensource/qiskit/qiskit/quantum_info/operators/measures.py`

Qiskit provides the building blocks for security analysis but no end-to-end QKD security analyzer:
- `state_fidelity()` -- fidelity between two quantum states
- `purity()` -- purity of a state
- `entropy()` -- von Neumann entropy
- `concurrence()` -- entanglement measure
- `negativity()` -- entanglement measure
- `process_fidelity()` -- channel quality measure
- `average_gate_fidelity()` -- gate quality measure
- `diamond_norm()` -- diamond distance for channel discrimination

Qiskit does NOT provide protocol-level security analysis (that's application-level).

### Discrepancies

| Issue | Detail | Severity |
|-------|--------|----------|
| **Key rate formula double-counts efficiency** | The formula applies the Devetak-Winter bound (I_AB - I_AE) which already accounts for privacy amplification overhead, THEN multiplies by a protocol efficiency factor. If `raw_rate` is already the sifted key rate, the efficiency factor double-counts sifting (50% for BB84). | MINOR |
| **Eve information model** | `min(1.0, qber * 2)` is extremely crude. For QBER=0.11, this gives I_AE = 0.22, which doesn't match the actual bound I_AE <= h2(0.11) ≈ 0.5. The `_calculate_corrected_key_rate` uses h2(QBER) for I_AE, but the `_estimate_eve_information` uses the linear model for privacy amplification leakage estimation. Inconsistent models. | MINOR |
| **Security level scoring** | The 1-5 security level score (lines 299-339) uses ad-hoc weighting: safety_margin * 3 capped at 2, vulnerability score 2*(1-max_vuln), plus base 1. This is not grounded in any standard security metric. | MINOR |
| **Attack vulnerability analysis** | The vulnerability assessments use fixed numerical heuristics (e.g., PNS vulnerability = min(1.0, mean_photon_number * 2.0)) that are not derived from physical models. These are qualitative indicators at best. | MEDIUM |
| **Entanglement attack model** | `channels.py` entanglement_attack (lines 325-357) applies a random rotation with 50% probability and randomly declares detection. This is NOT a physically meaningful entanglement attack -- a real attack would involve an entangled ancilla interacting with the signal qubit. | **MAJOR** |
| **E91 security threshold** | The E91 threshold of 0.071 corresponds to the CHSH violation condition. For |Phi+>, QBER = (1 - <CHSH>/(2*sqrt(2)))/2. When CHSH = 2, QBER = (1 - 2/(2*sqrt(2)))/2 ≈ 0.146. The actual bound for E91 is closer to 0.146, not 0.071. The threshold 0.071 is more conservative than necessary. | MINOR |

### Verdict

**Discrepancy level: MINOR** (with one MAJOR for the entanglement attack model). The security analysis provides reasonable high-level indicators but uses simplified/approximate models that don't match rigorous QKD security proofs. Key rate calculations have mild double-counting issues.

---

## 9. Additional Issues Found

### 9.1 Entanglement Entropy is a Stub

**File:** `E:/opensource/qkdpy/src/qkdpy/core/multiqubit.py`, lines 320-339

```python
def entanglement_entropy(self, subsystem_qubits: list[int]) -> float:
    # This is a complex calculation that would require partial trace computation
    # For now, we'll return a placeholder
    return 0.0
```

Always returns 0.0. This is a placeholder that silently returns wrong results. The function needs partial trace computation followed by von Neumann entropy of the reduced density matrix.

- **Discrepancy level: MAJOR**
- **Priority: HIGH**

### 9.2 GateUtils basis_switch 'circular' vs Qubit.measure 'circular' Matrix Difference

**File:** `E:/opensource/qkdpy/src/qkdpy/core/gate_utils.py`, line 28
```python
return np.array([[1, 1], [1j, -1j]], dtype=complex) / math.sqrt(2)
```

**File:** `E:/opensource/qkdpy/src/qkdpy/core/qubit.py`, line 122
```python
circ_gate = np.array([[1, -1j], [1, 1j]], dtype=complex) / math.sqrt(2)
```

These are adjoints of each other: `GateUtils = (Qubit.measure)†`. GateUtils maps from Z to Y basis; Qubit.measure maps from Y to Z basis. This is **not a bug** -- they serve inverse purposes (state preparation vs measurement). However, the inconsistency in naming could confuse users.

- **Discrepancy level: NONE** (consistent under inversion)
- **Priority: LOW**

### 9.3 Cascade Error Correction is Simplified

**File:** `E:/opensource/qkdpy/src/qkdpy/protocols/base.py`, lines 233-285

The Cascade implementation uses a single pass with block size 4 and binary search for error location. Real Cascade uses multiple passes with exponentially increasing block sizes. This simplified version will miss errors that have even parity within blocks and cannot correct all errors above the QBER threshold.

- **Discrepancy level: MINOR** (acceptable for simulation)
- **Priority: LOW**

### 9.4 Privacy Amplification Security Parameter Too Small

**File:** `E:/opensource/qkdpy/src/qkdpy/protocols/base.py`, line 305

```python
s = 10  # Security parameter
```

The leftover hash lemma gives key length r = n - s - leak. With s=10, the statistical distance from uniform is 2^(-10/2) = 2^(-5) ≈ 0.03, which is not cryptographically negligible. For QKD applications, s should be at least 64-128.

- **Discrepancy level: MEDIUM**
- **Priority: MEDIUM**

### 9.5 MultiQubitState.apply_gate for Multi-Qubit Gates Uses O(4^n) Algorithm

**File:** `E:/opensource/qkdpy/src/qkdpy/core/multiqubit.py`, lines 192-239

The general multi-qubit gate algorithm iterates over ALL 2^n basis states and for each non-zero amplitude, iterates over ALL gate output rows. This is O(4^n) in the worst case. For n=10 qubits, this would require ~10^12 operations. The single-qubit gate case uses efficient tensor products (O(2^n)).

- **Discrepancy level: MINOR** (performance issue, not correctness)
- **Priority: LOW**

### 9.6 Unitarity Check Uses Fixed Tolerance

**File:** `E:/opensource/qkdpy/src/qkdpy/core/qubit.py`, line 88

```python
if not np.allclose(gate @ gate.conj().T, identity, atol=1e-10):
```

The tolerance is hardcoded at 1e-10. Qiskit's `Operator.is_unitary()` uses configurable tolerance via `TolerancesMixin`. For some numerical use cases, this tolerance may be too tight or too loose.

- **Discrepancy level: MINOR**
- **Priority: LOW**

### 9.7 Unitary Gate Check Uses Conjugate Transpose (right), but Could Use `rtol` as Well

`np.allclose(gate @ gate.conj().T, identity, atol=1e-10)` only uses `atol` without `rtol`. The `np.allclose` default `rtol=1e-05` would still apply. For very small matrices this is fine.

- **Discrepancy level: NONE**
- **Priority: LOW**

---

## Summary Table

| Area | Discrepancy Level | Key Issues | Priority |
|------|-------------------|------------|----------|
| **1. Qubit State Evolution** | MINOR | Global phase not tracked; MSB-0 endianness differs from Qiskit | LOW |
| **2. Measurement** | **MAJOR** | measure() doesn't collapse; separate collapse_state() permits unphysical operations | **HIGH** |
| **3. Density Matrix** | **MAJOR** | Pure states only; no mixed state support; purity/entropy always trivial | **HIGH** |
| **4. Channel Noise Models** | **MAJOR** | Amplitude damping has double-probability bug and wrong collapse; no mixed-state evolution | **HIGH** |
| **5. BB84 Protocol** | MINOR | Full key used for QBER estimation (no sacrificial subset) | LOW |
| **6. E91 Protocol** | MINOR | Sequential measurement model; physically correct correlations | LOW |
| **7. QBER Calculation** | NONE | Formula is correct | -- |
| **8. Security Analysis** | MINOR | Key rate may double-count efficiency; entanglement attack is non-physical | MEDIUM |
| **9.1 Entanglement Entropy** | **MAJOR** | Stub returning 0.0 | **HIGH** |
| **9.4 Privacy Amplification** | MEDIUM | Security parameter s=10 is too small | MEDIUM |

### Priority Fix Order

1. **HIGH -- Amplitude damping noise** (channels.py:233-241): Double probability bug and wrong Kraus operator. Fix the implementation to use correct Kraus operators K0/K1.

2. **HIGH -- Measurement API redesign** (qubit.py:93-133): The temp-qubit + separate collapse_state pattern permits unphysical operations. Either make `measure()` collapse in-place or return the collapsed state as a new object (Qiskit pattern).

3. **HIGH -- Entanglement entropy stub** (multiqubit.py:320-339): Implement proper partial trace + von Neumann entropy, or raise NotImplementedError instead of silently returning 0.0.

4. **HIGH -- Density matrix / mixed state support**: Introduce proper mixed-state representation. Without this, all noise analysis is fundamentally limited to pure-state trajectories.

5. **MEDIUM -- Entanglement attack model** (channels.py:325-357): Replace random rotation with a physically meaningful entanglement+ancilla model.

6. **MEDIUM -- Privacy amplification security parameter** (base.py:305): Increase s from 10 to at least 64.

7. **LOW -- Key rate formula ambiguity** (security_analysis.py:112-157): Clarify whether `raw_rate` is pre- or post-sifting, and remove or justify the efficiency factor.

---

## Appendix: Key File:Line References

| Issue | File | Lines |
|-------|------|-------|
| Qubit.apply_gate | `E:/opensource/qkdpy/src/qkdpy/core/qubit.py` | 73-91 |
| Qubit.measure (temp qubit) | `E:/opensource/qkdpy/src/qkdpy/core/qubit.py` | 93-133 |
| Qubit.collapse_state | `E:/opensource/qkdpy/src/qkdpy/core/qubit.py` | 135-158 |
| Qubit.density_matrix | `E:/opensource/qkdpy/src/qkdpy/core/qubit.py` | 160-167 |
| Depolarizing noise | `E:/opensource/qkdpy/src/qkdpy/core/channels.py` | 202-217 |
| Bit flip noise | `E:/opensource/qkdpy/src/qkdpy/core/channels.py` | 219-224 |
| Phase flip noise | `E:/opensource/qkdpy/src/qkdpy/core/channels.py` | 226-231 |
| Amplitude damping noise (BUG) | `E:/opensource/qkdpy/src/qkdpy/core/channels.py` | 233-241 |
| Entanglement attack (non-physical) | `E:/opensource/qkdpy/src/qkdpy/core/channels.py` | 325-357 |
| Polarization drift | `E:/opensource/qkdpy/src/qkdpy/core/channels.py` | 359-385 |
| MultiQubitState.apply_gate | `E:/opensource/qkdpy/src/qkdpy/core/multiqubit.py` | 145-243 |
| MultiQubitState.entanglement_entropy (stub) | `E:/opensource/qkdpy/src/qkdpy/core/multiqubit.py` | 320-339 |
| BB84 prepare states | `E:/opensource/qkdpy/src/qkdpy/protocols/bb84.py` | 50-83 |
| BB84 sift keys | `E:/opensource/qkdpy/src/qkdpy/protocols/bb84.py` | 119-150 |
| BB84 QBER estimation | `E:/opensource/qkdpy/src/qkdpy/protocols/bb84.py` | 152-181 |
| E91 measure_states | `E:/opensource/qkdpy/src/qkdpy/protocols/e91.py` | 70-136 |
| E91 CHSH test | `E:/opensource/qkdpy/src/qkdpy/protocols/e91.py` | 177-239 |
| Key rate calculation | `E:/opensource/qkdpy/src/qkdpy/core/security_analysis.py` | 112-157 |
| Security thresholds | `E:/opensource/qkdpy/src/qkdpy/core/security_analysis.py` | 91-110 |
| Eve info estimation | `E:/opensource/qkdpy/src/qkdpy/protocols/base.py` | 329-344 |
| Cascade error correction | `E:/opensource/qkdpy/src/qkdpy/protocols/base.py` | 233-285 |
| Privacy amplification (s=10) | `E:/opensource/qkdpy/src/qkdpy/protocols/base.py` | 287-327 |
| BaseProtocol execute flow | `E:/opensource/qkdpy/src/qkdpy/protocols/base.py` | 130-219 |
| GateUtils basis_switch | `E:/opensource/qkdpy/src/qkdpy/core/gate_utils.py` | 8-30 |
