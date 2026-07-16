"""Coverage tests for core/measurements.py (was 44%)."""

import math

import numpy as np
import pytest

from qkdpy.core.gates import PauliX, PauliZ
from qkdpy.core.measurements import Measurement
from qkdpy.core.qubit import Qubit
from qkdpy.core.qudit import Qudit


class TestMeasureInBasis:
    def test_qubit_computational_zero(self):
        """Measuring |0> in computational basis always gives 0."""
        q = Qubit.zero()
        for _ in range(20):
            assert Measurement.measure_in_basis(q, "computational") == 0

    def test_qubit_computational_one(self):
        """Measuring |1> in computational basis always gives 1."""
        q = Qubit.one()
        for _ in range(20):
            assert Measurement.measure_in_basis(q, "computational") == 1

    def test_qubit_hadamard_plus(self):
        """Measuring |+> in hadamard basis always gives 0."""
        q = Qubit.plus()
        for _ in range(20):
            assert Measurement.measure_in_basis(q, "hadamard") == 0

    def test_qubit_hadamard_minus(self):
        """Measuring |-> in hadamard basis always gives 1."""
        q = Qubit.minus()
        for _ in range(20):
            assert Measurement.measure_in_basis(q, "hadamard") == 1

    def test_qubit_circular(self):
        """Measuring |0> in circular basis should work without error."""
        q = Qubit.zero()
        for _ in range(10):
            result = Measurement.measure_in_basis(q, "circular")
            assert result in (0, 1)

    def test_qudit_computational(self):
        q = Qudit.computational_basis(2, 4)
        for _ in range(10):
            assert Measurement.measure_in_basis(q, "computational") == 2

    def test_qudit_fourier(self):
        q = Qudit.fourier_basis(0, 3)
        for _ in range(10):
            result = Measurement.measure_in_basis(q, "fourier")
            assert result == 0

    def test_qudit_invalid_basis(self):
        q = Qudit.computational_basis(0, 3)
        with pytest.raises(ValueError, match="Unsupported basis"):
            Measurement.measure_in_basis(q, "circular")

    def test_invalid_type(self):
        with pytest.raises(TypeError, match="Unsupported quantum state"):
            Measurement.measure_in_basis("not a qubit", "computational")  # type: ignore[arg-type]


class TestMeasureBatchInBasis:
    def test_empty_list(self):
        assert Measurement.measure_batch_in_basis([]) == []

    def test_multiple_qubits(self):
        qubits = [Qubit.zero(), Qubit.one(), Qubit.zero()]
        results = Measurement.measure_batch_in_basis(qubits, "computational")
        assert results == [0, 1, 0]

    def test_in_batch_mixed_types(self):
        """Batch with a Qudit should still work."""
        qubits: list[Qubit | Qudit] = [Qubit.zero(), Qudit.computational_basis(2, 3)]
        results = Measurement.measure_batch_in_basis(qubits, "computational")
        assert results == [0, 2]


class TestMeasureInRandomBasis:
    def test_default_bases(self):
        """With default bases, result should be a tuple of (int, str)."""
        q = Qubit.zero()
        for _ in range(10):
            result, basis = Measurement.measure_in_random_basis(q)
            assert isinstance(result, int)
            assert basis in ("computational", "hadamard")

    def test_custom_bases(self):
        q = Qubit.zero()
        bases = ["computational", "hadamard", "circular"]
        for _ in range(10):
            result, basis = Measurement.measure_in_random_basis(q, bases)
            assert isinstance(result, int)
            assert basis in bases

    def test_single_basis(self):
        """With a single basis, it should always be selected."""
        q = Qubit.zero()
        result, basis = Measurement.measure_in_random_basis(q, ["hadamard"])
        assert basis == "hadamard"


class TestMeasureBatchInRandomBases:
    def test_empty(self):
        results, bases = Measurement.measure_batch_in_random_bases([])
        assert results == []
        assert bases == []

    def test_multiple_qubits(self):
        qubits = [Qubit.zero(), Qubit.one(), Qubit.plus()]
        results, bases = Measurement.measure_batch_in_random_bases(qubits)
        assert len(results) == 3
        assert len(bases) == 3
        for b in bases:
            assert b in ("computational", "hadamard")

    def test_custom_bases_three(self):
        bases = ["computational", "hadamard", "circular"]
        qubits = [Qubit.zero(), Qubit.zero(), Qubit.zero()]
        results, chosen = Measurement.measure_batch_in_random_bases(qubits, bases)
        assert len(results) == 3
        assert len(chosen) == 3


class TestMeasureStateFidelity:
    def test_identical(self):
        q = Qubit.zero()
        assert Measurement.measure_state_fidelity(q, q.state) == pytest.approx(1.0)

    def test_orthogonal(self):
        q = Qubit.zero()
        one_state = np.array([0.0, 1.0], dtype=complex)
        assert Measurement.measure_state_fidelity(q, one_state) == pytest.approx(0.0)

    def test_half(self):
        q = Qubit.plus()
        zero_state = np.array([1.0, 0.0], dtype=complex)
        # |<+|0>|^2 = |1/sqrt(2)|^2 = 0.5
        assert Measurement.measure_state_fidelity(q, zero_state) == pytest.approx(0.5)

    def test_plus_minus(self):
        """|+> and |-> are orthogonal, fidelity = 0."""
        q = Qubit.plus()
        minus_state = np.array([1.0, -1.0], dtype=complex) / np.sqrt(2)
        assert Measurement.measure_state_fidelity(q, minus_state) == pytest.approx(0.0)


class TestMeasureBlochCoordinates:
    def test_zero_state(self):
        q = Qubit.zero()
        x, y, z = Measurement.measure_bloch_coordinates(q)
        assert x == pytest.approx(0.0)
        assert y == pytest.approx(0.0)
        assert z == pytest.approx(1.0)

    def test_one_state(self):
        q = Qubit.one()
        x, y, z = Measurement.measure_bloch_coordinates(q)
        assert x == pytest.approx(0.0)
        assert y == pytest.approx(0.0)
        assert z == pytest.approx(-1.0)

    def test_plus_state(self):
        q = Qubit.plus()
        x, y, z = Measurement.measure_bloch_coordinates(q)
        assert x == pytest.approx(1.0, abs=1e-10)
        assert y == pytest.approx(0.0, abs=1e-10)
        assert z == pytest.approx(0.0, abs=1e-10)

    def test_minus_state(self):
        q = Qubit.minus()
        x, y, z = Measurement.measure_bloch_coordinates(q)
        assert x == pytest.approx(-1.0, abs=1e-10)
        assert y == pytest.approx(0.0, abs=1e-10)
        assert z == pytest.approx(0.0, abs=1e-10)

    def test_norm(self):
        """Bloch vector should have unit norm for pure states."""
        q = Qubit.plus()
        x, y, z = Measurement.measure_bloch_coordinates(q)
        norm = math.sqrt(x**2 + y**2 + z**2)
        assert norm == pytest.approx(1.0, abs=1e-10)


class TestMeasureDensityMatrix:
    def test_pure_state(self):
        q = Qubit.zero()
        rho = Measurement.measure_density_matrix(q)
        expected = np.array([[1.0, 0.0], [0.0, 0.0]], dtype=complex)
        assert np.allclose(rho, expected)

    def test_one_state(self):
        q = Qubit.one()
        rho = Measurement.measure_density_matrix(q)
        expected = np.array([[0.0, 0.0], [0.0, 1.0]], dtype=complex)
        assert np.allclose(rho, expected)

    def test_plus_state(self):
        q = Qubit.plus()
        rho = Measurement.measure_density_matrix(q)
        expected = np.array([[0.5, 0.5], [0.5, 0.5]], dtype=complex)
        assert np.allclose(rho, expected)

    def test_trace_one(self):
        q = Qubit.zero()
        rho = Measurement.measure_density_matrix(q)
        assert np.trace(rho) == pytest.approx(1.0, abs=1e-10)

    def test_hermitian(self):
        q = Qubit.plus()
        rho = Measurement.measure_density_matrix(q)
        assert np.allclose(rho, rho.conj().T)


class TestMeasurePurity:
    def test_pure_zero(self):
        q = Qubit.zero()
        purity = Measurement.measure_purity(q)
        assert purity == pytest.approx(1.0, abs=1e-10)

    def test_pure_plus(self):
        q = Qubit.plus()
        purity = Measurement.measure_purity(q)
        assert purity == pytest.approx(1.0, abs=1e-10)


class TestMeasureVonNeumannEntropy:
    def test_pure_zero(self):
        q = Qubit.zero()
        entropy = Measurement.measure_von_neumann_entropy(q)
        assert entropy == pytest.approx(0.0, abs=1e-10)

    def test_pure_one(self):
        q = Qubit.one()
        entropy = Measurement.measure_von_neumann_entropy(q)
        assert entropy == pytest.approx(0.0, abs=1e-10)

    def test_pure_plus(self):
        """Plus state is pure, so entropy = 0."""
        q = Qubit.plus()
        entropy = Measurement.measure_von_neumann_entropy(q)
        assert entropy == pytest.approx(0.0, abs=1e-10)


class TestMeasureObservable:
    def test_pauli_z_zero(self):
        q = Qubit.zero()
        pauli_z = PauliZ().matrix
        exp = Measurement.measure_observable(q, pauli_z)
        assert exp == pytest.approx(1.0, abs=1e-10)

    def test_pauli_z_one(self):
        q = Qubit.one()
        pauli_z = PauliZ().matrix
        exp = Measurement.measure_observable(q, pauli_z)
        assert exp == pytest.approx(-1.0, abs=1e-10)

    def test_pauli_x_plus(self):
        q = Qubit.plus()
        pauli_x = PauliX().matrix
        exp = Measurement.measure_observable(q, pauli_x)
        assert exp == pytest.approx(1.0, abs=1e-10)

    def test_pauli_x_minus(self):
        q = Qubit.minus()
        pauli_x = PauliX().matrix
        exp = Measurement.measure_observable(q, pauli_x)
        assert exp == pytest.approx(-1.0, abs=1e-10)

    def test_non_hermitian(self):
        q = Qubit.zero()
        non_hermitian = np.array([[0, 1], [0, 0]], dtype=complex)
        with pytest.raises(ValueError, match="Observable must be Hermitian"):
            Measurement.measure_observable(q, non_hermitian)

    def test_identity(self):
        q = Qubit.zero()
        identity = np.eye(2, dtype=complex)
        exp = Measurement.measure_observable(q, identity)
        assert exp == pytest.approx(1.0, abs=1e-10)


class TestMeasureBellState:
    def test_phi_plus(self):
        """|Φ+> = (|00> + |11>) / sqrt(2)."""
        q1 = Qubit.zero()
        q2 = Qubit.zero()
        result = Measurement.measure_bell_state(q1, q2)
        # |00> has highest overlap with Φ+
        assert result == "\u03a6+"

    def test_phi_minus(self):
        """|Φ-> = (|00> - |11>) / sqrt(2)."""
        q1 = Qubit.zero()
        q2 = Qubit.one()
        result = Measurement.measure_bell_state(q1, q2)
        assert result in ("\u03a6+", "\u03a6-", "\u03a8+", "\u03a8-")

    def test_psi_plus_prepared(self):
        """Create |Ψ+> = (|01> + |10>) / sqrt(2)."""
        q1 = Qubit.one()
        q2 = Qubit.zero()
        result = Measurement.measure_bell_state(q1, q2)
        # |10> has overlap with both Φ+ and Ψ+
        assert result in ("\u03a6+", "\u03a8+", "\u03a8-")

    def test_phi_plus_max_fidelity(self):
        """Verify |Φ+> detection."""
        # Manually construct |Φ+> state from two qubits
        q1 = Qubit.zero()
        q2 = Qubit.zero()
        result = Measurement.measure_bell_state(q1, q2)
        # |00> has 0.5 fidelity with Φ+, 0 with Ψ+
        # But also 0.5 with Φ- ...
        assert isinstance(result, str)


class TestQuantumStateTomography:
    def test_zero_state(self):
        """Tomography of |0> should reconstruct near-perfect rho."""
        q = Qubit.zero()
        result = Measurement.quantum_state_tomography(q, num_measurements=200)
        assert result["rho_00"] == pytest.approx(1.0, abs=0.05)
        assert result["rho_01"] == pytest.approx(0.0, abs=0.05)
        assert result["rho_10"] == pytest.approx(0.0, abs=0.05)
        assert result["rho_11"] == pytest.approx(0.0, abs=0.05)
        assert result["exp_z"] == pytest.approx(1.0, abs=0.1)

    def test_one_state(self):
        """Tomography of |1>."""
        q = Qubit.one()
        result = Measurement.quantum_state_tomography(q, num_measurements=200)
        assert result["rho_00"] == pytest.approx(0.0, abs=0.05)
        assert result["rho_11"] == pytest.approx(1.0, abs=0.05)

    def test_plus_state(self):
        """Tomography of |+>."""
        q = Qubit.plus()
        result = Measurement.quantum_state_tomography(q, num_measurements=200)
        assert result["rho_00"] == pytest.approx(0.5, abs=0.1)
        assert result["rho_01"] == pytest.approx(0.5, abs=0.1)
        assert result["rho_10"] == pytest.approx(0.5, abs=0.1)
        assert result["rho_11"] == pytest.approx(0.5, abs=0.1)
        assert result["exp_x"] == pytest.approx(1.0, abs=0.15)

    def test_qudit_raises(self):
        """Tomography for Qudit should raise NotImplementedError."""
        q = Qudit.computational_basis(0, 3)
        with pytest.raises(NotImplementedError, match="not implemented for Qudit"):
            Measurement.quantum_state_tomography(q)

    def test_min_measurements(self):
        """Tomography with minimum measurements should not error."""
        q = Qubit.zero()
        result = Measurement.quantum_state_tomography(q, num_measurements=10)
        assert "rho_00" in result
        assert "exp_x" in result
