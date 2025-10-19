"""Qudit class for representing and manipulating d-dimensional quantum systems."""

import numpy as np


class Qudit:
    """Represents a d-dimensional quantum system (qudit) with state manipulation capabilities.

    A qudit state is represented as a complex vector in a d-dimensional Hilbert space:
    |ψ> = Σ α_i |i> where i ∈ {0, 1, ..., d-1} and Σ |α_i|² = 1
    """

    def __init__(self, state: np.ndarray, dimension: int = 2):
        """Initialize a qudit with given state vector.

        Args:
            state: Complex state vector of length 'dimension'
            dimension: Dimension of the qudit system

        Raises:
            ValueError: If the state is not properly normalized or has incorrect length
        """
        if len(state) != dimension:
            raise ValueError(
                f"State vector length ({len(state)}) must match dimension ({dimension})"
            )

        # Normalize the state vector
        norm = np.sqrt(np.sum(np.abs(state) ** 2))
        if norm == 0:
            raise ValueError("Cannot create a qudit with zero norm")

        self._state = state / norm
        self.dimension = dimension

    @classmethod
    def computational_basis(cls, level: int, dimension: int) -> "Qudit":
        """Create a qudit in a computational basis state |level>.

        Args:
            level: Computational basis level (0 to dimension-1)
            dimension: Dimension of the qudit system

        Returns:
            Qudit in the specified computational basis state
        """
        if level < 0 or level >= dimension:
            raise ValueError(f"Level must be between 0 and {dimension-1}")

        state = np.zeros(dimension, dtype=complex)
        state[level] = 1.0
        return cls(state, dimension)

    @classmethod
    def uniform_superposition(cls, dimension: int) -> "Qudit":
        """Create a qudit in a uniform superposition state.

        Args:
            dimension: Dimension of the qudit system

        Returns:
            Qudit in uniform superposition state
        """
        state = np.ones(dimension, dtype=complex) / np.sqrt(dimension)
        return cls(state, dimension)

    @classmethod
    def fourier_basis(cls, level: int, dimension: int) -> "Qudit":
        """Create a qudit in a Fourier basis state.

        Args:
            level: Fourier basis level (0 to dimension-1)
            dimension: Dimension of the qudit system

        Returns:
            Qudit in the specified Fourier basis state
        """
        if level < 0 or level >= dimension:
            raise ValueError(f"Level must be between 0 and {dimension-1}")

        state = np.zeros(dimension, dtype=complex)
        for j in range(dimension):
            state[j] = np.exp(2j * np.pi * level * j / dimension) / np.sqrt(dimension)

        return cls(state, dimension)

    @property
    def state(self) -> np.ndarray:
        """Get the state vector of the qudit."""
        return self._state.copy()

    @property
    def probabilities(self) -> list[float]:
        """Get the probabilities of measuring each computational basis state.

        Returns:
            List of probabilities for each computational basis state
        """
        return [float(abs(coeff) ** 2) for coeff in self._state]

    def apply_unitary(self, operator: np.ndarray) -> None:
        """Apply a unitary operator to the qudit.

        Args:
            operator: d×d unitary matrix representing the quantum operation

        Raises:
            ValueError: If the operator is not a valid d×d unitary matrix
        """
        if operator.shape != (self.dimension, self.dimension):
            raise ValueError(
                f"Operator must be a {self.dimension}×{self.dimension} matrix"
            )

        # Check if operator is unitary (U * U† = I)
        identity = np.eye(self.dimension, dtype=complex)
        if not np.allclose(operator @ operator.conj().T, identity, atol=1e-10):
            raise ValueError("Operator must be unitary")

        self._state = operator @ self._state

    def measure(self, basis_matrix: np.ndarray = None) -> int:
        """Measure the qudit in the specified basis.

        Args:
            basis_matrix: d×d unitary matrix defining the measurement basis.
                         If None, measures in computational basis.

        Returns:
            Measurement result (integer from 0 to dimension-1)
        """
        if basis_matrix is None:
            # Measure in computational basis
            probabilities = self.probabilities
            # Sample according to probabilities
            result = np.random.choice(self.dimension, p=probabilities)
        else:
            # Transform to the measurement basis
            if basis_matrix.shape != (self.dimension, self.dimension):
                raise ValueError(
                    f"Basis matrix must be {self.dimension}×{self.dimension}"
                )

            # Apply inverse of the basis transformation to the state
            transformed_state = basis_matrix.conj().T @ self._state
            probabilities = [float(abs(coeff) ** 2) for coeff in transformed_state]

            # Sample according to probabilities
            result = np.random.choice(self.dimension, p=probabilities)

        return result

    def measure_computational(self) -> int:
        """Measure the qudit in the computational basis.

        Returns:
            Measurement result (integer from 0 to dimension-1)
        """
        return self.measure(None)

    def measure_fourier(self) -> int:
        """Measure the qudit in the Fourier basis.

        Returns:
            Measurement result (integer from 0 to dimension-1)
        """
        # Fourier basis transformation matrix
        fourier_matrix = np.zeros((self.dimension, self.dimension), dtype=complex)
        for j in range(self.dimension):
            for k in range(self.dimension):
                fourier_matrix[j, k] = np.exp(
                    2j * np.pi * j * k / self.dimension
                ) / np.sqrt(self.dimension)

        return self.measure(fourier_matrix)

    def collapse_state(self, result: int, basis_matrix: np.ndarray = None) -> None:
        """Collapse the qudit's state to a specific measurement result.

        Args:
            result: The measurement result (0 to dimension-1)
            basis_matrix: The measurement basis matrix used, or None for computational basis
        """
        if result < 0 or result >= self.dimension:
            raise ValueError(f"Result must be between 0 and {self.dimension-1}")

        if basis_matrix is None:
            # Collapses to computational basis state |result>
            new_state = np.zeros(self.dimension, dtype=complex)
            new_state[result] = 1.0
            self._state = new_state
        else:
            # Get the basis vector corresponding to the measurement result
            basis_vectors = (
                basis_matrix.conj().T
            )  # Columns of the conjugate transpose are the basis vectors
            new_state = basis_vectors[:, result]
            self._state = new_state

    def fidelity(self, other_qudit: "Qudit") -> float:
        """Calculate the fidelity between this qudit and another.

        Args:
            other_qudit: Another qudit to calculate fidelity with

        Returns:
            Fidelity value between 0 and 1
        """
        if self.dimension != other_qudit.dimension:
            raise ValueError(
                "Qudits must have the same dimension for fidelity calculation"
            )

        overlap = abs(np.vdot(self._state, other_qudit._state)) ** 2
        return float(overlap)

    def tensor_product(self, other: "Qudit") -> "Qudit":
        """Create the tensor product of this qudit with another.

        Args:
            other: Another qudit to tensor with this one

        Returns:
            New qudit representing the tensor product (has dimension self.dimension * other.dimension)
        """
        new_state = np.kron(self._state, other._state)
        return Qudit(new_state, self.dimension * other.dimension)

    def partial_trace(self, subsystem_index: int, subsystem_dimension: int) -> "Qudit":
        """Perform partial trace over a subsystem.

        Args:
            subsystem_index: Index of the subsystem to trace out (0 or 1 for bipartite systems)
            subsystem_dimension: Dimension of the subsystem to trace out

        Returns:
            Qudit representing the remaining subsystem
        """
        # This is a simplified implementation for a bipartite system
        # More complex implementation would be needed for multipartite systems
        if self.dimension % subsystem_dimension != 0:
            raise ValueError(
                "System dimension must be divisible by subsystem dimension"
            )

        # Reshape the state vector to a matrix
        total_subsystem_dim = self.dimension // subsystem_dimension
        if subsystem_index == 0:
            # Trace out first subsystem, keep second
            reshaped_state = self._state.reshape(
                subsystem_dimension, total_subsystem_dim
            )
            reduced_state = np.zeros(total_subsystem_dim, dtype=complex)
            for i in range(total_subsystem_dim):
                for j in range(subsystem_dimension):
                    reduced_state[i] += reshaped_state[j, i]
        else:
            # Trace out second subsystem, keep first
            reshaped_state = self._state.reshape(
                total_subsystem_dim, subsystem_dimension
            )
            reduced_state = np.zeros(total_subsystem_dim, dtype=complex)
            for i in range(total_subsystem_dim):
                for j in range(subsystem_dimension):
                    reduced_state[i] += reshaped_state[i, j]

        return Qudit(reduced_state, total_subsystem_dim)

    def __repr__(self) -> str:
        """String representation of the qudit."""
        state_str = ", ".join([f"{coeff:.3f}" for coeff in self._state])
        return f"Qudit(dimension={self.dimension}, state=[{state_str}])"

    def __eq__(self, other: object) -> bool:
        """Check if two qudits have the same state."""
        if not isinstance(other, Qudit):
            return NotImplemented

        if self.dimension != other.dimension:
            return False

        return np.allclose(self._state, other._state)
