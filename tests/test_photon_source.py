"""Tests for photon source models."""

import unittest

import numpy as np

from qkdpy.core.photon_source import (
    DecoyStateSource,
    ParametricDownConversionSource,
    PhotonSource,
    PhotonSourceManager,
    PhotonSourceState,
    WeakCoherentSource,
)


class TestPhotonSource(unittest.TestCase):
    """Test the base PhotonSource class."""

    def setUp(self):
        self.source = PhotonSource(
            name="Test Source",
            pulse_rate=1e9,
            wavelength=1550e-9,
            timing_jitter=1e-12,
            efficiency=0.5,
        )

    def test_initialization(self):
        """Source should initialize with expected attributes."""
        self.assertEqual(self.source.name, "Test Source")
        self.assertEqual(self.source.pulse_rate, 1e9)
        self.assertEqual(self.source.wavelength, 1550e-9)
        self.assertEqual(self.source.efficiency, 0.5)
        self.assertGreater(self.source.photon_energy, 0)

    def test_photon_energy_positive(self):
        """Photon energy should be a positive number."""
        self.assertGreater(self.source.photon_energy, 0)

    def test_generate_returns_tuple(self):
        """generate_photon_pulse returns a tuple of (bool, float)."""
        result = self.source.generate_photon_pulse(time=0.0)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        photon_present, actual_time = result
        self.assertIsInstance(photon_present, bool)
        self.assertIsInstance(actual_time, float)

    def test_generate_photon_present_with_efficiency(self):
        """With efficiency=1.0, a photon should always be present."""
        source = PhotonSource(efficiency=1.0, pulse_rate=1e9)
        results = [source.generate_photon_pulse(t)[0] for t in range(100)]
        self.assertTrue(all(results))

    def test_generate_photon_never_with_zero_efficiency(self):
        """With efficiency=0.0, a photon should never be present."""
        source = PhotonSource(efficiency=0.0, pulse_rate=1e9)
        results = [source.generate_photon_pulse(t)[0] for t in range(100)]
        self.assertFalse(any(results))

    def test_timing_jitter_affects_time(self):
        """Timing jitter should produce slightly different actual times."""
        source = PhotonSource(timing_jitter=1e-9, efficiency=1.0, pulse_rate=1e9)
        times = [source.generate_photon_pulse(0.0)[1] for _ in range(50)]
        # At least some should differ from the nominal time
        unique_times = len(set(round(t, 12) for t in times))
        self.assertGreater(unique_times, 1)


class TestWeakCoherentSource(unittest.TestCase):
    """Test the WeakCoherentSource class."""

    def setUp(self):
        self.source = WeakCoherentSource(mean_photon_number=0.5, pulse_rate=1e9)

    def test_initialization(self):
        """Source should have mean_photon_number set."""
        self.assertEqual(self.source.mean_photon_number, 0.5)

    def test_generate_returns_state_tuple(self):
        """generate_photon_pulse returns (PhotonSourceState, float)."""
        result = self.source.generate_photon_pulse(time=0.0)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        state, actual_time = result
        self.assertIsInstance(state, PhotonSourceState)
        self.assertIn(state, PhotonSourceState)
        self.assertIsInstance(actual_time, float)

    def test_statistics_approximate_poisson(self):
        """With low mean, vacuum should dominate; with high mean, multi-photon appears."""
        # Very low mean -> mostly vacuum
        weak = WeakCoherentSource(mean_photon_number=0.05)
        stats = weak.get_photon_statistics(num_pulses=2000)
        self.assertGreater(stats["vacuum_probability"], 0.8)

        # Higher mean -> more multi-photon events
        strong = WeakCoherentSource(mean_photon_number=2.0)
        stats2 = strong.get_photon_statistics(num_pulses=2000)
        self.assertGreater(stats2["multi_photon_probability"], 0.1)

    def test_get_photon_statistics_returns_dict(self):
        """get_photon_statistics returns a dict with expected keys."""
        stats = self.source.get_photon_statistics(num_pulses=500)
        self.assertIn("vacuum_probability", stats)
        self.assertIn("single_photon_probability", stats)
        self.assertIn("multi_photon_probability", stats)
        self.assertIn("mean_photon_number", stats)
        self.assertIn("g2_factor", stats)
        self.assertAlmostEqual(stats["mean_photon_number"], 0.5)

    def test_sum_of_probabilities_is_one(self):
        """Probabilities should sum to approximately 1."""
        stats = self.source.get_photon_statistics(num_pulses=1000)
        total = stats["vacuum_probability"] + stats["single_photon_probability"] + stats["multi_photon_probability"]
        self.assertAlmostEqual(total, 1.0, places=1)


class TestDecoyStateSource(unittest.TestCase):
    """Test the DecoyStateSource class."""

    def setUp(self):
        self.source = DecoyStateSource(
            signal_mean_photon_number=0.5,
            decoy_mean_photon_numbers=[0.1, 0.01],
            decoy_probability=0.2,
            pulse_rate=1e9,
        )

    def test_initialization(self):
        """Decoy state source should have correct attributes."""
        self.assertEqual(self.source.signal_mean_photon_number, 0.5)
        self.assertEqual(self.source.decoy_mean_photon_numbers, [0.1, 0.01])
        self.assertEqual(self.source.decoy_probability, 0.2)

    def test_generate_returns_three_tuple(self):
        """generate_photon_pulse returns (state, time, pulse_type)."""
        result = self.source.generate_photon_pulse(time=0.0)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 3)
        state, actual_time, pulse_type = result
        self.assertIsInstance(state, PhotonSourceState)
        self.assertIsInstance(actual_time, float)
        self.assertIsInstance(pulse_type, str)

    def test_generate_signal_pulse(self):
        """Signal pulse should have type 'signal'."""
        state, time, pulse_type = self.source.generate_signal_pulse(0.0)
        self.assertEqual(pulse_type, "signal")

    def test_generate_decoy_pulse(self):
        """Decoy pulse should have type starting with 'decoy_'."""
        state, time, pulse_type = self.source.generate_decoy_pulse(0.0)
        self.assertTrue(pulse_type.startswith("decoy_"))

    def test_signal_and_decoy_distribution(self):
        """decoy_probability should approximately match the ratio of decoy pulses."""
        results = [self.source.generate_photon_pulse(0.0) for _ in range(2000)]
        decoy_count = sum(1 for _, _, pt in results if pt.startswith("decoy_"))
        ratio = decoy_count / len(results)
        # With decoy_probability=0.2, expect ~0.2
        self.assertGreater(ratio, 0.05)
        self.assertLess(ratio, 0.5)

    def test_get_pulse_type_statistics(self):
        """get_pulse_type_statistics returns expected keys."""
        stats = self.source.get_pulse_type_statistics(num_pulses=500)
        self.assertIn("signal_probability", stats)
        self.assertIn("decoy_probability", stats)
        self.assertIn("decoy_probabilities_by_type", stats)
        self.assertAlmostEqual(stats["signal_probability"] + stats["decoy_probability"], 1.0, places=1)

    def test_custom_rng(self):
        """A custom numpy Generator can be passed."""
        rng = np.random.default_rng(42)
        source = DecoyStateSource(
            signal_mean_photon_number=0.5,
            decoy_probability=0.2,
            random_number_generator=rng,
        )
        result = source.generate_photon_pulse(0.0)
        self.assertEqual(len(result), 3)


class TestParametricDownConversionSource(unittest.TestCase):
    """Test the ParametricDownConversionSource class."""

    def setUp(self):
        self.source = ParametricDownConversionSource(
            pair_generation_rate=1e6,
            pulse_rate=1e8,
            heralding_efficiency=0.5,
            efficiency=0.5,
        )

    def test_initialization(self):
        """PDC source should have correct attributes."""
        self.assertEqual(self.source.pair_generation_rate, 1e6)
        self.assertEqual(self.source.heralding_efficiency, 0.5)
        self.assertGreater(self.source.heralding_probability, 0)

    def test_generate_returns_correct_tuple(self):
        """generate_photon_pulse returns (bool, float, dict)."""
        result = self.source.generate_photon_pulse(time=0.0)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 3)
        photon_present, actual_time, info = result
        self.assertIsInstance(photon_present, bool)
        self.assertIsInstance(actual_time, float)
        self.assertIsInstance(info, dict)

    def test_info_dict_keys(self):
        """The info dict should contain expected keys."""
        _, _, info = self.source.generate_photon_pulse(0.0)
        self.assertIn("pair_generated", info)
        self.assertIn("herald_detected", info)
        self.assertIn("photon_present", info)


class TestPhotonSourceManager(unittest.TestCase):
    """Test the PhotonSourceManager class."""

    def setUp(self):
        self.manager = PhotonSourceManager()
        self.source1 = PhotonSource(name="Source 1", efficiency=1.0, pulse_rate=1e9)
        self.source2 = WeakCoherentSource(name="Source 2", mean_photon_number=0.5)

    def test_add_and_set_active_source(self):
        """Sources can be added and activated."""
        self.manager.add_source("src1", self.source1)
        self.manager.set_active_source("src1")
        self.assertEqual(self.manager.active_source, "src1")

    def test_set_active_invalid_source_raises(self):
        """Setting an invalid source ID should raise ValueError."""
        with self.assertRaises(ValueError):
            self.manager.set_active_source("nonexistent")

    def test_generate_sequence_without_active_raises(self):
        """generate_sequence without active source and without source_id should raise."""
        with self.assertRaises(ValueError):
            self.manager.generate_sequence(duration=1e-9)

    def test_generate_sequence_with_source_id(self):
        """generate_sequence with a valid source_id should produce pulses."""
        self.manager.add_source("src1", self.source1)
        results = self.manager.generate_sequence(duration=1e-9, source_id="src1")
        self.assertGreater(len(results), 0)

    def test_generate_sequence_invalid_source_raises(self):
        """generate_sequence with an invalid source_id should raise ValueError."""
        with self.assertRaises(ValueError):
            self.manager.generate_sequence(duration=1e-9, source_id="nonexistent")

    def test_generate_sequence_at_timestamps(self):
        """Sequence can be generated at specific timestamps."""
        self.manager.add_source("src1", self.source1)
        self.manager.set_active_source("src1")
        timestamps = [0.0, 1e-9, 2e-9]
        results = self.manager.generate_sequence(duration=1.0, timestamps=timestamps)
        self.assertEqual(len(results), len(timestamps))


if __name__ == "__main__":
    unittest.main()
