"""Tests for advanced visualization tools."""

import unittest

# Set matplotlib backend to non-interactive to avoid GUI issues in tests
import matplotlib
import numpy as np

matplotlib.use("Agg")  # Use non-interactive backend

from qkdpy.core import Qubit
from qkdpy.utils import AdvancedKeyRateAnalyzer, AdvancedProtocolVisualizer


class TestAdvancedProtocolVisualizer(unittest.TestCase):
    """Test cases for the AdvancedProtocolVisualizer class."""

    def test_plot_quantum_state_evolution(self):
        """Test plotting quantum state evolution."""
        # Create a list of qubit states
        states = [Qubit.zero(), Qubit.plus(), Qubit.one(), Qubit.minus()]

        # Create the plot
        fig = AdvancedProtocolVisualizer.plot_quantum_state_evolution(
            states, "Test State Evolution"
        )

        # Check that we got a figure
        self.assertIsNotNone(fig)

    def test_plot_protocol_comparison(self):
        """Test plotting protocol comparison."""
        # Create test data
        protocols_data = {
            "BB84": {"key_rate": 0.8, "qber": 0.05, "efficiency": 0.7},
            "E91": {"key_rate": 0.6, "qber": 0.03, "efficiency": 0.8},
            "SARG04": {"key_rate": 0.7, "qber": 0.04, "efficiency": 0.75},
        }

        # Create the plot
        fig = AdvancedProtocolVisualizer.plot_protocol_comparison(
            protocols_data, "key_rate", "Test Protocol Comparison"
        )

        # Check that we got a figure
        self.assertIsNotNone(fig)

    def test_plot_security_bounds(self):
        """Test plotting security bounds."""
        # Create test QBER values
        qber_values = np.linspace(0, 0.2, 20)

        # Create the plot
        fig = AdvancedProtocolVisualizer.plot_security_bounds(
            qber_values, "Test Security Bounds"
        )

        # Check that we got a figure
        self.assertIsNotNone(fig)

    def test_plot_entanglement_verification(self):
        """Test plotting entanglement verification."""
        # Create test Bell test results
        bell_test_results = {
            "correlations": {
                "E(0,0)": 0.7,
                "E(0,1)": 0.6,
                "E(1,0)": 0.65,
                "E(1,1)": -0.75,
            },
            "s_value": 2.7,
        }

        # Create the plot
        fig = AdvancedProtocolVisualizer.plot_entanglement_verification(
            bell_test_results, "Test Entanglement Verification"
        )

        # Check that we got a figure
        self.assertIsNotNone(fig)


class TestAdvancedKeyRateAnalyzer(unittest.TestCase):
    """Test cases for the AdvancedKeyRateAnalyzer class."""

    def test_plot_key_rate_vs_parameters(self):
        """Test plotting key rate vs parameters."""

        # Create mock protocol
        class MockProtocol:
            pass

        protocol = MockProtocol()

        # Create test parameter values
        parameter_values = np.linspace(0, 0.5, 10)

        # Create the plot
        fig = AdvancedKeyRateAnalyzer.plot_key_rate_vs_parameters(
            protocol, "channel_loss", parameter_values, "Test Key Rate vs Loss"
        )

        # Check that we got a figure
        self.assertIsNotNone(fig)

    def test_plot_multi_dimensional_analysis(self):
        """Test plotting multi-dimensional analysis."""
        # Create test data
        protocols_data = {
            "BB84": {"key_rate": 0.8, "qber": 0.05, "distance": 10},
            "E91": {"key_rate": 0.6, "qber": 0.03, "distance": 15},
            "SARG04": {"key_rate": 0.7, "qber": 0.04, "distance": 12},
        }

        # Create the plot
        fig = AdvancedKeyRateAnalyzer.plot_multi_dimensional_analysis(
            protocols_data, "Test Multi-Dimensional Analysis"
        )

        # Check that we got a figure
        self.assertIsNotNone(fig)


if __name__ == "__main__":
    unittest.main()
