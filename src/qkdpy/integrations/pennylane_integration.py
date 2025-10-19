"""PennyLane integration plugin for QKDpy."""

try:
    import pennylane as qml
    from pennylane import numpy as pnp

    PENNYLANE_AVAILABLE = True
except ImportError:
    PENNYLANE_AVAILABLE = False
    pnp = None


import numpy as np

from ..core import QuantumChannel, Qubit
from ..protocols.bb84 import BB84


class PennyLaneIntegration:
    """Integration with PennyLane quantum computing framework."""

    def __init__(self):
        """Initialize PennyLane integration."""
        if not PENNYLANE_AVAILABLE:
            raise ImportError(
                "PennyLane is not installed. Please install it with 'pip install pennylane' "
                "to use PennyLane integration."
            )

    def qubit_to_pennylane(self, qkdpy_qubit: Qubit):
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

    def pennylane_to_qubit(self, pennylane_state) -> Qubit:
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

    def create_bb84_circuit(
        self,
        num_qubits: int = 1,
        alice_bases: list[str] | None = None,
        bob_bases: list[str] | None = None,
    ):
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
            alice_bases = [np.random.choice(["Z", "X"]) for _ in range(num_qubits)]
        if bob_bases is None:
            # Randomly choose bases for Bob
            bob_bases = [np.random.choice(["Z", "X"]) for _ in range(num_qubits)]

        # Create device
        dev = qml.device("default.qubit", wires=num_qubits)

        @qml.qnode(dev)
        def bb84_circuit():
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
        alice_bits = [np.random.randint(0, 2) for _ in range(num_qubits)]
        alice_bases = [np.random.choice(["Z", "X"]) for _ in range(num_qubits)]
        bob_bases = [np.random.choice(["Z", "X"]) for _ in range(num_qubits)]

        # Create device
        dev = qml.device("default.qubit", wires=num_qubits)

        # Add noise if specified
        if noise_model and noise_level > 0:
            # PennyLane handles noise differently, typically through noisy devices
            # For simplicity, we'll add noise to the device
            pass

        @qml.qnode(dev)
        def bb84_circuit():
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

    def convert_channel_to_pennylane(self, qkdpy_channel: QuantumChannel) -> dict:
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

    def create_entanglement_circuit(self, num_pairs: int = 1):
        """Create a PennyLane circuit for generating entangled pairs.

        Args:
            num_pairs: Number of entangled pairs to create

        Returns:
            PennyLane quantum function creating entangled pairs
        """
        # Create device
        dev = qml.device("default.qubit", wires=2 * num_pairs)

        @qml.qnode(dev)
        def entanglement_circuit():
            # Create entangled pairs using Hadamard and CNOT
            for i in range(num_pairs):
                qml.Hadamard(wires=i)  # Create superposition
                qml.CNOT(wires=[i, i + num_pairs])  # Create entanglement

            return [qml.expval(qml.PauliZ(i)) for i in range(2 * num_pairs)]

        return entanglement_circuit

    def benchmark_qkdpy_vs_pennylane(
        self, num_qubits: int = 100, num_trials: int = 10
    ) -> dict:
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
