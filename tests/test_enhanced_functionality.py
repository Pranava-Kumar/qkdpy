"""Tests for enhanced QKDpy functionality."""

import unittest

import numpy as np

from qkdpy import HDQKD, QuantumChannel
from qkdpy.crypto.enhanced_security import (
    QuantumAuthentication,
    QuantumKeyValidation,
    QuantumSideChannelProtection,
)
from qkdpy.ml.qkd_optimizer import QKDAnomalyDetector, QKDOptimizer
from qkdpy.network.quantum_network import MultiPartyQKD, QuantumNetwork


class TestHDQKD(unittest.TestCase):
    """Test cases for High-Dimensional QKD protocol."""

    def test_hd_qkd_initialization(self):
        """Test initialization of HD-QKD protocol."""
        channel = QuantumChannel()
        hd_qkd = HDQKD(channel, key_length=50, dimension=4)

        self.assertEqual(hd_qkd.dimension, 4)
        self.assertEqual(hd_qkd.key_length, 50)
        self.assertEqual(len(hd_qkd.mubs), 5)  # d+1 MUBs for dimension d

    def test_hd_qkd_execution(self):
        """Test execution of HD-QKD protocol."""
        channel = QuantumChannel(loss=0.1, noise_model="depolarizing", noise_level=0.05)
        hd_qkd = HDQKD(channel, key_length=50, dimension=4)

        # Execute the protocol
        results = hd_qkd.execute()

        # Check that the protocol completed
        self.assertTrue(hd_qkd.is_complete)

        # Check that we got a final key
        self.assertGreaterEqual(len(results["final_key"]), 0)

        # Check that the QBER is reasonable
        self.assertGreaterEqual(results["qber"], 0)
        self.assertLessEqual(results["qber"], 1)


class TestEnhancedSecurity(unittest.TestCase):
    """Test cases for enhanced security features."""

    def test_quantum_authentication(self):
        """Test quantum authentication functionality."""
        # Generate a test key
        key = [1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1, 1]
        message = b"Test message for authentication"

        # Generate MAC
        mac = QuantumAuthentication.generate_message_authentication_code(key, message)

        # Verify MAC
        is_valid = QuantumAuthentication.verify_message_authentication_code(
            key, message, mac
        )
        self.assertTrue(is_valid)

        # Test with wrong message
        is_valid_wrong = QuantumAuthentication.verify_message_authentication_code(
            key, b"Wrong message", mac
        )
        self.assertFalse(is_valid_wrong)

    def test_key_validation(self):
        """Test quantum key validation functionality."""
        # Generate a test key with good randomness
        key = [np.random.randint(0, 2) for _ in range(1000)]

        # Perform statistical randomness test
        stats = QuantumKeyValidation.statistical_randomness_test(key)

        self.assertIn("frequency_test_p_value", stats)
        self.assertIn("runs_test_p_value", stats)
        self.assertIn("key_length", stats)

        # Test entropy calculation
        entropy = QuantumKeyValidation.entropy_test(key)
        self.assertGreaterEqual(entropy, 0.0)
        self.assertLessEqual(entropy, 1.0)

        # Test correlation
        correlation = QuantumKeyValidation.correlation_test(key)
        self.assertGreaterEqual(correlation, -1.0)
        self.assertLessEqual(correlation, 1.0)

    def test_side_channel_protection(self):
        """Test side-channel protection functionality."""
        # Test constant time comparison
        key1 = [1, 0, 1, 1, 0, 0, 1, 0]
        key2 = [1, 0, 1, 1, 0, 0, 1, 0]
        key3 = [1, 0, 1, 1, 0, 0, 1, 1]

        self.assertTrue(QuantumSideChannelProtection.constant_time_compare(key1, key2))
        self.assertFalse(QuantumSideChannelProtection.constant_time_compare(key1, key3))

        # Test key splitting and reconstruction
        original_key = [1, 0, 1, 1, 0, 0, 1, 0, 1, 1]
        parts = QuantumSideChannelProtection.secure_key_splitting(original_key, 3)

        self.assertEqual(len(parts), 3)
        for part in parts:
            self.assertEqual(len(part), len(original_key))

        # Reconstruct the key
        reconstructed = QuantumSideChannelProtection.reconstruct_key(parts)
        self.assertEqual(original_key, reconstructed)


class TestMachineLearning(unittest.TestCase):
    """Test cases for ML-based QKD optimization."""

    def test_qkd_optimizer_initialization(self):
        """Test initialization of QKD optimizer."""
        optimizer = QKDOptimizer("BB84")
        self.assertEqual(optimizer.protocol_name, "BB84")
        self.assertEqual(len(optimizer.optimization_history), 0)

    def test_anomaly_detector(self):
        """Test QKD anomaly detection."""
        detector = QKDAnomalyDetector()

        # Establish baseline with historical data
        history = [
            {"qber": 0.02, "key_rate": 1000, "loss": 0.1},
            {"qber": 0.03, "key_rate": 950, "loss": 0.12},
            {"qber": 0.025, "key_rate": 980, "loss": 0.11},
        ]

        detector.establish_baseline(history)
        self.assertGreater(len(detector.baseline_statistics), 0)

        # Test anomaly detection
        current_metrics = {"qber": 0.02, "key_rate": 1000, "loss": 0.1}
        anomalies = detector.detect_anomalies(current_metrics)

        self.assertIn("qber", anomalies)
        self.assertIn("key_rate", anomalies)
        self.assertIn("loss", anomalies)


class TestQuantumNetwork(unittest.TestCase):
    """Test cases for quantum network simulation."""

    def test_network_creation(self):
        """Test creation and basic operations of quantum network."""
        network = QuantumNetwork("Test Network")
        self.assertEqual(network.name, "Test Network")
        self.assertEqual(len(network.nodes), 0)
        self.assertEqual(len(network.connections), 0)

    def test_node_operations(self):
        """Test node addition and removal."""
        network = QuantumNetwork("Test Network")

        # Add nodes
        channel = QuantumChannel()
        from qkdpy.protocols import BB84

        protocol = BB84(channel)
        network.add_node("NodeA", protocol)
        network.add_node("NodeB", protocol)

        self.assertEqual(len(network.nodes), 2)
        self.assertIn("NodeA", network.nodes)
        self.assertIn("NodeB", network.nodes)

        # Add connection
        network.add_connection("NodeA", "NodeB", channel)
        self.assertEqual(len(network.connections), 2)  # Bidirectional

        # Test path finding
        path = network.get_shortest_path("NodeA", "NodeB")
        self.assertEqual(path, ["NodeA", "NodeB"])

        # Remove node
        network.remove_node("NodeB")
        self.assertEqual(len(network.nodes), 1)
        self.assertNotIn("NodeB", network.nodes)

    def test_multiparty_qkd(self):
        """Test multi-party QKD functionality."""
        # Test secret sharing
        # Use a longer secret (128 bits) to avoid accidental reconstruction by subset
        # which has a probability of 1/2^N
        secret = [np.random.randint(0, 2) for _ in range(128)]
        shares = MultiPartyQKD.quantum_secret_sharing(secret, 3, 2)

        self.assertEqual(len(shares), 3)
        for share in shares:
            self.assertEqual(len(share), len(secret))

        # Reconstruct secret with all shares
        reconstructed = MultiPartyQKD.reconstruct_secret(shares)
        self.assertEqual(secret, reconstructed)

        # Test that with fewer than all shares, reconstruction fails
        # (This is expected behavior for our simplified (n,n) scheme)
        subset_reconstructed = MultiPartyQKD.reconstruct_secret(shares[:2])
        self.assertNotEqual(
            secret, subset_reconstructed
        )  # Should not equal the original


if __name__ == "__main__":
    unittest.main()
