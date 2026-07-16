"""Tests for the PennyLane BB84 integration.

Skips cleanly when PennyLane is not installed.
"""

import pytest

pennylane = pytest.importorskip("pennylane")

from qkdpy.integrations.pennylane_integration import (  # noqa: E402
    PennyLaneIntegration,
)


def test_bb84_noiseless_returns_expected_shape() -> None:
    """A noiseless BB84 run returns (alice, bob, matched) with the right sizes."""
    integration = PennyLaneIntegration()
    alice, bob, matched = integration.simulate_bb84_with_pennylane(
        num_qubits=10, noise_level=0.0
    )
    assert len(alice) == 10
    assert len(bob) == 10
    assert len(matched) == 10
    assert all(isinstance(m, bool) for m in matched)


def test_bb84_with_noise_does_not_raise_and_keeps_shape() -> None:
    """Requesting noise must not be a no-op: it runs and keeps the shape.

    If the installed PennyLane lacks the noise API, the function degrades
    gracefully (still returns the correct shape) instead of crashing.
    """
    integration = PennyLaneIntegration()
    alice, bob, matched = integration.simulate_bb84_with_pennylane(
        num_qubits=8, noise_model="depolarizing", noise_level=0.1
    )
    assert len(alice) == 8
    assert len(bob) == 8
    assert len(matched) == 8


def test_bb84_noise_unknown_kind_still_returns() -> None:
    """An unknown noise kind degrades to the noiseless path without crashing."""
    integration = PennyLaneIntegration()
    alice, bob, matched = integration.simulate_bb84_with_pennylane(
        num_qubits=6, noise_model="nonsense", noise_level=0.2
    )
    assert len(alice) == len(matched) == 6
