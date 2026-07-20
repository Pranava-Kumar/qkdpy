"""Density matrix representation for mixed quantum states.

A density matrix ρ represents a quantum state (pure or mixed) as a positive
semidefinite, trace-1 operator. Pure states satisfy ρ = |ψ⟩⟨ψ| and Tr(ρ²) = 1;
mixed states have Tr(ρ²) < 1.

This module enables simulation of:
- Decoherence and noise as CPTP maps
- Partial trace of entangled systems
- Channel tomography and process fidelity
- Proper treatment of thermal and depolarizing channels
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from .qubit import Qubit
from .qudit import Qudit

if TYPE_CHECKING:
    from collections.abc import Sequence


class DensityMatrix:
    """Density matrix representation of a quantum state.

    Attributes:
        matrix: The density matrix as a 2D complex numpy array.
        dimension: Dimension of the Hilbert space.
    """

    def __init__(self, matrix: np.ndarray) -> None:
        """Initialize a density matrix.

        Args:
            matrix: A square complex matrix representing the density operator.

        Raises:
            ValueError: If the matrix is not square, not Hermitian, not
                positive semidefinite, or does not have trace 1.
        """
        if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
            raise ValueError("Density matrix must be square")

        # Check Hermiticity
        if not np.allclose(matrix, matrix.conj().T, atol=1e-10):
            raise ValueError("Density matrix must be Hermitian")

        # Check positive semidefiniteness
        eigenvalues = np.linalg.eigvalsh(matrix)
        if np.any(eigenvalues < -1e-10):
            raise ValueError("Density matrix must be positive semidefinite")

        # Check trace 1
        trace = np.trace(matrix)
        if not np.isclose(trace, 1.0, atol=1e-10):
            raise ValueError(f"Density matrix must have trace 1, got {trace}")

        self.matrix = matrix.astype(complex)
        self.dimension = matrix.shape[0]

    @classmethod
    def from_pure(cls, state: Qubit | Qudit | np.ndarray) -> DensityMatrix:
        """Create a density matrix from a pure state.

        Args:
            state: A Qubit, Qudit, or statevector as numpy array.

        Returns:
            Density matrix ρ = |ψ⟩⟨ψ|.
        """
        if isinstance(state, Qubit):
            psi = state.state
        elif isinstance(state, Qudit):
            psi = state.state
        else:
            psi = np.asarray(state, dtype=complex)

        if psi.ndim != 1:
            raise ValueError("State must be a 1D vector")

        return cls(np.outer(psi, psi.conj()))

    @classmethod
    def maximally_mixed(cls, dimension: int) -> DensityMatrix:
        """Create the maximally mixed state I/d.

        Args:
            dimension: Dimension of the Hilbert space.

        Returns:
            Density matrix ρ = I/d.
        """
        return cls(np.eye(dimension, dtype=complex) / dimension)

    @classmethod
    def from_probabilities(
        cls,
        states: Sequence[Qubit | Qudit | np.ndarray],
        probabilities: Sequence[float],
    ) -> DensityMatrix:
        """Create a mixed state from an ensemble of pure states.

        Args:
            states: List of pure states (Qubit, Qudit, or statevectors).
            probabilities: List of probabilities (must sum to 1).

        Returns:
            Density matrix ρ = Σ pᵢ |ψᵢ⟩⟨ψᵢ|.

        Raises:
            ValueError: If probabilities don't sum to 1 or states have
                different dimensions.
        """
        if not np.isclose(sum(probabilities), 1.0, atol=1e-10):
            raise ValueError("Probabilities must sum to 1")

        matrices = []
        for state, prob in zip(states, probabilities, strict=True):
            rho_i = cls.from_pure(state)
            matrices.append(prob * rho_i.matrix)

        return cls(sum(matrices))

    def purity(self) -> float:
        """Compute the purity Tr(ρ²).

        Returns:
            Purity in [1/d, 1], where d is the dimension. Pure states have
            purity 1; the maximally mixed state has purity 1/d.
        """
        return float(np.real(np.trace(self.matrix @ self.matrix)))

    def entropy(self) -> float:
        """Compute the von Neumann entropy S(ρ) = -Tr(ρ log₂ ρ).

        Returns:
            Entropy in bits (base-2 logarithm). Zero for pure states,
            log₂(d) for the maximally mixed state.
        """
        eigenvalues = np.linalg.eigvalsh(self.matrix)
        # Filter out near-zero eigenvalues to avoid log(0)
        eigenvalues = eigenvalues[eigenvalues > 1e-15]
        return float(-np.sum(eigenvalues * np.log2(eigenvalues)))

    def fidelity(self, other: DensityMatrix) -> float:
        """Compute the Uhlmann fidelity F(ρ, σ) = (Tr √(√ρ σ √ρ))².

        For pure states, this reduces to |⟨ψ|φ⟩|². For a pure state |ψ⟩
        and mixed state σ, F = ⟨ψ|σ|ψ⟩.

        Args:
            other: Another density matrix.

        Returns:
            Fidelity in [0, 1]. Equals 1 iff ρ = σ.
        """
        # Compute √ρ via eigendecomposition
        eigenvalues, eigenvectors = np.linalg.eigh(self.matrix)
        eigenvalues = np.maximum(eigenvalues, 0)  # Numerical stability
        sqrt_rho = eigenvectors @ np.diag(np.sqrt(eigenvalues)) @ eigenvectors.conj().T

        # Compute √ρ σ √ρ
        product = sqrt_rho @ other.matrix @ sqrt_rho

        # Compute Tr √(√ρ σ √ρ)
        eigenvalues_product = np.linalg.eigvalsh(product)
        eigenvalues_product = np.maximum(eigenvalues_product, 0)
        trace_sqrt = np.sum(np.sqrt(eigenvalues_product))

        return float(trace_sqrt**2)

    def trace_distance(self, other: DensityMatrix) -> float:
        """Compute the trace distance T(ρ, σ) = (1/2) Tr|ρ - σ|.

        The trace distance quantifies the distinguishability of two quantum
        states. It equals the maximum probability of distinguishing them in
        a single measurement.

        Args:
            other: Another density matrix.

        Returns:
            Trace distance in [0, 1].
        """
        difference = self.matrix - other.matrix
        eigenvalues = np.linalg.eigvalsh(difference)
        return float(0.5 * np.sum(np.abs(eigenvalues)))

    def apply_channel(self, kraus_operators: Sequence[np.ndarray]) -> DensityMatrix:
        """Apply a completely-positive trace-preserving (CPTP) map.

        The channel is specified by Kraus operators {Kᵢ} satisfying
        Σ Kᵢ† Kᵢ = I. The output state is ρ' = Σ Kᵢ ρ Kᵢ†.

        Args:
            kraus_operators: List of Kraus operators.

        Returns:
            New density matrix after the channel.

        Raises:
            ValueError: If Kraus operators don't satisfy the completeness
                relation or have wrong dimensions.
        """
        # Verify completeness relation
        completeness = sum(K.conj().T @ K for K in kraus_operators)
        if not np.allclose(completeness, np.eye(self.dimension), atol=1e-10):
            raise ValueError("Kraus operators must satisfy Σ Kᵢ† Kᵢ = I")

        # Apply channel
        result = sum(K @ self.matrix @ K.conj().T for K in kraus_operators)
        return DensityMatrix(result)

    def partial_trace(self, subsystem_dims: list[int], keep: list[int]) -> DensityMatrix:
        """Trace out subsystems to get the reduced density matrix.

        For a bipartite system A⊗B, computing the partial trace over B
        gives ρ_A = Tr_B(ρ).

        Args:
            subsystem_dims: List of dimensions for each subsystem.
            keep: List of subsystem indices to keep (0-indexed).

        Returns:
            Reduced density matrix for the kept subsystems.

        Raises:
            ValueError: If dimensions don't match or keep indices are invalid.
        """
        if np.prod(subsystem_dims) != self.dimension:
            raise ValueError(
                f"Product of subsystem dimensions {subsystem_dims} "
                f"must equal total dimension {self.dimension}"
            )

        if not all(0 <= i < len(subsystem_dims) for i in keep):
            raise ValueError(f"Keep indices must be in range [0, {len(subsystem_dims)})")

        # Reshape density matrix into tensor
        n = len(subsystem_dims)

        # Use einsum for the partial trace: pair bra and ket indices of traced-out
        # subsystems so they contract, while keeping paired indices of kept subsystems.
        #   e.g. for 3 qubits, keep=[0]: "a b c d e f" -> bra_ket pairing of traced
        #   (1,2) gives "a b c d b c" -> output "a d"
        import string

        labels = list(string.ascii_lowercase[: 2 * n])

        # Pair ket index with bra index for traced-out subsystems (same letter = contraction)
        for i in range(n):
            if i not in keep:
                labels[i + n] = labels[i]

        inp = "".join(labels)

        # Output: all bra indices first, then all ket indices (tensor-product order)
        out_bras = "".join(labels[i] for i in keep)
        out_kets = "".join(labels[i + n] for i in keep)
        out = out_bras + out_kets

        subscripts = f"{inp}->{out}"
        rho_tensor = self.matrix.reshape(subsystem_dims * 2)
        rho_reduced = np.einsum(subscripts, rho_tensor)

        # Reshape back to matrix
        keep_dims = [subsystem_dims[i] for i in keep]
        reduced_dim = np.prod(keep_dims)
        return DensityMatrix(rho_reduced.reshape(reduced_dim, reduced_dim))

    def __repr__(self) -> str:
        return f"DensityMatrix(dimension={self.dimension}, purity={self.purity():.4f})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DensityMatrix):
            return False
        return np.allclose(self.matrix, other.matrix, atol=1e-10)


# --- Standard CPTP Channels ---


def depolarizing_channel(p: float, dimension: int = 2) -> list[np.ndarray]:
    """Kraus operators for the depolarizing channel.

    With probability p, the state is replaced by the maximally mixed state I/d.
    With probability 1-p, the state is unchanged.

    For qubits (d=2), the channel is:
        ρ → (1-p)ρ + p(I/2)

    Args:
        p: Depolarizing probability in [0, 1].
        dimension: Hilbert space dimension (default 2 for qubits).

    Returns:
        List of Kraus operators.
    """
    if not 0 <= p <= 1:
        raise ValueError("Depolarizing probability must be in [0, 1]")

    if dimension == 2:
        # Qubit depolarizing channel
        # Correct Kraus operators: K0 = sqrt(1-3p/4) I, K1,K2,K3 = sqrt(p/4) σ
        eye = np.eye(2, dtype=complex)
        X = np.array([[0, 1], [1, 0]], dtype=complex)
        Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
        Z = np.array([[1, 0], [0, -1]], dtype=complex)

        K0 = np.sqrt(1 - 3 * p / 4) * eye
        K1 = np.sqrt(p / 4) * X
        K2 = np.sqrt(p / 4) * Y
        K3 = np.sqrt(p / 4) * Z
        return [K0, K1, K2, K3]
    else:
        # General d-dimensional depolarizing channel
        # Use generalized Gell-Mann matrices (simplified for now)
        # For d > 2, use the isotropic channel form
        raise NotImplementedError("Depolarizing channel for d > 2 not yet implemented")


def amplitude_damping_channel(gamma: float) -> list[np.ndarray]:
    """Kraus operators for the amplitude damping channel.

    Models energy dissipation (e.g., spontaneous emission). The |1⟩ state
    decays to |0⟩ with probability γ.

    Args:
        gamma: Damping probability in [0, 1].

    Returns:
        List of Kraus operators (2 operators for qubits).
    """
    if not 0 <= gamma <= 1:
        raise ValueError("Damping probability must be in [0, 1]")

    K0 = np.array([[1, 0], [0, np.sqrt(1 - gamma)]], dtype=complex)
    K1 = np.array([[0, np.sqrt(gamma)], [0, 0]], dtype=complex)
    return [K0, K1]


def phase_damping_channel(gamma: float) -> list[np.ndarray]:
    """Kraus operators for the phase damping (dephasing) channel.

    Models loss of quantum coherence without energy dissipation. The
    off-diagonal elements of ρ decay with probability γ.

    Args:
        gamma: Dephasing probability in [0, 1].

    Returns:
        List of Kraus operators (2 operators for qubits).
    """
    if not 0 <= gamma <= 1:
        raise ValueError("Dephasing probability must be in [0, 1]")

    K0 = np.array([[1, 0], [0, np.sqrt(1 - gamma)]], dtype=complex)
    K1 = np.array([[0, 0], [0, np.sqrt(gamma)]], dtype=complex)
    return [K0, K1]


def bit_flip_channel(p: float) -> list[np.ndarray]:
    """Kraus operators for the bit flip channel.

    With probability p, applies the Pauli X gate (bit flip).

    Args:
        p: Flip probability in [0, 1].

    Returns:
        List of Kraus operators.
    """
    if not 0 <= p <= 1:
        raise ValueError("Flip probability must be in [0, 1]")

    eye = np.eye(2, dtype=complex)
    X = np.array([[0, 1], [1, 0]], dtype=complex)

    K0 = np.sqrt(1 - p) * eye
    K1 = np.sqrt(p) * X
    return [K0, K1]


def phase_flip_channel(p: float) -> list[np.ndarray]:
    """Kraus operators for the phase flip channel.

    With probability p, applies the Pauli Z gate (phase flip).

    Args:
        p: Flip probability in [0, 1].

    Returns:
        List of Kraus operators.
    """
    if not 0 <= p <= 1:
        raise ValueError("Flip probability must be in [0, 1]")

    eye = np.eye(2, dtype=complex)
    Z = np.array([[1, 0], [0, -1]], dtype=complex)

    K0 = np.sqrt(1 - p) * eye
    K1 = np.sqrt(p) * Z
    return [K0, K1]
