"""Tests for CPTP channel framework."""

import numpy as np
import pytest

from qkdpy.core import (
    CPTPChannel,
    DensityMatrix,
    Qubit,
)
from qkdpy.core.channels_cptp import (
    AmplitudeDampingChannel,
    BitFlipChannel,
    DepolarizingChannel,
    IdentityChannel,
    PhaseDampingChannel,
    PhaseFlipChannel,
)


class TestCPTPChannel:
    """Test CPTPChannel class."""

    def test_init_valid(self):
        """Test initialization with valid Kraus operators."""
        eye = np.eye(2, dtype=complex)
        channel = CPTPChannel([eye])
        assert channel.dimension == 2
        assert len(channel.kraus_ops) == 1

    def test_init_invalid_completeness(self):
        """Test that invalid Kraus operators raise error."""
        K = np.array([[1, 0], [0, 0.5]], dtype=complex)
        with pytest.raises(ValueError, match="Σ K_i† K_i = I"):
            CPTPChannel([K])

    def test_init_invalid_shape(self):
        """Test that mismatched shapes raise error."""
        K1 = np.eye(2, dtype=complex)
        K2 = np.eye(3, dtype=complex)
        with pytest.raises(ValueError, match="2×2"):
            CPTPChannel([K1, K2])

    def test_init_empty(self):
        """Test that empty Kraus operators raise error."""
        with pytest.raises(ValueError, match="at least one"):
            CPTPChannel([])

    def test_apply_density_matrix(self):
        """Test applying channel to DensityMatrix."""
        rho = DensityMatrix.from_pure(Qubit.zero())
        channel = IdentityChannel()
        rho_out = channel.apply(rho)
        assert np.allclose(rho_out.matrix, rho.matrix)

    def test_apply_qubit(self):
        """Test applying channel to Qubit."""
        qubit = Qubit.zero()
        channel = IdentityChannel()
        rho_out = channel.apply(qubit)
        assert isinstance(rho_out, DensityMatrix)
        assert np.allclose(rho_out.matrix[0, 0], 1.0)

    def test_apply_statevector(self):
        """Test applying channel to statevector."""
        psi = np.array([1, 0], dtype=complex)
        channel = IdentityChannel()
        rho_out = channel.apply(psi)
        assert isinstance(rho_out, DensityMatrix)

    def test_compose_identity(self):
        """Test composition with identity."""
        channel = DepolarizingChannel(0.1)
        identity = IdentityChannel()

        composed = channel.compose(identity)
        assert composed.dimension == 2
        assert len(composed.kraus_ops) == len(channel.kraus_ops)

    def test_compose_two_channels(self):
        """Test composition of two depolarizing channels."""
        c1 = DepolarizingChannel(0.1)
        c2 = DepolarizingChannel(0.2)

        composed = c1.compose(c2)
        # Should have 4 × 4 = 16 Kraus operators
        assert len(composed.kraus_ops) == 16

    def test_compose_dimension_mismatch(self):
        """Test that composing different dimensions raises error."""
        c1 = IdentityChannel(2)
        c2 = IdentityChannel(3)
        with pytest.raises(ValueError, match="different dimensions"):
            c1.compose(c2)

    def test_matmul_operator(self):
        """Test @ operator for composition."""
        c1 = DepolarizingChannel(0.1)
        c2 = DepolarizingChannel(0.2)
        composed = c1 @ c2
        assert len(composed.kraus_ops) == 16

    def test_tensor_product(self):
        """Test tensor product of channels."""
        c1 = DepolarizingChannel(0.1)
        c2 = DepolarizingChannel(0.2)

        tensor = c1.tensor_product(c2)
        # Should have 4 × 4 = 16 Kraus operators
        # Tensor product dimension is 2 × 2 = 4
        assert tensor.dimension == 4
        assert len(tensor.kraus_ops) == 16

    def test_choi_matrix_identity(self):
        """Test Choi matrix of identity channel."""
        channel = IdentityChannel()
        choi = channel.choi_matrix()

        # Choi matrix should be 4×4 for qubit
        assert choi.shape == (4, 4)

        # Should be positive semidefinite
        eigenvalues = np.linalg.eigvalsh(choi)
        assert np.all(eigenvalues >= -1e-10)

    def test_choi_matrix_depolarizing(self):
        """Test Choi matrix of depolarizing channel."""
        channel = DepolarizingChannel(0.5)
        choi = channel.choi_matrix()

        assert choi.shape == (4, 4)

        # Should be positive semidefinite
        eigenvalues = np.linalg.eigvalsh(choi)
        assert np.all(eigenvalues >= -1e-10)

    def test_choi_rank_unitary(self):
        """Test Choi rank of unitary channel."""
        # Identity is unitary, should have rank 1
        channel = IdentityChannel()
        assert channel.choi_rank() == 1

    def test_choi_rank_noisy(self):
        """Test Choi rank of noisy channel."""
        # Depolarizing channel should have rank > 1
        channel = DepolarizingChannel(0.5)
        assert channel.choi_rank() > 1

    def test_is_unitary_identity(self):
        """Test is_unitary for identity channel."""
        channel = IdentityChannel()
        assert channel.is_unitary()

    def test_is_unitary_depolarizing(self):
        """Test is_unitary for depolarizing channel."""
        channel = DepolarizingChannel(0.5)
        assert not channel.is_unitary()

    def test_is_identity(self):
        """Test is_identity method."""
        identity = IdentityChannel()
        assert identity.is_identity()

        depol = DepolarizingChannel(0.1)
        assert not depol.is_identity()

    def test_diamond_norm_identity(self):
        """Test diamond norm to identity."""
        identity = IdentityChannel()
        dist = identity.diamond_norm(identity)
        # Distance to itself should be 0
        assert dist < 1e-10

    def test_diamond_norm_depolarizing(self):
        """Test diamond norm of depolarizing channel."""
        identity = IdentityChannel()
        depol = DepolarizingChannel(0.3)

        dist = depol.diamond_norm(identity)
        # Should be positive
        assert dist > 0

    def test_diamond_norm_dimension_mismatch(self):
        """Test that diamond norm raises error for different dimensions."""
        c1 = IdentityChannel(2)
        c2 = IdentityChannel(3)
        with pytest.raises(ValueError, match="same dimension"):
            c1.diamond_norm(c2)


class TestStandardChannels:
    """Test standard channel library."""

    def test_depolarizing_channel(self):
        """Test DepolarizingChannel class."""
        channel = DepolarizingChannel(0.2)
        assert channel.probability == 0.2
        assert channel.dimension == 2
        assert len(channel.kraus_ops) == 4

    def test_depolarizing_invalid_prob(self):
        """Test invalid probability raises error."""
        with pytest.raises(ValueError, match="[0, 1]"):
            DepolarizingChannel(1.5)

    def test_amplitude_damping_channel(self):
        """Test AmplitudeDampingChannel class."""
        channel = AmplitudeDampingChannel(0.3)
        assert channel.gamma == 0.3
        assert channel.dimension == 2
        assert len(channel.kraus_ops) == 2

    def test_amplitude_damping_invalid_prob(self):
        """Test invalid probability raises error."""
        with pytest.raises(ValueError, match="[0, 1]"):
            AmplitudeDampingChannel(-0.1)

    def test_phase_damping_channel(self):
        """Test PhaseDampingChannel class."""
        channel = PhaseDampingChannel(0.4)
        assert channel.gamma == 0.4
        assert channel.dimension == 2
        assert len(channel.kraus_ops) == 2

    def test_phase_damping_invalid_prob(self):
        """Test invalid probability raises error."""
        with pytest.raises(ValueError, match="[0, 1]"):
            PhaseDampingChannel(2.0)

    def test_bit_flip_channel(self):
        """Test BitFlipChannel class."""
        channel = BitFlipChannel(0.1)
        assert channel.probability == 0.1
        assert channel.dimension == 2
        assert len(channel.kraus_ops) == 2

    def test_bit_flip_invalid_prob(self):
        """Test invalid probability raises error."""
        with pytest.raises(ValueError, match="[0, 1]"):
            BitFlipChannel(-0.5)

    def test_phase_flip_channel(self):
        """Test PhaseFlipChannel class."""
        channel = PhaseFlipChannel(0.2)
        assert channel.probability == 0.2
        assert channel.dimension == 2
        assert len(channel.kraus_ops) == 2

    def test_phase_flip_invalid_prob(self):
        """Test invalid probability raises error."""
        with pytest.raises(ValueError, match="[0, 1]"):
            PhaseFlipChannel(3.0)

    def test_identity_channel(self):
        """Test IdentityChannel class."""
        channel = IdentityChannel()
        assert channel.dimension == 2
        assert len(channel.kraus_ops) == 1
        assert np.allclose(channel.kraus_ops[0], np.eye(2))

    def test_identity_custom_dimension(self):
        """Test IdentityChannel with custom dimension."""
        channel = IdentityChannel(dimension=4)
        assert channel.dimension == 4
        assert np.allclose(channel.kraus_ops[0], np.eye(4))


class TestChannelIntegration:
    """Integration tests for channel operations."""

    def test_depolarizing_effect(self):
        """Test that depolarizing channel reduces purity."""
        rho = DensityMatrix.from_pure(Qubit.zero())
        initial_purity = rho.purity()

        channel = DepolarizingChannel(0.3)
        rho_out = channel.apply(rho)
        final_purity = rho_out.purity()

        assert final_purity < initial_purity

    def test_amplitude_damping_effect(self):
        """Test that amplitude damping drives |1⟩ to |0⟩."""
        rho = DensityMatrix.from_pure(Qubit.one())
        channel = AmplitudeDampingChannel(1.0)  # Full damping

        rho_out = channel.apply(rho)

        # Should end up in |0⟩
        assert np.allclose(rho_out.matrix[0, 0], 1.0, atol=1e-10)
        assert np.allclose(rho_out.matrix[1, 1], 0.0, atol=1e-10)

    def test_phase_damping_effect(self):
        """Test that phase damping destroys coherence."""
        rho = DensityMatrix.from_pure(Qubit.plus())
        initial_coherence = abs(rho.matrix[0, 1])

        channel = PhaseDampingChannel(1.0)  # Full dephasing
        rho_out = channel.apply(rho)
        final_coherence = abs(rho_out.matrix[0, 1])

        assert final_coherence < initial_coherence
        assert final_coherence < 1e-10  # Should be essentially zero

    def test_channel_composition_effect(self):
        """Test that composed channels have cumulative effect."""
        rho = DensityMatrix.from_pure(Qubit.zero())

        c1 = DepolarizingChannel(0.1)
        c2 = DepolarizingChannel(0.2)
        composed = c1.compose(c2)

        rho_after_c1 = c1.apply(rho)
        rho_after_c2 = c2.apply(rho_after_c1)
        rho_after_composed = composed.apply(rho)

        # Composed should equal sequential application
        assert np.allclose(rho_after_composed.matrix, rho_after_c2.matrix)

    def test_choi_matrix_trace(self):
        """Test that Choi matrix has trace equal to dimension."""
        channel = DepolarizingChannel(0.2)
        choi = channel.choi_matrix()

        # Trace should equal dimension
        assert np.isclose(np.trace(choi), channel.dimension)
