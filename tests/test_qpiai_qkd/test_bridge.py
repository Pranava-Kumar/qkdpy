"""Tests for the qpiai-qkd companion bridge (real-SDK-correct)."""

import math

import numpy as np
import pytest

from qkdpy.integrations.qpiai_qkd import QpiAIIntegration, qpiai_available
from qkdpy.integrations.qpiai_qkd._compat import QpiAISDKError

pytestmark = pytest.mark.skipif(
    not qpiai_available(), reason="qpiai_quantum SDK not installed"
)

from qpiai_quantum import Statevector  # noqa: E402


def _bell_dm() -> np.ndarray:
    s = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)
    return np.outer(s, s.conj())


def _zero_dm() -> np.ndarray:
    s = np.array([1, 0, 0, 0], dtype=complex)
    return np.outer(s, s.conj())


def test_concurrence_bell_is_one():
    qi = QpiAIIntegration()
    assert abs(qi.compute_concurrence(_bell_dm()) - 1.0) < 1e-9


def test_concurrence_separable_is_zero():
    qi = QpiAIIntegration()
    assert abs(qi.compute_concurrence(_zero_dm()) - 0.0) < 1e-9


def test_purity_bell_is_one():
    qi = QpiAIIntegration()
    assert abs(qi.compute_purity(_bell_dm()) - 1.0) < 1e-9


def test_concurrence_rejects_wrong_shape():
    qi = QpiAIIntegration()
    with pytest.raises(ValueError):
        qi.compute_concurrence(np.array([1, 0], dtype=complex))


def test_qber_basic():
    qi = QpiAIIntegration()
    assert qi.calculate_qber([0, 1, 0, 1], [0, 1, 0, 1]) == 0.0
    assert qi.calculate_qber([0, 1], [1, 0]) == 1.0
    # One mismatch in four bits -> 0.25
    assert qi.calculate_qber([0, 1, 0, 1], [0, 0, 0, 1]) == 0.25


def test_qber_length_mismatch_raises():
    qi = QpiAIIntegration()
    with pytest.raises(ValueError):
        qi.calculate_qber([0, 1], [0])


def test_chsh_violates_classical_bound():
    qi = QpiAIIntegration()
    # Exhaustively find the maximum of our CHSH form over the angle grid and
    # confirm it reaches the Tsirelson bound 2*sqrt(2).
    best = -9.0
    for a in np.linspace(0, math.pi, 24):
        for ap in np.linspace(0, math.pi, 24):
            for b in np.linspace(0, math.pi, 24):
                for bp in np.linspace(0, math.pi, 24):
                    best = max(best, qi.compute_chsh_value([a, ap, b, bp]))
    assert best > 2.0
    assert abs(best - 2 * math.sqrt(2)) < 0.05


def test_chsh_zero_angles_is_two():
    qi = QpiAIIntegration()
    assert abs(qi.compute_chsh_value([0, 0, 0, 0]) - 2.0) < 1e-9


def test_chsh_requires_four_angles():
    qi = QpiAIIntegration()
    with pytest.raises(ValueError):
        qi.compute_chsh_value([0, math.pi / 2])


def test_bb84_circuit_metadata_without_key():
    qi = QpiAIIntegration()
    circuit = qi.create_bb84_circuit(num_qubits=4)
    result = qi.simulate(circuit)
    assert "num_qubits" in result
    # No key -> inspectable metadata, no crash (bug #1 fixed).
    assert result["num_qubits"] == 4


def test_simulate_with_key_returns_state_info(monkeypatch):
    monkeypatch.setenv("QPIAI_API_KEY", "dummy-key")
    qi = QpiAIIntegration()
    circuit = qi.create_bb84_circuit(num_qubits=2)
    result = qi.simulate(circuit)
    assert result["simulation"] == "local_statevector"
    assert len(result["statevector"]) == 4


def test_submit_to_cloud_no_key_raises_value_error():
    qi = QpiAIIntegration()
    with pytest.raises(ValueError, match="API_KEY"):
        qi.submit_to_cloud(None)


def test_submit_to_cloud_with_key_surfaces_real_error(monkeypatch):
    # A fake key must NOT produce a silent AttributeError; the real SDK method
    # is used and its (genuine) failure is surfaced (bug #3 fixed).
    monkeypatch.setenv("QPIAI_API_KEY", "not-a-real-key")
    qi = QpiAIIntegration()
    circuit = qi.create_bb84_circuit(num_qubits=2)
    with pytest.raises((QpiAISDKError, ValueError)):
        qi.submit_to_cloud(circuit)


def test_qubit_round_trip():
    from qkdpy.core.qubit import Qubit

    qi = QpiAIIntegration()
    q = Qubit(alpha=1 / math.sqrt(2), beta=1 / math.sqrt(2))
    sv = qi.qubit_to_qpiai(q)
    assert isinstance(sv, Statevector)
    back = qi.qpiai_to_qubit(sv)
    assert abs(back.state[0] - q.state[0]) < 1e-9


def test_entanglement_circuit_description():
    qi = QpiAIIntegration()
    _, desc = qi.create_entanglement_circuit("|Ψ+>")
    assert "01" in desc
    _, desc2 = qi.create_entanglement_circuit("|Φ+>")
    assert "00" in desc2
