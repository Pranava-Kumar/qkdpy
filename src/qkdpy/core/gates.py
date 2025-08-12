"""Quantum gate implementations for qubit manipulation."""

import math

import numpy as np


class QuantumGate:
    """A collection of common quantum gates for qubit manipulation.

    This class provides static methods for various quantum gates that can be
    applied to qubits.
    """

    # Pauli gates
    @staticmethod
    def Identity() -> np.ndarray:
        """Identity gate."""
        return np.array([[1, 0], [0, 1]], dtype=complex)

    @staticmethod
    def X() -> np.ndarray:
        """Pauli-X gate (bit flip)."""
        return np.array([[0, 1], [1, 0]], dtype=complex)

    @staticmethod
    def Y() -> np.ndarray:
        """Pauli-Y gate."""
        return np.array([[0, -1j], [1j, 0]], dtype=complex)

    @staticmethod
    def Z() -> np.ndarray:
        """Pauli-Z gate (phase flip)."""
        return np.array([[1, 0], [0, -1]], dtype=complex)

    # Clifford gates
    @staticmethod
    def H() -> np.ndarray:
        """Hadamard gate."""
        return np.array([[1, 1], [1, -1]], dtype=complex) / math.sqrt(2)

    @staticmethod
    def S() -> np.ndarray:
        """Phase gate (sqrt(Z))."""
        return np.array([[1, 0], [0, 1j]], dtype=complex)

    @staticmethod
    def S_dag() -> np.ndarray:
        """Adjoint of phase gate."""
        return np.array([[1, 0], [0, -1j]], dtype=complex)

    @staticmethod
    def T() -> np.ndarray:
        """π/8 gate (sqrt(S))."""
        return np.array([[1, 0], [0, np.exp(1j * np.pi / 4)]], dtype=complex)

    @staticmethod
    def T_dag() -> np.ndarray:
        """Adjoint of π/8 gate."""
        return np.array([[1, 0], [0, np.exp(-1j * np.pi / 4)]], dtype=complex)

    # Rotation gates
    @staticmethod
    def Rx(theta: float) -> np.ndarray:
        """Rotation around X-axis.

        Args:
            theta: Rotation angle in radians

        Returns:
            2x2 unitary matrix for X rotation

        """
        return np.array(
            [
                [np.cos(theta / 2), -1j * np.sin(theta / 2)],
                [-1j * np.sin(theta / 2), np.cos(theta / 2)],
            ],
            dtype=complex,
        )

    @staticmethod
    def Ry(theta: float) -> np.ndarray:
        """Rotation around Y-axis.

        Args:
            theta: Rotation angle in radians

        Returns:
            2x2 unitary matrix for Y rotation

        """
        return np.array(
            [
                [np.cos(theta / 2), -np.sin(theta / 2)],
                [np.sin(theta / 2), np.cos(theta / 2)],
            ],
            dtype=complex,
        )

    @staticmethod
    def Rz(theta: float) -> np.ndarray:
        """Rotation around Z-axis.

        Args:
            theta: Rotation angle in radians

        Returns:
            2x2 unitary matrix for Z rotation

        """
        return np.array(
            [[np.exp(-1j * theta / 2), 0], [0, np.exp(1j * theta / 2)]], dtype=complex
        )

    # Two-qubit gates
    @staticmethod
    def CNOT() -> np.ndarray:
        """Controlled-NOT gate.

        Returns:
            4x4 unitary matrix for CNOT

        """
        return np.array(
            [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]], dtype=complex
        )

    @staticmethod
    def CZ() -> np.ndarray:
        """Controlled-Z gate.

        Returns:
            4x4 unitary matrix for CZ

        """
        return np.array(
            [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, -1]], dtype=complex
        )

    @staticmethod
    def SWAP() -> np.ndarray:
        """SWAP gate.

        Returns:
            4x4 unitary matrix for SWAP

        """
        return np.array(
            [[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], dtype=complex
        )

    # Special gates for QKD
    @staticmethod
    def basis_switch(basis: str) -> np.ndarray:
        """Get a gate to switch to a specific measurement basis.

        Args:
            basis: 'computational', 'hadamard', or 'circular'

        Returns:
            2x2 unitary matrix for basis switch

        Raises:
            ValueError: If the basis is not recognized

        """
        if basis == "computational":
            return QuantumGate.I()
        elif basis == "hadamard":
            return QuantumGate.H()
        elif basis == "circular":
            return np.array([[1, 1], [1j, -1j]], dtype=complex) / math.sqrt(2)
        else:
            raise ValueError("Basis must be 'computational', 'hadamard', or 'circular'")

    # Custom gates
    @staticmethod
    def random_unitary() -> np.ndarray:
        """Generate a random unitary matrix.

        Returns:
            2x2 random unitary matrix

        """
        # Generate a random complex matrix
        a = np.random.randn(2, 2) + 1j * np.random.randn(2, 2)

        # Perform QR decomposition to get a unitary matrix
        q, _ = np.linalg.qr(a)

        return q

    @staticmethod
    def unitary_from_angles(theta: float, phi: float, lam: float) -> np.ndarray:
        """Create a unitary matrix from Euler angles.

        Args:
            theta: First rotation angle
            phi: Second rotation angle
            lam: Third rotation angle

        Returns:
            2x2 unitary matrix

        """
        return np.array(
            [
                [np.cos(theta / 2), -np.exp(1j * lam) * np.sin(theta / 2)],
                [
                    np.exp(1j * phi) * np.sin(theta / 2),
                    np.exp(1j * (phi + lam)) * np.cos(theta / 2),
                ],
            ],
            dtype=complex,
        )

    # Gate composition
    @staticmethod
    def sequence(*gates: np.ndarray) -> np.ndarray:
        """Compose multiple gates in sequence.

        Args:
            *gates: Variable number of gates to apply in sequence

        Returns:
            Combined unitary matrix

        """
        result = gates[0]
        for gate in gates[1:]:
            result = gate @ result
        return result

    @staticmethod
    def tensor_product(*gates: np.ndarray) -> np.ndarray:
        """Compute the tensor product of multiple gates.

        Args:
            *gates: Variable number of gates

        Returns:
            Tensor product of all gates

        """
        result = gates[0]
        for gate in gates[1:]:
            result = np.kron(result, gate)
        return result

    # Gate properties
    @staticmethod
    def is_unitary(gate: np.ndarray, tol: float = 1e-10) -> bool:
        """Check if a matrix is unitary.

        Args:
            gate: Matrix to check
            tol: Tolerance for the unitarity check

        Returns:
            True if the matrix is unitary, False otherwise

        """
        n, m = gate.shape
        if n != m:
            return False

        # Check if U * U† = I
        identity = np.eye(n)
        return np.allclose(gate @ gate.conj().T, identity, atol=tol)

    @staticmethod
    def is_hermitian(gate: np.ndarray, tol: float = 1e-10) -> bool:
        """Check if a matrix is Hermitian.

        Args:
            gate: Matrix to check
            tol: Tolerance for the Hermitian check

        Returns:
            True if the matrix is Hermitian, False otherwise

        """
        n, m = gate.shape
        if n != m:
            return False

        # Check if A = A†
        return np.allclose(gate, gate.conj().T, atol=tol)
