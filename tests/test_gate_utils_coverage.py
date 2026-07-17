"""Coverage tests for core/gate_utils.py (was 71%)."""

import numpy as np
import pytest

from qkdpy.core.gate_utils import GateUtils


class TestBasisSwitch:
    def test_computational(self):
        """basis_switch('computational') returns identity."""
        m = GateUtils.basis_switch("computational")
        assert np.allclose(m, np.eye(2, dtype=complex))

    def test_hadamard(self):
        m = GateUtils.basis_switch("hadamard")
        expected = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
        assert np.allclose(m, expected)

    def test_circular(self):
        m = GateUtils.basis_switch("circular")
        expected = np.array([[1, -1j], [1, 1j]], dtype=complex) / np.sqrt(2)
        assert np.allclose(m, expected)

    def test_invalid_basis(self):
        with pytest.raises(ValueError, match="Basis must be"):
            GateUtils.basis_switch("unknown")

    def test_all_unitary(self):
        for basis in ("computational", "hadamard", "circular"):
            m = GateUtils.basis_switch(basis)
            assert GateUtils.is_unitary(m), f"{basis} basis switch is not unitary"


class TestRandomUnitary:
    def test_is_unitary(self):
        for _ in range(10):
            u = GateUtils.random_unitary()
            assert GateUtils.is_unitary(
                u
            ), "random_unitary should produce unitary matrices"

    def test_shape(self):
        u = GateUtils.random_unitary()
        assert u.shape == (2, 2)

    def test_different_calls_different(self):
        """High probability check that two calls differ."""
        u1 = GateUtils.random_unitary()
        u2 = GateUtils.random_unitary()
        assert not np.allclose(u1, u2)


class TestUnitaryFromAngles:
    def test_identity(self):
        """theta=0, phi=0, lam=0 should give identity."""
        u = GateUtils.unitary_from_angles(0.0, 0.0, 0.0)
        assert np.allclose(u, np.eye(2, dtype=complex))

    def test_pauli_x(self):
        """theta=pi, phi=0, lam=0 gives Pauli-X up to global phase."""
        u = GateUtils.unitary_from_angles(np.pi, 0.0, 0.0)
        pauli_x = np.array([[0, 1], [1, 0]], dtype=complex)
        # U should equal PauliX * global phase
        assert np.allclose(np.abs(u), np.abs(pauli_x))

    def test_is_unitary(self):
        for theta in [0.0, np.pi / 2, np.pi]:
            for phi in [0.0, np.pi / 3]:
                for lam in [0.0, np.pi / 4]:
                    u = GateUtils.unitary_from_angles(theta, phi, lam)
                    assert GateUtils.is_unitary(u)

    def test_rz_gate(self):
        """theta=0, phi=lam=pi/2 gives Pauli-Z (diag(1, -1))."""
        u = GateUtils.unitary_from_angles(0.0, np.pi / 2, np.pi / 2)
        # θ=0 → U = diag(1, exp(i(φ+λ))) = diag(1, exp(iπ)) = diag(1, -1)
        expected = np.array([[1, 0], [0, -1]], dtype=complex)
        assert np.allclose(u, expected)


class TestSequence:
    def test_single_gate(self):
        eye = np.eye(2, dtype=complex)
        result = GateUtils.sequence(eye)
        assert np.allclose(result, eye)

    def test_two_gates(self):
        H = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
        result = GateUtils.sequence(H, H)
        # H @ H = I
        assert np.allclose(result, np.eye(2, dtype=complex), atol=1e-10)

    def test_three_gates(self):
        X = np.array([[0, 1], [1, 0]], dtype=complex)
        Z = np.array([[1, 0], [0, -1]], dtype=complex)
        # X then Z then X
        result = GateUtils.sequence(X, Z, X)
        # X @ Z @ X = -Z  (up to global phase)
        assert np.allclose(result, -Z)

    def test_composition_order(self):
        """sequence(A, B) applies B after A: B @ A."""
        X = np.array([[0, 1], [1, 0]], dtype=complex)
        H = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
        manual = H @ X
        result = GateUtils.sequence(X, H)
        assert np.allclose(result, manual)


class TestTensorProduct:
    def test_two_qubit(self):
        eye = np.eye(2, dtype=complex)
        result = GateUtils.tensor_product(eye, eye)
        assert np.allclose(result, np.eye(4, dtype=complex))

    def test_single(self):
        eye = np.eye(2, dtype=complex)
        result = GateUtils.tensor_product(eye)
        assert np.allclose(result, eye)

    def test_x_and_i(self):
        X = np.array([[0, 1], [1, 0]], dtype=complex)
        eye = np.eye(2, dtype=complex)
        result = GateUtils.tensor_product(X, eye)
        expected = np.kron(X, eye)
        assert np.allclose(result, expected)

    def test_three_gates(self):
        X = np.array([[0, 1], [1, 0]], dtype=complex)
        Z = np.array([[1, 0], [0, -1]], dtype=complex)
        H = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
        result = GateUtils.tensor_product(X, Z, H)
        expected = np.kron(np.kron(X, Z), H)
        assert np.allclose(result, expected)


class TestIsUnitary:
    def test_identity(self):
        assert GateUtils.is_unitary(np.eye(2, dtype=complex)) is True

    def test_pauli(self):
        X = np.array([[0, 1], [1, 0]], dtype=complex)
        assert GateUtils.is_unitary(X) is True

    def test_non_square(self):
        assert GateUtils.is_unitary(np.array([[1, 0]])) is False

    def test_non_unitary(self):
        m = np.array([[1, 0], [0, 0]], dtype=complex)
        assert GateUtils.is_unitary(m) is False

    def test_custom_tolerance(self):
        near_identity = np.eye(2, dtype=complex) + 1e-8 * np.random.randn(2, 2)
        assert GateUtils.is_unitary(near_identity, tol=1e-6) is True

    def test_larger_matrix(self):
        """4x4 CNOT should also be unitary."""
        cnot = np.array(
            [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]], dtype=complex
        )
        assert GateUtils.is_unitary(cnot) is True


class TestIsHermitian:
    def test_pauli(self):
        X = np.array([[0, 1], [1, 0]], dtype=complex)
        Z = np.array([[1, 0], [0, -1]], dtype=complex)
        assert GateUtils.is_hermitian(X) is True
        assert GateUtils.is_hermitian(Z) is True

    def test_identity(self):
        assert GateUtils.is_hermitian(np.eye(2, dtype=complex)) is True

    def test_non_hermitian(self):
        m = np.array([[0, 1], [0, 0]], dtype=complex)
        assert GateUtils.is_hermitian(m) is False

    def test_non_square(self):
        assert GateUtils.is_hermitian(np.array([[1, 0, 0]])) is False

    def test_hadamard(self):
        H = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
        assert GateUtils.is_hermitian(H) is True

    def test_custom_tolerance(self):
        near_I = np.eye(2, dtype=complex) + 1e-8 * np.random.randn(2, 2)
        near_I = near_I + near_I.conj().T  # Force Hermitian
        assert GateUtils.is_hermitian(near_I, tol=1e-6) is True
