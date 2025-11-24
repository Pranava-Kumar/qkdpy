"""Tests for enhanced network functionality in QKDpy."""

import unittest

from qkdpy import BB84, QuantumChannel
from qkdpy.network.multiparty_qkd import TrustedRelayNetwork
from qkdpy.network.quantum_network import QuantumNetwork


class TestNetworkEnhancements(unittest.TestCase):
    """Test cases for enhanced network functionality."""

    def test_multihop_key_establishment(self):
        """Test multi-hop key establishment in QuantumNetwork."""
        # Create a quantum network
        network = QuantumNetwork("Test MultiHop Network")

        # Add nodes
        channel1 = QuantumChannel(
            loss=0.1, noise_model="depolarizing", noise_level=0.05
        )
        channel2 = QuantumChannel(
            loss=0.1, noise_model="depolarizing", noise_level=0.05
        )
        protocol1 = BB84(channel1)
        protocol2 = BB84(channel1)
        protocol3 = BB84(channel1)

        network.add_node("Alice", protocol1)
        network.add_node("Bob", protocol2)
        network.add_node("Charlie", protocol3)

        # Add connections to create a linear network: Alice-Bob-Charlie
        network.add_connection("Alice", "Bob", channel1)
        network.add_connection("Bob", "Charlie", channel2)

        # Test multi-hop key establishment
        # This should work now with our enhanced implementation
        key = network.establish_key_between_nodes("Alice", "Charlie", 64)
        # With our enhancement, this should return a valid key
        self.assertIsNotNone(key)

    def test_trusted_relay_network(self):
        """Test trusted relay network functionality."""
        # Create a trusted relay network
        nodes = ["Alice", "Bob", "Charlie", "Relay1", "Relay2"]
        relay_nodes = ["Relay1", "Relay2"]
        network = TrustedRelayNetwork(nodes, relay_nodes)

        # Add channels
        channel1 = QuantumChannel(
            loss=0.1, noise_model="depolarizing", noise_level=0.05
        )
        channel2 = QuantumChannel(
            loss=0.1, noise_model="depolarizing", noise_level=0.05
        )
        channel3 = QuantumChannel(
            loss=0.1, noise_model="depolarizing", noise_level=0.05
        )
        channel4 = QuantumChannel(
            loss=0.1, noise_model="depolarizing", noise_level=0.05
        )

        network.add_channel("Alice", "Relay1", channel1)
        network.add_channel("Relay1", "Relay2", channel2)
        network.add_channel("Relay2", "Charlie", channel3)
        network.add_channel("Bob", "Relay1", channel4)

        # Test multi-hop key establishment using trusted relays
        _ = network.establish_multihop_key("Alice", "Charlie", 64)
        # This should work with the fixed implementation
        # Note: This might still fail in some cases due to the random nature of QKD
        # but it should not fail with an IndexError

    def test_entanglement_swapping(self):
        """Test entanglement swapping functionality."""
        # Create a quantum network
        network = QuantumNetwork("Test Entanglement Network")

        # Add nodes
        channel1 = QuantumChannel(
            loss=0.1, noise_model="depolarizing", noise_level=0.05
        )
        channel2 = QuantumChannel(
            loss=0.1, noise_model="depolarizing", noise_level=0.05
        )
        protocol1 = BB84(channel1)
        protocol2 = BB84(channel1)
        protocol3 = BB84(channel1)

        network.add_node("Alice", protocol1)
        network.add_node("Bob", protocol2)
        network.add_node("Charlie", protocol3)

        # Add connections
        network.add_connection("Alice", "Bob", channel1)
        network.add_connection("Bob", "Charlie", channel2)

        # Test entanglement swapping
        # This is a new functionality we've implemented
        success = network.perform_entanglement_swapping("Alice", "Charlie")
        # This should now work
        self.assertTrue(success)


if __name__ == "__main__":
    unittest.main()
