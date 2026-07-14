# Qiskit Architecture Audit for QKDpy Integration Enhancement

**Date:** 2026-07-14
**Source:** `E:/opensource/qiskit/`
**Scope:** Full Qiskit 1.x source tree (no external packages like `qiskit-aer` or `qiskit-ibm-runtime`)
**Existing integration:** `E:/opensource/qkdpy/src/qkdpy/integrations/qiskit_integration.py`

---

## 0. Summary of Existing Integration

The current `qiskit_integration.py` provides:

- `QiskitIntegration` class wrapping `Statevector`, `QuantumCircuit`, `QuantumRegister`, `ClassicalRegister`
- `qubit_to_qiskit(qkdpy_qubit)` / `qiskit_to_qubit(qiskit_state)` conversion between QKDpy `Qubit` and `Statevector`
- `create_bb84_circuit(num_qubits, alice_bases, bob_bases)` -- generates BB84 encode+measure circuits with optional basis reconciliation
- `simulate(circuit, shots=1024)` -- runs `AerSimulator` (from external `qiskit-aer`)
- `entanglement_swap(circuits, ...)` and `bell_state_measurement(...)` -- Bell state analysis
- `calculate_qber(counts, alice_bases, bob_bases)` -- QBER from measurement counts
- `encode_bits(bits, bases)` / `measure_bits(circuit, qubits, bases)` -- bit encoding/decoding
- `compute_state_fidelity(state1, state2)` via `state_fidelity`

**Gaps identified:** No noise modeling, no transpilation, no quantum_info measures beyond fidelity, no Pauli/Clifford utilities, no circuit synthesis, no primitive-based execution, no mid-circuit measurement, no conditional operations.

---

## 1. Core Architecture

### 1.1 QuantumCircuit

**File:** `E:/opensource/qiskit/qiskit/circuit/quantumcircuit.py` (346K, ~7800 lines)

The central class. Key constructor and structural patterns:

```python
class QuantumCircuit:
    def __init__(self, *regs, name=None, global_phase=0, *args, **kwargs):
        # Accepts Register, int (creates QuantumRegister), or tuple(name, size)
```

**Registers and qubits:**
- `QuantumRegister` -- named group of qubits (from `qiskit.circuit`)
- `ClassicalRegister` -- named group of classical bits
- `Qubit` -- individual qubit
- `Clbit` -- individual classical bit
- `AncillaRegister`, `AncillaQubit` -- ancillary qubits

**Key methods (line numbers from source):**
| Method | Line | Signature |
|--------|------|-----------|
| `h` | 5158 | `h(self, qubit: QubitSpecifier) -> InstructionSet` |
| `x` | 6214 | `x(self, qubit: QubitSpecifier, label=None) -> InstructionSet` |
| `cx` | 6228 | `cx(self, control_qubit, target_qubit, label=None, ctrl_state=None) -> InstructionSet` |
| `rx` | 5634 | `rx(self, theta, qubit) -> InstructionSet` |
| `ry` | 5707 | `ry(self, theta, qubit) -> InstructionSet` |
| `rz` | 5780 | `rz(self, phi, qubit) -> InstructionSet` |
| `z` | 6483 | `z(self, qubit) -> InstructionSet` |
| `cz` | 6496 | `cz(self, control_qubit, target_qubit, label=None, ctrl_state=None) -> InstructionSet` |
| `barrier` | 5102 | `barrier(self, *qargs, label=None) -> InstructionSet` |
| `measure` | 4493 | `measure(self, qubit, cbit) -> InstructionSet` |
| `measure_all` | 4617 | `measure_all(self, inplace=True, add_bits=True) -> QuantumCircuit | None` |
| `reset` | 4449 | `reset(self, qubit) -> InstructionSet` |
| `initialize` | 6714 | `initialize(self, params, qubits=None, normalize=False) -> InstructionSet` |
| `copy_empty_like` | 4357 | `copy_empty_like(self) -> QuantumCircuit` |
| `compose` | 2038 | `compose(self, other, qubits=None, clbits=None, front=False, inplace=True, wrap=True) -> QuantumCircuit` |
| `append` | 2832 | `append(self, instruction, qargs=None, cargs=None) -> InstructionSet` |

`QubitSpecifier = Qubit | QuantumRegister | int | slice | Sequence[Qubit | int]`
`ClbitSpecifier = Clbit | ClassicalRegister | int | slice | Sequence[Clbit | int]`

**Data model:**
- `circuit.data` -- list of `CircuitInstruction` objects (op, qargs, cargs)
- `circuit.qubits` -- list of all qubits
- `circuit.clbits` -- list of all classical bits
- `circuit.num_qubits`, `circuit.num_clbits`, `circuit.num_parameters`
- `circuit.depth()`, `circuit.count_ops()`, `circuit.size()`
- `circuit.qregs`, `circuit.cregs` -- register lists

### 1.2 Instructions and Gates

**File:** `E:/opensource/qiskit/qiskit/circuit/instruction.py`
**File:** `E:/opensource/qiskit/qiskit/circuit/gate.py`
**File:** `E:/opensource/qiskit/qiskit/circuit/controlledgate.py`
**File:** `E:/opensource/qiskit/qiskit/circuit/operation.py`

Class hierarchy:
```
Operation (ABC) -> Instruction -> Gate -> (concrete gates like HGate, XGate, CXGate...)
Operation -> AnnotatedOperation
SingletonInstruction -> Measure, Reset
ControlFlowOp (ABC) -> IfElseOp, WhileLoopOp, ForLoopOp, SwitchCaseOp
```

**Standard gates library:** `E:/opensource/qiskit/qiskit/circuit/library/standard_gates/__init__.py`
All gates listed there with their controlled variants. Key gates for QKD:

| Gate Class | File | Controlled | Circuit method |
|-----------|------|-----------|----------------|
| `HGate` | `h.py` | `CHGate` | `circuit.h()` |
| `XGate` | `x.py` | `CXGate, CCXGate, ...` | `circuit.x()` |
| `ZGate` | `z.py` | `CZGate, CCZGate` | `circuit.z()` |
| `YGate` | `y.py` | `CYGate` | `circuit.y()` |
| `RXGate` | `rx.py` | `CRXGate` | `circuit.rx()` |
| `RYGate` | `ry.py` | `CRYGate` | `circuit.ry()` |
| `RZGate` | `rz.py` | `CRZGate` | `circuit.rz()` |
| `RXXGate` | `rxx.py` | -- | `circuit.rxx()` |
| `RZZGate` | `rzz.py` | -- | `circuit.rzz()` |
| `PhaseGate` | `p.py` | `CPhaseGate` | `circuit.p()` |
| `SGate` | `s.py` | `CSGate` | `circuit.s()` |
| `TGate` | `t.py` | -- | `circuit.t()` |
| `SwapGate` | `swap.py` | `CSwapGate` | `circuit.swap()` |
| `iSwapGate` | `iswap.py` | -- | `circuit.iswap()` |
| `UGate` | `u.py` | `CUGate` | `circuit.u()` |
| `ECRGate` | `ecr.py` | -- | `circuit.ecr()` |

**Measure:** `E:/opensource/qiskit/qiskit/circuit/measure.py`
```python
class Measure(SingletonInstruction):
    # num_qubits=1, num_clbits=1
    # broadcast_arguments: yields (qarg, carg) pairs, supports register-level broadcast
```

**Reset:** `E:/opensource/qiskit/qiskit/circuit/reset.py`
```python
class Reset(SingletonInstruction):
    # num_qubits=1, num_clbits=0
    # Incoherently resets a qubit to |0>
```

### 1.3 Transpilation Pipeline

**Entry point:** `E:/opensource/qiskit/qiskit/compiler/transpiler.py`
`transpile(circuits, backend, basis_gates, coupling_map, initial_layout, optimization_level=0..3, ...)` -- the main user-facing function.

**Preset pass managers:** `E:/opensource/qiskit/qiskit/transpiler/preset_passmanagers/`
Each level generates a `StagedPassManager` with stages: `init`, `layout`, `routing`, `translation`, `optimization`, `scheduling`.

| Level | File | Description |
|-------|------|-------------|
| 0 | `level0.py` | No optimization beyond mapping to backend |
| 1 | `level1.py` | Light optimization: adjacent gate collapse |
| 2 | `level2.py` | Medium: noise-adaptive layout + commutativity cancellation |
| 3 | `level3.py` | Heavy: plus unitary resynthesis of 2q blocks |

**Pass stages (from `common.py`):**
- `init` -- initial layout, ancilla allocation
- `layout` -- VF2Layout, SabreLayout, TrivialLayout, DenseLayout
- `routing` -- SabreSwap, BasicSwap, LookaheadSwap, StarPrerouting
- `translation` -- `BasisTranslator`, `UnitarySynthesis`, `HighLevelSynthesis`, `Unroll3qOrMore`, `ConsolidateBlocks`
- `optimization` -- 30+ passes (see below)
- `scheduling` -- `ALAPScheduleAnalysis`, `ASAPScheduleAnalysis`, `PadDelay`

**Key optimization passes:** `E:/opensource/qiskit/qiskit/transpiler/passes/optimization/`
- `optimize_1q_gates.py` -- 1q gate cancellation/merging
- `optimize_1q_decomposition.py` -- Euler-angle decomposition
- `commutative_cancellation.py` -- cancel commuting gates
- `commutative_inverse_cancellation.py` -- cancel inverse pairs
- `consolidate_blocks.py` -- collect blocks into unitary, then resynthesize
- `collect_1q_runs.py`, `collect_2q_blocks.py` -- block collection
- `hoare_opt.py` -- Hoare-style optimization (remove redundant gates)
- `remove_diagonal_gates_before_measure.py` -- QKD-relevant: removes Z-phase gates before measurement
- `optimize_swap_before_measure.py` -- QKD-relevant for measurement optimization
- `template_optimization.py` -- template-based replacement

**Common pass manager generators:** `E:/opensource/qiskit/qiskit/transpiler/preset_passmanagers/common.py`
Functions: `generate_unroll_3q()`, `generate_embed_passmanager()`, `generate_routing_passmanager()`, `generate_translation_passmanager()`, `generate_scheduling()`

### 1.4 Backend Architecture

**Abstract base:** `E:/opensource/qiskit/qiskit/providers/backend.py`
```python
class BackendV2(Backend):
    version = 2
    # Required: num_qubits, target, max_circuits, online_date, backend_name, backend_version
    # Methods: run(circuits, **kwargs), _default_options()
```

**Basic simulator:** `E:/opensource/qiskit/qiskit/providers/basic_provider/basic_simulator.py`
- `BasicSimulator` -- Python-based, returns counts from statevector simulation

**Generic backend:** `E:/opensource/qiskit/qiskit/providers/fake_provider/generic_backend_v2.py`
```python
class GenericBackendV2(BackendV2):
    def __init__(self, num_qubits, basis_gates=None, coupling_map=None, seed=42, ...)
```
Randomly samples noise default ranges from hardware-like distributions (T1, T2, gate errors, durations). Has `_NOISE_DEFAULTS` dict with realistic ranges for cx, id, rz, sx, x, measure, delay, reset.

**Target:** `E:/opensource/qiskit/qiskit/transpiler/target.py`
`Target` -- the instruction set architecture description. Contains `InstructionProperties` (error rate, duration) per qubit/qubit-pair, `QubitProperties` (T1, T2, frequency).

### 1.5 Primitives (Sampler & Estimator)

**Module:** `E:/opensource/qiskit/qiskit/primitives/`

**V2 hierarchy:**
- `BaseSamplerV2` / `BaseEstimatorV2` (abstract) -- `E:/opensource/qiskit/qiskit/primitives/base/`
- `StatevectorSampler(BaseSamplerV2)` -- `E:/opensource/qiskit/qiskit/primitives/statevector_sampler.py`
- `StatevectorEstimator(BaseEstimatorV2)` -- `E:/opensource/qiskit/qiskit/primitives/statevector_estimator.py`

```python
class StatevectorSampler(BaseSamplerV2):
    def run(pubs, *, shots=..., ...) -> PrimitiveResult[SamplerPubResult]
```

**Key containers:**
- `BitArray` -- compressed array of measurement bits
- `DataBin` -- output data container (meas outcomes per classical register)
- `SamplerPubResult` -- collection of per-PUB results
- `PrimitiveResult` -- top-level result

**Primitive Unified Blocs (PUBs):**
- `SamplerPub` : `(circuit, parameter_bindings, shots)`
- `EstimatorPub` : `(circuit, observables, parameter_bindings, precision)`

**V1 classes** (deprecated but still present):
- `BaseSamplerV1`, `BaseEstimatorV1` (backward compat)
- `Sampler`, `Estimator` (reference implementations)

**Backend-aware V2:**
- `BackendSamplerV2` -- `E:/opensource/qiskit/qiskit/primitives/backend_sampler_v2.py`
- `BackendEstimatorV2` -- `E:/opensource/qiskit/qiskit/primitives/backend_estimator_v2.py`

---

## 2. Quantum Information (`qiskit.quantum_info`)

### 2.1 Statevector

**File:** `E:/opensource/qiskit/qiskit/quantum_info/states/statevector.py`

```python
class Statevector(QuantumState, TolerancesMixin):
    def __init__(self, data: np.ndarray | list | Statevector | Operator | QuantumCircuit | Instruction, dims=None)
```

**Key methods:**
- `data` --> `np.ndarray` (the state vector)
- `dims()` --> tuple of subsystem dimensions
- `evolve(other, qargs=None)` -- apply operator/channel/instruction to subsystem
- `measure(qargs=None)` -- projective measurement, returns (outcome, Statevector)
- `probabilities(qargs=None, decimals=None)` -- marginal probabilities
- `probabilities_dict(qargs=None, decimals=None)`
- `sample_counts(shots, qargs=None)` -- sample measurement outcomes
- `sample_memory(shots, qargs=None)` -- raw measurement samples
- `from_label(label)` -- create from string like `"0"`, `"+"`, `"-"`, `"r"`, `"l"`
- `copy()`, `conjugate()`, `trace()`, `is_valid()`, `to_dict()`
- `reshape(input_dims, output_dims)` -- reshape subsystem structure

**Creation from circuits:** `Statevector(circuit)` evolves the all-zeros state through the circuit.

### 2.2 DensityMatrix

**File:** `E:/opensource/qiskit/qiskit/quantum_info/states/densitymatrix.py`

```python
class DensityMatrix(QuantumState, TolerancesMixin):
    def __init__(self, data: np.ndarray | list | DensityMatrix | Statevector | Operator | QuantumCircuit | Instruction, dims=None)
```

**Key methods:**
- `data` --> `np.ndarray` (density matrix)
- `evolve(other, qargs=None)` -- apply channel/operator
- `measure(qargs=None)` -- projective measurement
- `probabilities(qargs=None)`, `probabilities_dict(qargs=None)`
- `purity()` -- Tr(rho^2)
- `to_statevector()` -- only if pure (raises otherwise)

### 2.3 StabilizerState

**File:** `E:/opensource/qiskit/qiskit/quantum_info/states/stabilizerstate.py`

```python
class StabilizerState:
    def __init__(self, data: StabilizerState | Clifford | Pauli | list | QuantumCircuit | Instruction)
```
Efficient simulation of Clifford circuits (useful for entanglement swapping, Bell measurements). Uses tableau representation internally.

### 2.4 Operator (dense unitary)

**File:** `E:/opensource/qiskit/qiskit/quantum_info/operators/operator.py`

```python
class Operator(LinearOp):
    def __init__(self, data: np.ndarray | list | QuantumCircuit | Instruction | BaseOperator | Gate)
```

**Key methods:**
- `data` --> `np.ndarray` (matrix)
- `is_unitary()` -- checks unitarity
- `to_instruction()` -- convert to circuit instruction
- `power(n)` -- matrix power
- `expand(other)` -- tensor product (self on left)
- `tensor(other)` -- tensor product (self on right)
- `compose(other, qargs=None, front=False)` -- matrix multiplication
- `adjoint()` -- conjugate transpose

### 2.5 Pauli Algebra

**File:** `E:/opensource/qiskit/qiskit/quantum_info/operators/symplectic/pauli.py`

```python
class Pauli(BasePauli):
    def __init__(self, data: str | tuple | list | np.ndarray | Pauli)
```

Constructor accepts: string labels like `"XYZI"`, `"IIII"`, `"+Z"`, `"-iXY"`.

**Key methods:**
- `to_label()` -- string like `"XYZI"` or `"-iXY"`
- `to_matrix()` -- dense matrix
- `to_instruction()` -- circuit instruction (`PauliGate`)
- `evolve(other, qargs=None)` -- Clifford evolution
- `commutes(other)` -- check commutation
- `x` property -- boolean array of X bits
- `z` property -- boolean array of Z bits
- `phase` property -- 0, 1, 2, 3 (for (-i)^phase)

**SparsePauliOp:** `E:/opensource/qiskit/qiskit/quantum_info/operators/symplectic/sparse_pauli_op.py`

```python
class SparsePauliOp(LinearOp):
    def __init__(self, data: PauliList | list | str | ...)
```
Weighted sum of Pauli operators. Key for constructing Hamiltonians/observables.

**Key methods:**
- `paulis` --> `PauliList`
- `coeffs` --> `np.ndarray` of coefficients
- `simplify()` -- combine identical terms
- `to_operator()` -- convert to dense Operator
- `to_matrix(sparse=True)` -- sparse or dense

### 2.6 Clifford

**File:** `E:/opensource/qiskit/qiskit/quantum_info/operators/symplectic/clifford.py`

```python
class Clifford(BaseOperator, AdjointMixin, Operation):
    def __init__(self, data: Clifford | QuantumCircuit | Instruction | Operator | Pauli | str | ...)
```

Stabilizer tableau representation. Efficient simulation of Clifford circuits (H, S, CX).

**Key methods:**
- `to_instruction()` -- circuit instruction
- `to_circuit()` -- `QuantumCircuit` decomposition
- `compose(other)` -- group product
- `adjoint()` -- inverse

**Clifford circuits utility:** `E:/opensource/qiskit/qiskit/quantum_info/operators/symplectic/clifford_circuits.py`
Contains `_CLIFFORD_GATE_NAMES` list and the internal `_append_circuit`/`_append_operation`/`_prepend_circuit`/`_prepend_operation` helpers.

### 2.7 Entanglement Measures

**File:** `E:/opensource/qiskit/qiskit/quantum_info/states/measures.py`

```python
def state_fidelity(state1, state2, validate=True) -> float
def purity(state) -> float
def entropy(state, base=2) -> float          # von Neumann entropy
def concurrence(state) -> float              # Wootters concurrence
def entanglement_of_formation(state) -> float
def negativity(state) -> float               # for bipartite states
def mutual_information(state, base=2) -> float
```

All accept `Statevector` or `DensityMatrix`. Entanglement measures require bipartite states.

### 2.8 Operator Measures

**File:** `E:/opensource/qiskit/qiskit/quantum_info/operators/measures.py`

```python
def process_fidelity(channel, target=None, require_cp=True, require_tp=True) -> float
def average_gate_fidelity(channel, target=None, require_cp=True, require_tp=True, require_cptp=False) -> float
def gate_error(channel, target=None, require_cp=True, require_tp=True, require_cptp=False) -> float
def diamond_norm(channel, target=None, require_cp=True, require_tp=True, require_cptp=False, ...) -> float
```

### 2.9 State Utilities

**File:** `E:/opensource/qiskit/qiskit/quantum_info/states/utils.py`

```python
def partial_trace(state: Statevector | DensityMatrix, qargs: list) -> DensityMatrix
def schmidt_decomposition(state: Statevector | DensityMatrix, qargs: list) -> list[tuple[float, Statevector, Statevector]]
def shannon_entropy(vec, base=2) -> float
```

### 2.10 SparseObservable

**File:** internal Rust acceleration via `qiskit._accelerate.sparse_observable`
Also exposed as `SparseObservable` in `qiskit.quantum_info` (from `qiskit._accelerate.sparse_observable`).

---

## 3. Noise Modeling

### 3.1 No Built-in NoiseModel in Qiskit 1.x

**Critical finding:** The base `qiskit` package (1.x) does **not** contain a `NoiseModel` class, `ReadoutError`, `depolarizing_error`, or other structured noise-modeling tools. These are part of the **external** `qiskit-aer` package.

However, the `GenericBackendV2` (`E:/opensource/qiskit/qiskit/providers/fake_provider/generic_backend_v2.py`) does incorporate noise-like behavior through:

- `_NOISE_DEFAULTS` dict: sampled duration and error ranges for gates
- `_QUBIT_PROPERTIES`: T1, T2, frequency ranges
- Randomly generated `InstructionProperties` with `duration` and `error` fields
- `Target` objects with per-qubit/per-edge error rates

### 3.2 Target-Based Noise Information

**File:** `E:/opensource/qiskit/qiskit/transpiler/target.py`

The `Target` class holds:
- `InstructionProperties` -- `duration` (float) and `error` (float) per instruction+qubits
- `QubitProperties` -- `t1` (float), `t2` (float), `frequency` (float)
- Methods: `instruction_properties()`, `qubit_properties()`, `operation_names()`, `operations()`, `has_instruction()`, `get_non_global_operation_names()`

### 3.3 To Get Full Noise Models

For complete noise modeling (NoiseModel, depolarizing_error, thermal_relaxation_error, ReadoutError, amplitude_damping, phase_damping), the `qiskit-aer` package is required separately. None of these classes exist in the base `qiskit` source tree.

---

## 4. Circuit Synthesis

### 4.1 Synthesis Module

**File:** `E:/opensource/qiskit/qiskit/synthesis/__init__.py`

Main categories:
- **Evolution:** `EvolutionSynthesis`, `ProductFormula`, `LieTrotter`, `SuzukiTrotter`, `MatrixExponential`, `QDrift` -- for Hamiltonian simulation
- **Linear:** `synth_cnot_count_full_pmh`, `synth_cnot_depth_line_kms` -- CNOT optimization
- **Linear-Phase:** `synth_cz_depth_line_mr`, `synth_cx_cz_depth_line_my`, `synth_cnot_phase_aam`
- **Permutation:** `synth_permutation_depth_lnn_kms`, `synth_permutation_basic`, `synth_permutation_acg`
- **Clifford:** `synth_clifford_full`, `synth_clifford_ag`, `synth_clifford_bm`, `synth_clifford_greedy`, `synth_clifford_layers`, `synth_clifford_depth_lnn`
- **Stabilizer:** `synth_stabilizer_layers`, `synth_stabilizer_depth_lnn`, `synth_circuit_from_stabilizers`
- **Discrete basis:** `SolovayKitaevDecomposition`, `gridsynth_rz`, `gridsynth_unitary`, `generate_basic_approximations`
- **Basis change (QFT):** `synth_qft_line`, `synth_qft_full`
- **Unitary:** `qs_decomposition` -- general 2^n x 2^n unitary decomposition
- **1-qubit:** `OneQubitEulerDecomposer`
- **2-qubit:** `TwoQubitBasisDecomposer`, `XXDecomposer`, `TwoQubitWeylDecomposition`, `TwoQubitControlledUDecomposer`, `two_qubit_cnot_decompose`
- **Multi-controlled:** `synth_mcx_*`, `synth_c3x`, `synth_c4x`, `synth_mcmt_*`
- **Arithmetic:** various adders and multipliers

### 4.2 Circuit Library High-Level Gates

**File:** `E:/opensource/qiskit/qiskit/circuit/library/__init__.py`

Key classes:
- `QFT(num_qubits, approximation_degree, inverse, ...)` -- Quantum Fourier Transform
- `PhaseEstimation(num_evaluation_qubits, unitary)` -- Phase estimation circuit wrapper
- `GroverOperator(oracle, ...)` -- Grover iteration
- `PauliEvolutionGate(operator, time, ...)` -- Hamiltonian evolution via Pauli exponentials
- `HamiltonianGate(data, time, label)` -- direct Hamiltonian matrix evolution
- `StatePreparation(params, ...)` -- state initialization
- `Initialize(params)` -- reset + state prep
- `PauliGate(label)` -- multi-qubit Pauli (`circuit.pauli()`)
- `Permutation(pattern)` -- qubit permutation
- `LinearFunction(linear_matrix)` -- linear reversible classical function

**N-local circuits:** `E:/opensource/qiskit/qiskit/circuit/library/n_local/`
- `TwoLocal`, `RealAmplitudes`, `EfficientSU2`, `ExcitationPreserving`, `QAOAAnsatz`, `PauliTwoDesign`
- Base: `NLocal` -- generic layered circuit template

**Data preparation:** `E:/opensource/qiskit/qiskit/circuit/library/data_preparation/`
- `QRAM`, `QubitMapper`

### 4.3 Ising Gates (Pauli Rotations)

- `RXXGate(theta)` -- `exp(-i * theta/2 * X*X)` at `E:/opensource/qiskit/qiskit/circuit/library/standard_gates/rxx.py`
- `RYYGate(theta)` -- `exp(-i * theta/2 * Y*Y)` at `ryy.py`
- `RZZGate(theta)` -- `exp(-i * theta/2 * Z*Z)` at `rzz.py`
- `RZXGate(theta)` -- `exp(-i * theta/2 * Z*X)` at `rzx.py`
- `XXMinusYYGate(theta, beta)` -- `XXMinusYY` at `xx_minus_yy.py`
- `XXPlusYYGate(theta, beta)` -- `XXPlusYY` at `xx_plus_yy.py`

Each `RXXGate` at `theta=pi/2` gives an entangling gate equivalent to `(CX + rotations)`.

### 4.4 Transpiler Synthesis Passes

**File:** `E:/opensource/qiskit/qiskit/transpiler/passes/synthesis/`
- `high_level_synthesis.py` -- `HighLevelSynthesis` pass for decomposing high-level objects
- `unitary_synthesis.py` -- `UnitarySynthesis` pass for arbitrary unitary decomposition
- `solovay_kitaev_synthesis.py` -- Solovay-Kitaev algorithm for approximating arbitrary 1q gates
- `ross_selinger_plugin.py` -- optimized Clifford+T single-qubit synthesis

---

## 5. Measurement Handling

### 5.1 Classical Registers and Measurement Mapping

**Creating a circuit with registers:**
```python
qr = QuantumRegister(4, 'q')
cr = ClassicalRegister(4, 'c')
qc = QuantumCircuit(qr, cr)
qc.measure(qr, cr)  # maps all qubits to classical bits 1:1
```

**Individual measurement:**
```python
qc.measure(0, 0)  # measure qubit 0 into classical bit 0
qc.measure(qr[0], cr[1])  # measure qubit 0 into classical bit 1
```

**`measure_all`:**
```python
qc.measure_all()  # auto-creates 'meas' ClassicalRegister, measures all qubits
qc.measure_all(inplace=False, add_bits=True)  # returns new circuit
```

### 5.2 Mid-Circuit Measurement and Reset

**Both are supported in the base qiskit:**
```python
qc.measure(0, 0)
qc.reset(0)  # resets qubit 0 to |0>, can be reused
qc.measure(0, 1)  # measure the reset qubit again
```

Mid-circuit measurement with conditional operations:
```python
qc.measure(0, 0)
with qc.if_test((cr[0], 1)):  # cr is ClassicalRegister
    qc.x(1)  # flip qubit 1 if measured 1
```

### 5.3 Control Flow Operations

**File:** `E:/opensource/qiskit/qiskit/circuit/controlflow/`

| Class | File | Description |
|-------|------|-------------|
| `IfElseOp` | `if_else.py` | `IfElseOp(condition, true_body, false_body=None)` |
| `WhileLoopOp` | `while_loop.py` | `WhileLoopOp(condition, body)` |
| `ForLoopOp` | `for_loop.py` | `ForLoopOp(indexset, loop_parameter, body)` |
| `SwitchCaseOp` | `switch_case.py` | `SwitchCaseOp(target, cases, ...)` |
| `BreakLoopOp` | `break_loop.py` | Break from loop |
| `ContinueLoopOp` | `continue_loop.py` | Continue loop |
| `BoxOp` | `box.py` | Wraps subcircuit into single opaque box |

**Circuit builder context managers:**
```python
with qc.for_loop(range(5)): ...
with qc.while_loop((cr, 0)): ...
with qc.if_test((cr, 0)): ...
with qc.switch(cr[0]) as case:
    with case(0): ...
```

### 5.4 Conditional Operations (old-style)

Pre-control-flow, Qiskit supports conditional instructions via the `c_if` method on instructions:
```python
qc.h(0).c_if(cr, 1)  # apply H if classical register cr is 1 (condensed form, compatibility)
```
Note: The `.c_if()` approach is deprecated in Qiskit 1.x in favor of `if_test`.

### 5.5 Measurement Results

**Result class:** `E:/opensource/qiskit/qiskit/result/result.py`
```python
class Result:
    def get_counts(circuit=None, creg=None) -> dict[str, int]
    def get_memory(circuit=None) -> list[str]
    def data(circuit=None) -> ExperimentResultData
```

**Counts format:** `{"000": 487, "101": 523, ...}` (bitstring keys ordered as q_{n-1} ... q_0, i.e. little-endian)

---

## 6. QKD-Specific Patterns in Qiskit

### 6.1 BB84 State Preparation

The four BB84 states map directly to Qiskit gates:

| State | Basis | Qiskit construction |
|-------|-------|-------------------|
| `|0>` | Z | `qc.initialize([1, 0], 0)` or default after reset |
| `|1>` | Z | `qc.x(0)` or `qc.initialize([0, 1], 0)` |
| `|+>` | X | `qc.h(0)` applied to `|0>` |
| `|->` | X | `qc.h(0); qc.z(0)` or `qc.h(0); qc.x(0)` or `qc.initialize([1, -1], 0)` |

Using `Statevector.from_label()`:
```python
from qiskit.quantum_info import Statevector
sv_0 = Statevector.from_label('0')   # |0>
sv_1 = Statevector.from_label('1')   # |1>
sv_plus = Statevector.from_label('+')  # |+>
sv_minus = Statevector.from_label('-') # |->
```

### 6.2 BB84 Measurement (Basis Choice)

**Z-basis measurement:** `qc.measure(qubit, cbit)` -- standard computational basis measurement

**X-basis measurement:** Apply Hadamard before Z measurement:
```python
qc.h(qubit)  # rotate to X basis
qc.measure(qubit, cbit)
```

Thus the pattern for BB84 measurement is:
```python
if basis == 'X':
    qc.h(qubit)
qc.measure(qubit, cbit)
```

### 6.3 Modeling Channel Loss

Since base Qiskit has no built-in noise models, channel loss must be simulated through:

**Option 1: Post-selection from measurement results**
```python
# Simulate loss by randomly dropping some transmission events in post-processing
# rather than within the circuit itself
```

**Option 2: Using density matrices with loss channels (requires constructing Kraus operators)**
```python
from qiskit.quantum_info import Kraus, SuperOp
import numpy as np

# Loss channel: maps |1> to vacuum with probability p_loss (non-trace-preserving simplistically)
# Proper loss channel for single photon: E0 = |0><0| + sqrt(1-p_loss) * |1><1|, E1 = sqrt(p_loss) * |vac><1|
# But since Qiskit is qubit-based, you'd use amplitude damping:
from qiskit.quantum_info import Kraus
p_loss = 0.1
K0 = np.array([[1, 0], [0, np.sqrt(1-p_loss)]])  # keep
K1 = np.array([[0, np.sqrt(p_loss)], [0, 0]])      # loss
loss_kraus = Kraus([K0, K1])

# Apply to DensityMatrix
dm = DensityMatrix.from_label('1')
dm_after = dm.evolve(loss_kraus, [0])
```

**Option 3: Use `GenericBackendV2` with custom error rates**
```python
backend = GenericBackendV2(num_qubits=2, seed=42)
# The generated target has error rates for gates
target = backend.target
```

**Option 4: Mid-circuit measurement with reset for loss emulation**
```python
# Use measure+reset on an ancilla to probabilistically model loss
qc.reset(ancilla)
qc.h(ancilla)
qc.cx(ancilla, data_qubit)  # entangle
qc.measure(ancilla, cbit)
# If ancilla measured |1>, data qubit is lost
qc.reset(data_qubit)  # reset to |0> as "new photon"
```

### 6.4 Entanglement (Bell State) Generation

**Standard Bell state circuit:**
```python
from qiskit import QuantumCircuit
qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)

# Produces |Phi+> = (|00> + |11>)/sqrt(2)
```

**Other Bell states:**
```python
# |Phi-> = (|00> - |11>)/sqrt(2)
qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)
qc.z(0)  # or z on either qubit

# |Psi+> = (|01> + |10>)/sqrt(2)
qc = QuantumCircuit(2)
qc.x(1)  # start from |01>
qc.h(0)
qc.cx(0, 1)

# |Psi-> = (|01> - |10>)/sqrt(2)
qc = QuantumCircuit(2)
qc.x(1)
qc.h(0)
qc.cx(0, 1)
qc.z(0)
```

**Bell state measurement (BSM):**
```python
qc.cx(0, 1)
qc.h(0)
qc.measure(0, 0)
qc.measure(1, 1)
# Result maps: 00->|Phi+>, 01->|Phi->, 10->|Psi+>, 11->|Psi->
```

### 6.5 Entanglement Swapping

```python
# Create two Bell pairs
qc = QuantumCircuit(4)
# Bell pair 1: qubits 0-1
qc.h(0)
qc.cx(0, 1)
# Bell pair 2: qubits 2-3
qc.h(2)
qc.cx(2, 3)

# Bell state measurement on qubits 1 and 2
qc.cx(1, 2)
qc.h(1)
qc.measure(1, 0)  # measure qubit 1
qc.measure(2, 1)  # measure qubit 2

# After BSM, qubits 0 and 3 are entangled
# Post-select on measurement outcomes to determine which Bell state was swapped
```

### 6.6 E91 Protocol (Ekert91)

Based on entanglement + Bell test:
```python
# Create Bell pair
qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)

# Alice measures qubit 0 in varying bases
# Bob measures qubit 1 in varying bases
# After correlation measurement, CHSH inequality can be computed
```

### 6.7 QKD-Optimization via Transpilation

For QKD simulation circuits, optimization level 0 is typically sufficient (no need for hardware-specific optimizations). However, these passes are **relevant** for QKD circuits:

- `RemoveDiagonalGatesBeforeMeasure` -- removes Z-phase gates before measurement (X-basis states use H which transforms Z to X)
- `OptimizeSwapBeforeMeasure` -- if routing inserted swaps, optimize them out
- `CommutativeCancellation` -- cancels pairs like H-H, X-X

### 6.8 PauliLindbladMap (Noise Learning)

**File:** Exposed via `qiskit.quantum_info.PauliLindbladMap`

Represents noise as a Lindblad map on Pauli generators. Useful for:
- Modeling depolarizing noise channels for QKD
- Learning device noise via Pauli twirling
- Constructing noise models for entanglement-based QKD protocols

---

## Appendix: Key File Index

| Area | File Path |
|------|-----------|
| Main package | `E:/opensource/qiskit/qiskit/__init__.py` |
| QuantumCircuit | `E:/opensource/qiskit/qiskit/circuit/quantumcircuit.py` |
| Circuit data | `E:/opensource/qiskit/qiskit/circuit/quantumcircuitdata.py` |
| Circuit __init__ | `E:/opensource/qiskit/qiskit/circuit/__init__.py` |
| Instruction base | `E:/opensource/qiskit/qiskit/circuit/instruction.py` |
| Gate base | `E:/opensource/qiskit/qiskit/circuit/gate.py` |
| ControlledGate | `E:/opensource/qiskit/qiskit/circuit/controlledgate.py` |
| Measure | `E:/opensource/qiskit/qiskit/circuit/measure.py` |
| Reset | `E:/opensource/qiskit/qiskit/circuit/reset.py` |
| Standard gates | `E:/opensource/qiskit/qiskit/circuit/library/standard_gates/` |
| Generalized gates | `E:/opensource/qiskit/qiskit/circuit/library/generalized_gates/` |
| N-local circuits | `E:/opensource/qiskit/qiskit/circuit/library/n_local/` |
| Circuit library | `E:/opensource/qiskit/qiskit/circuit/library/__init__.py` |
| Phase Estimation | `E:/opensource/qiskit/qiskit/circuit/library/phase_estimation.py` |
| Control flow | `E:/opensource/qiskit/qiskit/circuit/controlflow/` |
| Statevector | `E:/opensource/qiskit/qiskit/quantum_info/states/statevector.py` |
| DensityMatrix | `E:/opensource/qiskit/qiskit/quantum_info/states/densitymatrix.py` |
| StabilizerState | `E:/opensource/qiskit/qiskit/quantum_info/states/stabilizerstate.py` |
| State measures | `E:/opensource/qiskit/qiskit/quantum_info/states/measures.py` |
| State utilities | `E:/opensource/qiskit/qiskit/quantum_info/states/utils.py` |
| Operator | `E:/opensource/qiskit/qiskit/quantum_info/operators/operator.py` |
| Operator measures | `E:/opensource/qiskit/qiskit/quantum_info/operators/measures.py` |
| Pauli | `E:/opensource/qiskit/qiskit/quantum_info/operators/symplectic/pauli.py` |
| SparsePauliOp | `E:/opensource/qiskit/qiskit/quantum_info/operators/symplectic/sparse_pauli_op.py` |
| Clifford | `E:/opensource/qiskit/qiskit/quantum_info/operators/symplectic/clifford.py` |
| Clifford circuits | `E:/opensource/qiskit/qiskit/quantum_info/operators/symplectic/clifford_circuits.py` |
| Kraus | `E:/opensource/qiskit/qiskit/quantum_info/operators/channel/kraus.py` |
| SuperOp | `E:/opensource/qiskit/qiskit/quantum_info/operators/channel/superop.py` |
| Choi | `E:/opensource/qiskit/qiskit/quantum_info/operators/channel/choi.py` |
| Quantum channel base | `E:/opensource/qiskit/qiskit/quantum_info/operators/channel/quantum_channel.py` |
| Transpile function | `E:/opensource/qiskit/qiskit/compiler/transpiler.py` |
| Pass managers L0-3 | `E:/opensource/qiskit/qiskit/transpiler/preset_passmanagers/level[0-3].py` |
| Common passes | `E:/opensource/qiskit/qiskit/transpiler/preset_passmanagers/common.py` |
| Optimization passes | `E:/opensource/qiskit/qiskit/transpiler/passes/optimization/` |
| Synthesis passes | `E:/opensource/qiskit/qiskit/transpiler/passes/synthesis/` |
| Basis passes | `E:/opensource/qiskit/qiskit/transpiler/passes/basis/` |
| Layout passes | `E:/opensource/qiskit/qiskit/transpiler/passes/layout/` |
| Routing passes | `E:/opensource/qiskit/qiskit/transpiler/passes/routing/` |
| Coupling map | `E:/opensource/qiskit/qiskit/transpiler/coupling.py` |
| Target | `E:/opensource/qiskit/qiskit/transpiler/target.py` |
| Primitives init | `E:/opensource/qiskit/qiskit/primitives/__init__.py` |
| StatevectorSampler | `E:/opensource/qiskit/qiskit/primitives/statevector_sampler.py` |
| StatevectorEstimator | `E:/opensource/qiskit/qiskit/primitives/statevector_estimator.py` |
| Backend V2 | `E:/opensource/qiskit/qiskit/providers/backend.py` |
| GenericBackendV2 | `E:/opensource/qiskit/qiskit/providers/fake_provider/generic_backend_v2.py` |
| BasicSimulator | `E:/opensource/qiskit/qiskit/providers/basic_provider/basic_simulator.py` |
| Result | `E:/opensource/qiskit/qiskit/result/result.py` |
| Counts | `E:/opensource/qiskit/qiskit/result/counts.py` |
| Synthesis init | `E:/opensource/qiskit/qiskit/synthesis/__init__.py` |
| QFT synthesis | `E:/opensource/qiskit/qiskit/synthesis/qft/` |
| Clifford synthesis | `E:/opensource/qiskit/qiskit/synthesis/clifford/` |

## Appendix: Key Gaps vs. `qiskit-aer`

The following are **NOT** in base qiskit and would require `qiskit-aer`:

- `NoiseModel` class
- `depolarizing_error`, `thermal_relaxation_error`, `amplitude_damping_error`, `phase_damping_error`
- `ReadoutError`
- `AerSimulator`, `QasmSimulator`, `StatevectorSimulator`, `UnitarySimulator`
- `AerJob`, `AerResult`
- Noise model circuit execution via `backend.run()` with noise model
- Pulse-level simulation
