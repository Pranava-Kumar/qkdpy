"""Tests for QKD protocol implementations."""

import unittest

from qkdpy import BB84, E91, SARG04, QuantumChannel


class TestBB84(unittest.TestCase):
    """Test cases for the BB84 protocol."""

    def test_bb84_execution(self):
        """Test execution of the BB84 protocol."""
        # Create a quantum channel with some noise and loss
        channel = QuantumChannel(loss=0.1, noise_model="depolarizing", noise_level=0.05)

        # Create a BB84 protocol instance
        bb84 = BB84(channel, key_length=100)

        # Execute the protocol
        results = bb84.execute()

        # Check that the protocol completed
        self.assertTrue(bb84.is_complete)

        # Check that we got a final key
        self.assertGreater(len(results["final_key"]), 0)

        # Check that the QBER is reasonable
        self.assertGreaterEqual(results["qber"], 0)
        self.assertLessEqual(results["qber"], 1)

    def test_bb84_sifting(self):
        """Test key sifting in BB84."""
        # Create a noiseless channel
        channel = QuantumChannel(loss=0.0, noise_model="depolarizing", noise_level=0.0)

        # Create a BB84 protocol instance
        bb84 = BB84(channel, key_length=100)

        # Execute the protocol
        results = bb84.execute()

        # Check that the sifted key is shorter than the raw key
        self.assertLessEqual(len(results["sifted_key"]), len(results["raw_key"]))

        # Check that the final key is shorter than the sifted key
        self.assertLessEqual(len(results["final_key"]), len(results["sifted_key"]))

    def test_bb84_security_threshold(self):
        """Test the security threshold of BB84."""
        # Create a channel with high noise
        channel = QuantumChannel(loss=0.0, noise_model="depolarizing", noise_level=0.5)

        # Create a BB84 protocol instance
        bb84 = BB84(channel, key_length=100, security_threshold=0.1)

        # Execute the protocol
        results = bb84.execute()

        # Check that the protocol is not secure with high noise
        self.assertFalse(results["is_secure"])


class TestE91(unittest.TestCase):
    """Test cases for the E91 protocol."""

    def test_e91_execution(self):
        """Test execution of the E91 protocol."""
        # Create a quantum channel with some noise and loss
        channel = QuantumChannel(loss=0.1, noise_model="depolarizing", noise_level=0.05)

        # Create an E91 protocol instance
        e91 = E91(channel, key_length=100)

        # Execute the protocol
        results = e91.execute()

        # Check that the protocol completed
        self.assertTrue(e91.is_complete)

        # Check that we got a final key
        self.assertGreater(len(results["final_key"]), 0)

        # Check that the QBER is reasonable
        self.assertGreaterEqual(results["qber"], 0)
        self.assertLessEqual(results["qber"], 1)

    def test_e91_bell_inequality(self):
        """Test Bell's inequality in E91."""
        # Create a noiseless channel
        channel = QuantumChannel(loss=0.0, noise_model="depolarizing", noise_level=0.0)

        # Create an E91 protocol instance
        e91 = E91(channel, key_length=100)

        # Execute the protocol
        e91.execute()

        # Test Bell's inequality
        bell_results = e91.test_bell_inequality()

        # Check that Bell's inequality is violated
        self.assertTrue(bell_results["is_violated"])

    def test_e91_security_threshold(self):
        """Test the security threshold of E91."""
        # Create a channel with high noise
        channel = QuantumChannel(loss=0.0, noise_model="depolarizing", noise_level=0.2)

        # Create an E91 protocol instance
        e91 = E91(channel, key_length=100, security_threshold=0.1)

        # Execute the protocol
        results = e91.execute()

        # Check that the protocol is not secure with high noise
        self.assertFalse(results["is_secure"])


class TestSARG04(unittest.TestCase):
    """Test cases for the SARG04 protocol."""

    def test_sarg04_execution(self):
        """Test execution of the SARG04 protocol."""
        # Create a quantum channel with some noise and loss
        channel = QuantumChannel(loss=0.1, noise_model="depolarizing", noise_level=0.05)

        # Create a SARG04 protocol instance
        sarg04 = SARG04(channel, key_length=100)

        # Execute the protocol
        results = sarg04.execute()

        # Check that the protocol completed
        self.assertTrue(sarg04.is_complete)

        # Check that we got a final key
        self.assertGreater(len(results["final_key"]), 0)

        # Check that the QBER is reasonable
        self.assertGreaterEqual(results["qber"], 0)
        self.assertLessEqual(results["qber"], 1)

    def test_sarg04_sifting(self):
        """Test key sifting in SARG04."""
        # Create a noiseless channel
        channel = QuantumChannel(loss=0.0, noise_model="depolarizing", noise_level=0.0)

        # Create a SARG04 protocol instance
        sarg04 = SARG04(channel, key_length=100)

        # Execute the protocol
        results = sarg04.execute()

        # Check that the sifted key is shorter than the raw key
        self.assertLessEqual(len(results["sifted_key"]), len(results["raw_key"]))

        # Check that the final key is shorter than the sifted key
        self.assertLessEqual(len(results["final_key"]), len(results["sifted_key"]))

    def test_sarg04_security_threshold(self):
        """Test the security threshold of SARG04."""
        # Create a channel with high noise
        channel = QuantumChannel(loss=0.0, noise_model="depolarizing", noise_level=0.2)

        # Create a SARG04 protocol instance
        sarg04 = SARG04(channel, key_length=100)

        # Execute the protocol
        results = sarg04.execute()

        # Check that the protocol is not secure with high noise
        self.assertFalse(results["is_secure"])


if __name__ == "__main__":
    unittest.main()
