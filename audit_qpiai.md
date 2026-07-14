# QpiAI Quantum SDK -- Architecture Audit for QKDPy Enhancement

**Date:** 2026-07-14  
**SDK Version:** 0.1.42 (from `pyproject.toml`, commit `829b162`)  
**Repository:** `E:/opensource/qpiai-quantum-sdk/`  
**License:** Apache-2.0  
**Python:** 3.10+ required, supports 3.13/3.14  

---

## 1. Core Architecture

### 1.1 Package Structure

```
qpiai_quantum/
  __init__.py                  # Public API surface (Circuit, Statevector, DensityMatrix, backends, algorithms)
  config.py                   # Server URL, HTTP timeouts, env-based config
  circuit/                    # Circuit builder, registers
  icr/                        # Intermediate Circuit Representation (ICR, CircuitOperation)
  simulator/                  # Local statevector simulator
  quantum_info/               # Statevector, DensityMatrix classes
  formalism/                  # Advanced density matrix formalism (noise, tomography)
  jobmanager/                 # Cloud job submission, polling, SSE, results
  authentication/             # API key auth, user context
  algorithms/                 # Quantum algorithms (QFT, Grover, Shor, Simon, BV, DJ, QPE, QRNG, AE)
  state_preparation/          # Bell, GHZ, W, Cluster state generators
  results/                    # BaseQuantumResult ABC
  iem/qasm/v2/                # OpenQASM 2.0 exporter
  adapters/                   # QuantumAppAdapter for cloud backend resolution
  visualization/              # Matplotlib, Plotly, LaTeX, Q-sphere visualizers
  circuitmanager/             # Additional circuit management
  utils/                      # Encoders, optimizers, visualization helpers
```

**File:** `E:\opensource\qpiai-quantum-sdk\qpiai_quantum\__init__.py`  
Exports the package-level public API.

### 1.2 Circuit System

**File:** `E:\opensource\qpiai-quantum-sdk\qpiai_quantum\circuit\circuit.py`  
**Class:** `Circuit`

The central abstraction. Wraps an `IntermediateCircuitRepresentation` (ICR). Constructed with:

```python
Circuit(5)                    # 5 qubits, 5 classical bits
Circuit(5, 3)                 # 5 qubits, 3 classical bits
Circuit(qreg, creg)           # explicit registers
```

**Key methods (shortcut wrappers on dynamically generated gate methods):**

| Method | Signature | Description |
|--------|-----------|-------------|
| `h` | `(qubit)` | Hadamard gate |
| `x, y, z` | `(qubit)` | Pauli gates |
| `id` | `(qubit)` | Identity |
| `s, sdg` | `(qubit)` | S / S-dagger |
| `t, tdg` | `(qubit)` | T / T-dagger |
| `sx` | `(qubit)` | SX (sqrt-X) |
| `rx, ry, rz` | `(qubit, theta)` | Rotation gates |
| `p` | `(qubit, theta)` | Phase gate |
| `cx, cy, cz` | `(control, target)` | Controlled Paulis |
| `swap` | `(q1, q2)` | SWAP gate |
| `iswap` | `(q1, q2)` | iSWAP gate |
| `cp` | `(control, target, theta)` | Controlled phase |
| `rzz` | `(q1, q2, theta)` | ZZ rotation |
| `ccx` | `(c1, c2, target)` | Toffoli gate |
| `cswap` | `(control, t1, t2)` | Fredkin gate |
| `mcx` | `(controls, target)` | Multi-controlled X |
| `barrier` | `(*qubits)` | Barrier |
| `measure` | `(qubit, clbit)` or lists | Measurement |
| `measure_all` | `()` | Measure all qubits |

**Circuit manipulation:**
- `compose(other, qubits=None)` -- append another circuit with optional qubit mapping
- `inverse()` -- returns new circuit with operations inverted in reverse order
- `remove_operation(upto=1)` -- remove last n operations
- `to_circuit_operation(name=None)` -- converts whole circuit into a single composite `CircuitOperation`
- `depth()` -- circuit depth (gate-level, not parallelized)
- `size()` -- number of operations
- `num_qubits`, `num_clbits` -- property accessors
- `list_gates()` -- returns gate count statistics (Clifford, parametric, etc.)
- `to_qasm()` -- exports to OpenQASM 2.0 string
- `show(theme, dpi, use_mathtext)` -- renders via MatplotlibVisualizer

**Dynamic gate creation:** `_create_gate_methods()` iterates all registered `CircuitOperation` subclasses and dynamically creates methods on the circuit object (e.g., `circuit.H(0)`, `circuit.RX(0, 1.57)`, etc.).

### 1.3 The ICR Layer

**File:** `E:\opensource\qpiai-quantum-sdk\qpiai_quantum\icr\icr.py`  
**Class:** `IntermediateCircuitRepresentation`

- Holds `QuantumRegister` list, `ClassicalRegister` list
- Stores operations in `CircuitEvolutionList` (list subclass)
- `_add_operation(op)`, `_remove_operation(n)`, `to_json()`

**File:** `E:\opensource\qpiai-quantum-sdk\qpiai_quantum\icr\circuitoperation.py`  
**Class:** `CircuitOperation` with auto-registration via `__init_subclass__`

**OperationType enum:**
```python
N_QUBIT_NON_PARAMETRIC, N_QUBIT_PARAMETRIC, MEASURE, BARRIER, SWAP, OPERATION
```

**Concrete gate classes (all extend CircuitOperation, auto-register):**

| Gate Class | Params | Type |
|-----------|--------|------|
| `HGate` | `qubit` | Non-parametric |
| `XGate`, `YGate`, `ZGate`, `IDGate` | `qubit` | Non-parametric |
| `SGate`, `SDGGate`, `TGate`, `TDGGate`, `SXGate` | `qubit` | Non-parametric |
| `RXGate`, `RYGate`, `RZGate`, `PGate` | `qubit, theta` | Parametric |
| `CXGate`, `CYGate`, `CZGate` | `ctrl, tgt` | Non-parametric |
| `SwapGate` | `q1, q2` | SWAP type |
| `ISwapGate` | `q1, q2` | Non-parametric |
| `CPGate`, `RZZGate` | `q1, q2, theta` | Parametric |
| `CCXGate` | `c1, c2, tgt` | Non-parametric |
| `CSwapGate` | `ctrl, t1, t2` | SWAP type |
| `MCXGate` | `controls, tgt` | Non-parametric |
| `MeasureOperation` | `qubit, clbit` | MEASURE |
| `BarrierOperation` | `*qubits` | BARRIER |
| `Operation` | generic | OPERATION (composite) |

**Composite gates:** `RZZGate` defines an `order` attribute with decomposition (CX, RZ, CX).

**Static methods:** `CircuitOperation.get_gate(name)`, `CircuitOperation.list_gates()` -- used by the circuit to dynamically create methods.

### 1.4 Backend/Simulator System

**File:** `E:\opensource\qpiai-quantum-sdk\qpiai_quantum\jobmanager\backend.py`  
**Class:** `Backend` (Enum)

| Enum Value | Device Name | Description |
|-----------|-------------|-------------|
| `STATEVECTOR_SIMULATOR_CPU` | `QpiAI-QSV-Simulator` | Cloud statevector |
| `DENSITY_MATRIX_SIMULATOR_CPU` | `QpiAI-QDM-Simulator` | Cloud density matrix |
| `INDUS_QPU` | `QpiAI-Indus-1` | Real QPU hardware |
| `TENSOR_NETWORK_SIMULATOR_CPU` | `QpiAI-QTN-Simulator` | Cloud tensor network |
| `LOCAL_SIMULATOR` | `QpiAI-QSV-Local` | Local NumPy simulator |

Plus Lite variants: `QpiAI-QSV-Lite`, `QpiAI-QDM-Lite`.

**Also available:** `ResolvedBackend` dataclass with `ID`, `backend_name`, `address`, `health_check`, `run`.

### 1.5 Cloud Access (QCloud API)

**Server:** `https://qcloud-server.qpiai.tech` (default, configurable via `QPIAI_SERVER_URL` env var)

**Authentication flow:**
1. `QpiAIQuantumAuth.login(api_key)` -- validates key via `/api/users/me`, stores in `SDKUser` contextvar
2. API key from env `API_KEY` or `qcloud.env` file
3. `ExecutionEngine.execute_circuit(...)` -- sets up user context, delegates to `JobManager`

---

## 2. Circuit System (Detailed)

### 2.1 All Gate Types

**Single-qubit non-parametric:** H, X, Y, Z, ID, S, SDG, T, TDG, SX  
**Single-qubit parametric:** RX(theta), RY(theta), RZ(theta), P(theta)  
**Two-qubit non-parametric:** CX, CY, CZ, SWAP, ISWAP  
**Two-qubit parametric:** CP(theta), RZZ(theta)  
**Three-qubit:** CCX (Toffoli), CSWAP (Fredkin), MCX (arbitrary controls)  
**Special:** Barrier, Measure, Operation (generic composite)

### 2.2 Circuit Construction Patterns

```python
# Pattern 1: Basic
qc = Circuit(2, 2)
qc.h(0)
qc.cx(0, 1)
qc.measure(0, 0); qc.measure(1, 1)

# Pattern 2: Custom registers
qreg = QuantumRegister(3)
creg = ClassicalRegister(3)
qc = Circuit(qreg, creg)

# Pattern 3: Chaining via dynamic methods
qc.H(0).CX(0, 1)  # Note: dynamic methods return None, no chaining

# Pattern 4: add_operation directly
qc.add_operation(CXGate(0, 1))
```

### 2.3 Parameterized Gates

All rotation gates accept `theta` in radians:
```python
qc.rx(0, np.pi/4)    # RX(pi/4)
qc.ry(1, 1.57)
qc.rz(0, np.pi)
qc.p(0, 0.5)         # Phase gate
qc.cp(0, 1, np.pi)   # Controlled phase
qc.rzz(0, 1, np.pi/2) # ZZ interaction
```

### 2.4 Compose and Inverse

**Compose:**
```python
qc1 = Circuit(3)
qc1.h(0); qc1.cx(0, 1)
qc2 = Circuit(3)
qc2.cx(1, 2)
qc1.compose(qc2)                    # Append qc2's operations
qc1.compose(qc2, qubits=[2, 1, 0])  # Remap qubits
```

**Inverse:**
```python
inv = qc.inverse()
# Self-inverse: H, X, Y, Z, ID, SX, CX, CY, CZ, SWAP, CCX, CSWAP, ISWAP, MCX
# Conjugate: S<->SDG, T<->TDG
# Negate params: RX, RY, RZ, P, CP, RZZ
```

### 2.5 Measurement Patterns

```python
# Single measurement
qc.measure(0, 0)

# Multiple measurements
qc.measure([0, 1, 2], [0, 1, 2])

# All qubits
qc.measure_all()
```

### 2.6 Gate Matrices (Simulator Layer)

**File:** `E:\opensource\qpiai-quantum-sdk\qpiai_quantum\simulator\gates.py`

Pure-math module with all gate matrix definitions. Key matrices:
- Standard Paulis: `I2`, `X`, `Y`, `Z`, `H`, `S`, `SDG`, `T`, `TDG`, `SX`, `SXDG`
- Multi-qubit: `SWAP`, `ISWAP`, `ECR`
- Parametric factories: `rx_matrix`, `ry_matrix`, `rz_matrix`, `rxx_matrix`, `ryy_matrix`, `rzz_matrix`, `u3_matrix`
- `controlled(U, n_ctrl)` -- creates controlled-U
- `gate_spec(name, params, num_qubits)` -- returns `(num_qubits, matrix)` tuple
- `decompose(name, qubits)` -- decomposition for `dcx`, `rccx`
- `ALL_KNOWN_GATES` set of 40+ gate names

**Additional known gates in gate_spec:** `ch`, `cs`, `dcx`, `ecr`, `rxx`, `ryy`, `crx`, `cry`, `crz`, `cu1`, `cu3`, `cu`, `rccx`

---

## 3. Quantum Information (`qpiai_quantum/quantum_info/`)

### 3.1 Statevector

**File:** `E:\opensource\qpiai-quantum-sdk\qpiai_quantum\quantum_info\statevector.py`  
**Class:** `Statevector`

**Constructor:**
```python
Statevector(data, dims=None, experiment_name="...", device_name="QpiAI-QSV-Local")
# data can be: list, np.ndarray, Circuit (simulates), Statevector (copy)
```

**Factory methods:**
- `from_label(label)` -- e.g., `Statevector.from_label("10")` creates |10>
- `from_circuit_object(circuit, ...)` -- simulates circuit

**Properties/Methods:**
- `probabilities()` -- returns np.array of |amplitude|^2
- `probabilities_dict(decimals=None)` -- dict mapping basis states to probs
- `to_dict(decimals=None)` -- dict mapping basis states to complex amplitudes
- `purity()` -- Tr(rho^2)
- `is_valid(atol)` -- checks normalization
- `to_density_matrix()` -- converts to DensityMatrix
- `evolve(other)` -- evolve by Circuit (NotImplementedError) or unitary matrix
- `copy()` -- deep copy
- Arithmetic: `__add__`, `__sub__`, `__mul__`, `__truediv__`, `__getitem__`, `__array__`

### 3.2 DensityMatrix

**File:** `E:\opensource\qpiai-quantum-sdk\qpiai_quantum\quantum_info\density_matrix.py`  
**Class:** `DensityMatrix` (extends `BaseDensityMatrix`)

**Constructor:** Same pattern as Statevector (list, ndarray, Circuit, copy)

**Inherited from BaseDensityMatrix** (`E:\opensource\qpiai-quantum-sdk\qpiai_quantum\formalism\density_matrix\base_density_matrix.py`):
- `purity()`, `von_neumann_entropy()`, `trace()`, `is_valid(atol)`, `is_pure(atol)`
- `fidelity(other, validate)` -- fidelity between two density matrices
- `partial_trace(qubits_to_keep, dims)` -- returns reduced density matrix

**Additional methods:**
- `probabilities()`, `probabilities_dict(decimals)`
- `entropy()` (alias for von_neumann_entropy)
- `to_statevector()` -- for pure states only
- `to_formalism()` -- convert to formalism.DensityMatrix (noise support)
- `from_formalism(formalism_dm)` -- convert back
- `copy()`, arithmetic operators

### 3.3 Formalism DensityMatrix (Advanced)

**File:** `E:\opensource\qpiai-quantum-sdk\qpiai_quantum\formalism\density_matrix\density_matrix.py`  
**Class:** `formalism.DensityMatrix`

Contains advanced operations:
- **Noise channels:** `ADC(param)` (amplitude damping), `depol(param)` (depolarizing) -- both 2-qubit only
- **Entropy:** `reyni(base, alpha)` -- Renyi entropy
- **Kraus operators:** `kraus(operator_list)` -- apply custom Kraus operators
- **Entanglement:** `concurrence()`, `eof()` (entanglement of formation), `schmidt_rank()`
- **Partial transpose:** `partial_transpose(dims, axis)`
- **Partial trace:** `partial_trace(dims, axis)`
- **Bell/CHSH:** `max_bell_value()`, `teleportation_fidelity()`
- **Distinguishability:** `distinguishability(X, ...)` -- state discrimination
- **Coherence:** `relative_entropy_coherence()`
- **Correlation:** `correlation_points(state)`, `plot_correlation_space_2q()`
- **Utilities:** `basis_operators()`, `check_MUB()`, `tensor_product()`, `gate_expand_2toN()`, `swap()`, `entangling_power_2q()`

---

## 4. Formalism (`qpiai_quantum/formalism/`)

### 4.1 Supported Formalisms

The formalism module currently provides:
- **Density Matrix formalism** with full advanced operations
- **BaseDensityMatrix** ABC defining the common contract

No stabilizer formalism is directly implemented in a dedicated module. However, the circuit's `list_gates()` method includes Clifford gate detection:

```python
clifford_gate_names = {"H", "X", "Y", "Z", "S", "SDG", "SX", "CX", "CY", "CZ", "SWAP", "ISWAP", "ID"}
```

This suggests partial Clifford/stabilizer awareness for gate counting, but there's no dedicated stabilizer simulation backend.

### 4.2 Density Matrix Representations

Two layers:
1. `quantum_info.DensityMatrix` -- user-facing, circuit-integrated
2. `formalism.DensityMatrix` -- advanced math operations

Convert between them via `quantum_info.DensityMatrix.to_formalism()` and `DensityMatrix.from_formalism()`.

---

## 5. Algorithms (`qpiai_quantum/algorithms/`)

### 5.1 Available Algorithms

| Algorithm | File | Class | Description |
|-----------|------|-------|-------------|
| QFT | `qft.py` | `QFT` | Quantum Fourier Transform (+ inverse) |
| Grover Search | `grover.py` | `GroverSearch` | Unstructured search |
| Shor's Factoring | `shor.py` | `ShorsAlgorithm` | Factoring (educational, N <= 20) |
| Simon's | `simon.py` | `SimonAlgorithm` | Hidden bitstring finder |
| Bernstein-Vazirani | `bernstein_vazirani.py` | `BernsteinVazirani` | Hidden string in 1 query |
| Deutsch-Jozsa | `deutsch_jozsa.py` | `DeutschJozsa` | Constant vs balanced |
| QPE | `phase_estimation.py` | `QuantumPhaseEstimation` | Phase estimation |
| QRNG | `qrng.py` | `QRNG` | Quantum random number generation |
| Amplitude Est. | `amplitude_estimation.py` | `EstimationProblem, AmplitudeEstimation, IterativeAmplitudeEstimation` | Amplitude estimation |
| VQE | `opt/solvers/vqe.py` | `VQESolver` | Variational quantum eigensolver |
| QAOA | `opt/solvers/qaoa.py` | (via VQE/QAOA framework) | Quantum approximate optimization |

### 5.2 Algorithm Base Class

**File:** `E:\opensource\qpiai-quantum-sdk\qpiai_quantum\algorithms\base.py`  
**Class:** `QuantumAlgorithm` (ABC)

```python
class QuantumAlgorithm(ABC):
    def __init__(self, num_qubits, name="QuantumAlgorithm")
    @abstractmethod
    def build_circuit(self, *args, **kwargs) -> Circuit
    def run(self, shots=1024, experiment_name="...", need_statevector=True,
            need_density_matrix=False, device_name="QpiAI-QSV-Local",
            reverse_bits=False, **kwargs) -> BaseQuantumResult
    def visualize(self, plot="circuit", result=None, **kwargs)
    def to_qasm(self)
    def get_info(self)
```

All algorithms follow this pattern: `build_circuit()` -> `run()` -> analyze results.

### 5.3 QRNG (QKD-relevant)

**File:** `E:\opensource\qpiai-quantum-sdk\qpiai_quantum\algorithms\qrng.py`

```python
class QRNG(QuantumAlgorithm):
    def __init__(self, n_bits=8)
    def build_circuit(self) -> Circuit  # H gates + measure all
    def generate(self, shots=1, output_format="int")  # "int", "bytes", "bitstring"
    def generate_batch(self, count, output_format="int")
```

QRNG creates superposition with Hadamard gates, measures all qubits, and converts bitstrings to int/bytes/bitstring. This is directly applicable to QKD key generation.

### 5.4 QPE (relevant for QKD distance bounding etc.)

```python
class QuantumPhaseEstimation(QuantumAlgorithm):
    def __init__(self, precision_qubits, eigenstate_qubits)
    def build_circuit(self, unitary="T", eigenstate_preparation=None)
    def estimate_phase(self, unitary="T") -> float
```

### 5.5 Optimization Algorithms

**VQE** (`opt/solvers/vqe.py`):
- Uses hardware-efficient ansatz, Ry rotations + entangling CX layers
- Classical optimizer: COBYLA, SPSA, etc.

**QAOA** (`opt/solvers/qaoa.py`):
- MaxCut problem encoding
- Parameterized alternating operator layers

**Ansatz classes:**
- `hardware_efficient.py` -- Ry + CX layers
- `standard.py` -- standard parameterized circuits
- `custom.py` -- custom ansatz with `NotImplementedError` stub

---

## 6. Hardware Integration

### 6.1 Authentication

**File:** `E:\opensource\qpiai-quantum-sdk\qpiai_quantum\authentication\auth.py`  
**Class:** `QpiAIQuantumAuth`

```python
QpiAIQuantumAuth.login(api_key)       # Validate and store
QpiAIQuantumAuth.logout()              # Clear user
QpiAIQuantumAuth.verify_api_key()      # Check validity
QpiAIQuantumAuth.me(api_key=None)      # Get user info
QpiAIQuantumAuth.list_compute_resources(display=True)  # List available backends
```

**User context** (`authentication/user.py`):
- `SDKUser` dataclass (name, email, api_key)
- `set_user()`, `get_user()`, `clear_user()` via `contextvars`
- `user_context(api_key)` context manager for scoped authentication

### 6.2 Circuit Execution Flow

**Via circuit.run():**
```python
result = circuit.run(
    shots=1024,
    experiment_name="Default Experiment",
    need_statevector=False,
    need_density_matrix=False,
    device_name="QpiAI-QSV-Simulator",  # or QpiAI-QSV-Local for local
    reverse_bits=False,
)
```

**Execution engine dispatch:**
1. `Circuit.run()` calls `ExecutionEngine.execute_circuit()`
2. If `QpiAI-QSV-Local`: uses local `StatevectorSimulator`
3. Otherwise: uses `JobManager.submit_and_wait_for_results_qasm()`
4. QASM string is generated via `QASM2.generate()`
5. Submitted to cloud API at `/api/circuits/create` then `/api/jobs/qasm`
6. Results polled or SSE-streamed back

### 6.3 Job Management

**File:** `E:\opensource\qpiai-quantum-sdk\qpiai_quantum\jobmanager\jobmanager.py`  
**Class:** `JobManager`

Key methods:
- `submit_qasm_job(qasm_string, ...)` -- submit OpenQASM 2.0 to cloud
- `submit_circuit_job(circuit, ...)` -- submit Circuit/ICR object
- `submit_and_wait_for_results_qasm(...)` -- all-in-one with SSE + polling fallback
- `get_job_status(job_id)` -- check status
- `get_job_results(job_id, device_name)` -- retrieve completed results
- `get_current_job()` -- currently running job
- `get_job_history(period, status, page, page_size)` -- list jobs
- `cancel_job(job_id)` -- cancel a job
- `delete_job(job_id)` -- delete a job
- `list_compute_resources()` -- list available backends

**SSE support:** `SSEResultHandler` for real-time job status events, with polling fallback for reliability.

### 6.4 Job Result

**File:** `E:\opensource\qpiai-quantum-sdk\qpiai_quantum\jobmanager\job_result.py`  
**Class:** `JobResult` (aliased as `JobExecutionResult`)

Properties: `counts`, `statevector`, `probabilities`, `density_matrix`, `execution_time`, `shots`, `job_id`, `job_status`, `method`, `credits_used`, `job_metadata`

Methods: `get(*params)`, `to_json()`, `plot(*others, **kwargs)` (inherited from BaseQuantumResult)

### 6.5 Static Job Methods on Circuit

```python
Circuit.get_job_status(job_id)
Circuit.check_job_status(job_id)
Circuit.get_job_results(job_id)
Circuit.cancel_job(job_id)
Circuit.delete_job(job_id)
Circuit.get_current_job()
Circuit.get_job_history(period, status, page, page_size)
Circuit.list_jobs(...)
```

### 6.6 QASM Exporter

**File:** `E:\opensource\qpiai-quantum-sdk\qpiai_quantum\iem\qasm\v2\exporter.py`  
**Class:** `QASM2`

```python
QASM2.generate(circuit) -> str  # OpenQASM 2.0 string
```

Handles: standard gates, parameterized gates with `(params)` syntax, measure, barrier, reset.

---

## 7. QKD-Relevant Capabilities

### 7.1 State Preparation Patterns

**Bell states** (entangled pairs for QKD):
```python
from qpiai_quantum.state_preparation import BellStateGenerator
bell = BellStateGenerator("|Ψ+>")  # or "|Ψ->", "|Φ+>", "|Φ->"
circuit = bell.build_circuit(measure=True)
result = bell.run(shots=1024)
```

**GHZ states** (multi-partite entanglement):
```python
ghz = GHZStateGenerator(num_qubits=3)
circuit = ghz.build_circuit(measure=True)
```

**W states** (robust entanglement):
```python
w = WStateGenerator(num_qubits=3)
circuit = w.build_circuit(measure=True)
```

**Cluster states** (measurement-based QC):
```python
cluster = ClusterStateGenerator(num_qubits=4)
circuit = cluster.build_circuit(measure=True)
```

### 7.2 Measurement Basis Rotation

The SDK provides rotation gates for basis changes:
```python
# H gate for X-basis measurement
qc.h(qubit)
qc.measure(qubit, clbit)

# RY for various basis rotations
qc.ry(qubit, theta)

# RX, RZ for other axes
qc.rx(qubit, theta)
qc.rz(qubit, theta)
```

No dedicated measurement-basis-rotation utility exists, but the building blocks are all there (H, RX, RY, RZ rotate into any basis).

### 7.3 Channel Noise Simulation

**Via formalism.DensityMatrix:**
```python
from qpiai_quantum.formalism import DensityMatrix as FDM

# Depolarizing noise
dm = FDM(state)
noisy = dm.depol(param=0.1)  # 10% depolarizing

# Amplitude damping
noisy = dm.ADC(param=0.1)

# Custom Kraus operators
noisy = dm.kraus([K0, K1])
```

**Limitation:** Both `ADC()` and `depol()` currently work only for 2-qubit states (4x4 matrices). The Kraus operator method also has the same restriction.

### 7.4 Entanglement Verification

Each state generator has `verify_entanglement(result, threshold)`:
- `BellStateGenerator.verify_entanglement()` -- checks expected outcome probabilities
- `GHZStateGenerator.verify_entanglement()` -- checks all-zeros and all-ones
- `WStateGenerator.verify_entanglement()` -- checks single-excitation distribution
- `ClusterStateGenerator.verify_entanglement()` -- checks uniformity

### 7.5 Key Generation Workflows

The **QRNG** algorithm is the most directly QKD-relevant:
```python
rng = QRNG(n_bits=256)  # 256-bit random number
key_int = rng.generate(output_format="int")    # single random int
key_bytes = rng.generate(output_format="bytes") # as bytes
key_bits = rng.generate(output_format="bitstring")  # as bitstring
batch = rng.generate_batch(count=10, output_format="int")  # batch
```

The base `QuantumAlgorithm.run()` method supports:
- Running on local simulator (`QpiAI-QSV-Local`)
- Running on cloud simulator (`QpiAI-QSV-Simulator`)
- Running on real QPU (`QpiAI-Indus-1`)
- Different methods: `statevector`, `density_matrix`, `tensor_network`

### 7.6 State Tomography and Analysis

Via `formalism.DensityMatrix`:
- `fidelity()` -- compare states
- `purity()` -- state purity
- `von_neumann_entropy()` -- entropy
- `concurrence()` -- entanglement measure
- `partial_trace()` -- reduced density matrices

---

## 8. Recent Changes

### 8.1 Git History Highlights (last ~30 commits)

```
829b162 Merge pull request #14 from qpiai/fix/sse-polling-fallback
184744a fix(jobs): fall back to polling for SSE
460d511 fix(http): add request timeouts
25e4183 docs: clarify modular exponentiation comment in Shor's algorithm
1f10cd9 docs: clarify AmplitudeEstimation availability
d54dd3b fix: replace silent stub in custom_ansatz with NotImplementedError
58c8674 build(deps): move ipykernel to dev dependencies
6011607 docs: fix overstated algorithm claims in Shor, AE, QRNG
084c6fa feat: add GitHub issue templates
aec1e9c ci: configure API_KEY secret for test execution
97af9ac build: bump version to 0.1.42 and declare dev dependencies
46f621d ci: configure github actions pipeline and declare python 3.13/3.14 support
e7fac7e build: upgrade locked dependencies to resolve security vulnerabilities
f22204d style: format files using ruff format
0c264bf docs: fix 'desnity' spelling typo in density_matrix.py
28864e2 refactor: rename misspelled core classes and fix typos
2138180 fix(jobmanager): wire access_token to actually authenticate requests
26a36fc refactor(env): standardize on API_KEY and qcloud.env
28947bb fix(circuit): prevent duplicate keyword argument crash in run()
7f4d912 fix(simulator): support OperationType.OPERATION recursively and fix ISwapGate type
9bc99a9 fix(circuit): rename IDGate name from I to ID and add visualizer mappings
```

### 8.2 Notable Fixes and Features

- **SSE + polling fallback** for job status monitoring (fixes reliability)
- **HTTP timeouts** added (10s connect, 120s response)
- **API_KEY standardization** across env and qcloud.env
- **IDGate renamed** from `I` to `ID` to avoid OpenQASM conflicts
- **Simulator supports `OperationType.OPERATION`** recursion (composite gates)
- **ISwapGate type** corrected
- **Duplicate keyword argument** bug in `circuit.run()` fixed
- **Class renaming** for misspelled classes
- **Algorithm docs** clarified limitations (Shor, AE, QRNG)

### 8.3 Test Coverage

Tests exist for:
- `tests/test_circuit_operations.py`
- `tests/test_cluster_state.py`
- `tests/test_http_timeouts.py`
- `tests/test_jobmanager_wait.py`
- `tests/test_matplotlib_visualizer.py`
- `tests/algorithms/` -- 13 algorithm test files
- `tests/formalism/` -- 2 formalism test files

---

## Summary of QKD-Relevant Findings

| Capability | Status | SDK Entry Points |
|-----------|--------|-----------------|
| Superposition | Available | `circuit.h(q)`, `circuit.rx/ry/rz(q, theta)` |
| Entanglement | Available | `BellStateGenerator`, `GHZStateGenerator`, manual H+CX |
| Measurement (Z-basis) | Available | `circuit.measure(q, c)`, `circuit.measure_all()` |
| Measurement (X/Y basis) | Building blocks | H for X-basis, no dedicated utility |
| Channel noise | Available | `formalism.DensityMatrix.depol()`, `.ADC()` (2-qubit only) |
| State fidelity | Available | `quantum_info.DensityMatrix.fidelity()` |
| Key generation | Available | `QRNG` algorithm with int/bytes/bitstring output |
| Cloud execution | Available | `circuit.run(device_name="QpiAI-QSV-Simulator")` |
| Real QPU | Available | `device_name="QpiAI-Indus-1"` (requires API key) |
| Composability | Available | `circuit.compose()`, `to_circuit_operation()` |
| Parameterized circuits | Available | RX, RY, RZ, P, CP, RZZ |
| Local simulation | Available | `StatevectorSimulator` (NumPy-based) |
| OpenQASM export | Available | `circuit.to_qasm()` |

### Key Gaps for QKD Implementation

1. **No dedicated QKD protocol modules** (BB84, E91, B92, etc.) -- would need to be built from scratch using the available building blocks
2. **No sifting/post-processing utilities** (basis reconciliation, error correction, privacy amplification)
3. **No quantum channel model** with configurable noise parameters (beyond the 2-qubit `depol()`/`ADC()`)
4. **No measurement-basis-choice utility** for randomizing between X and Z bases
5. **No key distillation workflow** -- would need to be implemented
6. **No E91-type entanglement-based QKD** -- though Bell/entangled states can be created
7. **No decoy-state protocol** support for practical QKD over lossy channels
