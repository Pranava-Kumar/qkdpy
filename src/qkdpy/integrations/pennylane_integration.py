"""PennyLane integration plugin for QKDpy."""

from typing import Any

try:
    import pennylane as qml
    from pennylane import numpy as pnp

    PENNYLANE_AVAILABLE = True
except ImportError:
    PENNYLANE_AVAILABLE = False
    pnp = None


import numpy as np

from qkdpy.core.secure_random import secure_choice, secure_randint

from ..core import QuantumChannel, Qubit
from ..protocols.bb84 import BB84


_CHSH_QNODE: Any = None


def _get_chsh_qnode() -> Any:
    """Get a cached CHSH QNode to avoid re-creating devices on every call."""
    global _CHSH_QNODE
    if _CHSH_QNODE is None:
        dev = qml.device("default.qubit", wires=2)

        @qml.qnode(dev)  # type: ignore
        def _chsh_circuit(a_angle: float, b_angle: float) -> float:
            qml.Hadamard(wires=0)
            qml.CNOT(wires=[0, 1])
            qml.RY(a_angle, wires=0)
            qml.RY(b_angle, wires=1)
            return qml.expval(qml.PauliZ(0) @ qml.PauliZ(1))

        _CHSH_QNODE = _chsh_circuit
    return _CHSH_QNODE


class PennyLaneIntegration:
    """Integration with PennyLane quantum computing framework."""

    def __init__(self) -> None:
        """Initialize PennyLane integration."""
        if not PENNYLANE_AVAILABLE:
            raise ImportError(
                "PennyLane is not installed. Please install it with 'pip install pennylane' "
                "to use PennyLane integration."
            )

    def qubit_to_pennylane(self, qkdpy_qubit: Qubit) -> Any:
        """Convert a QKDpy Qubit to a PennyLane state.

        Args:
            qkdpy_qubit: QKDpy Qubit object

        Returns:
            PennyLane tensor representing the same quantum state
        """
        if not PENNYLANE_AVAILABLE:
            raise ImportError("PennyLane is not installed")

        # Extract the state vector from QKDpy Qubit
        state = qkdpy_qubit.state
        # Create PennyLane tensor
        return pnp.tensor(state, requires_grad=False)

    def pennylane_to_qubit(self, pennylane_state: Any) -> Qubit:
        """Convert a PennyLane state to a QKDpy Qubit.

        Args:
            pennylane_state: PennyLane state

        Returns:
            QKDpy Qubit representing the same quantum state
        """
        if not PENNYLANE_AVAILABLE:
            raise ImportError("PennyLane is not installed")

        # Extract the state vector from PennyLane state
        state = pennylane_state.numpy()
        # Create QKDpy Qubit
        return Qubit(state[0], state[1])

    # ------------------------------------------------------------------ #
    #  Quantum Information Measures
    # ------------------------------------------------------------------ #

    def _ensure_density_matrix(self, state: np.ndarray) -> np.ndarray:
        """Convert state vector to density matrix if needed.

        PennyLane math functions require density matrices for
        entropy, purity, and related computations.

        Args:
            state: State vector (1D) or density matrix (2D)

        Returns:
            Density matrix (2D array)
        """
        if state.ndim == 1:
            return np.outer(state, np.conjugate(state))
        return state

    def compute_vn_entropy(self, state: np.ndarray, indices: list[int]) -> float:
        """Compute the von Neumann entropy of a subsystem from a state.

        Uses PennyLane's math module for direct computation on state vectors
        or density matrices.

        Args:
            state: State vector or density matrix
            indices: Subsystem indices to compute entropy for

        Returns:
            von Neumann entropy value
        """
        dm = self._ensure_density_matrix(state)
        return float(qml.math.vn_entropy(dm, indices=indices))

    def compute_mutual_info(
        self, state: np.ndarray, indices0: list[int], indices1: list[int]
    ) -> float:
        """Compute the mutual information between two subsystems.

        Args:
            state: State vector or density matrix
            indices0: First subsystem indices
            indices1: Second subsystem indices

        Returns:
            Mutual information value
        """
        dm = self._ensure_density_matrix(state)
        return float(
            qml.math.vn_entanglement_entropy(
                dm, indices0=indices0, indices1=indices1
            )
        )

    def compute_purity(self, state: np.ndarray, indices: list[int]) -> float:
        """Compute the purity of a subsystem from a state.

        Purity = Tr(ρ²) ranges from 1/d (maximally mixed) to 1 (pure).

        Args:
            state: State vector or density matrix
            indices: Subsystem indices

        Returns:
            Purity value
        """
        dm = self._ensure_density_matrix(state)
        return float(qml.math.purity(dm, indices=indices))

    def compute_fidelity(self, state1: np.ndarray, state2: np.ndarray) -> float:
        """Compute the fidelity between two quantum states.

        Args:
            state1: First quantum state (state vector or density matrix)
            state2: Second quantum state

        Returns:
            Fidelity value (0 to 1)
        """
        dm1 = self._ensure_density_matrix(state1)
        dm2 = self._ensure_density_matrix(state2)
        return float(qml.math.fidelity(dm1, dm2))

    def compute_trace_distance(
        self, state1: np.ndarray, state2: np.ndarray
    ) -> float:
        """Compute the trace distance between two quantum states.

        Args:
            state1: First quantum state
            state2: Second quantum state

        Returns:
            Trace distance value (0 to 1)
        """
        dm1 = self._ensure_density_matrix(state1)
        dm2 = self._ensure_density_matrix(state2)
        return float(qml.math.trace_distance(dm1, dm2))

    def compute_chsh_correlation(
        self,
        alice_angles: list[float],
        bob_angles: list[float],
        num_qubits: int = 100,
    ) -> float:
        """Compute the CHSH correlation value for DI-QKD verification.

        The CHSH inequality |⟨S⟩| ≤ 2 is violated by quantum mechanics.
        A value > 2 indicates non-local correlations suitable for DI-QKD.

        Uses exact analytic expectation values (shots parameter is accepted
        for backward compatibility but not used).

        Args:
            alice_angles: Measurement angles for Alice
            bob_angles: Measurement angles for Bob
            num_qubits: Ignored; kept for backward compatibility

        Returns:
            CHSH S-value
        """
        chsh_circuit = _get_chsh_qnode()

        # CHSH value S = E(a,b) + E(a,b') + E(a',b) - E(a',b')
        e_ab = chsh_circuit(alice_angles[0], bob_angles[0])
        e_ab_prime = chsh_circuit(alice_angles[0], bob_angles[1])
        e_a_prime_b = chsh_circuit(alice_angles[1], bob_angles[0])
        e_a_prime_b_prime = chsh_circuit(alice_angles[1], bob_angles[1])

        s_value = e_ab + e_ab_prime + e_a_prime_b - e_a_prime_b_prime
        return float(s_value)

    def create_state_tomography_circuit(self, num_qubits: int = 1) -> Any:
        """Create a circuit for quantum state tomography.

        Measures in Z, X, and Y bases to reconstruct the density matrix.

        Args:
            num_qubits: Number of qubits to perform tomography on

        Returns:
            QNode that returns measurement results in all bases
        """
        dev = qml.device("default.qubit", wires=num_qubits, shots=1000)
        measurements = []

        @qml.qnode(dev)  # type: ignore
        def tomography_circuit(basis: str) -> list[float]:
            if basis == "X":
                for i in range(num_qubits):
                    qml.Hadamard(wires=i)
            elif basis == "Y":
                for i in range(num_qubits):
                    qml.RX(-np.pi / 2, wires=i)
            # Z basis: no rotation needed
            return [qml.expval(qml.PauliZ(i)) for i in range(num_qubits)]

        def run_tomography() -> dict[str, list[float]]:
            return {
                "Z": tomography_circuit("Z"),
                "X": tomography_circuit("X"),
                "Y": tomography_circuit("Y"),
            }

        return run_tomography

    # ------------------------------------------------------------------ #
    #  Enhanced Circuit Construction
    # ------------------------------------------------------------------ #

    def create_e91_circuit(
        self,
        num_pairs: int = 1,
        alice_bases: list[str] | None = None,
        bob_bases: list[str] | None = None,
    ) -> Any:
        """Create a PennyLane circuit implementing the E91 protocol.

        Uses entangled pairs with measurement in Z, X, and W bases.

        Args:
            num_pairs: Number of entangled pairs
            alice_bases: Bases Alice uses ('Z', 'X', 'W')
            bob_bases: Bases Bob uses ('Z', 'X', 'W')

        Returns:
            QNode implementing E91
        """
        if alice_bases is None:
            alice_bases = [secure_choice(["Z", "X", "W"]) for _ in range(num_pairs)]
        if bob_bases is None:
            bob_bases = [secure_choice(["Z", "X", "W"]) for _ in range(num_pairs)]

        dev = qml.device("default.qubit", wires=2 * num_pairs, shots=1)

        @qml.qnode(dev)  # type: ignore
        def e91_circuit() -> list[Any]:
            # Create entangled pairs
            for i in range(num_pairs):
                qml.Hadamard(wires=i)
                qml.CNOT(wires=[i, i + num_pairs])

            # Alice measures her half
            for i, basis in enumerate(alice_bases):
                if basis == "X":
                    qml.Hadamard(wires=i)
                elif basis == "W":
                    qml.RY(-np.pi / 4, wires=i)
                # Z basis: no rotation

            # Bob measures his half
            for i, basis in enumerate(bob_bases):
                bob_wire = i + num_pairs
                if basis == "X":
                    qml.Hadamard(wires=bob_wire)
                elif basis == "W":
                    qml.RY(np.pi / 4, wires=bob_wire)
                # Z basis: no rotation

            return [
                qml.measure(wires=i) for i in range(2 * num_pairs)
            ]

        return e91_circuit

    def create_entanglement_circuit(self, num_pairs: int = 1) -> Any:
        """Create a PennyLane circuit that generates Bell state entangled pairs.

        Args:
            num_pairs: Number of entangled pairs to create

        Returns:
            QNode that generates Bell states
        """
        dev = qml.device("default.qubit", wires=2 * num_pairs, shots=1)

        @qml.qnode(dev)  # type: ignore
        def entanglement_circuit() -> list[Any]:
            for i in range(num_pairs):
                qml.Hadamard(wires=i)
                qml.CNOT(wires=[i, i + num_pairs])
            return [qml.measure(wires=i) for i in range(2 * num_pairs)]

        return entanglement_circuit

    def create_bb84_circuit(
        self,
        num_qubits: int = 1,
        alice_bases: list[str] | None = None,
        bob_bases: list[str] | None = None,
    ) -> Any:
        """Create a PennyLane circuit implementing the BB84 protocol.

        Args:
            num_qubits: Number of qubits to use
            alice_bases: List of bases Alice uses ('Z' for computational, 'X' for Hadamard)
            bob_bases: List of bases Bob uses ('Z' for computational, 'X' for Hadamard)

        Returns:
            PennyLane quantum function implementing BB84
        """
        if alice_bases is None:
            # Randomly choose bases for Alice
            alice_bases = [secure_choice(["Z", "X"]) for _ in range(num_qubits)]
        if bob_bases is None:
            # Randomly choose bases for Bob
            bob_bases = [secure_choice(["Z", "X"]) for _ in range(num_qubits)]

        # Create device
        dev = qml.device("default.qubit", wires=num_qubits)

        @qml.qnode(dev)  # type: ignore
        def bb84_circuit() -> list[Any]:
            # Alice prepares qubits
            for i, (basis,) in enumerate(zip(alice_bases, strict=False)):
                if basis == "X":  # Hadamard basis
                    qml.Hadamard(wires=i)

            # Bob measures qubits
            results = []
            for i, (basis,) in enumerate(zip(bob_bases, strict=False)):
                if basis == "X":  # Hadamard basis measurement
                    qml.Hadamard(wires=i)
                result = qml.measure(wires=i)
                results.append(result)

            return results

        return bb84_circuit

    def simulate_bb84_with_pennylane(
        self,
        num_qubits: int = 10,
        noise_model: str | None = None,
        noise_level: float = 0.0,
    ) -> tuple[list[int], list[int], list[bool]]:
        """Simulate BB84 protocol using PennyLane.

        Args:
            num_qubits: Number of qubits to simulate
            noise_model: Type of noise to add ('bit_flip', 'phase_flip', 'depolarizing')
            noise_level: Noise level (0.0 to 1.0)

        Returns:
            Tuple of (alice_bits, bob_bits, matching_bases)
        """
        # Randomly generate Alice's bits and bases
        alice_bits = [secure_randint(0, 2) for _ in range(num_qubits)]
        alice_bases = [secure_choice(["Z", "X"]) for _ in range(num_qubits)]
        bob_bases = [secure_choice(["Z", "X"]) for _ in range(num_qubits)]

        # Create device
        dev = qml.device("default.qubit", wires=num_qubits)

        # Add noise if specified
        if noise_model and noise_level > 0:
            # PennyLane handles noise differently, typically through noisy devices
            # For simplicity, we'll add noise to the device
            pass

        @qml.qnode(dev)  # type: ignore
        def bb84_circuit() -> list[Any]:
            # Alice prepares qubits
            for i, (bit, basis) in enumerate(
                zip(alice_bits, alice_bases, strict=False)
            ):
                if bit == 1:
                    qml.PauliX(wires=i)  # Prepare |1⟩
                if basis == "X":  # Hadamard basis
                    qml.Hadamard(wires=i)

            # Bob measures qubits
            results = []
            for i, (basis,) in enumerate(zip(bob_bases, strict=False)):
                if basis == "X":  # Hadamard basis measurement
                    qml.Hadamard(wires=i)
                result = qml.measure(wires=i)
                results.append(result)

            return results

        # Run the circuit
        bob_bits = bb84_circuit()

        # Convert measurements to integers
        bob_bits = [int(bit) for bit in bob_bits]

        # Determine matching bases
        matching_bases = [a == b for a, b in zip(alice_bases, bob_bases, strict=False)]

        return alice_bits, bob_bits, matching_bases

    def convert_channel_to_pennylane(
        self, qkdpy_channel: QuantumChannel
    ) -> dict[str, Any]:
        """Convert a QKDpy QuantumChannel to PennyLane noise parameters.

        Args:
            qkdpy_channel: QKDpy QuantumChannel

        Returns:
            Dictionary with PennyLane noise parameters
        """
        noise_params = {}

        # Add loss parameters
        noise_params["loss"] = qkdpy_channel.loss

        # Add noise parameters based on noise model
        if qkdpy_channel.noise_level > 0:
            if qkdpy_channel.noise_model == "depolarizing":
                noise_params["depolarizing"] = qkdpy_channel.noise_level
            elif qkdpy_channel.noise_model == "bit_flip":
                noise_params["bit_flip"] = qkdpy_channel.noise_level
            elif qkdpy_channel.noise_model == "phase_flip":
                noise_params["phase_flip"] = qkdpy_channel.noise_level

        return noise_params

    def benchmark_qkdpy_vs_pennylane(
        self, num_qubits: int = 100, num_trials: int = 10
    ) -> dict[str, Any]:
        """Benchmark QKDpy against PennyLane for BB84 protocol.

        Args:
            num_qubits: Number of qubits to simulate
            num_trials: Number of trials to run

        Returns:
            Dictionary with benchmark results
        """
        import time

        # Benchmark QKDpy
        qkdpy_times = []
        for _ in range(num_trials):
            channel = QuantumChannel(
                loss=0.1, noise_model="depolarizing", noise_level=0.05
            )
            protocol = BB84(channel, key_length=num_qubits)

            start_time = time.time()
            protocol.execute()
            end_time = time.time()

            qkdpy_times.append(end_time - start_time)

        # Benchmark PennyLane
        pennylane_times = []
        for _ in range(num_trials):
            start_time = time.time()
            alice_bits, bob_bits, matching_bases = self.simulate_bb84_with_pennylane(
                num_qubits=num_qubits, noise_model="depolarizing", noise_level=0.05
            )
            end_time = time.time()

            pennylane_times.append(end_time - start_time)

        # Calculate statistics
        qkdpy_avg = np.mean(qkdpy_times)
        qkdpy_std = np.std(qkdpy_times)
        pennylane_avg = np.mean(pennylane_times)
        pennylane_std = np.std(pennylane_times)

        return {
            "qkdpy_average_time": float(qkdpy_avg),
            "qkdpy_std_time": float(qkdpy_std),
            "pennylane_average_time": float(pennylane_avg),
            "pennylane_std_time": float(pennylane_std),
            "speedup_factor": (
                float(qkdpy_avg / pennylane_avg) if pennylane_avg > 0 else float("inf")
            ),
            "num_qubits": num_qubits,
            "num_trials": num_trials,
        }
