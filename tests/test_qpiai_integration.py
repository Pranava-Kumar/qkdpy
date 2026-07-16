"""Tests for the QpiAI integration simulate() path.

Skips cleanly when the optional qpiai_quantum package is not installed.
"""

import pytest

qpiai = pytest.importorskip("qpiai_quantum")
from qpiai_quantum import Circuit  # noqa: E402

from qkdpy.integrations.qpiai_integration import QpiAIIntegration  # noqa: E402


def test_simulate_without_key_returns_metadata() -> None:
    """Without an API key, simulate() still returns a dict with num_qubits."""
    # Avoid module-level __init__ side effects by forcing a clear key.
    integration = QpiAIIntegration.__new__(QpiAIIntegration)
    integration._api_key = None  # type: ignore[attr-defined]
    circuit = Circuit(2, 2)
    result = integration.simulate(circuit)
    assert isinstance(result, dict)
    assert "num_qubits" in result


def test_simulate_with_key_returns_state_info(monkeypatch) -> None:
    """With an API key available, simulate() performs a real local simulation.

    The qpiai_quantum Statevector simulator reads the key from the API_KEY
    environment variable, so we set it for this test.
    """
    monkeypatch.setenv("API_KEY", "dummy-key")
    integration = QpiAIIntegration.__new__(QpiAIIntegration)
    integration._api_key = "dummy-key"  # type: ignore[attr-defined]

    circuit = Circuit(2, 2)
    result = integration.simulate(circuit, shots=128)

    assert isinstance(result, dict)
    # Real simulation must expose state information, not just the circuit.
    assert result.get("simulation") == "local_statevector"
    assert "statevector" in result
    assert "probabilities" in result
    assert len(result.get("samples", [])) == 128
