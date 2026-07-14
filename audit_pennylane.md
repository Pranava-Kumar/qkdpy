# PennyLane Architecture Audit for qkdpy Integration Enhancement

**Audit Date:** 2026-07-14
**PennyLane Source:** E:/opensource/pennylane/
**Existing Integration:** E:/opensource/qkdpy/src/qkdpy/integrations/pennylane_integration.py

---

## Table of Contents

1. [Core Architecture](#1-core-architecture)
2. [Quantum Operations](#2-quantum-operations)
3. [QNode Execution Pipeline](#3-qnode-execution-pipeline)
4. [Optimization and ML](#4-optimization-and-ml)
5. [Noise and Hardware](#5-noise-and-hardware)
6. [QKD-Relevant Capabilities](#6-qkd-relevant-capabilities)

---

## 1. Core Architecture

### 1.1 QNode (Circuit Decorator and Execution Pipeline)

**File:** `E:/opensource/pennylane/pennylane/workflow/qnode.py`

The `QNode` class is the central abstraction. It wraps a quantum function and a device:

```python
class QNode:
    def __init__(self, func, device, interface="auto", diff_method="best",
                 grad_on_execution="best", cache="auto", cachesize=10000,
                 max_diff=1, device_vjp=None, postselect_mode=None,
                 mcm_method=None, gradient_kwargs=None, static_argnums=(),
                 executor_backend=None, shots="unset")
```

**Execution flow:**

1. **`__call__`** triggers `_impl_call` (line 785):
   - `construct(args, kwargs)` -- calls the quantum function inside an `AnnotatedQueue` context, producing a `QuantumScript` (tape)
   - Calls `execute((tape,), device, ...)` from the workflow module

2. **`construct`** (line 762):
   ```python
   def construct(self, args, kwargs) -> qp.tape.QuantumScript:
       with AnnotatedQueue() as q:
           self._qfunc_output = self.func(*args, **kwargs)
       tape = QuantumScript.from_queue(q, self.shots)
       params = tape.get_parameters(trainable_only=False)
       tape.trainable_params = math.get_trainable_indices(params)
       _validate_qfunc_output(self._qfunc_output, tape.measurements)
       self._tape = tape
       return tape
   ```

3. **Decorator usage** -- `qml.qnode(dev)` is the `qnode` decorator, which is an alias to constructing `QNode(func, dev)`.

**Key method:** `_impl_call` (line 785) calls `execute` from `pennylane.workflow.execution`, passing the tape, device, diff_method, interface, and transform program.

### 1.2 Device System

**Base class:** `E:/opensource/pennylane/pennylane/devices/device_api.py` -- `Device` ABC

Key abstract methods:
- `preprocess(execution_config)` -> `(CompilePipeline, ExecutionConfig)` -- preprocessing pipeline
- `execute(circuits, execution_config)` -> `ResultBatch` -- runs circuits
- `supports_derivatives(execution_config, circuit)` -> `bool`
- `compute_derivatives`, `compute_vjp`, `compute_jvp` -- differentiation support

**Devices available:**

| Device | File | Type |
|--------|------|------|
| `DefaultQubit` | `devices/default_qubit.py` | State-vector simulator, backprop/adjoint |
| `DefaultMixed` | `devices/default_mixed.py` | Density matrix simulator, noise channels |
| `DefaultClifford` | `devices/default_clifford.py` | Clifford simulator (stabilizer) |
| `DefaultGaussian` | `devices/default_gaussian.py` | CV Gaussian simulator |
| `DefaultQutrit` | `devices/default_qutrit.py` | Qutrit simulator |
| `DefaultQutritMixed` | `devices/default_qutrit_mixed.py` | Mixed qutrit |
| `DefaultTensor` | `devices/default_tensor.py` | Tensor network simulator |
| `NullQubit` | `devices/null_qubit.py` | No-op device for testing |
| Legacy devices | `_qubit_device.py` (74K) | Old `QubitDevice` base class |

**`DefaultQubit`** (`E:/opensource/pennylane/pennylane/devices/default_qubit.py`):
- State-vector simulation via `E:/opensource/pennylane/pennylane/devices/qubit/simulate.py`
- `apply_operation` uses singledispatch for per-gate optimizations (einsum, tensordot) -- `devices/qubit/apply_operation.py`
- Supports backpropagation (native autodiff through state vector)
- Supports adjoint differentiation
- Supports mid-circuit measurements (deferred, one-shot, tree-traversal strategies)
- Gate set: `ALL_DQ_GATES` includes all base gates + controlled variants + adjoint variants
- Special operator support: QFT (< 6 wires), GroverOperator (< 13 wires), FromBloq (< 4 wires), IQP (< 6 wires)

**`DefaultMixed`** (`E:/opensource/pennylane/pennylane/devices/default_mixed.py`):
- Density matrix simulation via `E:/opensource/pennylane/pennylane/devices/qubit_mixed/simulate.py`
- Full noise channel support
- Uses Kraus operator representation
- Supports all standard noise channels

### 1.3 Operator System

**File:** `E:/opensource/pennylane/pennylane/core/operator/base.py`

**Inheritance hierarchy:**
```
Operator (ABC)  -- base for all operators
  ├── Operator1  -- old interface marker
  ├── Operator2  -- new interface (2026+)
  ├── Operation  -- unitary gates, inherits Operator
  ├── Channel    -- noise channels, inherits Operation
  ├── StatePrepBase -- state preparation ops
  └── Observable -- measurement observables (mixin)
```

**Core `Operator` attributes:**
- `num_params`, `ndim_params` -- parameter metadata
- `wires` -- `Wires` object
- `data` -- parameter tensor(s)
- `has_matrix`, `has_decomposition`, `has_generator`, `has_adjoint`
- `grad_method` -- `"A"` (analytic/param-shift), `"F"` (finite-diff), `None`
- `grad_recipe` -- custom gradient recipes
- `compute_matrix(*params)` / `matrix()` -- matrix representation
- `compute_decomposition(*params, wires)` / `decomposition()` -- decomposition
- `compute_diagonalizing_gates` -- for observables
- `eigvals()` -- eigenvalues

**Operator Arithmetic (`ops/op_math/`):**

| Class | File | Purpose |
|-------|------|---------|
| `Adjoint` | `ops/op_math/adjoint.py` | `qml.adjoint(op)` |
| `Controlled` | `ops/op_math/controlled.py` | `qml.ctrl(op, control=...)` |
| `Controlled2` | `ops/op_math/controlled2.py` | New controlled base (2026) |
| `Pow` | `ops/op_math/pow.py` | `qml.pow(op, n)` |
| `Exp` | `ops/op_math/exp.py` | `qml.exp(op)` |
| `Sum` | `ops/op_math/sum.py` | `qml.sum(ops)` |
| `Prod` | `ops/op_math/prod.py` | `qml.prod(ops)` |
| `SProd` | `ops/op_math/sprod.py` | `qml.s_prod(scalar, op)` |
| `LinearCombination` | `ops/op_math/linear_combination.py` | `qml.Hamiltonian(coeffs, obs)` -- replaces old `Hamiltonian` |
| `Conditional` | `ops/op_math/conditional.py` | `qml.cond(meas_val, then_op, else_op)` |
| `Evolution` | `ops/op_math/evolution.py` | `qml.evolve(H, t)` time evolution |
| `SymbolicOp` | `ops/op_math/symbolicop.py` | Base for single-operand symbolic ops |
| `CompositeOp` | `ops/op_math/composite.py` | Base for multi-operand ops |
| `ChangeOpBasis` | `ops/op_math/change_op_basis.py` | Change of basis operations |

**Hamiltonian representation:** `LinearCombination` (in `ops/op_math/linear_combination.py`) is the modern replacement for the legacy `Hamiltonian` class. It inherits from `Sum` and represents `sum_k c_k O_k`.

### 1.4 Differentiation Engine

**File:** `E:/opensource/pennylane/pennylane/gradients/__init__.py`

**Gradient transforms available:**

| Transform | File | Description |
|-----------|------|-------------|
| `param_shift` | `gradients/param_shift.py` | Standard parameter-shift rule |
| `param_shift_cv` | `gradients/param_shift_cv.py` | CV parameter-shift |
| `param_shift_hessian` | `gradients/param_shift_hessian.py` | Second-order param-shift |
| `finite_diff` | `gradients/finite_diff.py` | Numerical finite differences |
| `spsa_grad` | `gradients/spsa_grad.py` | Simultaneous perturbation |
| `hadamard_grad` | `gradients/hadamard_grad.py` | Hadamard test gradient |
| `stoch_pulse_grad` | `gradients/stoch_pulse_grad.py` | Stochastic pulse gradient |
| `pulse_odegen` | `gradients/pulse_odegen.py` | ODE-based pulse gradient |

**Metric tensors:**
- `pennylane.adjoint_metric_tensor`
- `pennylane.metric_tensor`

**Differentiation methods (QNode `diff_method` parameter):**
- `"backprop"` -- classical backprop through simulator (fastest, simulator-only)
- `"adjoint"` -- adjoint differentiation (O(N^2) memory, simulator-only)
- `"parameter-shift"` -- analytic parameter-shift rule (hardware-compatible)
- `"hadamard"` -- Hadamard test gradient
- `"finite-diff"` -- numerical finite differences
- `"spsa"` -- simultaneous perturbation approximation
- `"device"` -- device-native gradient
- `"best"` -- auto-selects best available
- `None` -- no differentiation

**Differentiation resolution:** `E:/opensource/pennylane/pennylane/workflow/resolution.py`

---

## 2. Quantum Operations

### 2.1 Standard Gates

**File:** `E:/opensource/pennylane/pennylane/ops/qubit/`

**Non-parametric** (`non_parametric_ops.py`):
- `Hadamard`/`H`, `PauliX`/`X`, `PauliY`/`Y`, `PauliZ`/`Z`
- `S`, `T`, `SX` (sqrt-X)
- `SWAP`, `ISWAP`, `ECR`
- `CNOT`, `CY`, `CZ`, `CH`
- `Toffoli` (CCNOT), `CCZ`, `CSWAP`
- `MultiControlledX` -- multi-controlled NOT

**Single-qubit parametric** (`parametric_ops_single_qubit.py`):
- `RX(phi)`, `RY(phi)`, `RZ(phi)` -- Pauli rotations
- `PhaseShift(phi)` -- phase gate
- `Rot(phi, theta, omega)` -- Euler rotation (ZYZ convention)
- `PCPhase(phi, wires)` -- phase from controlled phase

**Multi-qubit parametric** (`parametric_ops_multi_qubit.py`):
- `MultiRZ(theta)` -- multi-qubit Z rotation
- `CRX`, `CRY`, `CRZ`, `CRot` -- controlled rotations
- `ControlledPhaseShift`
- `IsingXX(phi)`, `IsingYY(phi)`, `IsingZZ(phi)` -- Ising couplings
- `IsingXY(phi)` -- XY interaction
- `PSWAP(phi)` -- Parametric SWAP
- `FermionicSWAP`
- `SingleExcitation`, `DoubleExcitation`, `OrbitalRotation`
- `ParametrizedEvolution` -- pulse-level evolution

**Matrix-based** (`matrix_ops.py`):
- `QubitUnitary(U, wires)` -- arbitrary unitary
- `DiagonalQubitUnitary(D, wires)` -- diagonal unitary
- `BlockEncode(A, wires)` -- block encoding

**Arithmetic** (`arithmetic_ops.py`):
- `QubitCarry`, `QubitSum`, `IntegerComparator`

### 2.2 State Preparation Routines

**File:** `E:/opensource/pennylane/pennylane/ops/qubit/state_preparation.py`

| Class | Description |
|-------|-------------|
| `BasisState(state, wires)` | Prepare computational basis state |
| `StatePrep(state, wires)` | Prepare arbitrary state vector |
| `QubitDensityMatrix(rho, wires)` | Prepare density matrix (mixed state) |

State prep ops have `StatePrepBase` as base (in `core/operator/`).

### 2.3 Mid-Circuit Measurements and Conditional Operations

**File:** `E:/opensource/pennylane/pennylane/ops/mid_measure/`

```python
from pennylane.ops import measure, MidMeasure, MeasurementValue, pauli_measure, PauliMeasure
```

- **`measure(wires)`** -- Returns a `MeasurementValue` (MV) object used for classical feedforward
- **`MidMeasure`** -- The actual operation class that gets queued
- **`MeasurementValue`** -- Symbolic representation of mid-circuit measurement results
- **`pauli_measure(wires, pauli_word)`** -- Pauli measurement (destructive)
- **`get_mcm_predicates(mcm_values)`** -- Get predicates for postselection

**Conditional operations:**
- `qml.cond(measurement_value, true_fn, false_fn)` -- creates a `Conditional` operation
- Supports: `if measured == 0: do_x; else: do_y`
- `qml.ops.op_math.Conditional` -- the class underlying conditional ops

**MCM execution strategies (set via `mcm_method` in QNode):**
- `"deferred"` -- Deferred measurement principle (converts MCMs to controlled ops)
- `"one-shot"` -- One-shot execution (for finite shots)
- `"tree-traversal"` -- Tree traversal (only default.qubit and lightning.qubit)

### 2.4 Template Circuits

**File:** `E:/opensource/pennylane/pennylane/templates/__init__.py`

**Embeddings** (`templates/embeddings/`):
- `AmplitudeEmbedding`, `AngleEmbedding`, `BasisEmbedding`, `IQPEmbedding`, `QAOAEmbedding`
- `DisplacementEmbedding`, `SqueezingEmbedding` (CV)

**Layers** (`templates/layers/`):
- `BasicEntanglerLayers`, `StronglyEntanglingLayers`, `RandomLayers`
- `SimplifiedTwoDesign`, `CVNeuralNetLayers`
- `ParticleConservingU1`, `ParticleConservingU2`, `GateFabric`

**Subroutines** (`templates/subroutines/`):
- `QFT`, `QuantumPhaseEstimation`, `QuantumMonteCarlo`
- `GroverOperator`, `AmplitudeAmplification`
- `ArbitraryUnitary`, `Reflection`, `FlipSign`
- `Select`, `PrepSelPrep`, `Qubitization`
- `QSVT` / `qsvt` -- Quantum Singular Value Transformation
- `GQSP` -- Generalized QSP
- `TrotterProduct`, `ApproxTimeEvolution`, `CommutingEvolution`, `QDrift`
- `Interferometer`, `Permute`
- Arithmetic: `PhaseAdder`, `Adder`, `Multiplier`, `ModExp`, etc.
- QRAM: `BBQRAM`, `HybridQRAM`, `FFQRAM`
- QROM: `QROM`, `SelectOnlyQRAM`
- FABLE, FFFT, IQP

**Template core:** `templates/core.py` -- `SubroutineOp` and `Subroutine` base classes

**State preparation templates** (`templates/state_preparations/`):
- `MottonenStatePreparation`, `ArbitraryStatePreparation`

**Template helper:** `templates/layer.py` -- `layer()` function for repeating layers

### 2.5 Quantum Chemistry (qchem)

**File:** `E:/opensource/pennylane/pennylane/qchem/__init__.py`

Key capabilities:
- `molecular_hamiltonian(mol)` -- Build molecular Hamiltonian in second quantization
- `electron_integrals(mol, core, active)` -- One/two-electron integrals
- `dipole_integrals`, `dipole_moment` -- Dipole moment calculation
- `hf_energy`, `scf`, `nuclear_energy` -- Hartree-Fock
- `Molecule` class -- define molecular structure
- `load_basisset`, `BasisFunction` -- basis set data
- Converters: `import_operator`, `import_state` (Psi4, PySCF)
- OpenFermion: `from_openfermion`, `to_openfermion`

**QChem template subroutines** (`templates/subroutines/qchem/`):
- `UCCSD`, `kUpCCGSD`, `AllSinglesDoubles`
- `FermionicSingleExcitation`, `FermionicDoubleExcitation`
- `BasisRotation`

---

## 3. QNode Execution Pipeline

### 3.1 Circuit to Backend Conversion

The full pipeline from circuit definition to execution:

1. **QNode.__call__** calls `_impl_call`
2. **`construct`** wraps the quantum function in `AnnotatedQueue`, producing a `QuantumScript`
3. **`execute`** (in `workflow/execution.py`) orchestrates:
   - Resolve interface and diff method
   - Set up transform program (preprocessing)
   - Call `run()` (in `workflow/run.py`) to dispatch to device
4. **Device preprocessing** (`Device.preprocess`):
   - `setup_execution_config` -- configure MCM method, gradient method
   - `preprocess_transforms` -- add transforms: decompose, validate wires/measurements/observables, handle MCMs, handle non-commuting observables
5. **Device execution** (`Device.execute`) performs the actual simulation

### 3.2 Measurements

**File:** `E:/opensource/pennylane/pennylane/measurements/`

**Available measurements:**

| Function | Class | Description |
|----------|-------|-------------|
| `qml.expval(obs)` | `ExpectationMP` | Expectation value |
| `qml.var(obs)` | `VarianceMP` | Variance |
| `qml.probs(wires)` | `ProbabilityMP` | Measurement probabilities |
| `qml.sample(wires)` | `SampleMP` | Samples |
| `qml.state()` | `StateMP` | State vector |
| `qml.density_matrix(wires)` | `DensityMatrixMP` | Reduced density matrix |
| `qml.counts(wires)` | `CountsMP` | Count outcomes |
| `qml.mutual_info(wires1, wires2)` | `MutualInfoMP` | Mutual information |
| `qml.vn_entropy(wires)` | `VnEntropyMP` | Von Neumann entropy |
| `qml.purity(wires)` | `PurityMP` | Purity |
| `qml.classical_shadow(wires)` | `ClassicalShadowMP` | Classical shadows |
| `qml.shadow_expval(obs)` | `ShadowExpvalMP` | Shadow expectation value |
| `qml.measure(wires)` | MidCircuitMeasure | Mid-circuit measurement |

**Measurement base classes** (in `core/measurements.py`):
- `MeasurementProcess` -- base for all measurements
- `StateMeasurement` -- for analytic measurements (state-dependent)
- `SampleMeasurement` -- for shot-based measurements
- `MeasurementTransform` -- for measurement transforms

### 3.3 Shot-Based vs Analytic Simulation

**Shots configuration:**
- `qml.Shots(n)` -- set number of shots
- Shot-based: `SampleMP`, `CountsMP`, `ClassicalShadowMP`
- Analytic: `ExpectationMP`, `StateMP`, `ProbabilityMP` (when shots=None)

**Device behavior:**
- If `shots=None`: use analytic simulation (exact state vector/density matrix computation)
- If `shots > 0`: sample measurement outcomes using random number generator
- `DefaultQubit` applies measure-with-samples via `devices/qubit/sampling.py`
- `DefaultMixed` applies measure-with-samples via `devices/qubit_mixed/sampling.py`

**Key sampling code paths:**
- `devices/qubit/simulate.py` -- `measure()` and `measure_with_samples()`
- `devices/qubit/sampling.py` -- `measure_with_samples()` for DefaultQubit
- `devices/qubit_mixed/sampling.py` -- for DefaultMixed

---

## 4. Optimization and ML

### 4.1 Optimizers

**File:** `E:/opensource/pennylane/pennylane/optimize/__init__.py`

| Optimizer | Class | Description |
|-----------|-------|-------------|
| `GradientDescentOptimizer` | `gradient_descent.py` | Standard GD |
| `AdamOptimizer` | `adam.py` | Adam |
| `AdagradOptimizer` | `adagrad.py` | AdaGrad |
| `RMSPropOptimizer` | `rms_prop.py` | RMSProp |
| `MomentumOptimizer` | `momentum.py` | SGD with momentum |
| `NesterovMomentumOptimizer` | `nesterov_momentum.py` | Nesterov momentum |
| `QNGOptimizer` | `qng.py` | Quantum Natural Gradient |
| `QNSPSAOptimizer` | `qnspsa.py` | Quantum NSPSA |
| `MomentumQNGOptimizer` | `momentum_qng.py` | Momentum + QNG |
| `RiemannianGradientOptimizer` | `riemannian_gradient.py` | Riemannian gradient |
| `RotosolveOptimizer` | `rotosolve.py` | Rotosolve (no grad needed) |
| `RotoselectOptimizer` | `rotoselect.py` | Rotoselect |
| `ShotAdaptiveOptimizer` | `shot_adaptive.py` | Shot-adaptive |
| `SPSAOptimizer` | `spsa.py` | SPSA |
| `AdaptiveOptimizer` | `adaptive.py` | Adaptive (shorts) |

**JIT-compatible optimizers:**
- `QNGOptimizerQJIT`, `MomentumQNGOptimizerQJIT`

### 4.2 QNN Layer Types

**File:** `E:/opensource/pennylane/pennylane/qnn/__init__.py`

- **`TorchLayer`** (`qnn/torch.py`): wraps a QNode as a `torch.nn.Module`
  ```python
  class TorchLayer(torch.nn.Module):
      def __init__(self, qnode, weight_shapes, init_method=None, ...)
  ```
  - `weight_shapes` maps weight names to shapes
  - Forwards/backwards propagate through the QNode
  - Supports Torch's optimizer and Module API

- **`iqp_expval`** (`qnn/iqp.py`): IQP circuit expectation value estimator

**Note:** `KerasLayer` was previously available but has been removed (TF support deprecated in favor of Torch).

### 4.3 ML Pipeline Integration

**Interface support:**
- `"autograd"` -- PennyLane's own numpy wrapper (`pennylane.numpy`), provides `qml.grad`, `qml.jacobian`
- `"torch"` -- PyTorch tensors, works with `torch.nn.Module` via `TorchLayer`
- `"jax"` / `"jax-jit"` -- JAX arrays, works with `jax.grad`, `jax.jit`, `jax.vmap`
- `"auto"` -- auto-detect from input types
- `None` -- NumPy only (no differentiation)

**Key pattern for ML:**
```python
dev = qml.device("default.qubit", wires=2)
@qml.qnode(dev, interface="torch", diff_method="backprop")
def circuit(x, weights):
    qml.RX(x, wires=0)
    qml.StronglyEntanglingLayers(weights, wires=[0, 1])
    return qml.expval(qml.Z(0))

layer = qml.qnn.TorchLayer(circuit, {"weights": (n_layers, 2)})
```

**Execution resolution:** `E:/opensource/pennylane/pennylane/workflow/resolution.py` handles selecting the best diff method and interface.

### 4.4 Concurrency Support

- `DefaultQubit` supports `max_workers` for multiprocess execution
- Backends: native multiprocessing (`MPPoolExec`), configurable start methods
- `E:/opensource/pennylane/pennylane/concurrency/executors/`

---

## 5. Noise and Hardware

### 5.1 DefaultMixed Device

**File:** `E:/opensource/pennylane/pennylane/devices/default_mixed.py`

Simulates mixed states via density matrices. Operations are applied as:
- Unitary gates: `rho -> U * rho * U^dag`
- Channels: `rho -> sum_k K_k * rho * K_k^dag`

**Operation sets** (`DEFAULT_MIXED_GATES`):
All standard gates plus all noise channels.

**Simulation engine:** `E:/opensource/pennylane/pennylane/devices/qubit_mixed/simulate.py`
- `get_final_state(circuit)` -- returns final density matrix
- `measure(circuit, state, ...)` -- performs measurements
- `apply_operation(state, op, ...)` -- applies operation to density matrix

### 5.2 Noise Channels

**File:** `E:/opensource/pennylane/pennylane/ops/channel.py`

| Channel | Parameters | Description |
|---------|-----------|-------------|
| `AmplitudeDamping(gamma)` | gamma in [0,1] | Energy relaxation |
| `GeneralizedAmplitudeDamping(gamma, p)` | gamma, p | Thermal relaxation |
| `PhaseDamping(gamma)` | gamma in [0,1] | Dephasing |
| `DepolarizingChannel(p)` | p in [0,1] | Depolarizing |
| `BitFlip(p)` | p in [0,1] | Bit-flip error |
| `PhaseFlip(p)` | p in [0,1] | Phase-flip error |
| `PauliError(px, py, pz)` | probabilities | General Pauli error |
| `ResetError(prob0, prob1)` | probabilities | Reset to |0>/|1> |
| `QubitChannel(K_list)` | Kraus operators | Arbitrary channel |
| `ThermalRelaxationError(t1, t2, tg, pe)` | times | Thermal relaxation |

**Channel base class:** `Channel` in `Core/operator/__init__.py`, inherits from `Operation`.

### 5.3 Noise Models

**File:** `E:/opensource/pennylane/pennylane/noise/noise_model.py`

```python
class NoiseModel:
    def __init__(self, model_map=None, meas_map=None, **kwargs)
```

- `model_map`: `{BooleanFn: noise_fn}` -- gate error mapping
- `meas_map`: `{BooleanFn: noise_fn}` -- readout error mapping
- `noise_fn(op, **kwargs)` returns a noise operation to insert

**Conditionals** (`noise/conditionals.py`):
- `wires_in(wires)` -- matches operations on specified wires
- `wires_eq(wires)` -- matches exact wire sets
- `op_in(ops)` -- matches operation types
- `op_eq(op)` -- matches exact operation
- `meas_eq(mp)` -- matches measurement types
- `partial_wires(wires)` -- matches operations involving any of the wires

**Noise insertion** (`noise/add_noise.py`):
```python
@transform
def add_noise(tape, noise_model, level="user")
```
This is a transform that inserts noise operations according to the model.

**Noise mitigation** (`noise/mitigate.py`):
- `mitigate_with_zne(tape, scale_factors, extrapolate, folding)` -- Zero Noise Extrapolation
- `fold_global(tape, scale_factor)` -- global circuit folding
- `poly_extrapolate`, `richardson_extrapolate`, `exponential_extrapolate` -- extrapolation methods

**Noise insertion** (`noise/insert_ops.py`):
- `insert(op, op_fn, location)` -- insert operations at specified locations

### 5.4 Hardware Calibration

No direct hardware calibration data access was found in the core PennyLane source. Hardware-specific calibration is typically handled by device plugins (e.g., `pennylane-qiskit`, `pennylane-cirq`, `pennylane-braket`, `pennylane-ionq`, `pennylane-qsharp`). These plugins provide access to hardware backend properties through their respective SDKs.

---

## 6. QKD-Relevant Capabilities

### 6.1 Entanglement Generation and Verification

**Bell state preparation pattern:**
```python
@qml.qnode(dev)
def bell_state():
    qml.Hadamard(wires=0)
    qml.CNOT(wires=[0, 1])
    return qml.state()
```

**Entanglement verification:**
- Use `qml.probs(wires=[0,1])` to get joint probability distribution
- `qml.density_matrix(wires=[0])` to check reduced density matrix purity
- `qml.vn_entropy(wires=[0])` to compute entanglement entropy
- `qml.mutual_info(wires0=[0], wires1=[1])` for mutual information

**CHSH Bell test:**
```python
@qml.qnode(dev)
def chsh_circuit(theta_a, theta_b):
    # Create Bell state
    qml.Hadamard(wires=0)
    qml.CNOT(wires=[0, 1])
    # Measurement basis rotations (Alice)
    qml.RY(theta_a, wires=0)
    # Measurement basis rotations (Bob)
    qml.RY(theta_b, wires=1)
    return qml.expval(qml.Z(0) @ qml.Z(1))
```
Then evaluate at the 4 CHSH angle pairs and compute S = |E(a,b) + E(a,b') + E(a',b) - E(a',b')|.

### 6.2 Measurement in Various Bases

**Pauli measurement:**
```python
return qml.expval(qml.X(0))  # X basis
return qml.expval(qml.Y(0))  # Y basis
return qml.expval(qml.Z(0))  # Z basis
```

**Arbitrary basis via rotation:**
```python
def measure_in_basis(wire, theta, phi):
    """Measure in basis defined by spherical angles (theta, phi)."""
    qml.RY(theta, wires=wire)
    qml.RZ(phi, wires=wire)
    # Now measure in computational basis
```

**Separate measurements (Bell-state analyzers for QKD):**
```python
@qml.qnode(dev)
def qkd_measurement(alice_basis, bob_basis):
    # Alice encodes and measures
    qml.Hadamard(wires=0) if alice_basis == 'X' else qml.Identity(0)
    # ... entangling operation ...
    # Bob measures
    if bob_basis == 'X':
        return qml.probs(wires=1)
    else:
        return qml.probs(wires=0)  # etc.
```

### 6.3 Parameterized Rotation Gates for Basis Choice

**Key gates for basis selection:**
- `qml.RX(theta, wires)` -- rotate around X
- `qml.RY(theta, wires)` -- rotate around Y
- `qml.RZ(theta, wires)` -- rotate around Z
- `qml.Rot(phi, theta, omega, wires)` -- general Euler rotation

**Basis choice as training parameter (for ML-enhanced QKD):**
```python
@qml.qnode(dev, interface="torch")
def qkd_circuit(params, basis_angles):
    # params: encoding parameters
    # basis_angles: differentiable basis choices
    qml.RX(params[0], wires=0)
    qml.RY(basis_angles[0], wires=0)  # rotate measurement basis
    return qml.expval(qml.Z(0))
```

### 6.4 State Tomography

**Full state tomography:**
```python
@qml.qnode(dev)
def state_tomography():
    # ... state preparation ...
    return qml.state()  # full state vector
```

**Partial tomography via reduced density matrix:**
```python
@qml.qnode(dev)
def reduced_dm():
    # ... state preparation ...
    return qml.density_matrix(wires=[0, 1])  # 2-qubit subsystem
```

**Pauli tomography via expectation values:**
```python
@qml.qnode(dev)
def pauli_tomo(pauli_word):
    # ... state preparation ...
    obs = qml.pauli.string_to_pauli_word(pauli_word)  # e.g., "XYZ"
    return qml.expval(obs)
```

**Pauli decompositions:**
- `qml.pauli_decompose(H)` -- decompose matrix into Pauli basis
- `qml.pauli.PauliWord`, `qml.pauli.PauliSentence` -- Pauli word/sentence classes
- `qml.pauli.pauli_word_to_string`, `qml.pauli.string_to_pauli_word`
- `qml.pauli.group_observables` -- group commuting observables

### 6.5 QBER Calculation Patterns

**QBER from sifted key data:**
QBER computation is naturally done classically post-measurement, using `qml.sample()` or `qml.counts()`:

```python
@qml.qnode(dev, shots=10000)
def qber_circuit(alice_bit, alice_basis, bob_basis):
    # Alice encodes
    if alice_bit == 1:
        qml.PauliX(wires=0)
    # Alice chooses basis
    if alice_basis == 'X':
        qml.Hadamard(wires=0)
    # Send to Bob (via channel)
    # Bob measures in his basis
    if bob_basis == 'X':
        qml.Hadamard(wires=1)
    # Entangle or directly transmit
    qml.CNOT(wires=[0, 1])
    return qml.counts(wires=1)
```

**Key patterns for QBER:**
- Use `qml.counts(wires=...)` to get raw counts
- Use `qml.sample(wires=...)` to get raw samples
- Classical post-processing to compute error rate

### 6.6 ML-Enhanced QKD Capabilities

**Key rate prediction:**
QNodes are differentiable, enabling:
```python
@qml.qnode(dev, interface="torch", diff_method="parameter-shift")
def key_rate_predictor(params, channel_noise_params):
    # Simulate QKD protocol
    # params: protocol parameters (angles, intensities, etc.)
    # channel_noise_params: noise parameters
    # Returns key-rate-related observable
    return qml.expval(qml.Z(0) @ qml.Z(1))
```

**Optimization of protocol parameters:**
```python
dev = qml.device("default.mixed", wires=2)  # noise-capable device
@qml.qnode(dev, diff_method="parameter-shift")
def qkd_protocol(theta_alice, theta_bob, gamma):
    # Noise channel
    qml.AmplitudeDamping(gamma, wires=0)
    qml.AmplitudeDamping(gamma, wires=1)
    # Basis rotation angles to optimize
    qml.RY(theta_alice, wires=0)
    qml.RY(theta_bob, wires=1)
    return qml.expval(qml.Z(0) @ qml.Z(1))

opt = qml.AdamOptimizer(stepsize=0.1)
for step in range(100):
    theta_alice, theta_bob, gamma = ...  # differentiable params
    cost = qkd_protocol(theta_alice, theta_bob, gamma)
    # optimize to minimize QBER / maximize key rate
```

**Noise-aware optimization with DefaultMixed + NoiseModel:**
```python
nm = qml.NoiseModel({
    qml.noise.wires_in([0]): lambda op: qml.DepolarizingChannel(0.01, wires=op.wires),
    qml.noise.wires_in([1]): lambda op: qml.AmplitudeDamping(0.02, wires=op.wires),
})

@qml.qnode(dev, diff_method="parameter-shift")
def noisy_qkd(theta):
    qml.RY(theta, wires=0)
    qml.CNOT(wires=[0, 1])
    return qml.expval(qml.Z(0) @ qml.Z(1))

noisy_qkd = qml.noise.add_noise(noisy_qkd, noise_model=nm)
```

**Finite-size effects via shot-based simulation:**
```python
@qml.qnode(dev, shots=10000, diff_method="spsa")  # SPSA: hardware-compatible
def finite_size_qkd(theta):
    qml.RY(theta, wires=0)
    qml.CNOT(wires=[0, 1])
    return qml.sample(wires=qml.wires.Wires([0, 1]))
```
This enables studying statistical fluctuations and finite-size key rates.

---

## Key File Index

| Area | File Path |
|------|-----------|
| QNode | `E:/opensource/pennylane/pennylane/workflow/qnode.py` |
| Execute | `E:/opensource/pennylane/pennylane/workflow/execution.py` |
| Operator base | `E:/opensource/pennylane/pennylane/core/operator/base.py` |
| Device API | `E:/opensource/pennylane/pennylane/devices/device_api.py` |
| DefaultQubit | `E:/opensource/pennylane/pennylane/devices/default_qubit.py` |
| DefaultMixed | `E:/opensource/pennylane/pennylane/devices/default_mixed.py` |
| State simulation | `E:/opensource/pennylane/pennylane/devices/qubit/simulate.py` |
| Mixed simulation | `E:/opensource/pennylane/pennylane/devices/qubit_mixed/simulate.py` |
| Apply operation | `E:/opensource/pennylane/pennylane/devices/qubit/apply_operation.py` |
| QuantumScript | `E:/opensource/pennylane/pennylane/core/qscript.py` |
| Measurements | `E:/opensource/pennylane/pennylane/measurements/` |
| Gradients | `E:/opensource/pennylane/pennylane/gradients/` |
| Optimizers | `E:/opensource/pennylane/pennylane/optimize/` |
| QNN (TorchLayer) | `E:/opensource/pennylane/pennylane/qnn/torch.py` |
| Noise channels | `E:/opensource/pennylane/pennylane/ops/channel.py` |
| Noise model | `E:/opensource/pennylane/pennylane/noise/noise_model.py` |
| Noise add | `E:/opensource/pennylane/pennylane/noise/add_noise.py` |
| Noise mitigate | `E:/opensource/pennylane/pennylane/noise/mitigate.py` |
| Templates | `E:/opensource/pennylane/pennylane/templates/` |
| Embeddings | `E:/opensource/pennylane/pennylane/templates/embeddings/` |
| Layers | `E:/opensource/pennylane/pennylane/templates/layers/` |
| Subroutines | `E:/opensource/pennylane/pennylane/templates/subroutines/` |
| Op arithmetic | `E:/opensource/pennylane/pennylane/ops/op_math/` |
| Pauli utils | `E:/opensource/pennylane/pennylane/pauli/` |
| QChem | `E:/opensource/pennylane/pennylane/qchem/` |
| Mid-measure | `E:/opensource/pennylane/pennylane/ops/mid_measure/` |
| Drawer | `E:/opensource/pennylane/pennylane/drawer/` |
| Transforms | `E:/opensource/pennylane/pennylane/transforms/` |
| Decomposition | `E:/opensource/pennylane/pennylane/decomposition/` |
| Control flow | `E:/opensource/pennylane/pennylane/control_flow/` |

---

## Existing Integration Gaps

The current `pennylane_integration.py` only provides:
1. `qubit_to_pennylane()` -- wraps QKDpy Qubit state as PennyLane tensor
2. `pennylane_to_qubit()` -- extracts state back to QKDpy Qubit
3. `bb84_in_pennylane()` -- manual BB84 implementation using `qml.Hadamard` + `qml.CNOT` + `qml.RY`-based measurement

**Opportunities for enhancement:**
- Replace manual BB84 with template-based circuit construction
- Add noise model integration for realistic channel simulation
- Add entanglement-based protocol support (E91, MDI-QKD) using `qml.BellStatePreparation`-like patterns
- Integrate optimizers for protocol parameter tuning
- Add QBER computation as a measurement process
- Leverage `TorchLayer` for ML-enhanced QKD parameter optimization
- Use `DefaultMixed` with noise channels for realistic QKD channel models
- Add classical shadows for efficient state tomography
