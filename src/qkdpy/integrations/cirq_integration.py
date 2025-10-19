"""Cirq integration plugin for QKDpy."""

try:
    import cirq

    CIRQ_AVAILABLE = True
except ImportError:
    CIRQ_AVAILABLE = False


import numpy as np

from ..core import QuantumChannel, Qubit
from ..protocols.bb84 import BB84


class CirqIntegration:
    """Integration with Cirq quantum computing framework."""

    def __init__(self):
        """Initialize Cirq integration."""
        if not CIRQ_AVAILABLE:
            raise ImportError(
                "Cirq is not installed. Please install it with 'pip install cirq' "
                "to use Cirq integration."
            )

    def qubit_to_cirq(self, qkdpy_qubit: Qubit):
        """Convert a QKDpy Qubit to a Cirq state.

        Args:
            qkdpy_qubit: QKDpy Qubit object

        Returns:
            Cirq state representing the same quantum state
        """
        # Extract the state vector from QKDpy Qubit
        state = qkdpy_qubit.state
        # Create Cirq state
        return cirq.StateVectorSimulationState(state_vector=state)

    def cirq_to_qubit(self, cirq_state):
        """Convert a Cirq state to a QKDpy Qubit.

        Args:
            cirq_state: Cirq state

        Returns:
            QKDpy Qubit representing the same quantum state
        """
        # Extract the state vector from Cirq state
        state = cirq_state.state_vector()
        # Create QKDpy Qubit
        return Qubit(state[0], state[1])

    def create_bb84_circuit(
        self,
        num_qubits: int = 1,
        alice_bases: list[str] | None = None,
        bob_bases: list[str] | None = None,
    ):
        """Create a Cirq circuit implementing the BB84 protocol.

        Args:
            num_qubits: Number of qubits to use
            alice_bases: List of bases Alice uses ('Z' for computational, 'X' for Hadamard)
            bob_bases: List of bases Bob uses ('Z' for computational, 'X' for Hadamard)

        Returns:
            Cirq Circuit implementing BB84
        """
        if alice_bases is None:
            # Randomly choose bases for Alice
            alice_bases = [np.random.choice(["Z", "X"]) for _ in range(num_qubits)]
        if bob_bases is None:
            # Randomly choose bases for Bob
            bob_bases = [np.random.choice(["Z", "X"]) for _ in range(num_qubits)]

        # Create qubits
        qubits = [cirq.LineQubit(i) for i in range(num_qubits)]

        # Create circuit
        circuit = cirq.Circuit()

        # Alice prepares qubits
        for _i, (basis, qubit) in enumerate(zip(alice_bases, qubits, strict=False)):
            if basis == "X":  # Hadamard basis
                circuit.append(cirq.H(qubit))

        # Bob measures qubits
        for i, (basis, qubit) in enumerate(zip(bob_bases, qubits, strict=False)):
            if basis == "X":  # Hadamard basis measurement
                circuit.append(cirq.H(qubit))
            circuit.append(cirq.measure(qubit, key=f"result_{i}"))

        return circuit

    def simulate_bb84_with_cirq(
        self,
        num_qubits: int = 10,
        noise_model: str | None = None,
        noise_level: float = 0.0,
    ) -> tuple[list[int], list[int], list[bool]]:
        """Simulate BB84 protocol using Cirq.

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

        # Create qubits
        qubits = [cirq.LineQubit(i) for i in range(num_qubits)]

        # Create circuit
        circuit = cirq.Circuit()

        # Alice prepares qubits
        for i, (bit, basis) in enumerate(zip(alice_bits, alice_bases, strict=False)):
            if bit == 1:
                circuit.append(cirq.X(qubits[i]))  # Prepare |1⟩
            if basis == "X":  # Hadamard basis
                circuit.append(cirq.H(qubits[i]))

        # Add noise if specified
        if noise_model and noise_level > 0:
            if noise_model == "bit_flip":
                circuit.append(cirq.bit_flip(noise_level).on_each(qubits))
            elif noise_model == "phase_flip":
                circuit.append(cirq.phase_flip(noise_level).on_each(qubits))
            elif noise_model == "depolarizing":
                circuit.append(cirq.depolarize(noise_level).on_each(qubits))

        # Bob measures qubits
        for i, (basis, qubit) in enumerate(zip(bob_bases, qubits, strict=False)):
            if basis == "X":  # Hadamard basis measurement
                circuit.append(cirq.H(qubit))
            circuit.append(cirq.measure(qubit, key=f"result_{i}"))

        # Simulate the circuit
        simulator = cirq.Simulator()
        result = simulator.run(circuit, repetitions=1)

        # Extract Bob's measurement results
        bob_bits = []
        for i in range(num_qubits):
            measurement = result.measurements[f"result_{i}"][0]
            bob_bits.append(int(measurement))

        # Determine matching bases
        matching_bases = [a == b for a, b in zip(alice_bases, bob_bases, strict=False)]

        return alice_bits, bob_bits, matching_bases

    def convert_channel_to_cirq(self, qkdpy_channel: QuantumChannel):
        """Convert a QKDpy QuantumChannel to Cirq noise gates.

        Args:
            qkdpy_channel: QKDpy QuantumChannel

        Returns:
            List of Cirq gates representing the same channel characteristics
        """
        noise_gates = []

        # Add loss as amplitude damping (simplified model)
        if qkdpy_channel.loss > 0:
            # Loss is typically handled at the protocol level
            pass

        # Add noise based on noise model
        if qkdpy_channel.noise_level > 0:
            if qkdpy_channel.noise_model == "depolarizing":
                noise_gates.append(cirq.depolarize(qkdpy_channel.noise_level))
            elif qkdpy_channel.noise_model == "bit_flip":
                noise_gates.append(cirq.bit_flip(qkdpy_channel.noise_level))
            elif qkdpy_channel.noise_model == "phase_flip":
                noise_gates.append(cirq.phase_flip(qkdpy_channel.noise_level))

        return noise_gates

    def create_entanglement_circuit(self, num_pairs: int = 1):
        """Create a Cirq circuit for generating entangled pairs.

        Args:
            num_pairs: Number of entangled pairs to create

        Returns:
            Cirq Circuit creating entangled pairs
        """
        # Create qubits for Alice and Bob
        alice_qubits = [cirq.LineQubit(i) for i in range(num_pairs)]
        bob_qubits = [cirq.LineQubit(i + num_pairs) for i in range(num_pairs)]

        # Create circuit
        circuit = cirq.Circuit()

        # Create entangled pairs using Hadamard and CNOT
        for i in range(num_pairs):
            circuit.append(cirq.H(alice_qubits[i]))  # Create superposition
            circuit.append(
                cirq.CNOT(alice_qubits[i], bob_qubits[i])
            )  # Create entanglement

        return circuit

    def benchmark_qkdpy_vs_cirq(
        self, num_qubits: int = 100, num_trials: int = 10
    ) -> dict:
        """Benchmark QKDpy against Cirq for BB84 protocol.

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

        # Benchmark Cirq
        cirq_times = []
        for _ in range(num_trials):
            start_time = time.time()
            alice_bits, bob_bits, matching_bases = self.simulate_bb84_with_cirq(
                num_qubits=num_qubits, noise_model="depolarizing", noise_level=0.05
            )
            end_time = time.time()

            cirq_times.append(end_time - start_time)

        # Calculate statistics
        qkdpy_avg = np.mean(qkdpy_times)
        qkdpy_std = np.std(qkdpy_times)
        cirq_avg = np.mean(cirq_times)
        cirq_std = np.std(cirq_times)

        return {
            "qkdpy_average_time": float(qkdpy_avg),
            "qkdpy_std_time": float(qkdpy_std),
            "cirq_average_time": float(cirq_avg),
            "cirq_std_time": float(cirq_std),
            "speedup_factor": (
                float(qkdpy_avg / cirq_avg) if cirq_avg > 0 else float("inf")
            ),
            "num_qubits": num_qubits,
            "num_trials": num_trials,
        }
