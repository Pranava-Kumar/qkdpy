"""Quantum error correction codes for protecting quantum information."""

import numpy as np

from ..core import Qubit
from ..core.gates import PauliX, PauliZ


class QuantumErrorCorrection:
    """Implementation of quantum error correction codes."""

    @staticmethod
    def shor_code_encode(qubit: Qubit) -> list[Qubit]:
        """Encode a single qubit using the 9-qubit Shor code.

        The Shor code can correct arbitrary single-qubit errors.

        Args:
            qubit: The qubit to encode

        Returns:
            List of 9 qubits representing the encoded state
        """
        # The Shor code encodes 1 qubit into 9 qubits
        # It can correct any single-qubit error (X, Y, Z, or combinations)

        # First, we create 9 qubits in the |0> state
        encoded_qubits = [Qubit.zero() for _ in range(9)]

        # For simulation purposes, we'll encode the logical state
        # In a real implementation, this would involve complex quantum operations
        alpha, beta = qubit.state[0], qubit.state[1]

        # The Shor code creates the state:
        # |ψ⟩_L = α|0⟩_L + β|1⟩_L
        # where |0⟩_L = (|000⟩ + |111⟩)(|000⟩ + |111⟩)(|000⟩ + |111⟩)/√8
        # and |1⟩_L = (|000⟩ - |111⟩)(|000⟩ - |111⟩)(|000⟩ - |111⟩)/√8

        # For simulation, we'll just store the original state information
        # and add some redundancy
        encoded_qubits[0] = Qubit(alpha, beta)  # Original qubit
        # Add redundancy (in a real implementation, these would be entangled)
        for i in range(1, 9):
            encoded_qubits[i] = Qubit(alpha, beta)

        return encoded_qubits

    @staticmethod
    def shor_code_decode(qubits: list[Qubit]) -> Qubit:
        """Decode a qubit from the 9-qubit Shor code.

        Args:
            qubits: List of 9 qubits encoded with Shor code

        Returns:
            Decoded qubit
        """
        if len(qubits) != 9:
            raise ValueError("Shor code requires exactly 9 qubits")

        # In a real implementation, this would involve syndrome measurement
        # and error correction operations

        # For simulation, we'll just return the first qubit
        # (in a real implementation, this would be more complex)
        return qubits[0]

    @staticmethod
    def steane_code_encode(qubit: Qubit) -> list[Qubit]:
        """Encode a single qubit using the 7-qubit Steane code.

        The Steane code is a [[7,1,3]] quantum error correction code
        that can correct arbitrary single-qubit errors.

        Args:
            qubit: The qubit to encode

        Returns:
            List of 7 qubits representing the encoded state
        """
        # The Steane code encodes 1 qubit into 7 qubits
        # It's based on the classical Hamming code

        # Create 7 qubits
        encoded_qubits = [Qubit.zero() for _ in range(7)]

        # Extract the state amplitudes
        alpha, beta = qubit.state[0], qubit.state[1]

        # For simulation, we'll store the original state information
        # and add redundancy
        encoded_qubits[0] = Qubit(alpha, beta)  # Original qubit
        # Add redundancy
        for i in range(1, 7):
            encoded_qubits[i] = Qubit(alpha, beta)

        return encoded_qubits

    @staticmethod
    def steane_code_decode(qubits: list[Qubit]) -> Qubit:
        """Decode a qubit from the 7-qubit Steane code.

        Args:
            qubits: List of 7 qubits encoded with Steane code

        Returns:
            Decoded qubit
        """
        if len(qubits) != 7:
            raise ValueError("Steane code requires exactly 7 qubits")

        # For simulation, return the first qubit
        return qubits[0]

    @staticmethod
    def five_qubit_code_encode(qubit: Qubit) -> list[Qubit]:
        """Encode a single qubit using the 5-qubit perfect code.

        The 5-qubit code is the smallest possible quantum error correction code
        that can correct arbitrary single-qubit errors.

        Args:
            qubit: The qubit to encode

        Returns:
            List of 5 qubits representing the encoded state
        """
        # The 5-qubit code encodes 1 qubit into 5 qubits

        # Create 5 qubits
        encoded_qubits = [Qubit.zero() for _ in range(5)]

        # Extract the state amplitudes
        alpha, beta = qubit.state[0], qubit.state[1]

        # For simulation, store the original state information
        encoded_qubits[0] = Qubit(alpha, beta)  # Original qubit
        # Add redundancy
        for i in range(1, 5):
            encoded_qubits[i] = Qubit(alpha, beta)

        return encoded_qubits

    @staticmethod
    def five_qubit_code_decode(qubits: list[Qubit]) -> Qubit:
        """Decode a qubit from the 5-qubit perfect code.

        Args:
            qubits: List of 5 qubits encoded with 5-qubit code

        Returns:
            Decoded qubit
        """
        if len(qubits) != 5:
            raise ValueError("5-qubit code requires exactly 5 qubits")

        # For simulation, return the first qubit
        return qubits[0]

    @staticmethod
    def detect_and_correct_error(
        qubits: list[Qubit], error_type: str = "X"
    ) -> list[Qubit]:
        """Detect and correct a single-qubit error using syndrome measurement.

        Args:
            qubits: List of qubits that may contain an error
            error_type: Type of error to simulate ("X", "Z", or "Y")

        Returns:
            Corrected qubits
        """
        # This is a simplified simulation of error detection and correction
        # In a real implementation, this would involve:
        # 1. Syndrome measurement using ancilla qubits
        # 2. Classical processing of syndrome results
        # 3. Application of corrective operations

        corrected_qubits = list(qubits)

        # For simulation, we'll randomly "detect" and "correct" an error
        if (
            len(qubits) > 0 and np.random.random() < 0.3
        ):  # 30% chance of detecting an error
            error_position = np.random.randint(0, len(qubits))

            # Apply the inverse error to correct it
            if error_type == "X":
                # Apply Pauli-X to correct bit-flip error
                gate = PauliX().matrix
                corrected_qubits[error_position].apply_gate(gate)
            elif error_type == "Z":
                # Apply Pauli-Z to correct phase-flip error
                gate = PauliZ().matrix
                corrected_qubits[error_position].apply_gate(gate)
            elif error_type == "Y":
                # Apply Pauli-Y to correct Y error
                # Y = iXZ, so we need to apply Y† = -iZX
                gate = np.array([[0, 1j], [-1j, 0]], dtype=complex)
                corrected_qubits[error_position].apply_gate(gate)

        return corrected_qubits

    @staticmethod
    def quantum_error_correction_simulation(
        initial_qubit: Qubit, code_type: str = "shor", error_probability: float = 0.1
    ) -> tuple[Qubit, bool]:
        """Simulate the complete quantum error correction process.

        Args:
            initial_qubit: The initial qubit to protect
            code_type: Type of error correction code ("shor", "steane", "five_qubit")
            error_probability: Probability of error occurring on each qubit

        Returns:
            Tuple of (decoded_qubit, success) where success indicates if the
            decoded qubit matches the initial qubit
        """
        # 1. Encode the qubit
        if code_type == "shor":
            encoded_qubits = QuantumErrorCorrection.shor_code_encode(initial_qubit)
        elif code_type == "steane":
            encoded_qubits = QuantumErrorCorrection.steane_code_encode(initial_qubit)
        elif code_type == "five_qubit":
            encoded_qubits = QuantumErrorCorrection.five_qubit_code_encode(
                initial_qubit
            )
        else:
            raise ValueError(f"Unknown code type: {code_type}")

        # 2. Simulate errors
        errored_qubits = []
        for qubit in encoded_qubits:
            if np.random.random() < error_probability:
                # Apply a random error
                error_type = np.random.choice(["X", "Z", "Y"])
                if error_type == "X":
                    qubit.apply_gate(PauliX().matrix)
                elif error_type == "Z":
                    qubit.apply_gate(PauliZ().matrix)
                elif error_type == "Y":
                    gate = np.array([[0, -1j], [1j, 0]], dtype=complex)
                    qubit.apply_gate(gate)
            errored_qubits.append(qubit)

        # 3. Detect and correct errors
        corrected_qubits = QuantumErrorCorrection.detect_and_correct_error(
            errored_qubits, np.random.choice(["X", "Z", "Y"])
        )

        # 4. Decode the qubit
        if code_type == "shor":
            decoded_qubit = QuantumErrorCorrection.shor_code_decode(corrected_qubits)
        elif code_type == "steane":
            decoded_qubit = QuantumErrorCorrection.steane_code_decode(corrected_qubits)
        elif code_type == "five_qubit":
            decoded_qubit = QuantumErrorCorrection.five_qubit_code_decode(
                corrected_qubits
            )

        # 5. Check if correction was successful
        # Compare the final state with the initial state
        fidelity = abs(np.dot(initial_qubit.state.conj(), decoded_qubit.state)) ** 2
        success = bool(fidelity > 0.95)  # Consider successful if fidelity > 95%

        return decoded_qubit, success

    @staticmethod
    def get_code_parameters(code_type: str) -> dict:
        """Get parameters for different quantum error correction codes.

        Args:
            code_type: Type of error correction code

        Returns:
            Dictionary with code parameters
        """
        parameters = {
            "shor": {
                "n": 9,  # Number of physical qubits
                "k": 1,  # Number of logical qubits
                "d": 3,  # Distance (can correct up to (d-1)/2 errors)
                "description": "9-qubit Shor code",
            },
            "steane": {"n": 7, "k": 1, "d": 3, "description": "7-qubit Steane code"},
            "five_qubit": {
                "n": 5,
                "k": 1,
                "d": 3,
                "description": "5-qubit perfect code",
            },
        }

        return parameters.get(code_type, {})

    @staticmethod
    def simulate_error_correction_performance(
        num_trials: int = 1000, code_type: str = "shor", error_probability: float = 0.1
    ) -> dict:
        """Simulate the performance of quantum error correction.

        Args:
            num_trials: Number of trials to run
            code_type: Type of error correction code
            error_probability: Probability of error on each qubit

        Returns:
            Dictionary with performance statistics
        """
        successes = 0
        fidelities = []

        for _ in range(num_trials):
            # Create a random initial qubit
            alpha = complex(np.random.randn() + 1j * np.random.randn())
            beta = complex(np.random.randn() + 1j * np.random.randn())
            # Normalize
            norm = np.sqrt(abs(alpha) ** 2 + abs(beta) ** 2)
            alpha /= norm
            beta /= norm

            initial_qubit = Qubit(alpha, beta)

            # Run error correction
            decoded_qubit, success = (
                QuantumErrorCorrection.quantum_error_correction_simulation(
                    initial_qubit, code_type, error_probability
                )
            )

            if success:
                successes += 1

            # Calculate fidelity
            fidelity = abs(np.dot(initial_qubit.state.conj(), decoded_qubit.state)) ** 2
            fidelities.append(fidelity)

        success_rate = successes / num_trials
        avg_fidelity = np.mean(fidelities)
        std_fidelity = np.std(fidelities)

        return {
            "success_rate": float(success_rate),
            "average_fidelity": float(avg_fidelity),
            "fidelity_std": float(std_fidelity),
            "num_trials": num_trials,
            "code_type": code_type,
            "error_probability": error_probability,
        }
