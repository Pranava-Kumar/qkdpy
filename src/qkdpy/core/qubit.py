"""Qubit class for representing and manipulating quantum bits."""

import math

import numpy as np


class Qubit:
    """Represents a single qubit with state manipulation capabilities.

    A qubit state is represented as a complex vector [alpha, beta] where:
    |psi> = alpha|0> + beta|1>
    and |alpha|^2 + |beta|^2 = 1
    """

    def __init__(self, alpha: complex = 1 + 0j, beta: complex = 0 + 0j):
        """Initialize a qubit with given amplitudes.

        Args:
            alpha: Amplitude for |0> state
            beta: Amplitude for |1> state

        Raises:
            ValueError: If the state is not normalized

        """
        # Normalize the state
        norm = math.sqrt(abs(alpha) ** 2 + abs(beta) ** 2)
        if norm == 0:
            raise ValueError("Cannot create a qubit with zero norm")

        self._state = np.array([alpha / norm, beta / norm], dtype=complex)

    @classmethod
    def zero(cls) -> "Qubit":
        """Create a qubit in the |0> state."""
        return cls(1, 0)

    @classmethod
    def one(cls) -> "Qubit":
        """Create a qubit in the |1> state."""
        return cls(0, 1)

    @classmethod
    def plus(cls) -> "Qubit":
        """Create a qubit in the |+> state (Hadamard applied to |0>)."""
        return cls(1 / math.sqrt(2), 1 / math.sqrt(2))

    @classmethod
    def minus(cls) -> "Qubit":
        """Create a qubit in the |-> state (Hadamard applied to |1>)."""
        return cls(1 / math.sqrt(2), -1 / math.sqrt(2))

    @property
    def state(self) -> np.ndarray:
        """Get the state vector of the qubit."""
        return self._state.copy()

    @property
    def probabilities(self) -> tuple[float, float]:
        """Get the probabilities of measuring |0> and |1>.

        Returns:
            Tuple of (prob_0, prob_1)

        """
        prob_0 = abs(self._state[0]) ** 2
        prob_1 = abs(self._state[1]) ** 2
        return (prob_0, prob_1)

    def apply_gate(self, gate: np.ndarray) -> None:
        """Apply a quantum gate to the qubit.

        Args:
            gate: 2x2 unitary matrix representing the quantum gate

        Raises:
            ValueError: If the gate is not a valid 2x2 unitary matrix

        """
        if gate.shape != (2, 2):
            raise ValueError("Gate must be a 2x2 matrix")

        # Check if gate is unitary (U * U† = I)
        identity = np.eye(2)
        if not np.allclose(gate @ gate.conj().T, identity, atol=1e-10):
            raise ValueError("Gate must be unitary")

        self._state = gate @ self._state

    def measure(self, basis: str = "computational") -> int:
        """Measure the qubit in the specified basis.

        Args:
            basis: 'computational' (Z), 'hadamard' (X), or 'circular' (Y)

        Returns:
            Measurement result (0 or 1)

        """
        if basis == "computational":
            # Standard computational basis measurement
            prob_0, prob_1 = self.probabilities
            result = 0 if np.random.random() < prob_0 else 1

        elif basis == "hadamard":
            # Hadamard basis measurement
            # Transform to Hadamard basis, measure, then transform back
            h_gate = np.array([[1, 1], [1, -1]], dtype=complex) / math.sqrt(2)
            temp_qubit = Qubit(
                self._state[0], self._state[1]
            )  # Create a temporary qubit for measurement
            temp_qubit.apply_gate(h_gate)
            prob_0, prob_1 = temp_qubit.probabilities
            result = 0 if np.random.random() < prob_0 else 1

        elif basis == "circular":
            # Circular basis measurement
            # Transform to circular basis, measure, then transform back
            circ_gate = np.array([[1, -1j], [1, 1j]], dtype=complex) / math.sqrt(2)
            temp_qubit = Qubit(
                self._state[0], self._state[1]
            )  # Create a temporary qubit for measurement
            temp_qubit.apply_gate(circ_gate)
            prob_0, prob_1 = temp_qubit.probabilities
            result = 0 if np.random.random() < prob_0 else 1
        else:
            raise ValueError("Basis must be 'computational', 'hadamard', or 'circular'")

        return result

    def collapse_state(self, result: int, basis: str = "computational") -> None:
        """Collapse the qubit's state to the measured result in the specified basis.

        Args:
            result: The classical measurement result (0 or 1).
            basis: 'computational' (Z), 'hadamard' (X), or 'circular' (Y).
        """
        if basis == "computational":
            if result == 0:
                self._state = np.array([1, 0], dtype=complex)
            else:
                self._state = np.array([0, 1], dtype=complex)
        elif basis == "hadamard":
            if result == 0:
                self._state = np.array([1, 1], dtype=complex) / math.sqrt(2)
            else:
                self._state = np.array([1, -1], dtype=complex) / math.sqrt(2)
        elif basis == "circular":
            if result == 0:
                self._state = np.array([1, 1j], dtype=complex) / math.sqrt(2)
            else:
                self._state = np.array([1, -1j], dtype=complex) / math.sqrt(2)
        else:
            raise ValueError("Basis must be 'computational', 'hadamard', or 'circular'")

    def density_matrix(self) -> np.ndarray:
        """Calculate the density matrix of the qubit.

        Returns:
            2x2 density matrix

        """
        return np.outer(self._state, np.conjugate(self._state))

    def bloch_vector(self) -> tuple[float, float, float]:
        """Calculate the Bloch vector representation of the qubit.

        Returns:
            Tuple of (x, y, z) coordinates on the Bloch sphere

        """
        # Pauli matrices
        sigma_x = np.array([[0, 1], [1, 0]], dtype=complex)
        sigma_y = np.array([[0, -1j], [1j, 0]], dtype=complex)
        sigma_z = np.array([[1, 0], [0, -1]], dtype=complex)

        # Density matrix
        rho = self.density_matrix()

        # Calculate expectation values
        x = np.real(np.trace(rho @ sigma_x))
        y = np.real(np.trace(rho @ sigma_y))
        z = np.real(np.trace(rho @ sigma_z))

        return (x, y, z)

    def __repr__(self) -> str:
        """String representation of the qubit."""
        alpha, beta = self._state
        return f"Qubit({alpha:.3f}|0> + {beta:.3f}|1>)"

    def __eq__(self, other: "Qubit") -> bool:
        """Check if two qubits have the same state."""
        if not isinstance(other, Qubit):
            return False
        return np.allclose(self._state, other._state)
