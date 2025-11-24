"""Tests for Decoy-State BB84 QKD protocol."""

import unittest

from qkdpy.core import QuantumChannel
from qkdpy.protocols.decoy_state_bb84 import DecoyStateBB84


class TestDecoyStateBB84(unittest.TestCase):
    """Test cases for the Decoy-State BB84 protocol."""

    def test_decoy_state_bb84_initialization(self):
        """Test initialization of Decoy-State BB84 protocol."""
        channel = QuantumChannel()
        protocol = DecoyStateBB84(channel, key_length=50)

        self.assertEqual(protocol.key_length, 50)
        self.assertEqual(len(protocol.bases), 2)
        self.assertIn("computational", protocol.bases)
        self.assertIn("hadamard", protocol.bases)
        self.assertEqual(protocol.signal_intensity, 0.1)
        self.assertEqual(protocol.decoy_intensity, 0.05)

    def test_decoy_state_bb84_prepare_states(self):
        """Test state preparation in Decoy-State BB84."""
        channel = QuantumChannel()
        protocol = DecoyStateBB84(channel, key_length=10)

        pulses = protocol.prepare_states()

        self.assertEqual(len(pulses), protocol.num_pulses)
        self.assertEqual(len(protocol.alice_bits), protocol.num_pulses)
        self.assertEqual(len(protocol.alice_bases), protocol.num_pulses)
        self.assertEqual(len(protocol.alice_intensities), protocol.num_pulses)

        # Check that intensities are set correctly
        valid_intensities = ["signal", "decoy", "vacuum"]
        for intensity in protocol.alice_intensities:
            self.assertIn(intensity, valid_intensities)

    def test_decoy_state_bb84_execute(self):
        """Test execution of Decoy-State BB84 protocol."""
        channel = QuantumChannel(loss=0.1, noise_model="depolarizing", noise_level=0.05)
        protocol = DecoyStateBB84(channel, key_length=50)

        # Execute the protocol
        results = protocol.execute()

        # Check that the protocol completed
        self.assertTrue(protocol.is_complete)

        # Check that we got a final key
        self.assertIsInstance(results["final_key"], list)

        # Check that the QBER is reasonable
        self.assertGreaterEqual(results["qber"], 0)
        self.assertLessEqual(results["qber"], 1)

    def test_decoy_state_analysis(self):
        """Test decoy state analysis functionality."""
        channel = QuantumChannel()
        protocol = DecoyStateBB84(channel, key_length=10)

        # Prepare states to initialize counters
        protocol.prepare_states()

        # Analyze decoy states
        analysis = protocol.analyze_decoy_states()

        self.assertIn("total_pulses", analysis)
        self.assertIn("signal_pulses", analysis)
        self.assertIn("decoy_pulses", analysis)
        self.assertIn("vacuum_pulses", analysis)
        self.assertEqual(analysis["total_pulses"], protocol.num_pulses)

    def test_secure_key_rate_calculation(self):
        """Test secure key rate calculation."""
        channel = QuantumChannel()
        protocol = DecoyStateBB84(channel, key_length=10)

        # Prepare and measure states to initialize data
        qubits = protocol.prepare_states()
        protocol.measure_states(qubits)

        # Calculate secure key rate
        key_rate = protocol.calculate_secure_key_rate()

        # Key rate should be between 0 and 1
        self.assertGreaterEqual(key_rate, 0.0)
        self.assertLessEqual(key_rate, 1.0)


if __name__ == "__main__":
    unittest.main()
