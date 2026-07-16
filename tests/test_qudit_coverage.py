"""Coverage tests for core/qudit.py (was 44%)."""

import numpy as np
import pytest

from qkdpy.core.qudit import Qudit


class TestQuditInit:
    def test_basic_creation(self):
        state = np.array([1.0 + 0j, 0.0 + 0j, 0.0 + 0j])
        q = Qudit(state, dimension=3)
        assert q.dimension == 3
        assert np.allclose(q.state, state)

    def test_auto_normalization(self):
        q = Qudit(np.array([2.0, 0.0]), dimension=2)
        assert np.allclose(q.state, np.array([1.0, 0.0]))

    def test_zero_norm(self):
        with pytest.raises(ValueError, match="zero norm"):
            Qudit(np.array([0.0, 0.0]), dimension=2)

    def test_wrong_length(self):
        with pytest.raises(ValueError, match="must match dimension"):
            Qudit(np.array([1.0, 0.0, 0.0]), dimension=2)


class TestComputationalBasis:
    def test_zero_state(self):
        q = Qudit.computational_basis(0, 2)
        assert np.allclose(q.state, np.array([1.0, 0.0]))

    def test_one_state(self):
        q = Qudit.computational_basis(1, 2)
        assert np.allclose(q.state, np.array([0.0, 1.0]))

    def test_higher_dimension(self):
        q = Qudit.computational_basis(2, 4)
        expected = np.zeros(4, dtype=complex)
        expected[2] = 1.0
        assert np.allclose(q.state, expected)

    def test_invalid_level_negative(self):
        with pytest.raises(ValueError, match="Level must be between"):
            Qudit.computational_basis(-1, 3)

    def test_invalid_level_too_high(self):
        with pytest.raises(ValueError, match="Level must be between"):
            Qudit.computational_basis(3, 3)


class TestUniformSuperposition:
    def test_dim2(self):
        q = Qudit.uniform_superposition(2)
        expected = np.ones(2, dtype=complex) / np.sqrt(2)
        assert np.allclose(q.state, expected)

    def test_dim3(self):
        q = Qudit.uniform_superposition(3)
        expected = np.ones(3, dtype=complex) / np.sqrt(3)
        assert np.allclose(q.state, expected)

    def test_all_equal_probabilities(self):
        q = Qudit.uniform_superposition(4)
        probs = q.probabilities
        assert all(p == pytest.approx(0.25, abs=1e-10) for p in probs)


class TestFourierBasis:
    def test_level_0_is_uniform(self):
        q = Qudit.fourier_basis(0, 3)
        expected = np.ones(3, dtype=complex) / np.sqrt(3)
        assert np.allclose(q.state, expected)

    def test_invalid_level(self):
        with pytest.raises(ValueError, match="Level must be between"):
            Qudit.fourier_basis(5, 3)

    def test_dim2_level1(self):
        q = Qudit.fourier_basis(1, 2)
        expected = np.array([1.0, -1.0]) / np.sqrt(2)
        assert np.allclose(q.state, expected)


class TestProbabilities:
    def test_computational_basis(self):
        q = Qudit.computational_basis(0, 3)
        probs = q.probabilities
        assert probs[0] == pytest.approx(1.0)
        assert probs[1] == pytest.approx(0.0)
        assert probs[2] == pytest.approx(0.0)

    def test_uniform(self):
        q = Qudit.uniform_superposition(4)
        probs = q.probabilities
        assert all(p == pytest.approx(0.25, abs=1e-10) for p in probs)

    def test_sum_to_one(self):
        q = Qudit(np.array([1 + 2j, 3 - 1j, 0.5 + 0.5j]) / np.sqrt(17.5), dimension=3)
        probs = q.probabilities
        assert sum(probs) == pytest.approx(1.0, abs=1e-10)


class TestApplyUnitary:
    def test_identity(self):
        q = Qudit.computational_basis(1, 3)
        q.apply_unitary(np.eye(3, dtype=complex))
        assert np.allclose(q.state, np.array([0.0, 1.0, 0.0]))

    def test_swap_2d(self):
        """X gate on qubit swaps |0> and |1>."""
        q = Qudit.computational_basis(0, 2)
        X = np.array([[0, 1], [1, 0]], dtype=complex)
        q.apply_unitary(X)
        assert np.allclose(q.state, np.array([0.0, 1.0]))

    def test_wrong_shape(self):
        q = Qudit.computational_basis(0, 3)
        with pytest.raises(ValueError, match="must be a 3×3 matrix"):
            q.apply_unitary(np.eye(2, dtype=complex))

    def test_non_unitary(self):
        q = Qudit.computational_basis(0, 2)
        with pytest.raises(ValueError, match="must be unitary"):
            q.apply_unitary(np.array([[1, 0], [0, 0]], dtype=complex))

    def test_fourier_then_inverse(self):
        """Applying QFT then inverse QFT should give original state."""
        q = Qudit.computational_basis(2, 4)
        original = q.state.copy()

        # Build QFT matrix for d=4
        d = 4
        qft = np.zeros((d, d), dtype=complex)
        for j in range(d):
            for k in range(d):
                qft[j, k] = np.exp(2j * np.pi * j * k / d) / np.sqrt(d)

        q.apply_unitary(qft)
        q.apply_unitary(qft.conj().T)
        assert np.allclose(q.state, original, atol=1e-10)


class TestMeasure:
    def test_measure_computational_deterministic(self):
        """Measuring |0> in computational basis always gives 0."""
        q = Qudit.computational_basis(0, 3)
        for _ in range(20):
            assert q.measure_computational() == 0

    def test_measure_computational_ket1(self):
        """Measuring |1> in computational basis always gives 1."""
        q = Qudit.computational_basis(1, 3)
        for _ in range(20):
            assert q.measure_computational() == 1

    def test_measure_with_basis_matrix(self):
        """Measuring with identity basis should behave like computational."""
        q = Qudit.computational_basis(0, 3)
        for _ in range(20):
            assert q.measure(np.eye(3, dtype=complex)) == 0

    def test_measure_invalid_basis_shape(self):
        q = Qudit.computational_basis(0, 3)
        with pytest.raises(ValueError, match="must be 3×3"):
            q.measure(np.eye(2, dtype=complex))

    def test_measure_fourier_basis(self):
        """Fourier basis state |0> in Fourier basis = |0> in computational."""
        q = Qudit.fourier_basis(0, 3)
        result = q.measure_fourier()
        assert result == 0

    def test_measure_basic_no_matrix(self):
        q = Qudit.computational_basis(1, 2)
        assert q.measure(None) == 1


class TestCollapseState:
    def test_collapse_computational(self):
        q = Qudit.uniform_superposition(3)
        q.collapse_state(1)
        expected = np.zeros(3, dtype=complex)
        expected[1] = 1.0
        assert np.allclose(q.state, expected)

    def test_collapse_invalid_result(self):
        q = Qudit.computational_basis(0, 3)
        with pytest.raises(ValueError, match="must be between"):
            q.collapse_state(5)

    def test_collapse_with_basis_matrix(self):
        q = Qudit.uniform_superposition(2)
        basis = np.eye(2, dtype=complex)
        q.collapse_state(0, basis)
        assert np.allclose(q.state, np.array([1.0, 0.0]))


class TestFidelity:
    def test_identical(self):
        q1 = Qudit.uniform_superposition(3)
        q2 = Qudit.uniform_superposition(3)
        assert q1.fidelity(q2) == pytest.approx(1.0)

    def test_orthogonal(self):
        q1 = Qudit.computational_basis(0, 4)
        q2 = Qudit.computational_basis(2, 4)
        assert q1.fidelity(q2) == pytest.approx(0.0)

    def test_different_dimensions(self):
        q1 = Qudit.computational_basis(0, 2)
        q2 = Qudit.computational_basis(0, 3)
        with pytest.raises(ValueError, match="same dimension"):
            q1.fidelity(q2)


class TestTensorProduct:
    def test_two_qudits(self):
        q1 = Qudit.computational_basis(0, 2)
        q2 = Qudit.computational_basis(1, 2)
        result = q1.tensor_product(q2)
        assert result.dimension == 4
        expected = np.kron(q1.state, q2.state)
        assert np.allclose(result.state, expected)

    def test_diff_dimensions(self):
        q1 = Qudit.computational_basis(0, 2)
        q2 = Qudit.computational_basis(0, 3)
        result = q1.tensor_product(q2)
        assert result.dimension == 6


class TestPartialTrace:
    def test_trace_out_subsystem_0(self):
        """|0>|1> traced over subsystem 0 should give |1>."""
        q1 = Qudit.computational_basis(0, 2)
        q2 = Qudit.computational_basis(1, 2)
        combined = q1.tensor_product(q2)
        result = combined.partial_trace(0, 2)
        assert result.dimension == 2
        assert np.allclose(result.state, q2.state)

    def test_trace_out_subsystem_1(self):
        """|0>|1> traced over subsystem 1 should give |0>."""
        q1 = Qudit.computational_basis(0, 2)
        q2 = Qudit.computational_basis(1, 2)
        combined = q1.tensor_product(q2)
        result = combined.partial_trace(1, 2)
        assert result.dimension == 2
        assert np.allclose(result.state, q1.state)

    def test_invalid_dimension(self):
        q = Qudit.computational_basis(0, 4)
        with pytest.raises(ValueError, match="System dimension must be divisible"):
            q.partial_trace(0, 3)


class TestRepr:
    def test_repr(self):
        q = Qudit.computational_basis(0, 3)
        r = repr(q)
        assert "Qudit" in r
        assert "dimension=3" in r


class TestEq:
    def test_equal(self):
        q1 = Qudit.computational_basis(0, 2)
        q2 = Qudit.computational_basis(0, 2)
        assert q1 == q2

    def test_not_equal(self):
        q1 = Qudit.computational_basis(0, 2)
        q2 = Qudit.computational_basis(1, 2)
        assert q1 != q2

    def test_diff_dimension(self):
        q1 = Qudit.computational_basis(0, 2)
        q2 = Qudit.computational_basis(0, 3)
        assert q1 != q2

    def test_not_qudit(self):
        q = Qudit.computational_basis(0, 2)
        assert q.__eq__("not a qudit") is NotImplemented
