"""Qiskit integration plugin for QKDpy."""

try:
    from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
    from qiskit.quantum_info import Statevector

    QISKIT_AVAILABLE = True
except ImportError:
    QISKIT_AVAILABLE = False


import numpy as np

from ..core import QuantumChannel, Qubit
from ..protocols.bb84 import BB84


class QiskitIntegration:
    """Integration with Qiskit quantum computing framework."""

    def __init__(self):
        """Initialize Qiskit integration."""
        if not QISKIT_AVAILABLE:
            raise ImportError(
                "Qiskit is not installed. Please install it with 'pip install qiskit' "
                "to use Qiskit integration."
            )

    def qubit_to_qiskit(self, qkdpy_qubit: Qubit):
        """Convert a QKDpy Qubit to a Qiskit Statevector.

        Args:
            qkdpy_qubit: QKDpy Qubit object

        Returns:
            Qiskit Statevector representing the same quantum state
        """
        # Extract the state vector from QKDpy Qubit
        state = qkdpy_qubit.state
        # Create Qiskit Statevector
        return Statevector(state)

    def qiskit_to_qubit(self, qiskit_state):
        """Convert a Qiskit Statevector to a QKDpy Qubit.

        Args:
            qiskit_state: Qiskit Statevector

        Returns:
            QKDpy Qubit representing the same quantum state
        """
        # Extract the state vector from Qiskit Statevector
        state = qiskit_state.data
        # Create QKDpy Qubit
        return Qubit(state[0], state[1])

    def create_bb84_circuit(
        self,
        num_qubits: int = 1,
        alice_bases: list[str] | None = None,
        bob_bases: list[str] | None = None,
    ):
        """Create a Qiskit circuit implementing the BB84 protocol.

        Args:
            num_qubits: Number of qubits to use
            alice_bases: List of bases Alice uses ('Z' for computational, 'X' for Hadamard)
            bob_bases: List of bases Bob uses ('Z' for computational, 'X' for Hadamard)

        Returns:
            Qiskit QuantumCircuit implementing BB84
        """
        if alice_bases is None:
            # Randomly choose bases for Alice
            alice_bases = [np.random.choice(["Z", "X"]) for _ in range(num_qubits)]
        if bob_bases is None:
            # Randomly choose bases for Bob
            bob_bases = [np.random.choice(["Z", "X"]) for _ in range(num_qubits)]

        # Create quantum and classical registers
        qreg = QuantumRegister(num_qubits, "q")
        creg_alice = ClassicalRegister(num_qubits, "alice")
        creg_bob = ClassicalRegister(num_qubits, "bob")
        circuit = QuantumCircuit(qreg, creg_alice, creg_bob)

        # Alice prepares qubits
        for i, basis in enumerate(alice_bases):
            if basis == "X":  # Hadamard basis
                circuit.h(qreg[i])
            # For Z basis (computational), no operation needed

        # Bob measures qubits
        for i, basis in enumerate(bob_bases):
            if basis == "X":  # Hadamard basis measurement
                circuit.h(qreg[i])
            circuit.measure(qreg[i], creg_bob[i])

        return circuit

    def simulate_bb84_with_qiskit(
        self,
        num_qubits: int = 10,
        noise_model: str | None = None,
        noise_level: float = 0.0,
    ) -> tuple[list[int], list[int], list[bool]]:
        """Simulate BB84 protocol using Qiskit.

        Args:
            num_qubits: Number of qubits to simulate
            noise_model: Type of noise to add ('bit_flip', 'phase_flip', 'depolarizing')
            noise_level: Noise level (0.0 to 1.0)

        Returns:
            Tuple of (alice_bits, bob_bits, matching_bases)
        """
        from qiskit import transpile
        from qiskit_aer import AerSimulator

        # Randomly generate Alice's bits and bases
        alice_bits = [np.random.randint(0, 2) for _ in range(num_qubits)]
        alice_bases = [np.random.choice(["Z", "X"]) for _ in range(num_qubits)]
        bob_bases = [np.random.choice(["Z", "X"]) for _ in range(num_qubits)]

        # Create quantum circuit
        qreg = QuantumRegister(num_qubits, "q")
        creg_alice = ClassicalRegister(num_qubits, "alice")
        creg_bob = ClassicalRegister(num_qubits, "bob")
        circuit = QuantumCircuit(qreg, creg_alice, creg_bob)

        # Alice prepares qubits
        for i, (bit, basis) in enumerate(zip(alice_bits, alice_bases, strict=False)):
            if bit == 1:
                circuit.x(qreg[i])  # Prepare |1⟩
            if basis == "X":  # Hadamard basis
                circuit.h(qreg[i])

        # Add noise if specified
        if noise_model and noise_level > 0:
            from qiskit_aer.noise import NoiseModel, depolarizing_error, pauli_error

            noise_model_obj = NoiseModel()
            if noise_model == "bit_flip":
                error = pauli_error([("X", noise_level), ("I", 1 - noise_level)])
                noise_model_obj.add_all_qubit_quantum_error(error, ["id", "x", "h"])
            elif noise_model == "phase_flip":
                error = pauli_error([("Z", noise_level), ("I", 1 - noise_level)])
                noise_model_obj.add_all_qubit_quantum_error(error, ["id", "x", "h"])
            elif noise_model == "depolarizing":
                error = depolarizing_error(noise_level, 1)
                noise_model_obj.add_all_qubit_quantum_error(error, ["id", "x", "h"])

        # Bob measures qubits
        for i, basis in enumerate(bob_bases):
            if basis == "X":  # Hadamard basis measurement
                circuit.h(qreg[i])
            circuit.measure(qreg[i], creg_bob[i])

        # Simulate the circuit
        simulator = AerSimulator()
        if noise_model and noise_level > 0:
            simulator = AerSimulator(noise_model=noise_model_obj)

        # Transpile and run
        circuit = transpile(circuit, simulator)
        result = simulator.run(circuit, shots=1).result()
        counts = result.get_counts(circuit)

        # Extract Bob's measurement results
        # Get the most frequent outcome (should be only one with shots=1)
        outcome = list(counts.keys())[0]
        bob_bits = [int(bit) for bit in outcome[:num_qubits]]

        # Determine matching bases
        matching_bases = [a == b for a, b in zip(alice_bases, bob_bases, strict=False)]

        return alice_bits, bob_bits, matching_bases

    def convert_channel_to_qiskit(self, qkdpy_channel: QuantumChannel):
        """Convert a QKDpy QuantumChannel to a Qiskit NoiseModel.

        Args:
            qkdpy_channel: QKDpy QuantumChannel

        Returns:
            Qiskit NoiseModel representing the same channel characteristics
        """
        from qiskit_aer.noise import NoiseModel, depolarizing_error, pauli_error

        noise_model = NoiseModel()

        # Add loss as a reset error (simplified model)
        if qkdpy_channel.loss > 0:
            # For simplicity, we'll model loss as a combination of errors
            pass  # Loss is typically handled at the protocol level in Qiskit

        # Add noise based on noise model
        if qkdpy_channel.noise_level > 0:
            if qkdpy_channel.noise_model == "depolarizing":
                error = depolarizing_error(qkdpy_channel.noise_level, 1)
                noise_model.add_all_qubit_quantum_error(error, ["id", "x", "h", "cx"])
            elif qkdpy_channel.noise_model == "bit_flip":
                error = pauli_error(
                    [
                        ("X", qkdpy_channel.noise_level),
                        ("I", 1 - qkdpy_channel.noise_level),
                    ]
                )
                noise_model.add_all_qubit_quantum_error(error, ["id", "x", "h"])
            elif qkdpy_channel.noise_model == "phase_flip":
                error = pauli_error(
                    [
                        ("Z", qkdpy_channel.noise_level),
                        ("I", 1 - qkdpy_channel.noise_level),
                    ]
                )
                noise_model.add_all_qubit_quantum_error(error, ["id", "x", "h"])

        return noise_model

    def create_entanglement_circuit(self, num_pairs: int = 1):
        """Create a Qiskit circuit for generating entangled pairs.

        Args:
            num_pairs: Number of entangled pairs to create

        Returns:
            Qiskit QuantumCircuit creating entangled pairs
        """
        # Create quantum registers for Alice and Bob
        qreg_alice = QuantumRegister(num_pairs, "alice")
        qreg_bob = QuantumRegister(num_pairs, "bob")
        circuit = QuantumCircuit(qreg_alice, qreg_bob)

        # Create entangled pairs using Hadamard and CNOT
        for i in range(num_pairs):
            circuit.h(qreg_alice[i])  # Create superposition
            circuit.cx(qreg_alice[i], qreg_bob[i])  # Create entanglement

        return circuit

    def benchmark_qkdpy_vs_qiskit(
        self, num_qubits: int = 100, num_trials: int = 10
    ) -> dict:
        """Benchmark QKDpy against Qiskit for BB84 protocol.

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

        # Benchmark Qiskit
        qiskit_times = []
        for _ in range(num_trials):
            start_time = time.time()
            alice_bits, bob_bits, matching_bases = self.simulate_bb84_with_qiskit(
                num_qubits=num_qubits, noise_model="depolarizing", noise_level=0.05
            )
            end_time = time.time()

            qiskit_times.append(end_time - start_time)

        # Calculate statistics
        qkdpy_avg = np.mean(qkdpy_times)
        qkdpy_std = np.std(qkdpy_times)
        qiskit_avg = np.mean(qiskit_times)
        qiskit_std = np.std(qiskit_times)

        return {
            "qkdpy_average_time": float(qkdpy_avg),
            "qkdpy_std_time": float(qkdpy_std),
            "qiskit_average_time": float(qiskit_avg),
            "qiskit_std_time": float(qiskit_std),
            "speedup_factor": (
                float(qkdpy_avg / qiskit_avg) if qiskit_avg > 0 else float("inf")
            ),
            "num_qubits": num_qubits,
            "num_trials": num_trials,
        }
