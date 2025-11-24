"""Tests for device-independent QKD protocol."""

import unittest

from qkdpy.core import QuantumChannel
from qkdpy.protocols import DeviceIndependentQKD


class TestDeviceIndependentQKD(unittest.TestCase):
    """Test cases for the device-independent QKD protocol."""

    def test_di_qkd_initialization(self):
        """Test device-independent QKD initialization."""
        channel = QuantumChannel()
        di_qkd = DeviceIndependentQKD(channel, key_length=50)

        self.assertEqual(di_qkd.key_length, 50)
        self.assertEqual(di_qkd.security_threshold, 2.0)
        self.assertFalse(di_qkd.is_complete)

    def test_di_qkd_prepare_states(self):
        """Test DI-QKD state preparation."""
        channel = QuantumChannel()
        di_qkd = DeviceIndependentQKD(channel, key_length=10)

        qubits = di_qkd.prepare_states()

        # Check that we have the right number of qubits
        self.assertEqual(len(qubits), di_qkd.num_pairs)
        # Check that they are None (placeholders)
        self.assertIsNone(qubits[0])

    def test_di_qkd_bell_test(self):
        """Test Bell inequality testing in DI-QKD."""
        channel = QuantumChannel()
        di_qkd = DeviceIndependentQKD(channel, key_length=20)

        # Prepare and measure states
        qubits = di_qkd.prepare_states()
        _ = di_qkd.measure_states(qubits)

        # Test Bell's inequality
        bell_results = di_qkd.test_bell_inequality()

        # Check that we get the expected results structure
        self.assertIn("s_value", bell_results)
        self.assertIn("e00", bell_results)
        self.assertIn("e01", bell_results)
        self.assertIn("e10", bell_results)
        self.assertIn("e11", bell_results)

    def test_di_qkd_execute(self):
        """Test DI-QKD protocol execution."""
        channel = QuantumChannel(loss=0.1, noise_level=0.05)
        di_qkd = DeviceIndependentQKD(channel, key_length=20)

        # Execute the protocol
        results = di_qkd.execute()

        # Check that the protocol completed
        self.assertTrue(di_qkd.is_complete)

        # Check that we got a final key
        self.assertIn("final_key", results)
        self.assertIn("qber", results)
        self.assertIn("is_secure", results)


if __name__ == "__main__":
    unittest.main()
