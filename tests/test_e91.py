"""Tests for E91 QKD protocol."""

import unittest

from qkdpy.core import QuantumChannel
from qkdpy.protocols import E91


class TestE91(unittest.TestCase):
    """Test cases for the E91 QKD protocol."""

    def test_e91_initialization(self):
        """Test E91 initialization."""
        channel = QuantumChannel()
        e91 = E91(channel, key_length=50)

        self.assertEqual(e91.key_length, 50)
        self.assertEqual(e91.security_threshold, 0.1)
        self.assertFalse(e91.is_complete)

    def test_e91_prepare_states(self):
        """Test E91 state preparation."""
        channel = QuantumChannel()
        e91 = E91(channel, key_length=10)

        qubits = e91.prepare_states()

        # Check that we have the right number of placeholders
        self.assertEqual(len(qubits), e91.num_pairs)
        self.assertIsNotNone(qubits[0])

    def test_e91_bell_test(self):
        """Test Bell inequality testing in E91."""
        channel = QuantumChannel()
        e91 = E91(channel, key_length=20)

        # Execute measure_states to generate results
        e91.measure_states([None] * e91.num_pairs)

        # Test Bell's inequality
        bell_results = e91.test_bell_inequality()

        # Check that we get the expected results structure
        self.assertIn("s_value", bell_results)
        self.assertIn("is_violated", bell_results)
        self.assertIn("estimated_qber", bell_results)

    def test_e91_execute(self):
        """Test E91 protocol execution."""
        channel = QuantumChannel(loss=0.1, noise_level=0.01)
        e91 = E91(channel, key_length=20)

        # Execute the protocol
        results = e91.execute()

        # Check that the protocol completed
        self.assertTrue(e91.is_complete)

        # Check that we got a final key
        self.assertIn("final_key", results)
        self.assertIn("qber", results)
        self.assertIn("is_secure", results)
        self.assertIn("bell_test", results)

        # Check S-value is reasonable (should violate Bell inequality for low noise)
        s_value = results["bell_test"]["s_value"]
        self.assertTrue(abs(s_value) > 2.0)


if __name__ == "__main__":
    unittest.main()
