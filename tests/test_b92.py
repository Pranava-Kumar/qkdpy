"""Tests for B92 protocol implementation."""

import unittest

import numpy as np

from qkdpy.core import QuantumChannel
from qkdpy.protocols import B92


class TestB92(unittest.TestCase):
    """Test cases for the B92 protocol."""

    def test_b92_initialization(self):
        """Test B92 protocol initialization."""
        channel = QuantumChannel()
        b92 = B92(channel, key_length=50)

        self.assertEqual(b92.key_length, 50)
        self.assertEqual(b92.security_threshold, 0.25)
        self.assertFalse(b92.is_complete)

    def test_b92_prepare_states(self):
        """Test B92 state preparation."""
        channel = QuantumChannel()
        b92 = B92(channel, key_length=10)

        qubits = b92.prepare_states()

        # Check that we have the right number of qubits
        self.assertEqual(len(qubits), b92.num_qubits)

        # Check that all qubits are valid
        for qubit in qubits:
            self.assertIsNotNone(qubit)
            # Qubit state should be either |0> or |+>
            self.assertTrue(
                np.allclose(qubit.state, np.array([1, 0]))  # |0>
                or np.allclose(
                    qubit.state, np.array([1 / np.sqrt(2), 1 / np.sqrt(2)])
                )  # |+>
            )

    def test_b92_sift_keys(self):
        """Test B92 key sifting."""
        channel = QuantumChannel()
        b92 = B92(channel, key_length=10)

        # Prepare states first
        qubits = b92.prepare_states()

        # Measure states
        _ = b92.measure_states(qubits)

        # Sift keys
        alice_sifted, bob_sifted = b92.sift_keys()

        # Check that sifted keys have the same length
        self.assertEqual(len(alice_sifted), len(bob_sifted))

    def test_b92_execute(self):
        """Test B92 protocol execution."""
        channel = QuantumChannel(loss=0.1, noise_level=0.05)
        b92 = B92(channel, key_length=20)

        # Execute the protocol
        results = b92.execute()

        # Check that the protocol completed
        self.assertTrue(b92.is_complete)

        # Check that we got a final key
        self.assertIn("final_key", results)
        self.assertIn("qber", results)
        self.assertIn("is_secure", results)


if __name__ == "__main__":
    unittest.main()
