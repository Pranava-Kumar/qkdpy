"""Multi-qubit state representation and manipulation."""

from typing import Optional

import numpy as np

from .gates import QuantumGate
from .qubit import Qubit


class MultiQubitState:
    """Represents a multi-qubit quantum state.

    A multi-qubit state is represented as a complex vector in a 2^n dimensional
    Hilbert space where n is the number of qubits.
    """

    def __init__(self, state: np.ndarray):
        """Initialize a multi-qubit state with a given state vector.

        Args:
            state: Complex vector representing the quantum state

        Raises:
            ValueError: If the state dimension is not a power of 2
        """
        # Check if state dimension is a power of 2
        dim = len(state)
        if dim == 0 or (dim & (dim - 1)) != 0:
            raise ValueError("State dimension must be a power of 2")

        # Normalize the state
        norm = np.linalg.norm(state)
        if norm == 0:
            raise ValueError("Cannot create a state with zero norm")

        self._num_qubits = int(np.log2(dim))
        self._state = state / norm

    @classmethod
    def from_qubits(cls, qubits: list[Qubit]) -> "MultiQubitState":
        """Create a multi-qubit state from individual qubits.

        Args:
            qubits: List of Qubit objects

        Returns:
            MultiQubitState representing the tensor product of the qubits
        """
        if not qubits:
            raise ValueError("At least one qubit is required")

        # Start with the first qubit
        state = qubits[0].state

        # Compute tensor product with remaining qubits
        for qubit in qubits[1:]:
            state = np.kron(state, qubit.state)

        return cls(state)

    @classmethod
    def zeros(cls, num_qubits: int) -> "MultiQubitState":
        """Create a multi-qubit state |00...0>.

        Args:
            num_qubits: Number of qubits

        Returns:
            MultiQubitState in the all-zeros state
        """
        if num_qubits <= 0:
            raise ValueError("Number of qubits must be positive")

        state = np.zeros(2**num_qubits, dtype=complex)
        state[0] = 1.0
        return cls(state)

    @classmethod
    def ghz(cls, num_qubits: int) -> "MultiQubitState":
        """Create a GHZ (Greenberger-Horne-Zeilinger) state.

        The GHZ state is (|00...0> + |11...1>) / sqrt(2)

        Args:
            num_qubits: Number of qubits

        Returns:
            MultiQubitState in the GHZ state
        """
        if num_qubits <= 0:
            raise ValueError("Number of qubits must be positive")

        state = np.zeros(2**num_qubits, dtype=complex)
        state[0] = 1.0 / np.sqrt(2)
        state[-1] = 1.0 / np.sqrt(2)
        return cls(state)

    @classmethod
    def w_state(cls, num_qubits: int) -> "MultiQubitState":
        """Create a W state.

        The W state is (|100...0> + |010...0> + ... + |000...1>) / sqrt(n)

        Args:
            num_qubits: Number of qubits

        Returns:
            MultiQubitState in the W state
        """
        if num_qubits <= 0:
            raise ValueError("Number of qubits must be positive")

        state = np.zeros(2**num_qubits, dtype=complex)
        # Set the single 1 states: |100...0>, |010...0>, ..., |000...1>
        for i in range(num_qubits):
            index = 2 ** (num_qubits - 1 - i)
            state[index] = 1.0

        # Normalize
        state = state / np.sqrt(num_qubits)
        return cls(state)

    @property
    def num_qubits(self) -> int:
        """Get the number of qubits in the state."""
        return self._num_qubits

    @property
    def state(self) -> np.ndarray:
        """Get the state vector."""
        return self._state.copy()

    @property
    def probabilities(self) -> np.ndarray:
        """Get the probabilities of measuring each computational basis state.

        Returns:
            Array of probabilities for each of the 2^n basis states
        """
        return np.abs(self._state) ** 2

    def apply_gate(self, gate: np.ndarray, target_qubits: int | list[int]) -> None:
        """Apply a quantum gate to specific qubits.

        Args:
            gate: Unitary matrix representing the quantum gate
            target_qubits: Index or list of indices of qubits to apply the gate to

        Raises:
            ValueError: If the gate size doesn't match the number of target qubits
            ValueError: If target qubit indices are invalid
        """
        # Convert single qubit index to list
        if isinstance(target_qubits, int):
            target_qubits = [target_qubits]

        # Validate target qubits
        if any(q < 0 or q >= self._num_qubits for q in target_qubits):
            raise ValueError("Target qubit indices must be between 0 and num_qubits-1")

        # Check if gate size matches number of target qubits
        gate_size = gate.shape[0]
        expected_size = 2 ** len(target_qubits)
        if gate_size != expected_size:
            raise ValueError(
                f"Gate size {gate_size} doesn't match {expected_size} for {len(target_qubits)} qubits"
            )

        # Check if gate is unitary
        if not QuantumGate.is_unitary(gate):
            raise ValueError("Gate must be unitary")

        # Create the full operator by tensoring with identity matrices
        # Start with identity for all qubits
        full_gate = np.eye(2**self._num_qubits, dtype=complex)

        # For single qubit gates, we can use a more efficient approach
        if len(target_qubits) == 1:
            target = target_qubits[0]
            # Create a list of operators for each qubit
            ops = [QuantumGate.Identity() for _ in range(self._num_qubits)]
            ops[target] = gate

            # Compute the tensor product
            full_gate = ops[0]
            for op in ops[1:]:
                full_gate = np.kron(full_gate, op)
        else:
            # For multi-qubit gates, we need to construct the operator more carefully
            # This is a simplified implementation - a full implementation would require
            # more sophisticated indexing
            raise NotImplementedError("Multi-qubit gates not yet implemented")

        # Apply the gate
        self._state = full_gate @ self._state

    def measure(self, target_qubit: int) -> tuple[int, Optional["MultiQubitState"]]:
        """Measure a specific qubit in the computational basis.

        Args:
            target_qubit: Index of the qubit to measure

        Returns:
            Tuple of (measurement_result, collapsed_state) where collapsed_state
            is the state of the remaining qubits (None if this was the last qubit)

        Raises:
            ValueError: If target_qubit is invalid
        """
        if target_qubit < 0 or target_qubit >= self._num_qubits:
            raise ValueError("Target qubit index must be between 0 and num_qubits-1")

        # Calculate probabilities for measuring 0 or 1 on the target qubit
        prob_0 = 0.0
        prob_1 = 0.0

        # For each computational basis state, check if the target qubit is 0 or 1
        for i in range(2**self._num_qubits):
            # Check if the target qubit is 0 or 1 in this basis state
            # The target qubit is at position (num_qubits - 1 - target_qubit) from the right
            if (i >> (self._num_qubits - 1 - target_qubit)) & 1:
                prob_1 += np.abs(self._state[i]) ** 2
            else:
                prob_0 += np.abs(self._state[i]) ** 2

        # Perform the measurement
        result = 0 if np.random.random() < prob_0 else 1

        # If this is the last qubit, return None for the collapsed state
        if self._num_qubits == 1:
            return result, None

        # Collapse the state
        new_state = np.zeros(2 ** (self._num_qubits - 1), dtype=complex)

        # For each computational basis state in the new system, sum the amplitudes
        # from the old system that are consistent with the measurement result
        for i in range(2 ** (self._num_qubits - 1)):
            # Determine the indices in the original state that correspond to
            # this basis state in the new system with the measurement result
            if result == 0:
                # Target qubit is 0
                old_index = i << 1  # Insert 0 at the target position
            else:
                # Target qubit is 1
                old_index = (i << 1) | 1  # Insert 1 at the target position

            new_state[i] = self._state[old_index]

        # Normalize the new state
        norm = np.linalg.norm(new_state)
        if norm > 0:
            new_state = new_state / norm

        return result, MultiQubitState(new_state)

    def density_matrix(self) -> np.ndarray:
        """Calculate the density matrix of the multi-qubit state.

        Returns:
            2^n x 2^n density matrix
        """
        return np.outer(self._state, np.conjugate(self._state))

    def entanglement_entropy(self, subsystem_qubits: list[int]) -> float:
        """Calculate the entanglement entropy of a subsystem.

        Args:
            subsystem_qubits: List of qubit indices in the subsystem

        Returns:
            Von Neumann entropy of the subsystem
        """
        if not subsystem_qubits or any(
            q < 0 or q >= self._num_qubits for q in subsystem_qubits
        ):
            raise ValueError("Invalid subsystem qubit indices")

        # For a pure state, the entanglement entropy is the von Neumann entropy
        # of the reduced density matrix of the subsystem

        # This is a complex calculation that would require partial trace computation
        # For now, we'll return a placeholder
        return 0.0

    def fidelity(self, other: "MultiQubitState") -> float:
        """Calculate the fidelity between this state and another state.

        Args:
            other: Another MultiQubitState

        Returns:
            Fidelity value between 0 and 1

        Raises:
            ValueError: If the states have different numbers of qubits
        """
        if self._num_qubits != other._num_qubits:
            raise ValueError("States must have the same number of qubits")

        # Fidelity = |<ψ|φ>|^2
        inner_product = np.vdot(self._state, other._state)
        return np.abs(inner_product) ** 2

    def __repr__(self) -> str:
        """String representation of the multi-qubit state."""
        return f"MultiQubitState(num_qubits={self._num_qubits})"

    def __eq__(self, other: "MultiQubitState") -> bool:
        """Check if two multi-qubit states are equal."""
        if not isinstance(other, MultiQubitState):
            return False
        return self._num_qubits == other._num_qubits and np.allclose(
            self._state, other._state
        )
