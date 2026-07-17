"""Coverage tests for core.extended_channels (was 59%).

Exercises ExtendedQuantumChannel with all noise models, eavesdropping,
statistics, and edge cases.
"""

import pytest

from qkdpy.core import Qubit
from qkdpy.core.extended_channels import ExtendedQuantumChannel


class TestExtendedQuantumChannel:
    """ExtendedQuantumChannel test cases."""

    # ── Construction ──────────────────────────────────────────────────

    def test_default_construction(self) -> None:
        ch = ExtendedQuantumChannel()
        assert ch.loss == 0.0
        assert ch.noise_level == 0.0
        assert ch.noise_model == "depolarizing"
        assert ch.eavesdropper is None

    def test_construction_clamps_values(self) -> None:
        ch = ExtendedQuantumChannel(loss=-0.5, noise_level=2.0)
        assert ch.loss == 0.0
        assert ch.noise_level == 1.0

    def test_construction_with_eavesdropper(self) -> None:
        def eve(q: Qubit) -> tuple[Qubit, bool]:
            return q, False

        ch = ExtendedQuantumChannel(eavesdropper=eve)
        assert ch.eavesdropper is not None

    # ── Transmit without loss ─────────────────────────────────────────

    def test_transmit_no_noise(self) -> None:
        ch = ExtendedQuantumChannel(noise_level=0.0)
        q = Qubit(1.0, 0.0)
        result = ch.transmit(q)
        assert result is not None
        assert abs(result.state[0] - 1.0) < 1e-10
        assert ch.transmitted_count == 1

    def test_transmit_complete_loss(self) -> None:
        ch = ExtendedQuantumChannel(loss=1.0)
        q = Qubit(1.0, 0.0)
        result = ch.transmit(q)
        assert result is None
        assert ch.lost_count == 1

    # ── All noise models ──────────────────────────────────────────────

    @pytest.mark.parametrize(
        "noise_model",
        [
            "depolarizing",
            "bit_flip",
            "phase_flip",
            "amplitude_damping",
            "phase_damping",
            "generalized_amplitude_damping",
        ],
    )
    def test_transmit_with_noise(self, noise_model: str) -> None:
        ch = ExtendedQuantumChannel(loss=0.0, noise_model=noise_model, noise_level=1.0)
        q = Qubit(1.0, 0.0)
        result = ch.transmit(q)
        # At noise_level=1.0 the qubit may be altered, but should still
        # be returned (not None, since loss=0).
        assert result is not None
        assert ch.transmitted_count == 1

    # ── Eavesdropping ─────────────────────────────────────────────────

    def test_eavesdropper_detected(self) -> None:
        def eve(q: Qubit) -> tuple[Qubit, bool]:
            return q, True

        ch = ExtendedQuantumChannel(loss=0.0, eavesdropper=eve)
        q = Qubit(1.0, 0.0)
        result = ch.transmit(q)
        assert result is not None
        assert ch.eavesdropped_count == 1
        assert ch.eavesdropper_detected is True

    def test_eavesdropper_not_detected(self) -> None:
        def eve(q: Qubit) -> tuple[Qubit, bool]:
            return q, False

        ch = ExtendedQuantumChannel(loss=0.0, eavesdropper=eve)
        q = Qubit(1.0, 0.0)
        result = ch.transmit(q)
        assert result is not None
        assert ch.eavesdropped_count == 1
        assert ch.eavesdropper_detected is False

    # ── Statistics ────────────────────────────────────────────────────

    def test_get_statistics_after_transmit(self) -> None:
        ch = ExtendedQuantumChannel(loss=0.5, noise_level=0.5)
        q = Qubit(1.0, 0.0)
        for _ in range(10):
            ch.transmit(q)
        stats = ch.get_statistics()
        assert stats["transmitted"] == 10
        assert 0 <= stats["loss_rate"] <= 1.0
        assert 0 <= stats["error_rate"] <= 1.0

    def test_reset_statistics(self) -> None:
        ch = ExtendedQuantumChannel(loss=0.5)
        q = Qubit(1.0, 0.0)
        ch.transmit(q)
        assert ch.transmitted_count > 0
        ch.reset_statistics()
        assert ch.transmitted_count == 0
        assert ch.lost_count == 0
        assert ch.error_count == 0
        assert ch.eavesdropped_count == 0
        assert ch.eavesdropper_detected is False

    # ── set_eavesdropper ──────────────────────────────────────────────

    def test_set_and_remove_eavesdropper(self) -> None:
        ch = ExtendedQuantumChannel()
        assert ch.eavesdropper is None

        def eve(q: Qubit) -> tuple[Qubit, bool]:
            return q, False

        ch.set_eavesdropper(eve)
        assert ch.eavesdropper is not None
        ch.set_eavesdropper(None)
        assert ch.eavesdropper is None
