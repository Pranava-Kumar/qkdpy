"""Tests for enhanced continuous-variable QKD protocol."""

import unittest

from qkdpy.core import QuantumChannel
from qkdpy.protocols.enhanced_cv_qkd import EnhancedCVQKD


class TestEnhancedCVQKD(unittest.TestCase):
    """Test cases for enhanced CV-QKD protocol."""

    def test_initialization(self):
        """Test initialization of EnhancedCVQKD protocol."""
        channel = QuantumChannel()
        protocol = EnhancedCVQKD(channel, key_length=50)

        self.assertEqual(protocol.key_length, 50)
        self.assertEqual(protocol.num_signals, 50 * 20)  # 20x key length
        self.assertEqual(protocol.modulation_variance, 2.0)
        self.assertEqual(protocol.detection_efficiency, 0.6)

    def test_prepare_states(self):
        """Test state preparation in EnhancedCVQKD."""
        channel = QuantumChannel()
        protocol = EnhancedCVQKD(channel, key_length=10)

        states = protocol.prepare_states()

        self.assertEqual(len(states), protocol.num_signals)
        self.assertEqual(len(protocol.alice_bits), protocol.num_signals)
        self.assertEqual(len(protocol.alice_modulations_x), protocol.num_signals)
        self.assertEqual(len(protocol.alice_modulations_p), protocol.num_signals)

    def test_measure_states(self):
        """Test state measurement in EnhancedCVQKD."""
        channel = QuantumChannel()
        protocol = EnhancedCVQKD(channel, key_length=10)

        # Prepare states first
        qubits = protocol.prepare_states()

        # Measure states
        measurements = protocol.measure_states(qubits)

        self.assertEqual(len(measurements), protocol.num_signals)
        self.assertEqual(len(protocol.bob_measurements_x), protocol.num_signals)
        self.assertEqual(len(protocol.bob_measurements_p), protocol.num_signals)

        # Check that measurements are discrete (0 or 1)
        for measurement in measurements:
            self.assertIn(measurement, [0, 1])

    def test_sift_keys(self):
        """Test key sifting in EnhancedCVQKD."""
        channel = QuantumChannel()
        protocol = EnhancedCVQKD(channel, key_length=10)

        # Prepare and measure states
        states = protocol.prepare_states()
        protocol.measure_states(states)

        # Sift keys
        alice_sifted, bob_sifted = protocol.sift_keys()

        self.assertEqual(len(alice_sifted), len(bob_sifted))
        self.assertLessEqual(len(alice_sifted), protocol.num_signals)

    def test_estimate_qber(self):
        """Test QBER estimation in EnhancedCVQKD."""
        channel = QuantumChannel()
        protocol = EnhancedCVQKD(channel, key_length=10)

        # Prepare and measure states
        states = protocol.prepare_states()
        protocol.measure_states(states)

        # Estimate QBER
        qber = protocol.estimate_qber()

        self.assertGreaterEqual(qber, 0.0)
        self.assertLessEqual(qber, 1.0)

    def test_calculate_secret_fraction(self):
        """Test secret fraction calculation."""
        channel = QuantumChannel()
        protocol = EnhancedCVQKD(channel, key_length=10)

        # Prepare and measure states
        states = protocol.prepare_states()
        protocol.measure_states(states)

        # Calculate secret fraction
        secret_fraction = protocol.calculate_secret_fraction()

        self.assertGreaterEqual(secret_fraction, 0.0)

    def test_get_excess_noise(self):
        """Test excess noise estimation."""
        channel = QuantumChannel()
        protocol = EnhancedCVQKD(channel, key_length=10)

        # Prepare and measure states
        states = protocol.prepare_states()
        protocol.measure_states(states)

        # Get excess noise
        excess_noise = protocol.get_excess_noise()

        self.assertGreaterEqual(excess_noise, 0.0)
        self.assertLessEqual(excess_noise, 1.0)

    def test_execute_protocol(self):
        """Test complete protocol execution."""
        channel = QuantumChannel(loss=0.1, noise_model="depolarizing", noise_level=0.05)
        protocol = EnhancedCVQKD(channel, key_length=20)

        # Execute the protocol
        results = protocol.execute()

        # Check that the protocol completed
        self.assertTrue(protocol.is_complete)

        # Check results
        self.assertIn("final_key", results)
        self.assertIn("qber", results)
        self.assertIn("is_secure", results)

        # Check that QBER is reasonable
        self.assertGreaterEqual(results["qber"], 0)
        self.assertLessEqual(results["qber"], 1)

    def test_get_protocol_parameters(self):
        """Test protocol parameters retrieval."""
        channel = QuantumChannel()
        protocol = EnhancedCVQKD(channel, key_length=10)

        params = protocol.get_protocol_parameters()

        self.assertIn("modulation_variance", params)
        self.assertIn("detection_efficiency", params)
        self.assertIn("transmission_t", params)
        self.assertIn("excess_noise", params)
        self.assertIn("security_threshold", params)
        self.assertIn("num_signals", params)
        self.assertIn("secret_fraction", params)


if __name__ == "__main__":
    unittest.main()
