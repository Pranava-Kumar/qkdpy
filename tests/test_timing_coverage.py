"""Coverage tests for core.timing (was 32%).

Exercises TimingSynchronizer, PhotonTimingModel, QBERTimingAnalysis,
and ProtocolTimingManager.
"""

import pytest

from qkdpy.core.timing import (
    PhotonTimingModel,
    ProtocolTimingManager,
    QBERTimingAnalysis,
    TimingSynchronizer,
)


class TestTimingSynchronizer:
    def test_construction(self) -> None:
        ts = TimingSynchronizer()
        assert ts.clock_frequency == 1e9
        assert ts.timing_jitter == 1e-12
        assert ts.synchronization_accuracy == 1e-9
        assert ts.max_drift_rate == 1e-6
        assert isinstance(ts.alice_clock_drift, float)
        assert isinstance(ts.bob_clock_drift, float)

    def test_synchronize_clocks(self) -> None:
        ts = TimingSynchronizer()
        result = ts.synchronize_clocks(100.0)
        assert result["synchronization_time"] == 100.0
        assert result["synchronization_error"] >= 0
        assert isinstance(result["alice_offset_after_sync"], float)
        assert isinstance(result["bob_offset_after_sync"], float)

    def test_get_alice_time(self) -> None:
        ts = TimingSynchronizer()
        t = ts.get_alice_time(100.0)
        assert isinstance(t, float)

    def test_get_bob_time(self) -> None:
        ts = TimingSynchronizer()
        t = ts.get_bob_time(100.0)
        assert isinstance(t, float)

    def test_calculate_time_difference(self) -> None:
        ts = TimingSynchronizer()
        diff = ts.calculate_time_difference(100.0)
        assert isinstance(diff, float)

    def test_update_clock_drift(self) -> None:
        ts = TimingSynchronizer()
        ts.update_clock_drift()
        assert isinstance(ts.alice_clock_drift, float)
        assert isinstance(ts.bob_clock_drift, float)
        # Drift should stay within bounds
        assert abs(ts.alice_clock_drift) <= ts.max_drift_rate
        assert abs(ts.bob_clock_drift) <= ts.max_drift_rate


class TestPhotonTimingModel:
    def test_construction(self) -> None:
        ptm = PhotonTimingModel(fiber_length=1000)
        assert ptm.fiber_length == 1000
        assert ptm.propagation_time > 0

    def test_emit_photon(self) -> None:
        ptm = PhotonTimingModel(fiber_length=1000)
        emitted = ptm.emit_photon(0.0)
        assert isinstance(emitted, float)

    def test_detect_photon(self) -> None:
        ptm = PhotonTimingModel(fiber_length=1000)
        detected = ptm.detect_photon(1e-5)
        assert isinstance(detected, float)

    def test_photon_transit_time(self) -> None:
        ptm = PhotonTimingModel(fiber_length=1000)
        tt = ptm.photon_transit_time()
        assert tt > 0
        assert tt == ptm.propagation_time


class TestQBERTimingAnalysis:
    def test_construction(self) -> None:
        qta = QBERTimingAnalysis(timing_window=1e-9)
        assert qta.timing_window == 1e-9

    def test_calculate_temporal_qber_perfect(self) -> None:
        qta = QBERTimingAnalysis(timing_window=1e-6)
        alice = [0.0, 1e-7, 2e-7]
        bob = [0.0, 1e-7, 2e-7]
        qber = qta.calculate_temporal_qber(alice, bob, expected_delay=0.0)
        assert qber == 0.0

    def test_calculate_temporal_qber_all_mismatch(self) -> None:
        qta = QBERTimingAnalysis(timing_window=1e-12)
        alice = [0.0, 1e-7, 2e-7]
        bob = [1.0, 1.0, 1.0]
        qber = qta.calculate_temporal_qber(alice, bob, expected_delay=0.0)
        assert qber == 1.0

    def test_calculate_temporal_qber_empty(self) -> None:
        qta = QBERTimingAnalysis()
        qber = qta.calculate_temporal_qber([], [])
        assert qber == 0.0

    def test_calculate_temporal_qber_mismatched_length(self) -> None:
        qta = QBERTimingAnalysis()
        with pytest.raises(ValueError, match="same length"):
            qta.calculate_temporal_qber([0.0], [0.0, 1.0])

    def test_update_with_drift(self) -> None:
        qta = QBERTimingAnalysis(timing_window=1e-9)
        new_window = qta.update_with_drift(drift_rate=1e-6, time_elapsed=100.0)
        assert new_window > 1e-9
        assert abs(new_window - (1e-9 + 1e-4)) < 1e-10


class TestProtocolTimingManager:
    def test_send_and_receive(self) -> None:
        ts = TimingSynchronizer()
        ptm_model = PhotonTimingModel(fiber_length=1000)
        qta = QBERTimingAnalysis()
        manager = ProtocolTimingManager(ts, ptm_model, qta)

        emitted, bases = manager.send_photon_sequence(
            start_time=0.0,
            pulse_interval=1e-9,
            num_photons=5,
            basis_sequence=["Z", "X", "Z", "X", "Z"],
        )
        assert len(emitted) == 5
        assert len(bases) == 5

        detected, meas_bases, tqber = manager.receive_photon_sequence(
            emitted, expected_delay=ptm_model.propagation_time, basis_sequence=bases
        )
        assert len(detected) == 5
        assert len(meas_bases) == 5
        assert 0.0 <= tqber <= 1.0

    def test_get_timing_stats(self) -> None:
        ts = TimingSynchronizer()
        ptm_model = PhotonTimingModel(fiber_length=1000)
        qta = QBERTimingAnalysis()
        manager = ProtocolTimingManager(ts, ptm_model, qta)

        stats = manager.get_timing_stats()
        assert "propagation_time" in stats
        assert "timing_window" in stats
        assert "current_alice_drift" in stats
        assert "current_bob_drift" in stats
