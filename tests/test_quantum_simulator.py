"""Tests for quantum simulator and network analyzer."""

import unittest

from qkdpy.core import QuantumChannel, Qubit
from qkdpy.protocols import BB84
from qkdpy.utils import QuantumNetworkAnalyzer, QuantumSimulator


class TestQuantumSimulator(unittest.TestCase):
    """Test cases for the QuantumSimulator class."""

    def setUp(self):
        """Set up test fixtures."""
        self.simulator = QuantumSimulator()

    def test_simulator_initialization(self):
        """Test quantum simulator initialization."""
        self.assertEqual(len(self.simulator.simulation_history), 0)
        self.assertEqual(len(self.simulator.performance_stats), 0)

    def test_simulate_channel_performance(self):
        """Test simulating channel performance."""
        channel = QuantumChannel(loss=0.1, noise_level=0.05)
        initial_state = Qubit.zero()

        # Run simulation
        results = self.simulator.simulate_channel_performance(
            channel, num_trials=100, initial_state=initial_state
        )

        # Check results
        self.assertIn("transmission_rate", results)
        self.assertIn("average_fidelity", results)
        self.assertIn("channel_stats", results)

    def test_analyze_protocol_security(self):
        """Test analyzing protocol security."""
        channel = QuantumChannel(loss=0.1, noise_level=0.05)
        protocol = BB84(channel, key_length=50)

        # Run security analysis
        results = self.simulator.analyze_protocol_security(
            protocol, num_simulations=10, eavesdropping_probability=0.5
        )

        # Check results
        self.assertIn("security_rate", results)
        self.assertIn("average_qber", results)
        self.assertIn("average_key_rate", results)

    def test_benchmark_protocols(self):
        """Test benchmarking protocols."""
        channel = QuantumChannel(loss=0.1, noise_level=0.05)
        protocols = [BB84(channel, key_length=50), BB84(channel, key_length=50)]

        # Run benchmark
        results = self.simulator.benchmark_protocols(protocols, num_trials=5)

        # Check results
        self.assertIn("protocol_0", results)
        self.assertIn("protocol_1", results)

    def test_get_simulation_history(self):
        """Test getting simulation history."""
        # Run a simulation to populate history
        channel = QuantumChannel()
        self.simulator.simulate_channel_performance(channel, num_trials=10)

        # Get history
        history = self.simulator.get_simulation_history()

        # Check that we have history
        self.assertGreater(len(history), 0)

    def test_get_performance_statistics(self):
        """Test getting performance statistics."""
        # Run a simulation to populate history
        channel = QuantumChannel()
        self.simulator.simulate_channel_performance(channel, num_trials=10)

        # Get statistics
        stats = self.simulator.get_performance_statistics()

        # Check statistics
        self.assertIn("total_simulations", stats)
        self.assertIn("simulation_types", stats)


class TestQuantumNetworkAnalyzer(unittest.TestCase):
    """Test cases for the QuantumNetworkAnalyzer class."""

    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = QuantumNetworkAnalyzer()

    def test_analyzer_initialization(self):
        """Test quantum network analyzer initialization."""
        self.assertEqual(len(self.analyzer.network_topology), 0)
        self.assertEqual(len(self.analyzer.node_performance), 0)

    def test_analyze_network_topology(self):
        """Test analyzing network topology."""
        nodes = ["A", "B", "C", "D"]
        connections = [
            ("A", "B", 10.0),
            ("B", "C", 15.0),
            ("C", "D", 12.0),
            ("A", "D", 20.0),
        ]

        # Analyze topology
        results = self.analyzer.analyze_network_topology(nodes, connections)

        # Check results
        self.assertIn("num_nodes", results)
        self.assertIn("num_connections", results)
        self.assertIn("average_distance", results)
        self.assertIn("is_connected", results)

    def test_simulate_network_performance(self):
        """Test simulating network performance."""
        node_performance = {
            "A": {"key_rate": 0.8, "qber": 0.05, "distance": 10},
            "B": {"key_rate": 0.7, "qber": 0.06, "distance": 15},
            "C": {"key_rate": 0.75, "qber": 0.04, "distance": 12},
        }

        # Simulate performance
        results = self.analyzer.simulate_network_performance(node_performance)

        # Check results
        self.assertIn("network_avg_key_rate", results)
        self.assertIn("network_avg_qber", results)
        self.assertIn("best_performing_node", results)

    def test_get_network_statistics(self):
        """Test getting network statistics."""
        # Get statistics
        stats = self.analyzer.get_network_statistics()

        # Check statistics
        self.assertIn("topology", stats)
        self.assertIn("node_performance", stats)


if __name__ == "__main__":
    unittest.main()
