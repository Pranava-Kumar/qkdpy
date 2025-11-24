"""Tests for realistic quantum network simulation."""

import unittest

from qkdpy.core import QuantumChannel
from qkdpy.network.realistic_quantum_network import (
    RealisticQuantumNetwork,
    RealisticQuantumNode,
)
from qkdpy.protocols.bb84 import BB84


class TestRealisticQuantumNetwork(unittest.TestCase):
    """Test cases for realistic quantum network simulation."""

    def test_realistic_quantum_node_initialization(self):
        """Test initialization of RealisticQuantumNode."""
        channel = QuantumChannel()
        protocol = BB84(channel)
        node = RealisticQuantumNode("Node1", protocol)

        self.assertEqual(node.node_id, "Node1")
        self.assertEqual(node.memory_capacity, 1000)
        self.assertEqual(node.memory_used, 0)
        self.assertEqual(node.processing_rate, 1000)
        self.assertEqual(node.detection_efficiency, 0.7)
        self.assertEqual(node.hardware_status, "operational")
        self.assertEqual(node.health, 1.0)

    def test_realistic_quantum_node_key_management(self):
        """Test key management in RealisticQuantumNode."""
        channel = QuantumChannel()
        protocol = BB84(channel)
        node = RealisticQuantumNode("Node1", protocol)

        # Test storing a key
        key = [1, 0, 1, 1, 0, 0, 1, 0]
        success = node.store_key("Node2", key)
        self.assertTrue(success)
        self.assertEqual(node.memory_used, len(key))

        # Test retrieving a key
        retrieved_key = node.get_key("Node2")
        self.assertEqual(retrieved_key, key)

        # Test removing a key
        success = node.remove_key("Node2")
        self.assertTrue(success)
        self.assertEqual(node.memory_used, 0)

        # Test retrieving a non-existent key
        retrieved_key = node.get_key("Node3")
        self.assertIsNone(retrieved_key)

    def test_realistic_quantum_node_hardware_status(self):
        """Test hardware status management in RealisticQuantumNode."""
        channel = QuantumChannel()
        protocol = BB84(channel)
        node = RealisticQuantumNode("Node1", protocol)

        # Test initial status
        self.assertEqual(node.hardware_status, "operational")

        # Simulate hardware degradation
        node.degradation_rate = 0.1  # More reasonable degradation rate for testing
        node.update_hardware_status()
        self.assertLess(node.health, 1.0)

        # Test calibration
        initial_health = node.health
        success = node.calibrate()
        self.assertTrue(success)
        self.assertGreaterEqual(node.health, initial_health)

    def test_realistic_quantum_network_initialization(self):
        """Test initialization of RealisticQuantumNetwork."""
        network = RealisticQuantumNetwork("Test Network")

        self.assertEqual(network.name, "Test Network")
        self.assertEqual(network.network_status, "operational")
        self.assertEqual(len(network.nodes), 0)
        self.assertEqual(len(network.connections), 0)

    def test_realistic_quantum_network_node_management(self):
        """Test node management in RealisticQuantumNetwork."""
        network = RealisticQuantumNetwork("Test Network")

        # Test adding a node
        success = network.add_node("Node1")
        self.assertTrue(success)
        self.assertEqual(len(network.nodes), 1)
        self.assertIn("Node1", network.nodes)

        # Test adding duplicate node
        success = network.add_node("Node1")
        self.assertFalse(success)
        self.assertEqual(len(network.nodes), 1)

        # Test removing a node
        success = network.remove_node("Node1")
        self.assertTrue(success)
        self.assertEqual(len(network.nodes), 0)
        self.assertNotIn("Node1", network.nodes)

    def test_realistic_quantum_network_connection_management(self):
        """Test connection management in RealisticQuantumNetwork."""
        network = RealisticQuantumNetwork("Test Network")

        # Add nodes
        network.add_node("Node1")
        network.add_node("Node2")

        # Test adding a connection
        success = network.add_connection("Node1", "Node2")
        self.assertTrue(success)
        self.assertEqual(len(network.connections), 2)  # Bidirectional
        self.assertIn(("Node1", "Node2"), network.connections)
        self.assertIn(("Node2", "Node1"), network.connections)

    def test_realistic_quantum_network_pathfinding(self):
        """Test pathfinding in RealisticQuantumNetwork."""
        network = RealisticQuantumNetwork("Test Network")

        # Add nodes
        network.add_node("Node1")
        network.add_node("Node2")
        network.add_node("Node3")

        # Add connections to create a linear network: Node1-Node2-Node3
        network.add_connection("Node1", "Node2")
        network.add_connection("Node2", "Node3")

        # Test pathfinding
        path = network.get_shortest_path("Node1", "Node3")
        self.assertEqual(path, ["Node1", "Node2", "Node3"])

        # Test pathfinding with non-existent nodes
        with self.assertRaises(ValueError):
            network.get_shortest_path("Node1", "Node4")

    def test_realistic_quantum_network_statistics(self):
        """Test network statistics in RealisticQuantumNetwork."""
        network = RealisticQuantumNetwork("Test Network")

        # Add nodes
        network.add_node("Node1")
        network.add_node("Node2")

        # Add connection
        network.add_connection("Node1", "Node2")

        # Get statistics
        stats = network.get_network_statistics()

        self.assertIn("network_name", stats)
        self.assertIn("network_status", stats)
        self.assertIn("num_nodes", stats)
        self.assertIn("num_connections", stats)
        self.assertIn("average_degree", stats)
        self.assertIn("network_diameter", stats)
        self.assertIn("average_node_health", stats)
        self.assertIn("memory_usage", stats)

    def test_realistic_quantum_network_calibration(self):
        """Test network calibration in RealisticQuantumNetwork."""
        network = RealisticQuantumNetwork("Test Network")

        # Add nodes
        network.add_node("Node1")
        network.add_node("Node2")

        # Calibrate network
        results = network.calibrate_network()

        self.assertIn("successful_calibrations", results)
        self.assertIn("failed_calibrations", results)
        self.assertIn("calibrated_nodes", results)
        self.assertIn("failed_nodes", results)

        # All nodes should be successfully calibrated
        self.assertEqual(results["successful_calibrations"], 2)
        self.assertEqual(results["failed_calibrations"], 0)
        self.assertEqual(len(results["calibrated_nodes"]), 2)
        self.assertEqual(len(results["failed_nodes"]), 0)

    def test_realistic_quantum_network_environmental_effects(self):
        """Test environmental effects simulation in RealisticQuantumNetwork."""
        network = RealisticQuantumNetwork("Test Network")

        # Add a node
        network.add_node("Node1")

        # Store initial values
        initial_temp = network.ambient_temperature
        initial_emi = network.electromagnetic_interference
        initial_vibration = network.vibration_level

        # Simulate environmental effects
        network.simulate_environmental_effects(1.0)

        # Values should have changed (random fluctuations)
        # Note: This test might occasionally fail due to randomness
        # but it's unlikely that all three values remain exactly the same
        changes = (
            network.ambient_temperature != initial_temp
            or network.electromagnetic_interference != initial_emi
            or network.vibration_level != initial_vibration
        )

        # At least one value should have changed
        self.assertTrue(changes)


if __name__ == "__main__":
    unittest.main()
