"""Tests for qkdpy.network.satellite_qkd.

Covers SatelliteQKD, FreeSpaceOpticalChannel, and AtmosphericProfile.
"""

import unittest

from qkdpy.network.satellite_qkd import (
    AtmosphericProfile,
    FreeSpaceOpticalChannel,
    SatellitePosition,
    SatelliteQKD,
)


class TestAtmosphericProfile(unittest.TestCase):
    """Atmospheric profile is a dataclass with default fields."""

    def test_default_profile(self):
        atm = AtmosphericProfile()
        self.assertGreater(atm.visibility_km, 0)

    def test_profile_is_reproducible(self):
        a = AtmosphericProfile()
        b = AtmosphericProfile()
        self.assertEqual(a.visibility_km, b.visibility_km)


class TestFreeSpaceOpticalChannel(unittest.TestCase):
    """Free-space optical channel behaves correctly."""

    def _make_channel(self, elevation_deg: float) -> FreeSpaceOpticalChannel:
        pos = SatellitePosition(
            altitude_km=500.0,
            latitude=40.0,
            longitude=-74.0,
            elevation_angle=elevation_deg,
            slant_range_km=1000.0,
        )
        return FreeSpaceOpticalChannel(pos)

    def test_channel_has_loss(self):
        channel = self._make_channel(45.0)
        self.assertGreaterEqual(channel.loss, 0.0)
        self.assertLessEqual(channel.loss, 1.0)

    def test_channel_loss_decreases_with_elevation(self):
        """Higher elevation → less atmosphere → lower loss."""
        low = self._make_channel(20.0).loss
        high = self._make_channel(80.0).loss
        self.assertGreater(low, high)

    def test_channel_loss_db_positive(self):
        channel = self._make_channel(45.0)
        db = channel._loss_to_db(channel.loss)
        self.assertGreaterEqual(db, 0.0)


class TestSatelliteQKD(unittest.TestCase):
    """SatelliteQKD link simulation."""

    def setUp(self):
        self.link = SatelliteQKD(
            altitude_km=500.0,
            ground_station_lat=40.0,
            ground_station_lon=-74.0,
        )

    def test_simulate_pass_returns_expected_keys(self):
        result = self.link.simulate_pass(duration_seconds=300, time_steps=10)
        expected_keys = {
            "time_points",
            "elevation_angles",
            "channel_losses_db",
            "key_rates_bps",
            "qber_values",
            "total_key_bits",
        }
        self.assertSetEqual(set(result.keys()), expected_keys)
        self.assertEqual(len(result["time_points"]), 10)

    def test_elevation_angles_vary(self):
        result = self.link.simulate_pass(300, 20)
        self.assertGreater(max(result["elevation_angles"]), 40)
        # Minimum elevation depends on geometry; just check it's positive
        self.assertGreater(min(result["elevation_angles"]), 0)

    def test_key_rate_positive(self):
        result = self.link.simulate_pass(300, 10)
        for rate in result["key_rates_bps"]:
            self.assertGreaterEqual(rate, 0.0)

    def test_total_key_bits_positive(self):
        result = self.link.simulate_pass(300, 10)
        self.assertGreater(result["total_key_bits"], 0)

    def test_single_time_step(self):
        """time_steps=1 should not produce division errors."""
        result = self.link.simulate_pass(300, 1)
        self.assertEqual(len(result["time_points"]), 1)

    def test_qber_not_hardcoded(self):
        """QBER should vary across the pass, not stay constant at 2%."""
        result = self.link.simulate_pass(300, 20)
        self.assertGreater(max(result["qber_values"]), min(result["qber_values"]))


if __name__ == "__main__":
    unittest.main()
