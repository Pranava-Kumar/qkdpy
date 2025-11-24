"""Tests for quantum error correction codes."""

import unittest

import numpy as np

from qkdpy.core import Qubit
from qkdpy.key_management.quantum_error_correction import QuantumErrorCorrection


class TestQuantumErrorCorrection(unittest.TestCase):
    """Test cases for quantum error correction codes."""

    def test_shor_code_encoding_decoding(self):
        """Test Shor code encoding and decoding."""
        # Create a test qubit
        qubit = Qubit.plus()  # |+⟩ state

        # Encode using Shor code
        encoded_qubits = QuantumErrorCorrection.shor_code_encode(qubit)
        self.assertEqual(len(encoded_qubits), 9)

        # Decode using Shor code
        decoded_qubit = QuantumErrorCorrection.shor_code_decode(encoded_qubits)

        # Check that the decoded qubit is close to the original
        fidelity = abs(np.dot(qubit.state.conj(), decoded_qubit.state)) ** 2
        self.assertGreater(fidelity, 0.9)

    def test_steane_code_encoding_decoding(self):
        """Test Steane code encoding and decoding."""
        # Create a test qubit
        qubit = Qubit.minus()  # |-⟩ state

        # Encode using Steane code
        encoded_qubits = QuantumErrorCorrection.steane_code_encode(qubit)
        self.assertEqual(len(encoded_qubits), 7)

        # Decode using Steane code
        decoded_qubit = QuantumErrorCorrection.steane_code_decode(encoded_qubits)

        # Check that the decoded qubit is close to the original
        fidelity = abs(np.dot(qubit.state.conj(), decoded_qubit.state)) ** 2
        self.assertGreater(fidelity, 0.9)

    def test_five_qubit_code_encoding_decoding(self):
        """Test 5-qubit code encoding and decoding."""
        # Create a test qubit
        qubit = Qubit.zero()  # |0⟩ state

        # Encode using 5-qubit code
        encoded_qubits = QuantumErrorCorrection.five_qubit_code_encode(qubit)
        self.assertEqual(len(encoded_qubits), 5)

        # Decode using 5-qubit code
        decoded_qubit = QuantumErrorCorrection.five_qubit_code_decode(encoded_qubits)

        # Check that the decoded qubit is close to the original
        fidelity = abs(np.dot(qubit.state.conj(), decoded_qubit.state)) ** 2
        self.assertGreater(fidelity, 0.9)

    def test_error_detection_and_correction(self):
        """Test error detection and correction."""
        # Create test qubits
        qubits = [Qubit.zero(), Qubit.one(), Qubit.plus()]

        # Test error correction
        corrected_qubits = QuantumErrorCorrection.detect_and_correct_error(qubits, "X")
        self.assertEqual(len(corrected_qubits), 3)

    def test_quantum_error_correction_simulation(self):
        """Test complete quantum error correction simulation."""
        # Create a test qubit
        qubit = Qubit.zero()

        # Run simulation with Shor code
        decoded_qubit, success = (
            QuantumErrorCorrection.quantum_error_correction_simulation(
                qubit, "shor", 0.1
            )
        )

        # Check results
        self.assertIsInstance(decoded_qubit, Qubit)
        self.assertIsInstance(success, (bool, np.bool_))

    def test_code_parameters(self):
        """Test code parameters retrieval."""
        # Test Shor code parameters
        shor_params = QuantumErrorCorrection.get_code_parameters("shor")
        self.assertEqual(shor_params["n"], 9)
        self.assertEqual(shor_params["k"], 1)
        self.assertEqual(shor_params["d"], 3)

        # Test Steane code parameters
        steane_params = QuantumErrorCorrection.get_code_parameters("steane")
        self.assertEqual(steane_params["n"], 7)
        self.assertEqual(steane_params["k"], 1)
        self.assertEqual(steane_params["d"], 3)

        # Test 5-qubit code parameters
        five_qubit_params = QuantumErrorCorrection.get_code_parameters("five_qubit")
        self.assertEqual(five_qubit_params["n"], 5)
        self.assertEqual(five_qubit_params["k"], 1)
        self.assertEqual(five_qubit_params["d"], 3)

    def test_error_correction_performance(self):
        """Test error correction performance simulation."""
        # Run performance simulation
        results = QuantumErrorCorrection.simulate_error_correction_performance(
            num_trials=100, code_type="shor", error_probability=0.05
        )

        # Check results
        self.assertIn("success_rate", results)
        self.assertIn("average_fidelity", results)
        self.assertIn("fidelity_std", results)
        self.assertGreaterEqual(results["success_rate"], 0.0)
        self.assertLessEqual(results["success_rate"], 1.0)
        self.assertGreaterEqual(results["average_fidelity"], 0.0)
        self.assertLessEqual(results["average_fidelity"], 1.0)


if __name__ == "__main__":
    unittest.main()
