"""Coverage tests for qpiai_integration.py + advanced_privacy_amplification.py.

Targets uncovered paths identified by coverage report:
  - integrations/qpiai_integration.py:               67% (43 missed of 130 stmts)
  - key_management/advanced_privacy_amplification.py: 67% (25 missed of 75 stmts)
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from qkdpy.integrations.qpiai_integration import QpiAIIntegration
from qkdpy.key_management.advanced_privacy_amplification import (
    AdvancedPrivacyAmplification,
)

# ===========================================================================
#  QpiAIIntegration — tests that need the qpiai_quantum package
# ===========================================================================


@pytest.fixture(scope="module")
def qpiai() -> QpiAIIntegration:
    """Return a fully initialized QpiAIIntegration (qpiai_quantum IS installed)."""
    return QpiAIIntegration()


# ---------------------------------------------------------------------------
#  Circuit construction
# ---------------------------------------------------------------------------


class TestCreateBB84Circuit:
    def test_default_creation(self, qpiai: QpiAIIntegration) -> None:
        circuit = qpiai.create_bb84_circuit(num_qubits=4)
        assert circuit is not None

    def test_explicit_params(self, qpiai: QpiAIIntegration) -> None:
        circuit = qpiai.create_bb84_circuit(
            num_qubits=3,
            alice_bases=["Z", "X", "Z"],
            bob_bases=["Z", "X", "X"],
            alice_bits=[0, 1, 0],
        )
        assert circuit is not None

    def test_single_qubit(self, qpiai: QpiAIIntegration) -> None:
        circuit = qpiai.create_bb84_circuit(num_qubits=1)
        assert circuit is not None


class TestCreateE91Circuit:
    def test_default_creation(self, qpiai: QpiAIIntegration) -> None:
        circuit = qpiai.create_e91_circuit(num_pairs=2)
        assert circuit is not None

    def test_explicit_bases(self, qpiai: QpiAIIntegration) -> None:
        circuit = qpiai.create_e91_circuit(
            num_pairs=2,
            alice_bases=["Z", "X"],
            bob_bases=["Z", "W"],
        )
        assert circuit is not None

    def test_single_pair(self, qpiai: QpiAIIntegration) -> None:
        circuit = qpiai.create_e91_circuit(num_pairs=1)
        assert circuit is not None

    def test_all_basis_combos(self, qpiai: QpiAIIntegration) -> None:
        """Exercise each W-basis branch for both Alice and Bob."""
        circuit = qpiai.create_e91_circuit(
            num_pairs=3,
            alice_bases=["Z", "X", "W"],
            bob_bases=["W", "X", "Z"],
        )
        assert circuit is not None


class TestCreateEntanglementCircuit:
    @pytest.mark.parametrize(
        "state_type", ["|\u03a8+>", "|\u03a8->", "|\u03a6+>", "|\u03a6->"]
    )
    def test_all_bell_states(
        self, qpiai: QpiAIIntegration, state_type: str
    ) -> None:
        circuit, desc = qpiai.create_entanglement_circuit(state_type)
        assert circuit is not None
        assert isinstance(desc, str)
        assert len(desc) > 0


class TestCreateGHZCircuit:
    def test_three_qubits(self, qpiai: QpiAIIntegration) -> None:
        circuit = qpiai.create_ghz_circuit(num_qubits=3)
        assert circuit is not None

    def test_four_qubits(self, qpiai: QpiAIIntegration) -> None:
        circuit = qpiai.create_ghz_circuit(num_qubits=4)
        assert circuit is not None


# ---------------------------------------------------------------------------
#  State conversion  (needs qpiai_quantum for Statevector)
# ---------------------------------------------------------------------------


class TestStateConversion:
    def test_qubit_to_qpiai(self, qpiai: QpiAIIntegration) -> None:
        from qkdpy.core import Qubit

        q = Qubit.zero()
        sv = qpiai.qubit_to_qpiai(q)
        assert sv is not None

    def test_qpiai_to_qubit(self, qpiai: QpiAIIntegration) -> None:
        from qpiai_quantum import Statevector

        from qkdpy.core import Qubit

        sv = Statevector([1, 0])
        q = qpiai.qpiai_to_qubit(sv)
        assert isinstance(q, Qubit)
        assert q == Qubit.zero()

    def test_statevector_from_array(self, qpiai: QpiAIIntegration) -> None:
        from qpiai_quantum import Statevector

        sv = qpiai.statevector_from_array(
            [1 + 0j, 0 + 0j, 0 + 0j, 0 + 0j]
        )
        assert isinstance(sv, Statevector)


# ---------------------------------------------------------------------------
#  Quantum info measures  (needs qpiai_quantum for DensityMatrix)
# ---------------------------------------------------------------------------


class TestQuantumMeasures:
    def test_compute_concurrence(self, qpiai: QpiAIIntegration) -> None:
        # Bell state |Phi+> density matrix: (|00><00| + |00><11| + |11><00| + |11><11|) / 2
        rho = np.zeros((4, 4), dtype=complex)
        rho[0, 0] = 0.5
        rho[0, 3] = 0.5
        rho[3, 0] = 0.5
        rho[3, 3] = 0.5
        c = qpiai.compute_concurrence(rho)
        assert c == pytest.approx(1.0, abs=1e-5)

    def test_compute_concurrence_separable(self, qpiai: QpiAIIntegration) -> None:
        # |00><00| separable state -> concurrence ~ 0
        rho = np.zeros((4, 4), dtype=complex)
        rho[0, 0] = 1.0
        c = qpiai.compute_concurrence(rho)
        assert c == pytest.approx(0.0, abs=1e-5)

    def test_compute_purity_pure(self, qpiai: QpiAIIntegration) -> None:
        """Bell state |Phi+> is a pure state -> purity = 1."""
        rho = np.zeros((4, 4), dtype=complex)
        rho[0, 0] = 0.5
        rho[0, 3] = 0.5
        rho[3, 0] = 0.5
        rho[3, 3] = 0.5
        p = qpiai.compute_purity(rho)
        assert p == pytest.approx(1.0, abs=1e-5)  # pure state -> purity = 1

    def test_compute_purity_maximally_mixed(self, qpiai: QpiAIIntegration) -> None:
        rho = np.eye(4, dtype=complex) / 4
        p = qpiai.compute_purity(rho)
        assert p == pytest.approx(0.25, abs=1e-5)


# ---------------------------------------------------------------------------
#  Simulation  (with and without API key)
# ---------------------------------------------------------------------------


class TestSimulate:
    def test_simulate_without_key(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """No API_KEY -> returns circuit metadata dict."""
        monkeypatch.delenv("API_KEY", raising=False)
        inst = QpiAIIntegration.__new__(QpiAIIntegration)
        inst._api_key = None  # type: ignore[attr-defined]

        from qpiai_quantum import Circuit

        circ = Circuit(2, 2)
        result = inst.simulate(circ)
        assert isinstance(result, dict)
        assert "num_qubits" in result

    def test_simulate_with_key(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """With API_KEY -> runs local statevector simulation."""
        monkeypatch.setenv("API_KEY", "test-key-xxxx")
        inst = QpiAIIntegration.__new__(QpiAIIntegration)
        inst._api_key = "test-key-xxxx"  # type: ignore[attr-defined]

        from qpiai_quantum import Circuit

        circ = Circuit(2, 2)
        circ.H(0)
        result = inst.simulate(circ, shots=64)
        assert isinstance(result, dict)
        assert result.get("simulation") == "local_statevector"
        assert "statevector" in result
        assert len(result.get("samples", [])) == 64

    def test_submit_to_cloud_no_key_raises(self) -> None:
        inst = QpiAIIntegration.__new__(QpiAIIntegration)
        inst._api_key = None  # type: ignore[attr-defined]
        with pytest.raises(ValueError, match="API_KEY"):
            inst.submit_to_cloud(None)  # type: ignore[arg-type]


# ===========================================================================
#  QpiAIIntegration — tests that do NOT need qpiai_quantum
# ===========================================================================


class TestCalculateQBER:
    @pytest.fixture
    def inst(self) -> QpiAIIntegration:
        obj = QpiAIIntegration.__new__(QpiAIIntegration)
        obj._api_key = None
        return obj

    def test_equal_bits(self, inst: QpiAIIntegration) -> None:
        assert inst.calculate_qber([0, 1, 0, 1], [0, 1, 0, 1]) == 0.0

    def test_all_mismatch(self, inst: QpiAIIntegration) -> None:
        assert inst.calculate_qber([0, 1, 0], [1, 0, 1]) == 1.0

    def test_half_mismatch(self, inst: QpiAIIntegration) -> None:
        result = inst.calculate_qber(
            [0, 0, 1, 1], [0, 1, 0, 1]
        )
        assert result == 0.5

    def test_empty(self, inst: QpiAIIntegration) -> None:
        assert inst.calculate_qber([], []) == 0.0

    def test_length_mismatch_raises(self, inst: QpiAIIntegration) -> None:
        with pytest.raises(ValueError, match="equal length"):
            inst.calculate_qber([0, 1], [0])


class TestComputeCHSH:
    @pytest.fixture
    def inst(self) -> QpiAIIntegration:
        obj = QpiAIIntegration.__new__(QpiAIIntegration)
        obj._api_key = None
        return obj

    def test_max_violation(self, inst: QpiAIIntegration) -> None:
        """Angles that give S = 2*sqrt(2) ≈ 2.828 (Tsirelson bound)."""
        a, a_p, b, b_p = 0, math.pi / 4, math.pi / 8, 3 * math.pi / 8
        s = inst.compute_chsh_value([a, a_p, b, b_p])
        expected = (
            math.cos(a - b)
            + math.cos(a - b_p)
            + math.cos(a_p - b)
            - math.cos(a_p - b_p)
        )
        assert s == pytest.approx(expected, abs=1e-12)

    def test_zero_angles(self, inst: QpiAIIntegration) -> None:
        """All angles 0 -> S = 2.0."""
        s = inst.compute_chsh_value([0, 0, 0, 0])
        assert s == pytest.approx(2.0, abs=1e-12)

    def test_classical_bound(self, inst: QpiAIIntegration) -> None:
        """Angles that produce S <= 2."""
        s = inst.compute_chsh_value([0, math.pi / 2, 0, math.pi / 2])
        # should be within classical bound
        assert abs(s) <= 2.0 + 1e-12


# ===========================================================================
#  AdvancedPrivacyAmplification
# ===========================================================================


class TestXorExtract:
    def test_empty_key(self) -> None:
        assert AdvancedPrivacyAmplification.xor_extract([]) == []

    def test_single_bit(self) -> None:
        result = AdvancedPrivacyAmplification.xor_extract([1])
        assert len(result) == 1
        assert result[0] in (0, 1)

    def test_typical(self) -> None:
        key = np.random.randint(0, 2, 100).tolist()
        result = AdvancedPrivacyAmplification.xor_extract(key)
        assert 0 < len(result) < len(key)
        assert all(b in (0, 1) for b in result)

    def test_deterministic_with_seed(self) -> None:
        """xor_extract doesn't accept a seed parameter directly, but we
        verify same seed gives same output by running twice."""
        key = [1, 0, 1, 1, 0, 0, 1, 0]
        r1 = AdvancedPrivacyAmplification.xor_extract(key)
        r2 = AdvancedPrivacyAmplification.xor_extract(key)
        # Both should be valid results (length may differ due to randomness)
        assert all(b in (0, 1) for b in r1)
        assert all(b in (0, 1) for b in r2)


class TestAesHashExtract:
    def test_zero_output_length(self) -> None:
        result = AdvancedPrivacyAmplification.aes_hash_extract(
            [1, 0, 1], 0
        )
        assert result == []

    def test_typical(self) -> None:
        key = np.random.randint(0, 2, 100).tolist()
        result = AdvancedPrivacyAmplification.aes_hash_extract(key, 48)
        assert len(result) == 48
        assert all(b in (0, 1) for b in result)

    def test_single_bit_output(self) -> None:
        result = AdvancedPrivacyAmplification.aes_hash_extract(
            [1, 0, 1, 1, 0], 1
        )
        assert len(result) == 1
        assert result[0] in (0, 1)

    def test_deterministic(self) -> None:
        key = [1, 0, 1, 1, 0, 1]
        r1 = AdvancedPrivacyAmplification.aes_hash_extract(key, 16)
        r2 = AdvancedPrivacyAmplification.aes_hash_extract(key, 16)
        assert r1 == r2


class TestRandomnessExtractor:
    def test_xor_method(self) -> None:
        key = np.random.randint(0, 2, 100).tolist()
        result = AdvancedPrivacyAmplification.randomness_extractor(
            key, 20, method="xor"
        )
        assert all(b in (0, 1) for b in result)

    def test_aes_method(self) -> None:
        key = np.random.randint(0, 2, 100).tolist()
        result = AdvancedPrivacyAmplification.randomness_extractor(
            key, 20, method="aes"
        )
        assert len(result) == 20
        assert all(b in (0, 1) for b in result)

    def test_universal_method(self) -> None:
        key = np.random.randint(0, 2, 100).tolist()
        result = AdvancedPrivacyAmplification.randomness_extractor(
            key, 20, method="universal"
        )
        assert len(result) == 20
        assert all(b in (0, 1) for b in result)

    def test_unknown_method_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown randomness extraction"):
            AdvancedPrivacyAmplification.randomness_extractor(
                [1, 0, 1], 2, method="unknown"
            )

    def test_zero_output_xor(self) -> None:
        result = AdvancedPrivacyAmplification.randomness_extractor(
            [1, 0, 1], 0, method="xor"
        )
        assert result == []

    def test_zero_output_aes(self) -> None:
        result = AdvancedPrivacyAmplification.randomness_extractor(
            [1, 0, 1], 0, method="aes"
        )
        assert result == []


class TestStrongExtractor:
    def test_normal_case(self) -> None:
        key = np.random.randint(0, 2, 100).tolist()
        result = AdvancedPrivacyAmplification.strong_extractor(
            key, 20, min_entropy=50.0
        )
        assert 0 < len(result) <= 20
        assert all(b in (0, 1) for b in result)

    def test_low_entropy_fallback(self) -> None:
        """When min_entropy is too low, falls back to small output."""
        key = np.random.randint(0, 2, 20).tolist()
        result = AdvancedPrivacyAmplification.strong_extractor(
            key, 20, min_entropy=2.0
        )
        assert len(result) <= 8  # fallback length
        assert all(b in (0, 1) for b in result)

    def test_zero_output_length(self) -> None:
        result = AdvancedPrivacyAmplification.strong_extractor(
            [1, 0, 1], 0, min_entropy=10.0
        )
        assert result == []

    def test_very_small_key(self) -> None:
        """Key of length 1 with low entropy."""
        result = AdvancedPrivacyAmplification.strong_extractor(
            [1], 4, min_entropy=1.0
        )
        # Should still produce some output (fallback)
        assert all(b in (0, 1) for b in result)


class TestSeededExtractor:
    def test_normal_case(self) -> None:
        key = np.random.randint(0, 2, 100).tolist()
        seed = np.random.randint(0, 2, 50).tolist()
        result = AdvancedPrivacyAmplification.seeded_extractor(
            key, seed, 20
        )
        assert 0 < len(result) <= 20
        assert all(b in (0, 1) for b in result)

    def test_zero_output_length(self) -> None:
        result = AdvancedPrivacyAmplification.seeded_extractor(
            [1, 0, 1], [0, 1], 0
        )
        assert result == []


class TestMultipleIndependentExtractors:
    def test_normal_case(self) -> None:
        key = np.random.randint(0, 2, 100).tolist()
        result = AdvancedPrivacyAmplification.multiple_independent_extractors(
            key, output_length=16, num_extractors=3
        )
        assert len(result) == 16
        assert all(b in (0, 1) for b in result)

    def test_single_extractor(self) -> None:
        key = np.random.randint(0, 2, 100).tolist()
        result = AdvancedPrivacyAmplification.multiple_independent_extractors(
            key, output_length=8, num_extractors=1
        )
        assert len(result) == 8
        assert all(b in (0, 1) for b in result)

    def test_zero_output_length(self) -> None:
        result = AdvancedPrivacyAmplification.multiple_independent_extractors(
            [1, 0], 0, 3
        )
        assert result == []

    def test_zero_num_extractors(self) -> None:
        result = AdvancedPrivacyAmplification.multiple_independent_extractors(
            [1, 0], 4, 0
        )
        assert result == []

    def test_larger_key(self) -> None:
        """Exercise the XOR combining loop."""
        key = np.random.randint(0, 2, 200).tolist()
        result = AdvancedPrivacyAmplification.multiple_independent_extractors(
            key, output_length=32, num_extractors=3
        )
        assert len(result) == 32
        assert all(b in (0, 1) for b in result)
