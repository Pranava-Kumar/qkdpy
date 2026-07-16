# QKDPY Enhancement Plan

Based on deep architectural audits of **Qiskit** (826 lines), **PennyLane** (793 lines), and **QpiAI Quantum SDK** (702 lines).

---

## Audits Completed

| Framework | File | Size | Coverage |
|-----------|------|------|----------|
| Qiskit 1.x | `audit_qiskit.md` | 826 lines | Core arch, quantum_info, synthesis, noise, measurement patterns |
| PennyLane | `audit_pennylane.md` | 793 lines | QNode pipeline, ops, optimization/ML, noise models, QKD patterns |
| QpiAI Quantum SDK | `audit_qpiai.md` | 702 lines | Circuit system, quantum_info, formalism, algorithms, cloud execution |

---

## Current State of qkdpy Integrations

### Qiskit (`qkdpy/integrations/qiskit_integration.py`)
- `QiskitIntegration` class wrapping `Statevector`, `QuantumCircuit`
- `qubit_to_qiskit()` / `qiskit_to_qubit()` conversion between QKDpy `Qubit` and `Statevector`
- `create_bb84_circuit()` — BB84 encode+measure circuits
- `simulate()` — runs `AerSimulator` (requires qiskit-aer)
- `convert_channel_to_qiskit()` — bridges `QuantumChannel` loss into `amplitude_damping_error`
- Real entanglement measures via `quantum_info` (`concurrence`, `negativity`, `partial_trace`, `schmidt`)

**Noise modeling & transpilation — SUPPORTED:** `simulate()` accepts a `noise_model` parameter (`bit_flip` / `phase_flip` / `depolarizing`) and builds a `NoiseModel`; circuits are run through `qiskit.compiler.transpile` before execution on the noisy `AerSimulator`. (Earlier plan notes claiming "no noise modeling, no transpilation" are stale and incorrect.)

**Remaining Gaps (verified against code):** no Pauli/Clifford utility helpers, no circuit-synthesis layer, no primitive-based (`Estimator`/`Sampler`) execution path, no mid-circuit measurement.

### Cirq (`qkdpy/integrations/cirq_integration.py`)
- `CirqIntegration` class
- `qubit_to_cirq()` / `cirq_to_qubit()` conversion
- `create_bb84_circuit()` — limited to simple H + CNOT per qubit
- `simulate_bb84_with_cirq()` — runs Cirq simulator with noise
- `create_entanglement_circuit()` — Bell pair generation
- `benchmark_qkdpy_vs_cirq()` — performance comparison

**Gaps:** No custom noise model beyond default, no channel simulation, no E91 protocol, no MEAS/Prepare circuits, no qudit support, no serialization.

### PennyLane (`qkdpy/integrations/pennylane_integration.py`)
- `PennyLaneIntegration` class
- `qubit_to_pennylane()` / `pennylane_to_qubit()` conversion
- `bb84_in_pennylane()` — manual BB84 using `qml.Hadamard` + `qml.CNOT`
- `simulate_with_pennylane()` — runs simplex noise options
- `pennylane_qkd_channel()` — adds depolarizing / amplitude damping noise
- `create_entanglement_circuit()` — basic Bell pair creation
- `benchmark_qkdpy_vs_pennylane()` — performance comparison

**Gaps:** No `DefaultMixed` with full noise channels, no `NoiseModel` transform, no QNode-based protocol, no ML pipeline integration (`TorchLayer`), no optimizers, no CHSH test for DI-QKD.

### QpiAI Quantum SDK
- **No integration exists.** This would be entirely new.

---

## Enhancement Opportunities

### 1. Qiskit Integration — High Impact

| # | Enhancement | Source | Effort | Benefit |
|---|-------------|--------|--------|---------|
| 1.1 | Add Kraus-based noise simulation (`AmplitudeDamping`, `PhaseDamping`, `Depolarizing`) | `qiskit.quantum_info.Kraus` | Low | Realistic channel loss simulation in base Qiskit |
| 1.2 | Add entanglement measures (`concurrence`, `entanglement_of_formation`, `negativity`) | `qiskit.quantum_info.states.measures` | Low | DI-QKD security verification |
| 1.3 | Add `partial_trace` and `schmidt_decomposition` | `qiskit.quantum_info.states.utils` | Low | Entanglement verification |
| 1.4 | Add `StabilizerState`-based efficient Cliffords for entanglement swapping | `qiskit.quantum_info.StabilizerState` | Medium | Fast simulation of large swapping networks |
| 1.5 | Add `Statevector.from_label()` for BB84 state prep (more efficient) | `qiskit.quantum_info.Statevector` | Low | Cleaner BB84 encoding |
| 1.6 | Add `GenericBackendV2` for realistic device noise profiles | `qiskit.providers.fake_provider` | Medium | Hardware-realistic QKD simulation |
| 1.7 | Add transpilation pipeline integration for circuit optimization | `qiskit.compiler.transpile` | Medium | Gate count reduction, basis translation |
| 1.8 | Add `PauliLindbladMap` for noise learning / Pauli twirling | `qiskit.quantum_info.PauliLindbladMap` | Medium | Advanced noise characterization |
| 1.9 | Add mid-circuit measurement + conditional ops for active QKD | `qiskit.circuit.IfElseOp`, `.if_test()` | Medium | Active basis reconciliation |
| 1.10 | Add `StatevectorSampler` primitive-based execution (V2 API) | `qiskit.primitives.StatevectorSampler` | Low | Modern Qiskit execution pattern |

### 2. PennyLane Integration — High Impact

| # | Enhancement | Source | Effort | Benefit |
|---|-------------|--------|--------|---------|
| 2.1 | Add `DefaultMixed` device with full noise channel simulation | `pennylane.devices.DefaultMixed` | Medium | The most realistic QKD noise simulation available |
| 2.2 | Add `NoiseModel` transform integration (`add_noise`) | `pennylane.noise.NoiseModel` | Medium | Flexible gate-level noise insertion |
| 2.3 | Add QNode-based protocol definitions (BB84, E91 as QNodes) | `pennylane.QNode` | Medium | Differentiable protocols with gradient support |
| 2.4 | Add CHSH Bell test for DI-QKD verification | `qml.expval(qml.Z(0) @ qml.Z(1))` | Low | Bell inequality violation measurement |
| 2.5 | Add `TorchLayer` ML-enhanced QKD optimization pipeline | `pennylane.qnn.TorchLayer` | High | Full hybrid quantum-classical optimization |
| 2.6 | Add entanglement measures (`vn_entropy`, `mutual_info`, `purity`) | `qml.vn_entropy()`, `qml.mutual_info()` | Low | Built-in entanglement verification |
| 2.7 | Add optimizer integration (`AdamOptimizer`, `QNGOptimizer`) for protocol tuning | `pennylane.optimize` | Medium | Automatic parameter optimization |
| 2.8 | Add template-based circuit construction (`StronglyEntanglingLayers`) | `pennylane.templates.layers` | Low | ML-enhanced QKD circuit design |
| 2.9 | Add `qml.qinfo` integration (fidelity, trace distance, entropy) | `pennylane.qinfo` | Low | Advanced quantum information measures |
| 2.10 | Add classical shadows for efficient tomography | `qml.classical_shadow()` | Medium | Efficient state characterization |

### 3. QpiAI Quantum SDK — New Integration

| # | Enhancement | Source | Effort | Benefit |
|---|-------------|--------|--------|---------|
| 3.1 | Create `QpiAIIntegration` class | New file | Medium | Bridge QKDpy protocols to QpiAI hardware |
| 3.2 | Add `Circuit`-based state preparation (BB84 states via H/RX) | `qpiai_quantum.Circuit` | Low | Protocol execution on QpiAI |
| 3.3 | Add Bell/GHZ state generation using built-in generators | `qpiai_quantum.state_preparation` | Low | Entanglement-based protocols |
| 3.4 | Add `formalism.DensityMatrix` noise simulation (ADC, depolarizing via Kraus) | `qpiai_quantum.formalism.DensityMatrix` | Medium | Realistic noise on QpiAI circuits |
| 3.5 | Add entanglement verification (concurrence, EOF, Schmidt rank) | `formalism.DensityMatrix` methods | Low | Security verification |
| 3.6 | Add cloud execution via `JobManager` | `qpiai_quantum.jobmanager` | Medium | Actual quantum hardware runs |
| 3.7 | Add QRNG-based key generation | `qpiai_quantum.algorithms.QRNG` | Medium | True random key material |
| 3.8 | Add CHSH Bell value computation for DI-QKD | `formalism.DensityMatrix` | Low | Device-independent verification |
| 3.9 | Add OpenQASM 2.0 export for circuit interoperability | `qpiai_quantum.iem.qasm` | Low | Cross-platform circuit sharing |
| 3.10 | Add QKD-specific algorithm templates | New file | High | High-level QKD workflow abstraction |

### 4. Existing Integration Deepening

| # | Enhancement | Framework | Effort | Benefit |
|---|-------------|-----------|--------|---------|
| 4.1 | Add QKD protocol simulation function (BB84, E91, DI-QKD as circuits) | All three | Medium | One-call protocol simulation |
| 4.2 | Add channel-to-noise-model converter | All three | Medium | Use QKDpy `QuantumChannel` params to configure framework noise |
| 4.3 | Add key sifting as classical post-processing | All three | Low | Complete QKD workflow |
| 4.4 | Add error correction integration (Cascade, LDPC) | All three | Medium | Post-processing pipeline |
| 4.5 | Add privacy amplification | All three | Low | Final key generation |
| 4.6 | Add benchmarking framework across all frameworks | All three | Medium | Compare performance/fidelity |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                       qkdpy                                         │
├─────────────────────────────────────────────────────────────────────┤
│  Protocols     │  Core       │  ML            │  Network            │
│  BB84  E91     │  Qubit      │  Optimizer     │  QuantumNetwork     │
│  CV-QKD DI-QKD │  Channel    │  Predictor     │  SatelliteQKD       │
│  HD-QKD SARG04 │  Detector   │  Distillation  │  MultiPartyQKD      │
│  Decoy B92     │  MultiQubit │                │  EntanglementSwap   │
├────────────────┴─────────────┴────────────────┴─────────────────────┤
│                     Integration Layer                               │
├──────────────┬──────────────┬──────────────┬────────────────────────┤
│  Qiskit      │  Cirq        │  PennyLane   │  QpiAI (new)          │
│  Integration │  Integration │  Integration │  Integration          │
│  (enhanced)  │  (enhanced)  │  (enhanced)  │  (new)                │
├──────────────┴──────────────┴──────────────┴────────────────────────┤
│  Quantum Frameworks                                                  │
│  Qiskit 1.x  │  Cirq 1.x   │  PennyLane    │  QpiAI Quantum SDK    │
│  (locally)   │  (installed) │  (installed)  │  (locally)            │
└─────────────────────────────────────────────────────────────────────┘
```

## Priority Recommendations

### Tier 1 (Highest Impact, Lowest Effort — Do First)
1. **Qiskit 1.2, 1.3, 1.5** — Add `concurrence`, `partial_trace`, `state_fidelity` from `qiskit.quantum_info.states.measures`
2. **PennyLane 2.6, 2.9** — Add `vn_entropy`, `mutual_info`, `qml.qinfo` measures
3. **QpiAI 3.2, 3.3** — Create basic `QpiAIIntegration` with circuit conversion and Bell state generation

### Tier 2 (High Impact, Medium Effort — Do Next)
4. **Qiskit 1.1, 1.6** — Add Kraus-based noise + `GenericBackendV2` integration
5. **PennyLane 2.1, 2.3** — Add `DefaultMixed` device with QNode-based protocol definitions
6. **QpiAI 3.4, 3.5** — Add `formalism.DensityMatrix` noise simulation and entanglement verification

### Tier 3 (Enables Advanced Features)
7. **PennyLane 2.5** — `TorchLayer` ML-enhanced QKD pipeline
8. **QpiAI 3.6, 3.7** — Cloud execution + QRNG key generation
9. **Channel-to-NoiseModel converter(4.2)** — Bridge between QKDpy channels and all frameworks
10. **Complete QKD workflow(4.3-4.5)** — Sifting + error correction + privacy amplification

## Implementation Guide

### Adding New Framework Integration (QpiAI)
Pattern to follow (from existing integrations):

```python
# qkdpy/integrations/qpiai_integration.py
class QpiAIIntegration:
    def __init__(self):
        from qpiai_quantum import Circuit, Backend
        self.Circuit = Circuit

    def qubit_to_qpiai(self, qkdpy_qubit):
        """Convert QKDpy Qubit to QpiAI circuit state."""
        ...

    def qpiai_to_qubit(self, qpiai_state):
        """Extract QKDpy Qubit from QpiAI simulation."""
        ...

    def create_bb84_circuit(self, num_qubits, alice_bases, bob_bases):
        """Create QpiAI circuit for BB84."""
        circuit = self.Circuit(num_qubits * 2)
        for i in range(num_qubits):
            if alice_bases[i] == "X":
                circuit.h(i)
        return circuit
```

### Noise Model Bridge
Convert QKDpy `QuantumChannel` params to framework-specific noise:

```python
def qkdpy_channel_to_framework_noise(
    channel_params: dict,
    framework: str = "qiskit"
) -> Any:
    """Convert QKDpy QuantumChannel parameters to framework noise objects."""
    noise_level = channel_params.get("noise_level", 0.0)
    noise_model = channel_params.get("noise_model", "none")

    if framework == "pennylane":
        # Return PennyLane noise channels
        return {
            "depolarizing": qml.DepolarizingChannel(noise_level, wires=0),
            "amplitude_damping": qml.AmplitudeDamping(noise_level, wires=0),
        }
    elif framework == "qiskit":
        # Return Kraus operators
        K0 = np.array([[1, 0], [0, np.sqrt(1 - noise_level)]])
        K1 = np.array([[0, np.sqrt(noise_level)], [0, 0]])
        return Kraus([K0, K1])
```

### Test Pattern for Framework Integrations
```python
class TestFrameworkIntegration:
    def test_bb84_roundtrip(self):
        """BB84 protocol executes correctly on framework simulator."""
        ...

    def test_noise_simulation(self):
        """Channel noise matches expected QBER."""
        ...

    def test_entanglement_generation(self):
        """Bell pairs are correctly generated and verified."""
        ...

    def test_benchmark_vs_native_qkdpy(self):
        """Framework simulation produces comparable results."""
        ...
```
