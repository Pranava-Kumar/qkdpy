# 3. Core Quantum Stack

## Class Hierarchy


.. image:: 03-core-quantum-stacka.png
   :alt: 03-core-quantum-stack (slide a)
   :width: 100%
   :align: center

<!-- Original mermaid source retained for editor / GitHub viewers.
classDiagram
    class Qubit {
        -_state: np.ndarray[complex]
        +state: np.ndarray
        +probabilities: tuple[float, float]
        +zero() Qubit
        +one() Qubit
        +plus() Qubit
        +minus() Qubit
        +apply_gate(gate: np.ndarray)
        +measure(basis: str) int
        +collapse_state(result: int, basis: str)
        +density_matrix() np.ndarray
        +bloch_vector() tuple[float, float, float]
    }

    class Qudit {
        -_state: np.ndarray[complex]
        +dimension: int
        +state: np.ndarray
        +probabilities: list[float]
        +computational_basis(level, dim) Qudit
        +uniform_superposition(dim) Qudit
        +fourier_basis(level, dim) Qudit
        +apply_unitary(operator: np.ndarray)
        +measure(basis_matrix) int
        +partial_trace(idx, dim) Qudit
        +fidelity(other) float
    }

    class MultiQubitState {
        -_state: np.ndarray[complex]
        -_num_qubits: int
        +state: np.ndarray
        +probabilities: np.ndarray
        +from_qubits(list[Qubit]) MultiQubitState
        +zeros(n) MultiQubitState
        +ghz(n) MultiQubitState
        +w_state(n) MultiQubitState
        +apply_gate(gate, target_qubits)
        +measure(target) tuple[int, MultiQubitState]
        +entanglement_entropy(subsystem) float
        +fidelity(other) float
        +density_matrix() np.ndarray
    }

    class QuantumChannel {
        +distance: float
        +loss: float
        +noise_model: str
        +noise_level: float
        +transmit(qubit, timestamp) Qubit|None
        +transmit_batch(qubits) list[Qubit|None]
        +static intercept_resend_attack()
        +static entanglement_attack()
        +get_statistics() dict
        +reset_statistics()
    }

    class QuantumGate {
        +matrix: np.ndarray
    }

    class Identity {
        +__init__()
    }
    class PauliX { }
    class PauliY { }
    class PauliZ { }
    class Hadamard { }
    class S { }
    class SDag { }
    class T { }
    class Rx {
        +__init__(theta)
    }
    class Ry {
        +__init__(theta)
    }
    class Rz {
        +__init__(theta)
    }
    class CNOT { }
    class CZ { }
    class SWAP { }

    class GateUtils {
        +static basis_switch(basis) np.ndarray
        +static random_unitary() np.ndarray
        +static unitary_from_angles(theta, phi, lam) np.ndarray
        +static sequence(*gates) np.ndarray
        +static tensor_product(*gates) np.ndarray
        +static is_unitary(gate) bool
        +static is_hermitian(gate) bool
    }

    class Measurement {
        +static measure_in_basis(qubit, basis) int
        +static measure_batch_in_basis(qubits, basis) list[int]
        +static measure_in_random_basis(qubit, bases) tuple[int, str]
        +static measure_batch_in_random_bases(qubits, bases) tuple[list[int], list[str]]
        +static measure_state_fidelity(qubit, target) float
        +static measure_bloch_coordinates(qubit) tuple
        +static measure_density_matrix(qubit) np.ndarray
        +static measure_purity(qubit) float
        +static measure_von_neumann_entropy(qubit) float
        +static measure_observable(qubit, observable) float
        +static measure_bell_state(q1, q2) str
        +static quantum_state_tomography(qubit, n) dict
    }

    class QuantumDetector {
        +efficiency: float
        +dark_count_rate: float
        +detect(photon_present, timestamp) tuple
        +get_statistics() dict
        +reset()
        +static measure_state(state) int
    }

    class DetectorArray {
        +detectors: list[QuantumDetector]
        +measure_in_basis(qubit, basis, timestamp) int
        +get_statistics() list[dict]
        +static measure_state(state) int
    }

    class PhotonSource {
        +wavelength: float
        +intensity: float
        +generate_pulse() Photon
        +get_statistics() dict
    }

    QuantumGate <|-- Identity
    QuantumGate <|-- PauliX
    QuantumGate <|-- PauliY
    QuantumGate <|-- PauliZ
    QuantumGate <|-- Hadamard
    QuantumGate <|-- S
    QuantumGate <|-- SDag
    QuantumGate <|-- T
    QuantumGate <|-- Rx
    QuantumGate <|-- Ry
    QuantumGate <|-- Rz
    QuantumGate <|-- CNOT
    QuantumGate <|-- CZ
    QuantumGate <|-- SWAP

    QuantumDetector --> DetectorArray : composed in
-->


## Physical Channel Effects


.. image:: 03-core-quantum-stackb.png
   :alt: 03-core-quantum-stack (slide b)
   :width: 100%
   :align: center

<!-- Original mermaid source retained for editor / GitHub viewers.
flowchart TD
    subgraph Input["Input Qubit"]
        IQ["|ψ⟩ = α|0⟩ + β|1⟩"]
    end

    subgraph Loss["1. Photon Loss"]
        L1["Calculate survival: exp(-α·d)"]
        L2{"secure_random() < loss?"}
        L3["Qubit lost → None"]
        L4["Qubit survives → continue"]
        L1 --> L2
        L2 -->|yes| L3
        L2 -->|no| L4
    end

    subgraph Eve["2. Eavesdropping (optional)"]
        E1{"Eavesdropper present?"}
        E2["Intercept-Resend Attack:<br/>Measure in random basis<br/>Resend new qubit"]
        E3["Entanglement Attack:<br/>CNOT with ancilla<br/>Measure ancilla later"]
        E1 -->|yes| E2
        E1 -->|yes| E3
    end

    subgraph Physical["3. Physical Effects"]
        P1["Polarization Drift<br/>Ry(θ_drift) where θ_drift = N(0, rate)·t"]
        P2["Phase Fluctuations<br/>Rz(φ) where φ = N(0, rate)·t"]
        P3["Misalignment Errors<br/>Small random rotation with prob p"]
        P4["Thermal Noise<br/>Random Pauli with prob T(temperature)"]
        P1 --> P2 --> P3 --> P4
    end

    subgraph NoiseModel["4. Noise Models"]
        N1["Depolarizing: ρ → (1-p)ρ + p/3·(XρX + YρY + ZρZ)"]
        N2["Bit Flip: ρ → (1-p)ρ + p·XρX"]
        N3["Phase Flip: ρ → (1-p)ρ + p·ZρZ"]
        N4["Amplitude Damping: K₀, K₁ Kraus operators"]
    end

    subgraph Output["Output (Received Qubit)"]
        OQ["|ψ'⟩ (noisy, may be None)"]
    end

    Input --> Loss --> Eve --> Physical --> NoiseModel --> Output

    style Input fill:#bbdefb,stroke:#1565c0
    style Loss fill:#ffe0b2,stroke:#e65100
    style Eve fill:#ffcdd2,stroke:#c62828
    style Physical fill:#e1bee7,stroke:#6a1b9a
    style NoiseModel fill:#d1c4e9,stroke:#4527a0
    style Output fill:#c8e6c9,stroke:#2e7d32
-->


## Noise Model Kraus Operators


.. image:: 03-core-quantum-stackc.png
   :alt: 03-core-quantum-stack (slide c)
   :width: 100%
   :align: center

<!-- Original mermaid source retained for editor / GitHub viewers.
graph TD
    subgraph Depol["Depolarizing Channel"]
        D0["K₀ = √(1-p) · I"]
        D1["K₁ = √(p/3) · X"]
        D2["K₂ = √(p/3) · Y"]
        D3["K₃ = √(p/3) · Z"]
        D0 --- D1 --- D2 --- D3
        D_APPLY["ρ → Σ KᵢρKᵢ†<br/>Trajectory: apply random non-identity Pauli"]
    end

    subgraph AmpDamp["Amplitude Damping"]
        AD0["K₀ = [[1, 0], [0, √(1-γ)]]"]
        AD1["K₁ = [[0, √γ], [0, 0]]"]
        AD0 --- AD1
        AD_APPLY["Jump: |1⟩ → |0⟩ with prob γ|β|²<br/>No-jump: damp |1⟩ by √(1-γ)"]
    end

    subgraph PhaseFlip["Phase Flip (Dephasing)"]
        PF0["K₀ = √(1-p) · I"]
        PF1["K₁ = √p · Z"]
        PF0 --- PF1
        PF_APPLY["Apply Z with prob p<br/>Decoheres off-diagonals"]
    end
-->


## Security Analysis


.. image:: 03-core-quantum-stackd.png
   :alt: 03-core-quantum-stack (slide d)
   :width: 100%
   :align: center

<!-- Original mermaid source retained for editor / GitHub viewers.
flowchart LR
    subgraph Metrics["Security Metrics"]
        M1["QBER: Error rate in sample"]
        M2["CHSH S-value for E91"]
        M3["Eve's mutual information"]
        M4["Key rate: final/raw ratio"]
    end

    subgraph Thresholds["Thresholds"]
        T1["BB84: QBER ≤ 11%"]
        T2["E91: |S| > 2 (Bell violation)"]
        T3["B92: QBER ≤ 4.6%"]
        T4["DI-QKD: CHSH > 2"]
    end

    subgraph Attacks["Attack Detection"]
        A1["Intercept-resend → QBER spike"]
        A2["PNS attack → Multi-photon rate"]
        A3["Entanglement → Bell violation drop"]
    end

    Metrics --> Thresholds
    Thresholds --> Attacks
-->


## Bloch Sphere Representation


.. image:: 03-core-quantum-stacke.png
   :alt: 03-core-quantum-stack (slide e)
   :width: 100%
   :align: center

<!-- Original mermaid source retained for editor / GitHub viewers.
graph TD
    subgraph States["Qubit States on Bloch Sphere"]
        ZERO["|0⟩ = (0,0,1)<br/>Computational 0"]
        ONE["|1⟩ = (0,0,-1)<br/>Computational 1"]
        PLUS["|+⟩ = (1,0,0)<br/>Hadamard 0"]
        MINUS["|-⟩ = (-1,0,0)<br/>Hadamard 1"]
        YPLUS["|y+⟩ = (0,1,0)<br/>Circular 0"]
        YMINUS["|y-⟩ = (0,-1,0)<br/>Circular 1"]
    end

    subgraph Gates["Gate Rotations"]
        RX["Rx(θ): rotate around X axis<br/>[[cos(θ/2), -i·sin(θ/2)],<br/>[-i·sin(θ/2), cos(θ/2)]]"]
        RY["Ry(θ): rotate around Y axis<br/>[[cos(θ/2), -sin(θ/2)],<br/>[sin(θ/2), cos(θ/2)]]"]
        RZ["Rz(θ): rotate around Z axis<br/>[[e^(-iθ/2), 0],<br/>[0, e^(iθ/2)]]"]
        H["H: X ↦ Z basis swap<br/>[[1,1],[1,-1]]/√2"]
    end

    States -.->|measurement projects| Gates
-->
