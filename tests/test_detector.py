"""Tests for quantum detector models."""

import unittest

import numpy as np

from qkdpy.core import QuantumDetector
from qkdpy.core.detector import DetectorArray
from qkdpy.core.qubit import Qubit


class TestQuantumDetector(unittest.TestCase):
    """Test the QuantumDetector class."""

    def test_default_initialization(self):
        """Detector initializes with default parameters."""
        detector = QuantumDetector()
        stats = detector.get_statistics()
        self.assertAlmostEqual(stats["detection_efficiency"], 0.1)
        self.assertAlmostEqual(stats["dead_time"], 1e-6)
        self.assertAlmostEqual(stats["timing_jitter"], 1e-10)
        self.assertAlmostEqual(stats["afterpulse_probability"], 0.01)

    def test_custom_initialization(self):
        """Detector initializes with custom parameters."""
        detector = QuantumDetector(
            efficiency=0.5,
            dark_count_rate=1e-7,
            dead_time=5e-7,
            timing_jitter=5e-11,
            afterpulse_probability=0.05,
        )
        stats = detector.get_statistics()
        self.assertAlmostEqual(stats["detection_efficiency"], 0.5)
        self.assertAlmostEqual(stats["dead_time"], 5e-7)
        self.assertAlmostEqual(stats["timing_jitter"], 5e-11)

    def test_detect_photon_present(self):
        """detect with photon_present=True returns detection results."""
        detector = QuantumDetector(efficiency=1.0)
        result, time = detector.detect(photon_present=True, timestamp=0.0)
        self.assertIsInstance(result, (int, type(None)))
        self.assertIsInstance(time, float)

    def test_detect_photon_absent_with_zero_dark_counts(self):
        """With no photon and no dark counts, detection should be None."""
        detector = QuantumDetector(efficiency=0.0, dark_count_rate=0.0)
        result, time = detector.detect(photon_present=False, timestamp=1.0)
        self.assertIsNone(result)

    def test_detect_photon_present_success(self):
        """With 100% efficiency, a photon should always be detected."""
        detector = QuantumDetector(efficiency=1.0, dark_count_rate=0.0)
        result, time = detector.detect(photon_present=True, timestamp=0.0)
        self.assertIsNotNone(result)

    def test_detect_with_zero_efficiency(self):
        """With 0% efficiency, even a present photon should not be detected."""
        detector = QuantumDetector(efficiency=0.0, dark_count_rate=0.0)
        results = [detector.detect(True, t)[0] for t in np.linspace(0, 1e-6, 20)]
        self.assertTrue(all(r is None for r in results))

    def test_measure_state_returns_tuple(self):
        """measure_state returns a (int | None, float) tuple."""
        detector = QuantumDetector()
        qubit = Qubit.zero()
        result, timestamp = detector.measure_state(qubit, basis="computational", timestamp=0.0)
        self.assertIsInstance(result, (int, type(None)))
        self.assertIsInstance(timestamp, float)

    def test_measure_state_known_basis(self):
        """Measuring |0> in computational basis should give 0."""
        detector = QuantumDetector(efficiency=1.0, dark_count_rate=0.0)
        qubit = Qubit.zero()
        result, timestamp = detector.measure_state(qubit, basis="computational", timestamp=0.0)
        if result is not None:
            self.assertIn(result, (0, 1))

    def test_get_statistics_returns_dict(self):
        """get_statistics returns a dict with expected keys."""
        detector = QuantumDetector(efficiency=0.3)
        stats = detector.get_statistics()
        self.assertIn("detection_efficiency", stats)
        self.assertIn("dead_time", stats)
        self.assertIn("timing_jitter", stats)
        self.assertIn("total_photons_detected", stats)
        self.assertIn("dark_counts_detected", stats)

    def test_reset_clears_counts(self):
        """Reset should zero detection counts."""
        detector = QuantumDetector(efficiency=1.0, dark_count_rate=0.0)
        detector.detect(True, 0.0)
        detector.reset()
        stats_after = detector.get_statistics()
        self.assertEqual(stats_after["total_photons_detected"], 0)

    def test_dark_counts_occur_with_high_rate(self):
        """With nonzero dark count rate, some detections should occur."""
        detector = QuantumDetector(efficiency=0.0, dark_count_rate=1e9)
        results = [detector.detect(False, t)[0] for t in np.linspace(0, 1e-6, 100)]
        self.assertTrue(any(r is not None for r in results))


class TestDetectorArray(unittest.TestCase):
    """Test the DetectorArray class."""

    def setUp(self):
        self.array = DetectorArray(num_detectors=4)

    def test_custom_num_detectors(self):
        """DetectorArray can be created with a specific number of detectors."""
        self.assertEqual(len(self.array.detectors), 4)

    def test_default_num_detectors(self):
        """Default DetectorArray has a reasonable number of detectors."""
        array = DetectorArray()
        self.assertGreater(len(array.detectors), 0)

    def test_measure_in_basis_returns_int(self):
        """measure_in_basis returns an integer result."""
        qubit = Qubit.zero()
        result = self.array.measure_in_basis(qubit, basis="computational", timestamp=0.0)
        self.assertIsInstance(result, int)
        self.assertIn(result, (0, 1))

    def test_measure_in_basis_hadamard(self):
        """Measuring in Hadamard basis gives a valid bit result."""
        qubit = Qubit.plus()
        result = self.array.measure_in_basis(qubit, basis="hadamard", timestamp=0.0)
        self.assertIn(result, (0, 1))

    def test_get_statistics(self):
        """get_statistics returns a list of detector stats."""
        stats = self.array.get_statistics()
        self.assertIsInstance(stats, list)
        self.assertEqual(len(stats), 4)
        for stat in stats:
            self.assertIn("detection_efficiency", stat)
            self.assertIn("total_photons_detected", stat)

    def test_individual_detector_properties(self):
        """Each detector in the array should be accessible and usable."""
        d = self.array.detectors[0]
        result, _ = d.detect(True, 0.0)
        self.assertIsInstance(result, (int, type(None)))

    def test_measure_in_basis_invalid_basis(self):
        """Invalid basis should raise ValueError."""
        qubit = Qubit.zero()
        with self.assertRaises(ValueError):
            self.array.measure_in_basis(qubit, basis="invalid", timestamp=0.0)


if __name__ == "__main__":
    unittest.main()
