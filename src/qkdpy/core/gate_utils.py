import math

import numpy as np


class GateUtils:
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
            return np.array([[1, 0], [0, 1]], dtype=complex)  # Identity matrix
        elif basis == "hadamard":
            return np.array([[1, 1], [1, -1]], dtype=complex) / math.sqrt(
                2
            )  # Hadamard matrix
        elif basis == "circular":
            return np.array([[1, 1], [1j, -1j]], dtype=complex) / math.sqrt(2)
        else:
            raise ValueError("Basis must be 'computational', 'hadamard', or 'circular'")

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
