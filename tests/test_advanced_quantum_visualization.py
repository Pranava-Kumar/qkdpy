"""Tests for advanced quantum visualization tools."""

import os
import sys
import unittest

# Set matplotlib backend before importing pyplot
import matplotlib

matplotlib.use("Agg")  # Use non-interactive backend
import matplotlib.pyplot as plt

# Add the src directory to the path so we can import qkdpy
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from qkdpy.core import QuantumChannel, Qubit
from qkdpy.utils.advanced_quantum_visualization import (
    InteractiveQuantumVisualizer,
    ProtocolExecutionVisualizer,
    QuantumStateVisualizer,
)


class TestAdvancedQuantumVisualization(unittest.TestCase):
    """Test cases for advanced quantum visualization tools."""

    def setUp(self):
        """Set up test fixtures."""
        # Create test qubits
        self.qubit_zero = Qubit.zero()
        self.qubit_one = Qubit.one()
        self.qubit_plus = Qubit.plus()
        self.qubit_minus = Qubit.minus()

        # Create test quantum channel
        self.channel = QuantumChannel(
            loss=0.1, noise_model="depolarizing", noise_level=0.05
        )

    def test_density_matrix_visualization(self):
        """Test density matrix visualization."""
        # Test with |0⟩ state
        fig = QuantumStateVisualizer.plot_density_matrix(
            self.qubit_zero, title="Test Density Matrix"
        )

        # Check that figure was created
        self.assertIsNotNone(fig)

        # Close the figure to free memory

        plt.close(fig)

    def test_bloch_vector_evolution(self):
        """Test Bloch vector evolution visualization."""
        # Create a list of qubit states
        qubit_states = [
            self.qubit_zero,
            self.qubit_plus,
            self.qubit_one,
            self.qubit_minus,
        ]
        time_points = [0, 1, 2, 3]

        fig = QuantumStateVisualizer.plot_bloch_vector_evolution(
            qubit_states, time_points, title="Test Bloch Vector Evolution"
        )

        # Check that figure was created
        self.assertIsNotNone(fig)

        # Close the figure to free memory

        plt.close(fig)

    def test_quantum_state_histogram(self):
        """Test quantum state histogram visualization."""
        # Create a list of qubit states
        qubit_states = [
            self.qubit_zero,
            self.qubit_plus,
            self.qubit_one,
            self.qubit_minus,
        ]

        fig = QuantumStateVisualizer.plot_quantum_state_histogram(
            qubit_states, measurement_axis="Z", title="Test Quantum State Histogram"
        )

        # Check that figure was created
        self.assertIsNotNone(fig)

        # Close the figure to free memory

        plt.close(fig)

    def test_quantum_channel_characteristics(self):
        """Test quantum channel characteristics visualization."""
        fig = QuantumStateVisualizer.plot_quantum_channel_characteristics(
            self.channel, title="Test Channel Characteristics"
        )

        # Check that figure was created
        self.assertIsNotNone(fig)

        # Close the figure to free memory

        plt.close(fig)

    def test_protocol_execution_timeline(self):
        """Test protocol execution timeline visualization."""
        # This is a simplified test since we don't have a real protocol object
        # We'll test the functionality by mocking the necessary attributes

        class MockProtocol:
            pass

        mock_protocol = MockProtocol()

        fig = ProtocolExecutionVisualizer.plot_protocol_execution_timeline(
            mock_protocol, title="Test Protocol Timeline"
        )

        # Check that figure was created
        self.assertIsNotNone(fig)

        # Close the figure to free memory

        plt.close(fig)

    def test_key_generation_performance(self):
        """Test key generation performance visualization."""
        # Create test data
        key_lengths = [128, 256, 512, 1024, 2048]
        execution_times = [0.1, 0.2, 0.5, 1.2, 2.8]
        qber_values = [0.01, 0.02, 0.03, 0.04, 0.05]

        fig = ProtocolExecutionVisualizer.plot_key_generation_performance(
            key_lengths,
            execution_times,
            qber_values,
            title="Test Key Generation Performance",
        )

        # Check that figure was created
        self.assertIsNotNone(fig)

        # Close the figure to free memory

        plt.close(fig)

    def test_security_analysis(self):
        """Test security analysis visualization."""
        # Create test QBER values
        qber_values = [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10]
        secure_threshold = 0.08

        fig = ProtocolExecutionVisualizer.plot_security_analysis(
            qber_values, secure_threshold, title="Test Security Analysis"
        )

        # Check that figure was created
        self.assertIsNotNone(fig)

        # Close the figure to free memory

        plt.close(fig)

    def test_protocol_comparison(self):
        """Test protocol comparison visualization."""
        # Create test data
        protocol_results = {
            "BB84": {"key_rate": 1000, "qber": 0.02, "execution_time": 0.5},
            "E91": {"key_rate": 800, "qber": 0.01, "execution_time": 0.8},
            "SARG04": {"key_rate": 1200, "qber": 0.03, "execution_time": 0.4},
        }

        fig = ProtocolExecutionVisualizer.plot_protocol_comparison(
            protocol_results,
            metrics=["key_rate", "qber", "execution_time"],
            title="Test Protocol Comparison",
        )

        # Check that figure was created
        self.assertIsNotNone(fig)

        # Close the figure to free memory

        plt.close(fig)

    def test_interactive_bloch_sphere(self):
        """Test interactive Bloch sphere visualization."""
        fig = InteractiveQuantumVisualizer.create_interactive_bloch_sphere(
            self.qubit_plus, title="Test Interactive Bloch Sphere"
        )

        # Check that figure was created
        self.assertIsNotNone(fig)

        # Close the figure to free memory

        plt.close(fig)

    def test_animate_qubit_evolution(self):
        """Test animated qubit evolution visualization."""
        # Create a list of qubit states
        qubit_states = [
            self.qubit_zero,
            self.qubit_plus,
            self.qubit_one,
            self.qubit_minus,
        ]

        fig = InteractiveQuantumVisualizer.animate_qubit_evolution(
            qubit_states, interval=200, title="Test Animated Qubit Evolution"
        )

        # Check that figure was created
        self.assertIsNotNone(fig)

        # Close the figure to free memory

        plt.close(fig)


if __name__ == "__main__":
    unittest.main()
