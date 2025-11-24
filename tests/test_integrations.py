"""Tests for quantum computing framework integrations."""

import os
import sys
import unittest

# Add the src directory to the path so we can import qkdpy
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


class TestIntegrations(unittest.TestCase):
    """Test cases for quantum computing framework integrations."""

    def test_qiskit_integration_import(self):
        """Test Qiskit integration import."""
        try:
            from qkdpy.integrations.qiskit_integration import QiskitIntegration

            # If we get here, the import succeeded
            qiskit_available = True
        except ImportError:
            # Qiskit is not installed
            qiskit_available = False

        # We'll just check that the module can be imported if Qiskit is available
        # In a real test environment, we would install Qiskit and test functionality
        if qiskit_available:
            # Try to create an instance
            try:
                integration = QiskitIntegration()
                self.assertIsInstance(integration, QiskitIntegration)
            except ImportError as e:
                # This means Qiskit is not properly installed
                self.skipTest(f"Qiskit not properly installed: {e}")
        else:
            # Skip the test if Qiskit is not available
            self.skipTest("Qiskit not installed")

    def test_cirq_integration_import(self):
        """Test Cirq integration import."""
        try:
            from qkdpy.integrations.cirq_integration import CirqIntegration

            # If we get here, the import succeeded
            cirq_available = True
        except ImportError:
            # Cirq is not installed
            cirq_available = False

        # We'll just check that the module can be imported if Cirq is available
        if cirq_available:
            # Try to create an instance
            try:
                integration = CirqIntegration()
                self.assertIsInstance(integration, CirqIntegration)
            except ImportError as e:
                # This means Cirq is not properly installed
                self.skipTest(f"Cirq not properly installed: {e}")
        else:
            # Skip the test if Cirq is not available
            self.skipTest("Cirq not installed")

    def test_pennylane_integration_import(self):
        """Test PennyLane integration import."""
        try:
            from qkdpy.integrations.pennylane_integration import PennyLaneIntegration

            # If we get here, the import succeeded
            pennylane_available = True
        except ImportError:
            # PennyLane is not installed
            pennylane_available = False

        # We'll just check that the module can be imported if PennyLane is available
        if pennylane_available:
            # Try to create an instance
            try:
                integration = PennyLaneIntegration()
                self.assertIsInstance(integration, PennyLaneIntegration)
            except ImportError as e:
                # This means PennyLane is not properly installed
                self.skipTest(f"PennyLane not properly installed: {e}")
        else:
            # Skip the test if PennyLane is not available
            self.skipTest("PennyLane not installed")

    def test_integrations_module_import(self):
        """Test integrations module import."""
        try:
            from qkdpy import integrations

            # Check that the module was imported successfully
            self.assertTrue(hasattr(integrations, "__all__"))
        except ImportError:
            self.fail("Failed to import integrations module")


if __name__ == "__main__":
    unittest.main()
