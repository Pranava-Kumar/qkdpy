# QKDpy vs PennyLane: Quantum Logic Comparison

**Date:** 2026-07-14
**Scope:** qkdpy core quantum logic compared against PennyLane's hardware-verified implementations
**Method:** Static code analysis of qkdpy source vs PennyLane architecture audit

---

## Executive Summary

| Area | Discrepancy Level | Priority |
|------|-------------------|----------|
| 1. Differentiation & Gradients | MAJOR | HIGH |
| 2. Noise Channels | MODERATE/MAJOR | HIGH |
| 3. Measurement | MINOR | LOW |
| 4. Custom Noisy Channel | NONE (not implemented) | MEDIUM |
| 5. BB84/E91 Protocol Logic | MINOR | LOW |
| 6. QuantumInfo (Purity, Entropy) | MINOR | LOW |
| 7. Optimization | MAJOR | HIGH |
| 8. Entanglement Measures | MAJOR | HIGH |

---

## 1. Differentiation & Gradients

### What qkdpy does

**No gradient computation exists anywhere in qkdpy's protocol layer.** The `Qubit` class is a plain numpy implementation with no autodiff support. Protocols execute imperatively: `prepare_states()` -> `transmit_batch()` -> `measure_states()` -> `sift_keys()` -> `estimate_qber()` -- no parameters are tracked or differentiated.

qkdpy's ML module (`ml/qkd_optimizer.py`) uses classical black-box optimization:
- Bayesian optimization via sklearn `GaussianProcessRegressor` (line 136-137)
- Genetic algorithms with tournament selection (line 501-516)
- Neural network surrogate models (line 559-702) trained on historical simulation data

None of these interact with differentiable quantum circuits. They treat the protocol as an opaque objective function.

The PennyLane integration (`integrations/pennylane_integration.py`) creates QNodes but never sets `diff_method` or `interface`, making them non-differentiable:
- `create_bb84_circuit()` (line 344): `@qml.qnode(dev)` -- no diff_method
- `create_e91_circuit()` (line 268): `@qml.qnode(dev)` -- no diff_method

### What PennyLane validates

PennyLane supports 6+ differentiation methods (`param_shift`, `adjoint`, `backprop`, `finite-diff`, `spsa`, `hadamard`), 16 optimizers (`AdamOptimizer`, `QNGOptimizer`, `RotosolveOptimizer`, etc.), and 3 ML framework interfaces (`torch`, `jax`, `autograd`). QNodes with `diff_method="parameter-shift"` are hardware-compatible and differentiable.

Key audit reference: `pennylane/gradients/` directory with 8+ gradient transforms; `pennylane/optimize/` with 16+ optimizers; `pennylane/qnn/torch.py` for `TorchLayer`.

### Discrepancy Level: MAJOR

qkdpy has **no quantum circuit differentiation capability at all**. The existing `QKDOptimizer` class uses classical surrogate-model optimization that is disconnected from the quantum simulation.

### Recommendations

1. **HIGH** -- Enable differentiation in the PennyLane integration by adding `diff_method="parameter-shift"` and `interface="torch"` to existing QNodes, enabling gradient-based optimization of protocol parameters (e.g., basis rotation angles, noise thresholds).

2. **HIGH** -- Replace `QKDOptimizer._neural_network_optimization` (ml/qkd_optimizer.py:559-702) with PennyLane's `AdamOptimizer` or `RotosolveOptimizer` applied directly to differentiable E91/BB84 circuit parameters.

3. **MEDIUM** -- Wire `TorchLayer` (from `pennylane.qnn.TorchLayer`) to create end-to-end differentiable QKD protocol models that can be trained with PyTorch optimizers.

---

## 2. Noise Channels

### What qkdpy does

**File:** `src/qkdpy/core/channels.py`

#### Depolarizing Noise (lines 202-217)

```python
def _depolarizing_noise(self, qubit: Qubit) -> Qubit:
    if np.random.random() < self.noise_level:
        gate = random.choice([Identity, PauliX, PauliY, PauliZ])
        qubit.apply_gate(gate)
    return qubit
```

**Problem:** This implements the channel:
```
rho -> (1-p)*rho + p/4*(I*rho*I + X*rho*X + Y*rho*Y + Z*rho*Z)
     = (1-3p/4)*rho + p/4*(X*rho*X + Y*rho*Y + Z*rho*Z)
```

The standard depolarizing channel is:
```
rho -> (1-p)*rho + p/3*(X*rho*X + Y*rho*Y + Z*rho*Z)
```

qkdpy includes Identity in the random choice (1/4 probability each), which changes the effective error probability from `p` to `3p/4` and alters the noise distribution. This is a **systematic quantitative error**: the effective noise rate is 75% of the specified `noise_level`.

#### Amplitude Damping (lines 233-241)

```python
def _amplitude_damping_noise(self, qubit: Qubit) -> Qubit:
    if np.random.random() < self.noise_level:
        gamma = self.noise_level
        if qubit.probabilities[1] > 0 and np.random.random() < gamma:
            qubit._state = np.array([1, 0], dtype=complex)
    return qubit
```

**Problem -- MATHEMATICALLY WRONG.** The correct Kraus operators for amplitude damping are:
```
K0 = [[1, 0], [0, sqrt(1-gamma)]]
K1 = [[0, sqrt(gamma)], [0, 0]]
```

Effect on density matrix:
```
rho -> K0 * rho * K0^dag + K1 * rho * K1^dag
```

qkdpy's implementation collapses the entire state vector to `|0>` when the `|1>` amplitude is nonzero. This is incorrect for several reasons:
- A state `alpha|0> + beta|1>` should become `(alpha/sqrt(|alpha|^2 + |beta|^2*(1-gamma)))|0>` + `(beta*sqrt(1-gamma)/sqrt(...))|1>`, not `|0>`.
- The coherence between `|0>` and `|1>` is partially preserved (by factor `sqrt(1-gamma)`), but qkdpy destroys it entirely.
- For gamma=0.5, the correct behavior damps the `|1>` amplitude by `sqrt(0.5) ~ 0.707`; qkdpy sets it to zero.

#### Bit Flip / Phase Flip (lines 219-231)

These are correct for state-vector Monte Carlo sampling: apply X with probability `noise_level` (bit flip), apply Z with probability `noise_level` (phase flip).

#### Polarization Drift (lines 359-385)

Uses SO(2) rotation `[[cos(angle), -sin(angle)], [sin(angle), cos(angle)]]`. This IS a valid unitary (Ry(2*angle)), but the factor-of-2 between the SU(2) rotation angle and the Bloch sphere rotation is not accounted for. A drift angle `theta` on the Bloch sphere should correspond to `Ry(theta)` in SU(2), but qkdpy applies `Ry(2*theta)`, meaning the physical rotation is twice as large as the parameter suggests.

**Same issue** in `_apply_misalignment_errors` (lines 407-427).

### What PennyLane validates

**File:** `pennylane/ops/channel.py`

| Channel | Kraus Operators | Verification |
|---------|----------------|--------------|
| `DepolarizingChannel(p)` | `{sqrt(1-p)*I, sqrt(p/3)*X, sqrt(p/3)*Y, sqrt(p/3)*Z}` | Standard formula |
| `AmplitudeDamping(gamma)` | `{[1,0;0,sqrt(1-gamma)], [0,sqrt(gamma);0,0]}` | Standard formula |
| `BitFlip(p)` | `{sqrt(1-p)*I, sqrt(p)*X}` | Standard formula |
| `PhaseFlip(p)` | `{sqrt(1-p)*I, sqrt(p)*Z}` | Standard formula |
| `PhaseDamping(gamma)` | `{[1,0;0,sqrt(1-gamma)], [0,0;0,sqrt(gamma)]}` | Standard formula |
| `GeneralizedAmplitudeDamping(gamma, p)` | 4 Kraus operators | Thermal relaxation |
| `PauliError(px, py, pz)` | `{sqrt(1-px-py-pz)*I, sqrt(px)*X, sqrt(py)*Y, sqrt(pz)*Z}` | General Pauli |
| `QubitChannel(K_list)` | Arbitrary user-defined | Flexible |

PennyLane applies channels via density matrix evolution: `rho -> sum_k K_k * rho * K_k^dag`. This is mathematically exact. The `DefaultMixed` device (`pennylane/devices/default_mixed.py`) handles this natively.

### Discrepancy Level: MODERATE to MAJOR

1. **Amplitude Damping: MAJOR** -- The implementation is mathematically incorrect and does not match physically expected behavior.
2. **Depolarizing Channel: MODERATE** -- Quantitatively wrong (effective rate is 3p/4 instead of p), though qualitatively similar.
3. **SO(2)/SU(2) factor: MINOR** -- Valid unitaries, but physical angle interpretation is off by 2x.

### Concrete Fixes

#### Fix for Amplitude Damping (channels.py:233-241)

Replace the entire method with proper Kraus operator sampling:

```python
def _amplitude_damping_noise(self, qubit: Qubit) -> Qubit:
    gamma = self.noise_level
    if gamma <= 0:
        return qubit
    # Kraus operators for amplitude damping
    K0 = np.array([[1, 0], [0, np.sqrt(1 - gamma)]], dtype=complex)
    K1 = np.array([[0, np.sqrt(gamma)], [0, 0]], dtype=complex)
    # Apply to density matrix
    rho = qubit.density_matrix()
    rho_new = K0 @ rho @ K0.conj().T + K1 @ rho @ K1.conj().T
    # Convert back to state vector (sampling)
    if np.random.random() < np.trace(rho_new @ rho_new).real:  # probabilistic collapse
        # Pure state approximation: re-sample from density matrix
        eigvals, eigvecs = np.linalg.eigh(rho_new)
        probs = np.maximum(0, eigvals.real)
        probs = probs / probs.sum()
        idx = np.random.choice([0, 1], p=probs)
        qubit._state = eigvecs[:, idx]
    return qubit
```

Or better, switch the channel to operate on density matrices only.

#### Fix for Depolarizing (channels.py:202-217)

Remove Identity from the random choice and fix probability:

```python
def _depolarizing_noise(self, qubit: Qubit) -> Qubit:
    p = self.noise_level
    if p > 0 and np.random.random() < p:
        gate = random.choice([PauliX().matrix, PauliY().matrix, PauliZ().matrix])
        self.error_count += 1
        qubit.apply_gate(gate)
    return qubit
```

#### Fix for SO(2)/SU(2) angle (channels.py:376-382, 420-425)

Replace `[[cos(angle), -sin(angle)], [sin(angle), cos(angle)]]` with `Ry(angle)`:

```python
rotation_matrix = np.array([
    [np.cos(drift_angle), -np.sin(drift_angle)],
    [np.sin(drift_angle), np.cos(drift_angle)]
], dtype=complex)
```

This is already `Ry(2*drift_angle)`. To fix, change to:

```python
rotation_matrix = np.array([
    [np.cos(drift_angle / 2), -np.sin(drift_angle / 2)],
    [np.sin(drift_angle / 2), np.cos(drift_angle / 2)]
], dtype=complex)
```

---

## 3. Measurement

### What qkdpy does

**File:** `src/qkdpy/core/qubit.py` (lines 93-158)

`Qubit.measure()` returns a measurement result (0 or 1) by computing probabilities from the state vector and sampling. It does **not** collapse the qubit state -- `collapse_state()` is a separate method that must be called explicitly.

For Hadamard basis measurement (line 108-117): Creates a temporary qubit, applies `H`, measures computationally. The original qubit is unmodified.

For Circular basis measurement (line 119-128): Same approach using `(1/sqrt(2))[[1, -i], [1, i]]` -- which is `H*S^dag`, correctly mapping circular basis states `{|L>, |R>}` to computational basis `{|0>, |1>}`.

`collapse_state()` for circular basis (line 152-156): Collapses to `|L> = (|0> + i|1>)/sqrt(2)` or `|R> = (|0> - i|1>)/sqrt(2)`. Correct.

**File:** `src/qkdpy/core/measurements.py`

`quantum_state_tomography()` (line 254-328): Uses sequential measurement with state reset between each measurement. Reconstructs density matrix via `rho = (I + <X>X + <Y>Y + <Z>Z)/2`. This formula is **correct** for single-qubit tomography.

### What PennyLane validates

PennyLane provides first-class measurement processes:
- `qml.expval(obs)` -- expectation value (analytic)
- `qml.probs(wires)` -- probability distribution
- `qml.sample(wires)` -- shot-based sampling
- `qml.state()` -- full state vector
- `qml.density_matrix(wires)` -- reduced density matrix
- `qml.measure(wires)` -- mid-circuit measurement

Mid-circuit measurements support 3 execution strategies: `deferred`, `one-shot`, `tree-traversal`. Post-measurement state is handled automatically based on the strategy.

### Discrepancy Level: MINOR

qkdpy's measurement is functionally correct. Key differences:
1. qkdpy separates measurement and collapse into two calls; PennyLane handles collapse automatically.
2. qkdpy lacks native expectation value computation (`expval`), which is not needed for current protocols but would be useful for optimization.
3. Tomography reconstruction formula is correct for pure and mixed states.

### Recommendations

1. **LOW** -- Add `expectation_value()` method to `Qubit` class for convenience (even though `measure_observable()` exists in measurements.py).

---

## 4. Custom Noisy Channel (pennylane_qkd_channel)

### What qkdpy does

**No `pennylane_qkd_channel()` function exists in the codebase.** A grep for `pennylane_qkd_channel` and `qkd_channel` returned no results.

The closest functionality is `convert_channel_to_pennylane()` in `pennylane_integration.py` (lines 425-450), which converts a qkdpy `QuantumChannel` to a flat dictionary of noise parameters -- it does not create actual PennyLane channel operations.

### What PennyLane validates

PennyLane's `QubitChannel(K_list)` accepts arbitrary Kraus operators, and `DefaultMixed` applies them to density matrices. The `NoiseModel` class (`pennylane/noise/noise_model.py`) provides conditional noise insertion with gate-level granularity:
```python
NoiseModel({BooleanFn: noise_fn}, meas_map={BooleanFn: noise_fn})
```

### Discrepancy Level: NONE (feature not implemented)

The conversion layer from qkdpy's channel model to PennyLane's noise model does not exist.

### Recommendations

1. **MEDIUM** -- Implement `pennylane_qkd_channel()` that converts qkdpy's physical channel parameters (loss, polarization drift, phase fluctuations, thermal noise, misalignment) into equivalent PennyLane operations. Each qkdpy noise type maps to a PennyLane channel:
   - `polarization_drift` -> `qml.RY(angle, wires=w)` or use `NoiseModel` with conditional rotations
   - `phase_fluctuations` -> `qml.PhaseDamping(gamma, wires=w)`
   - `misalignment_error` -> `qml.DepolarizingChannel(p, wires=w)` with small p
   - `thermal_noise` -> `qml.GeneralizedAmplitudeDamping(gamma, p, wires=w)`

2. **MEDIUM** -- Build `qkdpy_noise_model(quantum_channel)` returning a `qml.NoiseModel` object, enabling realistic QKD channel simulation inside PennyLane circuits.

---

## 5. BB84 / E91 Protocol Implementations

### BB84

**File:** `src/qkdpy/protocols/bb84.py`

| Aspect | qkdpy | PennyLane Equivalent | Correctness |
|--------|-------|---------------------|-------------|
| State prep | `Qubit.zero()/one()/plus()/minus()` | `qml.PauliX` + `qml.Hadamard` | Both correct |
| Basis choice | `secure_choice(["computational", "hadamard"])` | `np.random.choice(["Z", "X"])` | Equivalent |
| Measurement | `Measurement.measure_in_basis(q, basis)` | `qml.measure(wire)` | Equivalent |
| Sifting | Compare basis lists | Classical post-processing | Both correct |
| QBER | `errors / len(sifted_key)` | Classical post-processing | Correct |
| CSPRNG | `secure_random`, `secure_choice` | `np.random` | qkdpy stronger |

**Known simplification:** QBER estimation (line 169) uses the entire sifted key rather than a random subset. In real QKD, only a sample is disclosed for parameter estimation. This affects simulated key lengths but not correctness.

**Issue:** `num_qubits = key_length * 5` (line 40) is a fixed multiplier that doesn't account for channel loss. Under high loss, the final key may be shorter than requested.

### E91

**File:** `src/qkdpy/protocols/e91.py`

| Aspect | qkdpy | PennyLane Equivalent | Correctness |
|--------|-------|---------------------|-------------|
| Bell state | `MultiQubitState.ghz(2)` = `(|00> + |11>)/sqrt(2)` | `qml.Hadamard(0)` + `qml.CNOT([0,1])` | Both correct |
| Alice rotation | `Ry(-angle_a)` on qubit 0 | `qml.RY(angle, wires=0)` | Conventions differ; both valid |
| Bob rotation | `Ry(-angle_b)` on qubit 1 | `qml.RY(angle, wires=1)` | Same |
| CHSH angles | Alice: {0, pi/4, pi/2}; Bob: {pi/4, pi/2, 3pi/4} | Same (standard) | Correct |
| Sequential meas. | Alice measures, then Bob measures collapsed state | Simultaneous | Equivalent (measurements commute) |
| CHSH formula | S = E(A1,B1) - E(A1,B3) + E(A3,B1) + E(A3,B3) | Same | Correct |
| Max CHSH value | 2*sqrt(2) ~ 2.828 | 2*sqrt(2) | Correct |

**Design issue:** `prepare_states()` (line 62-68) returns `[Qubit.zero()]` dummy placeholders. The actual Bell state creation happens in `measure_states()` which ignores its input. This violates the `BaseProtocol` contract where `prepare_states()` outputs go through the channel, then into `measure_states()`.

**Subtle simulation concern:** In `measure_states()` (line 88-136), noise is applied directly to the Bell pair (line 98-110), but the channel's `noise_model` is used independently of the `quantum_channel`'s `transmit()` method. The `QuantumChannel.transmit()` is never called in E91 -- noise is simulated manually. This means channel-level effects (loss, polarization drift, phase fluctuations) are bypassed.

### Discrepancy Level: MINOR

The quantum logic of both protocols is mathematically correct. The E91 has design issues that affect simulation fidelity:
1. **E91 line 62-68**: `prepare_states()` returns dummy qubits, violating the protocol abstraction.
2. **E91 line 96-110**: Channel noise is simulated manually instead of going through `QuantumChannel.transmit()`.

### Recommendations

1. **LOW** -- Fix E91's `prepare_states()` to return actual Bell states and use `QuantumChannel.transmit()` for consistency with `BaseProtocol.execute()`.

2. **LOW** -- Implement E91 using PennyLane's native entanglement (`qml.Hadamard` + `qml.CNOT`) via the integration layer.

---

## 6. QuantumInfo (Purity, von Neumann Entropy, Fidelity)

### What qkdpy does

**File:** `src/qkdpy/core/measurements.py`

| Function | Formula | Correctness |
|----------|---------|-------------|
| `measure_purity()` (line 160) | `Tr(rho^2)` via `Qubit.density_matrix()` | Correct, but always 1.0 for Qubit objects (pure states) |
| `measure_vn_entropy()` (line 174) | `-sum(lambda * log2(lambda))` via `eigvalsh(rho)` | Correct, but always 0.0 for Qubit objects |
| `measure_state_fidelity()` (line 117) | `|<psi|phi>|^2` | Correct for pure states |
| `measure_observable()` (line 196) | `Tr(rho * O)` | Correct for Hermitian observables |
| `density_matrix()` (qubit.py:160) | `|psi><psi|` | Correct |

**Key limitation:** All these functions operate on `Qubit` objects, which are always pure states. The density matrix is reconstructed from the state vector via `np.outer(state, conj(state))`, which is correct for pure states but will never represent mixed states. Since the `Qubit` class does not support mixed states natively:
- `measure_purity()` will always return 1.0
- `measure_vn_entropy()` will always return 0.0
- These functions are essentially meaningless for noise analysis

**File:** `src/qkdpy/core/security_analysis.py`

`_calculate_corrected_key_rate()` (line 112-157): Uses the binary entropy function `h2(x) = -x*log2(x) - (1-x)*log2(1-x)` (line 127-128). Formula is correct.

### What PennyLane validates

PennyLane's `qml.math` module provides:
- `qml.math.purity(dm, indices)` -- works on density matrices with subsystem support
- `qml.math.vn_entropy(dm, indices)` -- works on density matrices with subsystem support
- `qml.math.fidelity(dm1, dm2)` -- works on both pure and mixed states
- `qml.math.trace_distance(dm1, dm2)` -- trace distance

These are implemented in the `DefaultMixed` device path (`pennylane/devices/qubit_mixed/`) and support arbitrary mixed states.

### Discrepancy Level: MINOR

The formulas are mathematically correct but qkdpy's API limits them to pure-state Qubit objects, making purity and entropy non-informative.

### Recommendations

1. **LOW** -- Add a `MixedState` class (or density-matrix-based Qubit variant) that allows purity < 1 and non-zero entropy, enabling meaningful noise analysis.

2. **LOW** -- The `SecurityAnalyzer._calculate_corrected_key_rate()` binary entropy function is correct and well-implemented.

---

## 7. Optimization

### What qkdpy does

**Directory:** `src/qkdpy/ml/`

qkdpy has a complete classical ML pipeline for protocol parameter optimization:

| Module | What it does | Limitation |
|--------|-------------|------------|
| `QKDOptimizer` (qkd_optimizer.py) | Bayesian optimization (GP), genetic algorithms, NN surrogate | Treats protocol as black box; no quantum gradient awareness |
| `EfficientQKDPredictor` (efficient_models.py) | Hand-rolled neural network for key rate prediction | Trained on historical data only; disconnected from quantum simulation |
| `AdaptiveModelSelector` (model_selector.py) | Chooses model architecture based on available memory | Resource management only |
| `KnowledgeDistillation` (knowledge_distillation.py) | Teacher-student model compression | Classical ML technique |

These are all **classical surrogate-based optimization** approaches. They are disconnected from the quantum circuit simulation -- they optimize protocol parameters (channel loss, noise level, mean photon number) by fitting a surrogate model to historical simulation data, then optimizing the surrogate. The quantum simulation itself is never differentiated through.

### What PennyLane validates

PennyLane provides **differentiable quantum circuits** that enable end-to-end optimization:
- 16 optimizers including `AdamOptimizer`, `QNGOptimizer`, `RotosolveOptimizer`, `SPSAOptimizer`
- 6 differentiation methods including hardware-compatible `parameter-shift`
- `TorchLayer` wraps QNodes as `torch.nn.Module` for integration with PyTorch's optimizer ecosystem
- Multi-framework support (Torch, JAX, Autograd)

**Key pattern for QKD optimization** (from audit):
```python
dev = qml.device("default.mixed", wires=2)
@qml.qnode(dev, diff_method="parameter-shift")
def qkd_protocol(theta_alice, theta_bob, gamma):
    qml.AmplitudeDamping(gamma, wires=0)
    qml.RY(theta_alice, wires=0)
    qml.RY(theta_bob, wires=1)
    return qml.expval(qml.Z(0) @ qml.Z(1))

opt = qml.AdamOptimizer(stepsize=0.1)
for step in range(100):
    theta_a, theta_b, gamma = params
    cost = qkd_protocol(theta_a, theta_b, gamma)
    params = opt.step(lambda p: qkd_protocol(*p), params)
```

### Discrepancy Level: MAJOR

qkdpy's ML approach is architecturally disconnected from quantum circuit differentiation. The gap is not in the classical ML code (which is well-written) but in the missing bridge between differentiable quantum simulation and protocol parameter optimization.

### Recommendations

1. **HIGH** -- Replace `QKDOptimizer._neural_network_optimization` (lines 559-702) with PennyLane-based differentiable circuit optimization. The hand-rolled neural network (lines 704-789) is redundant when PennyLane provides verified gradient computation.

2. **HIGH** -- Implement a `DifferentiableQKDProtocol` wrapper that exposes protocol parameters (basis angles, noise levels) as differentiable QNode parameters using `diff_method="parameter-shift"`.

3. **MEDIUM** -- Integrate `TorchLayer` to enable PyTorch-based training pipelines for QKD parameter optimization, replacing the sklearn-based `_bayesian_optimization` (lines 71-213).

4. **LOW** -- The `EfficientQKDPredictor` (efficient_models.py) and `KnowledgeDistillation` module are well-designed for deployment-side inference but should be separated from protocol optimization logic.

---

## 8. Entanglement Measures

### What qkdpy does

**File:** `src/qkdpy/core/multiqubit.py`

#### `entanglement_entropy()` (lines 320-339)

```python
def entanglement_entropy(self, subsystem_qubits: list[int]) -> float:
    # This is a complex calculation that would require partial trace computation
    # For now, we'll return a placeholder
    return 0.0
```

**Not implemented.** Returns 0.0 unconditionally. This is a documented placeholder.

#### `fidelity()` (lines 341-358)

`F = |<psi|phi>|^2` -- correct for pure state vectors.

#### `measure_bell_state()` (measurements.py:218-252)

Computes fidelity against 4 Bell states and returns the label with highest fidelity. Correct comparison logic but returns a string, not a quantitative measure.

#### `test_bell_inequality()` (e91.py:177-239)

Full CHSH calculation with S-value:
- `S = E(A1,B1) - E(A1,B3) + E(A3,B1) + E(A3,B3)` (line 232)
- Correlation computed as `E = 2*P(match) - 1` (line 223)
- QBER estimated as `0.5 * (1 - S / (2*sqrt(2)))` (line 237)

All mathematically correct. For an ideal Bell state, S=2.828, QBER=0.

### What PennyLane validates

PennyLane provides first-class entanglement computations:

| Function | Description |
|----------|-------------|
| `qml.math.vn_entanglement_entropy(dm, indices0, indices1)` | Full entanglement entropy via partial trace |
| `qml.mutual_info(wires0, wires1)` | Mutual information between subsystems |
| `qml.math.purity(dm, indices)` | Subsystem purity for entanglement detection |
| `qml.density_matrix(wires)` | Reduced density matrix computation |

All are verified in `DefaultMixed` and `DefaultQubit` devices.

### Discrepancy Level: MAJOR for entropy, MINOR for bell test

`entanglement_entropy()` is a documented no-op returning 0.0. The CHSH test in E91 is correct. `measure_bell_state()` is correct but limited.

### Concrete Fix

#### Fix for `entanglement_entropy()` (multiqubit.py:320-339)

Replace the placeholder with a proper implementation:

```python
def entanglement_entropy(self, subsystem_qubits: list[int]) -> float:
    if not subsystem_qubits or any(
        q < 0 or q >= self._num_qubits for q in subsystem_qubits
    ):
        raise ValueError("Invalid subsystem qubit indices")

    # Compute reduced density matrix via partial trace
    # Identify qubits NOT in the subsystem (traced out)
    all_qubits = set(range(self._num_qubits))
    subsystem_set = set(subsystem_qubits)
    traced_qubits = sorted(all_qubits - subsystem_set)

    if not traced_qubits:
        # Subsystem is the full system; entropy = 0 for pure state
        return 0.0

    # Compute reduced density matrix via partial trace
    rho = self.density_matrix()  # 2^n x 2^n
    dim = 2 ** len(traced_qubits)
    sub_dim = 2 ** len(subsystem_qubits)

    rho_reduced = np.zeros((sub_dim, sub_dim), dtype=complex)

    # Sum over traced-out basis states
    for i in range(dim):
        for j in range(dim):
            # Build the full index from traced and subsystem indices
            # This is a simplified implementation; real code needs
            # careful index mapping
            rho_reduced += ...  # partial trace summation

    # Von Neumann entropy of reduced density matrix
    eigenvalues = np.linalg.eigvalsh(rho_reduced)
    eigenvalues = eigenvalues[eigenvalues > 1e-10]
    entropy = -np.sum(eigenvalues * np.log2(eigenvalues))

    return float(entropy)
```

Better yet, use the PennyLane integration:

```python
def entanglement_entropy(self, subsystem_qubits: list[int]) -> float:
    from ..integrations.pennylane_integration import PennyLaneIntegration
    pl = PennyLaneIntegration()
    return pl.compute_vn_entropy(self._state, indices=subsystem_qubits)
```

---

## Cross-Cutting Findings

### Finding A: State-Vector-Only Architecture

The entire qkdpy core (`Qubit`, `MultiQubitState`) operates on pure state vectors only. There is no density-matrix-based state representation. This means:
- All noise channels must use Monte Carlo sampling (stochastic gate application) rather than Kraus operator evolution
- Purity and entropy are always trivial (1.0 and 0.0)
- Mixed-state analysis is impossible without running many statistical trials

**Impact:** HIGH. The architecture fundamentally limits noise simulation fidelity.

**PennyLane comparison:** PennyLane's `DefaultMixed` device operates on density matrices natively, enabling exact Kraus operator evolution and mixed-state analysis.

### Finding B: E91 Bypasses QuantumChannel

`E91.measure_states()` (e91.py:88-136) directly applies noise to Bell pairs without calling `QuantumChannel.transmit()`. This means channel-level effects (polarization drift, phase fluctuations, misalignment, thermal noise, loss) are completely bypassed in E91 simulation. Only depolarizing noise is applied manually.

**Impact:** MODERATE. E91 simulations do not reflect realistic channel conditions.

**File reference:** `e91.py` line 96-110 vs `QuantumChannel.transmit()` at `channels.py` line 114-177.

### Finding C: No `pennylane_qkd_channel()` Exists

The function described in the comparison prompt does not exist in the codebase. The integration file (`pennylane_integration.py`) has `convert_channel_to_pennylane()` (line 425) which creates a flat dict, not a PennyLane channel.

### Finding D: SO(2) vs SU(2) in Rotation Matrices

`channels.py` uses real SO(2) rotation matrices in `_apply_polarization_drift` (line 376-382) and `_apply_misalignment_errors` (line 420-425). While these are valid unitary matrices (Ry(2*angle)), the factor-of-2 discrepancy means the effective rotation on the Bloch sphere is twice the parameter value. This is a quantitative, not qualitative, error.

---

## Summary of Priorities

| Priority | Area | Issue | File:Line |
|----------|------|-------|-----------|
| HIGH | Noise: Amplitude Damping | Mathematically wrong Kraus operator | `channels.py:233-241` |
| HIGH | Noise: Depolarizing | Includes Identity in Pauli choice; effective rate = 3p/4 | `channels.py:202-217` |
| HIGH | Differentiation | No quantum gradient capability; PennyLane QNodes lack diff_method | `pennylane_integration.py:344,268` |
| HIGH | Optimization | Classical ML disconnected from differentiable circuits | `ml/qkd_optimizer.py:559-702` |
| HIGH | Entanglement entropy | Placeholder returning 0.0 | `multiqubit.py:320-339` |
| MEDIUM | Noise: SO(2) vs SU(2) | Bloch sphere rotation angle off by 2x | `channels.py:376-382,420-425` |
| MEDIUM | Custom PL channel | `pennylane_qkd_channel()` does not exist | `pennylane_integration.py:425-450` |
| MEDIUM | E91 bypasses channel | Noise applied directly, not via QuantumChannel | `e91.py:96-110` |
| LOW | Purity/Entropy on Qubit | Always returns trivial values due to pure-state-only API | `measurements.py:160-193` |
| LOW | E91 prepare_states | Returns dummy qubits | `e91.py:62-68` |
| LOW | BB84 QBER sample | Uses full sifted key, not a random subset | `bb84.py:169` |

---

## File Index

| File | Purpose |
|------|---------|
| `E:/opensource/qkdpy/src/qkdpy/core/qubit.py` | Qubit class: state, gates, measurement, collapse |
| `E:/opensource/qkdpy/src/qkdpy/core/channels.py` | QuantumChannel: noise models, transmission, eavesdropping |
| `E:/opensource/qkdpy/src/qkdpy/core/measurements.py` | Measurement: bases, tomography, purity, entropy |
| `E:/opensource/qkdpy/src/qkdpy/core/gates.py` | Gate definitions: Pauli, Hadamard, rotation, CNOT |
| `E:/opensource/qkdpy/src/qkdpy/core/gate_utils.py` | Gate utilities: unitarity checks, basis switches |
| `E:/opensource/qkdpy/src/qkdpy/core/multiqubit.py` | MultiQubitState: tensor products, GHZ, W, entanglement |
| `E:/opensource/qkdpy/src/qkdpy/protocols/bb84.py` | BB84 protocol implementation |
| `E:/opensource/qkdpy/src/qkdpy/protocols/e91.py` | E91 protocol implementation with CHSH |
| `E:/opensource/qkdpy/src/qkdpy/protocols/base.py` | BaseProtocol: execute pipeline, error correction, PA |
| `E:/opensource/qkdpy/src/qkdpy/core/security_analysis.py` | Security analysis: QBER trends, attack simulation |
| `E:/opensource/qkdpy/src/qkdpy/integrations/pennylane_integration.py` | PennyLane integration: conversion, BB84/E91 circuits |
| `E:/opensource/qkdpy/src/qkdpy/ml/qkd_optimizer.py` | QKD optimizer: Bayesian, genetic, NN methods |
| `E:/opensource/qkdpy/src/qkdpy/ml/efficient_models.py` | Efficient NN predictor for resource-constrained devices |
| `E:/opensource/qkdpy/audit_pennylane.md` | PennyLane architecture audit document |
