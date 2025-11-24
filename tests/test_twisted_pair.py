"""Tests for twisted pair QKD protocol."""

import unittest

from qkdpy.core import QuantumChannel
from qkdpy.protocols import TwistedPairQKD


class TestTwistedPairQKD(unittest.TestCase):
    """Test cases for the twisted pair QKD protocol."""

    def test_twisted_pair_initialization(self):
        """Test twisted pair QKD initialization."""
        channel = QuantumChannel()
        tp_qkd = TwistedPairQKD(channel, key_length=50)

        self.assertEqual(tp_qkd.key_length, 50)
        self.assertEqual(tp_qkd.security_threshold, 0.11)
        self.assertFalse(tp_qkd.is_complete)
        self.assertEqual(tp_qkd.twist_factor, 2)

    def test_twisted_pair_prepare_states(self):
        """Test twisted pair state preparation."""
        channel = QuantumChannel()
        tp_qkd = TwistedPairQKD(channel, key_length=10)

        qubits = tp_qkd.prepare_states()

        # Check that we have the right number of qubits
        self.assertEqual(len(qubits), tp_qkd.num_qubits)

        # Check that all qubits are valid
        for qubit in qubits:
            self.assertIsNotNone(qubit)

    def test_twisted_pair_sift_keys(self):
        """Test twisted pair key sifting."""
        channel = QuantumChannel()
        tp_qkd = TwistedPairQKD(channel, key_length=10)

        # Prepare states first
        qubits = tp_qkd.prepare_states()

        # Measure states
        _ = tp_qkd.measure_states(qubits)

        # Sift keys
        alice_sifted, bob_sifted = tp_qkd.sift_keys()

        # Check that sifted keys have the same length
        self.assertEqual(len(alice_sifted), len(bob_sifted))

    def test_twisted_pair_execute(self):
        """Test twisted pair protocol execution."""
        channel = QuantumChannel(loss=0.1, noise_level=0.05)
        tp_qkd = TwistedPairQKD(channel, key_length=20)

        # Execute the protocol
        results = tp_qkd.execute()

        # Check that the protocol completed
        self.assertTrue(tp_qkd.is_complete)

        # Check that we got a final key
        self.assertIn("final_key", results)
        self.assertIn("qber", results)
        self.assertIn("is_secure", results)


if __name__ == "__main__":
    unittest.main()
