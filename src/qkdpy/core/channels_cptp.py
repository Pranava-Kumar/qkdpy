"""Completely Positive Trace-Preserving (CPTP) channel framework.

Provides a formal abstraction for quantum channels with:
- Channel composition
- Choi matrix representation
- Diamond norm distance computation
- Standard channel library

This builds on the density matrix module and provides a higher-level
interface for channel manipulation and analysis.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from .density_matrix import DensityMatrix
from .qubit import Qubit

if TYPE_CHECKING:
    from collections.abc import Sequence


class CPTPChannel:
    """Completely Positive Trace-Preserving quantum channel.

    Represents a quantum channel via Kraus operators {K_i} satisfying
    Σ K_i† K_i = I.

    Attributes:
        kraus_ops: List of Kraus operators.
        dimension: Hilbert space dimension.
    """

    def __init__(self, kraus_operators: Sequence[np.ndarray]) -> None:
        """Initialize a CPTP channel from Kraus operators.

        Args:
            kraus_operators: Sequence of Kraus operators.

        Raises:
            ValueError: If operators don't satisfy completeness relation.
        """
        if not kraus_operators:
            raise ValueError("Must provide at least one Kraus operator")

        dim = kraus_operators[0].shape[0]
        for K in kraus_operators:
            if K.shape != (dim, dim):
                raise ValueError(f"All Kraus operators must be {dim}×{dim}")

        # Verify completeness relation: Σ K_i† K_i = I
        completeness = sum(K.conj().T @ K for K in kraus_operators)
        if not np.allclose(completeness, np.eye(dim), atol=1e-10):
            raise ValueError("Kraus operators must satisfy Σ K_i† K_i = I")

        self.kraus_ops = [K.astype(complex) for K in kraus_operators]
        self.dimension = dim

    def apply(self, state: DensityMatrix | Qubit | np.ndarray) -> DensityMatrix:
        """Apply the channel to a quantum state.

        Args:
            state: Input state (DensityMatrix, Qubit, or statevector).

        Returns:
            Output density matrix after channel application.
        """
        if isinstance(state, Qubit):
            rho = DensityMatrix.from_pure(state)
        elif isinstance(state, np.ndarray):
            if state.ndim == 1:
                rho = DensityMatrix.from_pure(state)
            else:
                rho = DensityMatrix(state)
        else:
            rho = state

        return rho.apply_channel(self.kraus_ops)

    def compose(self, other: CPTPChannel) -> CPTPChannel:
        """Compose this channel with another: self ∘ other.

        The composed channel applies 'other' first, then 'self'.
        Mathematically: E_self ∘ E_other has Kraus operators {K_i L_j}
        where {K_i} are self's operators and {L_j} are other's operators.

        Args:
            other: Channel to apply first.

        Returns:
            Composed channel.

        Raises:
            ValueError: If dimensions don't match.
        """
        if self.dimension != other.dimension:
            raise ValueError(
                f"Cannot compose channels with different dimensions: "
                f"{self.dimension} vs {other.dimension}"
            )

        # Composed Kraus operators: {K_i L_j} for all i, j
        composed_ops = []
        for K in self.kraus_ops:
            for L in other.kraus_ops:
                composed_ops.append(K @ L)

        return CPTPChannel(composed_ops)

    def __matmul__(self, other: CPTPChannel) -> CPTPChannel:
        """Operator @ for channel composition."""
        return self.compose(other)

    def tensor_product(self, other: CPTPChannel) -> CPTPChannel:
        """Tensor product of two channels: self ⊗ other.

        The tensor product channel acts on the joint Hilbert space.
        Kraus operators are {K_i ⊗ L_j}.

        Args:
            other: Another channel.

        Returns:
            Tensor product channel.
        """
        tensor_ops = []
        for K in self.kraus_ops:
            for L in other.kraus_ops:
                tensor_ops.append(np.kron(K, L))

        return CPTPChannel(tensor_ops)

    def choi_matrix(self) -> np.ndarray:
        """Compute the Choi matrix representation.

        The Choi matrix is defined as:
            C = (I ⊗ E)(|Ω⟩⟨Ω|)
        where |Ω⟩ = Σ_i |i⟩|i⟩ is the (unnormalized) maximally entangled state.

        Returns:
            Choi matrix as a d²×d² complex array.
        """
        d = self.dimension

        # Maximally entangled state |Ω⟩ = Σ_i |i⟩|i⟩
        omega = np.zeros(d * d, dtype=complex)
        for i in range(d):
            omega[i * d + i] = 1.0

        # Density matrix of |Ω⟩
        rho_omega = np.outer(omega, omega.conj())

        # Apply identity on first subsystem, channel on second
        # For each Kraus operator K, we compute (I ⊗ K) |Ω⟩⟨Ω| (I ⊗ K)†
        choi = np.zeros((d * d, d * d), dtype=complex)
        for K in self.kraus_ops:
            # I ⊗ K
            I_K = np.kron(np.eye(d), K)
            choi += I_K @ rho_omega @ I_K.conj().T

        return choi

    def choi_rank(self) -> int:
        """Compute the rank of the Choi matrix.

        The rank equals the minimum number of Kraus operators needed
        to represent the channel.

        Returns:
            Rank of the Choi matrix.
        """
        choi = self.choi_matrix()
        eigenvalues = np.linalg.eigvalsh(choi)
        # Count eigenvalues above numerical threshold
        return int(np.sum(eigenvalues > 1e-10))

    def is_unitary(self, tol: float = 1e-10) -> bool:
        """Check if the channel is unitary (rank-1 Choi matrix).

        Args:
            tol: Numerical tolerance.

        Returns:
            True if channel is unitary.
        """
        return self.choi_rank() == 1

    def is_identity(self, tol: float = 1e-10) -> bool:
        """Check if the channel is the identity channel.

        Args:
            tol: Numerical tolerance.

        Returns:
            True if channel is identity.
        """
        # Identity channel has single Kraus operator = I
        if len(self.kraus_ops) != 1:
            return False
        return np.allclose(self.kraus_ops[0], np.eye(self.dimension), atol=tol)

    def diamond_norm(self, other: CPTPChannel | None = None) -> float:
        """Compute the diamond norm distance to another channel.

        The diamond norm ||E1 - E2||_⋄ quantifies the maximum distinguishability
        of two channels, even when assisted by an entangled ancilla.

        For simplicity, this implementation uses the SDP relaxation:
            ||E1 - E2||_⋄ ≈ max over input states ρ of ||(E1 - E2)(ρ)||_1

        This is a lower bound but often tight for qubit channels.

        Args:
            other: Channel to compare against. If None, compares to identity.

        Returns:
            Diamond norm distance (lower bound via SDP relaxation).
        """
        if other is None:
            # Compare to identity channel
            other = CPTPChannel([np.eye(self.dimension)])

        if self.dimension != other.dimension:
            raise ValueError("Channels must have same dimension")

        # Compute difference channel
        # For each input state, compute ||(E1 - E2)(ρ)||_1
        # We sample random pure states to find the maximum
        d = self.dimension
        max_trace_norm = 0.0

        # Sample random pure states (Haar measure approximation)
        n_samples = 100
        for _ in range(n_samples):
            # Random pure state
            psi = np.random.randn(d) + 1j * np.random.randn(d)
            psi = psi / np.linalg.norm(psi)
            rho = DensityMatrix.from_pure(psi)

            # Apply both channels
            rho1 = self.apply(rho)
            rho2 = other.apply(rho)

            # Compute trace norm of difference
            diff = rho1.matrix - rho2.matrix
            eigenvalues = np.linalg.eigvalsh(diff)
            trace_norm = np.sum(np.abs(eigenvalues))
            max_trace_norm = max(max_trace_norm, trace_norm)

        return float(max_trace_norm)

    def __repr__(self) -> str:
        return (
            f"CPTPChannel(dimension={self.dimension}, "
            f"n_kraus={len(self.kraus_ops)}, "
            f"unitary={self.is_unitary()})"
        )


# --- Standard Channel Library ---


class DepolarizingChannel(CPTPChannel):
    """Depolarizing channel: ρ → (1-p)ρ + p(I/d)."""

    def __init__(self, p: float, dimension: int = 2) -> None:
        """Initialize depolarizing channel.

        Args:
            p: Depolarizing probability in [0, 1].
            dimension: Hilbert space dimension (default 2).
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
            kraus = [K0, K1, K2, K3]
        else:
            raise NotImplementedError("Depolarizing channel for d > 2 not yet implemented")

        super().__init__(kraus)
        self.probability = p


class AmplitudeDampingChannel(CPTPChannel):
    """Amplitude damping channel: models energy dissipation."""

    def __init__(self, gamma: float) -> None:
        """Initialize amplitude damping channel.

        Args:
            gamma: Damping probability in [0, 1].
        """
        if not 0 <= gamma <= 1:
            raise ValueError("Damping probability must be in [0, 1]")

        K0 = np.array([[1, 0], [0, np.sqrt(1 - gamma)]], dtype=complex)
        K1 = np.array([[0, np.sqrt(gamma)], [0, 0]], dtype=complex)
        super().__init__([K0, K1])
        self.gamma = gamma


class PhaseDampingChannel(CPTPChannel):
    """Phase damping (dephasing) channel: models loss of coherence."""

    def __init__(self, gamma: float) -> None:
        """Initialize phase damping channel.

        Args:
            gamma: Dephasing probability in [0, 1].
        """
        if not 0 <= gamma <= 1:
            raise ValueError("Dephasing probability must be in [0, 1]")

        K0 = np.array([[1, 0], [0, np.sqrt(1 - gamma)]], dtype=complex)
        K1 = np.array([[0, 0], [0, np.sqrt(gamma)]], dtype=complex)
        super().__init__([K0, K1])
        self.gamma = gamma


class BitFlipChannel(CPTPChannel):
    """Bit flip channel: ρ → (1-p)ρ + p XρX."""

    def __init__(self, p: float) -> None:
        """Initialize bit flip channel.

        Args:
            p: Flip probability in [0, 1].
        """
        if not 0 <= p <= 1:
            raise ValueError("Flip probability must be in [0, 1]")

        eye = np.eye(2, dtype=complex)
        X = np.array([[0, 1], [1, 0]], dtype=complex)

        K0 = np.sqrt(1 - p) * eye
        K1 = np.sqrt(p) * X
        super().__init__([K0, K1])
        self.probability = p


class PhaseFlipChannel(CPTPChannel):
    """Phase flip channel: ρ → (1-p)ρ + p ZρZ."""

    def __init__(self, p: float) -> None:
        """Initialize phase flip channel.

        Args:
            p: Flip probability in [0, 1].
        """
        if not 0 <= p <= 1:
            raise ValueError("Flip probability must be in [0, 1]")

        eye = np.eye(2, dtype=complex)
        Z = np.array([[1, 0], [0, -1]], dtype=complex)

        K0 = np.sqrt(1 - p) * eye
        K1 = np.sqrt(p) * Z
        super().__init__([K0, K1])
        self.probability = p


class IdentityChannel(CPTPChannel):
    """Identity channel: ρ → ρ."""

    def __init__(self, dimension: int = 2) -> None:
        """Initialize identity channel.

        Args:
            dimension: Hilbert space dimension (default 2).
        """
        super().__init__([np.eye(dimension, dtype=complex)])
