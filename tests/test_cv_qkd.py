"""Tests for continuous-variable QKD protocol."""

import unittest

from qkdpy.core import QuantumChannel
from qkdpy.protocols import CVQKD


class TestCVQKD(unittest.TestCase):
    """Test cases for the continuous-variable QKD protocol."""

    def test_cv_qkd_initialization(self):
        """Test CV-QKD initialization."""
        channel = QuantumChannel()
        cv_qkd = CVQKD(channel, key_length=50)

        self.assertEqual(cv_qkd.key_length, 50)
        self.assertEqual(cv_qkd.security_threshold, 0.1)
        self.assertFalse(cv_qkd.is_complete)

    def test_cv_qkd_prepare_states(self):
        """Test CV-QKD state preparation."""
        channel = QuantumChannel()
        cv_qkd = CVQKD(channel, key_length=10)

        qubits = cv_qkd.prepare_states()

        # Check that we have the right number of qubits
        # Check that we have the right number of placeholders
        self.assertEqual(len(qubits), cv_qkd.block_size)

        # Check that internal states are populated
        self.assertEqual(len(cv_qkd.alice_x), cv_qkd.block_size)
        self.assertEqual(len(cv_qkd.alice_p), cv_qkd.block_size)

        # Check that returned list contains None (as we use internal arrays)
        for item in qubits:
            self.assertIsNone(item)

    def test_cv_qkd_sift_keys(self):
        """Test CV-QKD key sifting."""
        channel = QuantumChannel()
        cv_qkd = CVQKD(channel, key_length=10)

        # Prepare states first
        signals = cv_qkd.prepare_states()

        # Measure states
        _ = cv_qkd.measure_states(signals)

        # Sift keys
        alice_sifted, bob_sifted = cv_qkd.sift_keys()

        # Check that sifted keys have the same length
        self.assertEqual(len(alice_sifted), len(bob_sifted))

    def test_cv_qkd_execute(self):
        """Test CV-QKD protocol execution."""
        channel = QuantumChannel(loss=0.1, noise_level=0.05)
        cv_qkd = CVQKD(channel, key_length=20)

        # Execute the protocol
        results = cv_qkd.execute()

        # Check that the protocol completed
        self.assertTrue(cv_qkd.is_complete)

        # Check that we got a final key
        self.assertIn("final_key", results)
        self.assertIn("qber", results)
        self.assertIn("is_secure", results)


if __name__ == "__main__":
    unittest.main()
