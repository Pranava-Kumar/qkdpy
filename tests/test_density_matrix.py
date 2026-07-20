"""Tests for density matrix module."""

import numpy as np
import pytest

from qkdpy.core import (
    DensityMatrix,
    Qubit,
    amplitude_damping_channel,
    bit_flip_channel,
    depolarizing_channel,
    phase_damping_channel,
    phase_flip_channel,
)


class TestDensityMatrix:
    """Test DensityMatrix class."""

    def test_from_pure_qubit(self):
        """Test creating density matrix from Qubit."""
        rho = DensityMatrix.from_pure(Qubit.zero())
        assert rho.dimension == 2
        assert np.isclose(rho.purity(), 1.0)
        assert np.isclose(rho.matrix[0, 0], 1.0)

    def test_from_pure_statevector(self):
        """Test creating density matrix from numpy array."""
        psi = np.array([1, 0], dtype=complex)
        rho = DensityMatrix.from_pure(psi)
        assert rho.dimension == 2
        assert np.isclose(rho.purity(), 1.0)

    def test_maximally_mixed(self):
        """Test maximally mixed state."""
        rho = DensityMatrix.maximally_mixed(2)
        assert rho.dimension == 2
        assert np.isclose(rho.purity(), 0.5)
        assert np.isclose(rho.entropy(), 1.0)
        expected = np.eye(2) / 2
        assert np.allclose(rho.matrix, expected)

    def test_purity_pure_state(self):
        """Purity of pure state should be 1."""
        rho = DensityMatrix.from_pure(Qubit.plus())
        assert np.isclose(rho.purity(), 1.0)

    def test_purity_mixed_state(self):
        """Purity of maximally mixed state should be 1/d."""
        rho = DensityMatrix.maximally_mixed(2)
        assert np.isclose(rho.purity(), 0.5)

    def test_entropy_pure_state(self):
        """Entropy of pure state should be 0."""
        rho = DensityMatrix.from_pure(Qubit.zero())
        assert np.isclose(rho.entropy(), 0.0, atol=1e-10)

    def test_entropy_mixed_state(self):
        """Entropy of maximally mixed qubit should be 1 bit."""
        rho = DensityMatrix.maximally_mixed(2)
        assert np.isclose(rho.entropy(), 1.0)

    def test_fidelity_identical_states(self):
        """Fidelity of identical states should be 1."""
        rho = DensityMatrix.from_pure(Qubit.zero())
        sigma = DensityMatrix.from_pure(Qubit.zero())
        assert np.isclose(rho.fidelity(sigma), 1.0)

    def test_fidelity_orthogonal_states(self):
        """Fidelity of orthogonal states should be 0."""
        rho = DensityMatrix.from_pure(Qubit.zero())
        sigma = DensityMatrix.from_pure(Qubit.one())
        assert np.isclose(rho.fidelity(sigma), 0.0, atol=1e-10)

    def test_fidelity_pure_mixed(self):
        """Fidelity of pure state with maximally mixed."""
        rho = DensityMatrix.from_pure(Qubit.zero())
        mixed = DensityMatrix.maximally_mixed(2)
        # F(|0⟩⟨0|, I/2) = ⟨0|I/2|0⟩ = 1/2
        assert np.isclose(rho.fidelity(mixed), 0.5)

    def test_trace_distance_identical(self):
        """Trace distance of identical states should be 0."""
        rho = DensityMatrix.from_pure(Qubit.plus())
        assert np.isclose(rho.trace_distance(rho), 0.0, atol=1e-10)

    def test_trace_distance_orthogonal(self):
        """Trace distance of orthogonal states should be 1."""
        rho = DensityMatrix.from_pure(Qubit.zero())
        sigma = DensityMatrix.from_pure(Qubit.one())
        assert np.isclose(rho.trace_distance(sigma), 1.0)

    def test_apply_channel_identity(self):
        """Identity channel should not change state."""
        rho = DensityMatrix.from_pure(Qubit.plus())
        eye = np.eye(2, dtype=complex)
        rho_after = rho.apply_channel([eye])
        assert np.allclose(rho.matrix, rho_after.matrix)

    def test_apply_channel_depolarizing(self):
        """Depolarizing channel should reduce purity."""
        rho = DensityMatrix.from_pure(Qubit.zero())
        kraus = depolarizing_channel(0.5)
        rho_after = rho.apply_channel(kraus)
        assert rho_after.purity() < rho.purity()

    def test_apply_channel_invalid_kraus(self):
        """Should reject invalid Kraus operators."""
        rho = DensityMatrix.from_pure(Qubit.zero())
        # Invalid: doesn't satisfy completeness relation
        K = np.array([[1, 0], [0, 0.5]], dtype=complex)
        with pytest.raises(ValueError, match="must satisfy"):
            rho.apply_channel([K])

    def test_from_probabilities(self):
        """Test creating mixed state from ensemble."""
        states = [Qubit.zero(), Qubit.one()]
        probs = [0.7, 0.3]
        rho = DensityMatrix.from_probabilities(states, probs)
        assert np.isclose(rho.purity(), 0.7**2 + 0.3**2)
        assert np.isclose(rho.matrix[0, 0], 0.7)
        assert np.isclose(rho.matrix[1, 1], 0.3)

    def test_from_probabilities_invalid(self):
        """Should reject probabilities that don't sum to 1."""
        states = [Qubit.zero(), Qubit.one()]
        probs = [0.5, 0.3]  # Sum = 0.8
        with pytest.raises(ValueError, match="sum to 1"):
            DensityMatrix.from_probabilities(states, probs)

    def test_partial_trace_product_state(self):
        """Partial trace of product state should give reduced state."""
        # Create |0⟩⊗|1⟩
        rho_0 = DensityMatrix.from_pure(Qubit.zero())
        rho_1 = DensityMatrix.from_pure(Qubit.one())
        rho_total = DensityMatrix(np.kron(rho_0.matrix, rho_1.matrix))

        # Trace out second qubit
        rho_reduced = rho_total.partial_trace([2, 2], keep=[0])
        assert rho_reduced.dimension == 2
        assert np.allclose(rho_reduced.matrix, rho_0.matrix)

    def test_partial_trace_entangled_state(self):
        """Partial trace of Bell state should give maximally mixed."""
        # Create Bell state |Φ+⟩ = (|00⟩ + |11⟩)/√2
        bell = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)
        rho_bell = DensityMatrix.from_pure(bell)

        # Trace out second qubit
        rho_reduced = rho_bell.partial_trace([2, 2], keep=[0])
        assert rho_reduced.dimension == 2
        # Should be maximally mixed
        assert np.isclose(rho_reduced.purity(), 0.5)
        assert np.isclose(rho_reduced.entropy(), 1.0)

    def test_invalid_non_hermitian(self):
        """Should reject non-Hermitian matrix."""
        rho = np.array([[1, 1j], [0, 0]], dtype=complex)
        with pytest.raises(ValueError, match="Hermitian"):
            DensityMatrix(rho)

    def test_invalid_non_unit_trace(self):
        """Should reject matrix with trace != 1."""
        rho = np.array([[2, 0], [0, 0]], dtype=complex)
        with pytest.raises(ValueError, match="trace 1"):
            DensityMatrix(rho)

    def test_invalid_non_positive(self):
        """Should reject non-positive-semidefinite matrix."""
        rho = np.array([[1, 0], [0, -0.1]], dtype=complex)
        with pytest.raises(ValueError, match="positive semidefinite"):
            DensityMatrix(rho)


class TestCPTPChannels:
    """Test standard CPTP channels."""

    def test_depolarizing_channel_completeness(self):
        """Depolarizing channel should satisfy completeness relation."""
        kraus = depolarizing_channel(0.3)
        completeness = sum(K.conj().T @ K for K in kraus)
        assert np.allclose(completeness, np.eye(2))

    def test_depolarizing_channel_zero(self):
        """Depolarizing with p=0 should be identity."""
        rho = DensityMatrix.from_pure(Qubit.plus())
        kraus = depolarizing_channel(0.0)
        rho_after = rho.apply_channel(kraus)
        assert np.allclose(rho.matrix, rho_after.matrix)

    def test_depolarizing_channel_full(self):
        """Depolarizing with p=1 should give maximally mixed."""
        rho = DensityMatrix.from_pure(Qubit.zero())
        kraus = depolarizing_channel(1.0)
        rho_after = rho.apply_channel(kraus)
        assert np.allclose(rho_after.matrix, np.eye(2) / 2)

    def test_depolarizing_channel_invalid_prob(self):
        """Should reject invalid probability."""
        with pytest.raises(ValueError, match="[0, 1]"):
            depolarizing_channel(1.5)

    def test_amplitude_damping_completeness(self):
        """Amplitude damping should satisfy completeness relation."""
        kraus = amplitude_damping_channel(0.2)
        completeness = sum(K.conj().T @ K for K in kraus)
        assert np.allclose(completeness, np.eye(2))

    def test_amplitude_damping_effect(self):
        """Amplitude damping should drive |1⟩ to |0⟩."""
        rho = DensityMatrix.from_pure(Qubit.one())
        kraus = amplitude_damping_channel(1.0)
        rho_after = rho.apply_channel(kraus)
        # Full damping: |1⟩ → |0⟩
        assert np.allclose(rho_after.matrix, DensityMatrix.from_pure(Qubit.zero()).matrix)

    def test_phase_damping_completeness(self):
        """Phase damping should satisfy completeness relation."""
        kraus = phase_damping_channel(0.5)
        completeness = sum(K.conj().T @ K for K in kraus)
        assert np.allclose(completeness, np.eye(2))

    def test_phase_damping_effect(self):
        """Phase damping should destroy off-diagonal coherences."""
        rho = DensityMatrix.from_pure(Qubit.plus())
        kraus = phase_damping_channel(1.0)
        rho_after = rho.apply_channel(kraus)
        # Full dephasing: off-diagonal elements should vanish
        assert np.isclose(rho_after.matrix[0, 1], 0.0, atol=1e-10)
        assert np.isclose(rho_after.matrix[1, 0], 0.0, atol=1e-10)

    def test_bit_flip_completeness(self):
        """Bit flip should satisfy completeness relation."""
        kraus = bit_flip_channel(0.3)
        completeness = sum(K.conj().T @ K for K in kraus)
        assert np.allclose(completeness, np.eye(2))

    def test_bit_flip_full(self):
        """Full bit flip should flip |0⟩ to |1⟩."""
        rho = DensityMatrix.from_pure(Qubit.zero())
        kraus = bit_flip_channel(1.0)
        rho_after = rho.apply_channel(kraus)
        assert np.allclose(rho_after.matrix, DensityMatrix.from_pure(Qubit.one()).matrix)

    def test_phase_flip_completeness(self):
        """Phase flip should satisfy completeness relation."""
        kraus = phase_flip_channel(0.3)
        completeness = sum(K.conj().T @ K for K in kraus)
        assert np.allclose(completeness, np.eye(2))
