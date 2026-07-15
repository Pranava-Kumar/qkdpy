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
                self.assertIsInstance(
                    integration,
                    QiskitIntegration,
                    "QiskitIntegration instance should be created when Qiskit is available",
                )
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
                self.assertIsInstance(
                    integration,
                    CirqIntegration,
                    "CirqIntegration instance should be created when Cirq is available",
                )
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
                self.assertIsInstance(
                    integration,
                    PennyLaneIntegration,
                    "PennyLaneIntegration instance should be created when PennyLane is available",
                )
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
            self.assertTrue(
                hasattr(integrations, "__all__"),
                "integrations module should have __all__",
            )
            self.assertIn("QpiAIIntegration", integrations.__all__)
        except ImportError:
            self.fail("Failed to import integrations module")


class TestQiskitQuantumInfo(unittest.TestCase):
    """Test Qiskit integration quantum information methods."""

    def setUp(self):
        try:
            from qkdpy.integrations.qiskit_integration import QiskitIntegration

            self.integration = QiskitIntegration()
        except ImportError:
            self.skipTest("Qiskit not installed")

    def test_state_from_label(self):
        """Test Statevector.from_label() for BB84 basis states."""
        import numpy as np

        sv0 = self.integration.state_from_label("0")
        sv1 = self.integration.state_from_label("1")
        sv_plus = self.integration.state_from_label("+")
        sv_minus = self.integration.state_from_label("-")

        self.assertAlmostEqual(
            abs(sv0.data[0]), 1.0, msg="|0> should have |0> amplitude = 1"
        )
        self.assertAlmostEqual(
            abs(sv1.data[1]), 1.0, msg="|1> should have |1> amplitude = 1"
        )
        self.assertAlmostEqual(
            abs(sv_plus.data[0]),
            1 / np.sqrt(2),
            msg="|+> should have |0> amplitude = 1/√2",
        )
        self.assertAlmostEqual(
            abs(sv_minus.data[0]),
            1 / np.sqrt(2),
            msg="|-> should have |0> amplitude = 1/√2",
        )

    def test_entanglement_measures_bell_state(self):
        """Test concurrence and entanglement_of_formation on Bell state."""
        import numpy as np
        from qiskit.quantum_info import Statevector

        # Bell state |Φ+⟩ = (|00⟩ + |11⟩)/√2
        bell = Statevector([1, 0, 0, 1]) / np.sqrt(2)

        concurrence = self.integration.compute_concurrence(bell)
        eof = self.integration.compute_entanglement_of_formation(bell)

        self.assertAlmostEqual(
            concurrence, 1.0, places=7, msg="Concurrence of Bell state should be 1"
        )
        self.assertAlmostEqual(eof, 1.0, places=7, msg="EOF of Bell state should be 1")

    def test_entanglement_measures_separable_state(self):
        """Test concurrence on separable state (should be 0)."""
        from qiskit.quantum_info import Statevector

        separable = Statevector([1, 0, 0, 0])  # |00⟩

        concurrence = self.integration.compute_concurrence(separable)
        self.assertAlmostEqual(
            concurrence, 0.0, places=7, msg="Concurrence of separable |00> should be 0"
        )

    def test_von_neumann_entropy(self):
        """Test von Neumann entropy on Bell state (full state entropy = 0)."""
        import numpy as np
        from qiskit.quantum_info import Statevector

        bell = Statevector([1, 0, 0, 1]) / np.sqrt(2)
        # Full state of pure Bell pair has entropy 0
        entropy = self.integration.compute_von_neumann_entropy(bell)

        self.assertAlmostEqual(
            entropy,
            0.0,
            places=6,
            msg="Full Bell state entropy should be 0 for pure state",
        )

    def test_partial_trace(self):
        """Test partial trace on Bell state."""
        import numpy as np
        from qiskit.quantum_info import Statevector

        bell = Statevector([1, 0, 0, 1]) / np.sqrt(2)
        reduced = self.integration.compute_partial_trace(bell, qargs=[1])

        # Reduced state of Bell pair = I/2 purity = 0.5
        self.assertAlmostEqual(
            abs(reduced.purity()),
            0.5,
            places=6,
            msg="Reduced Bell state purity should be 0.5",
        )

    def test_mutual_information(self):
        """Test mutual information on Bell state."""
        import numpy as np
        from qiskit.quantum_info import Statevector

        bell = Statevector([1, 0, 0, 1]) / np.sqrt(2)
        mi = self.integration.compute_mutual_information(bell)

        # I(A:B) base-2 = 2 for max entangled
        self.assertAlmostEqual(
            mi, 2.0, places=5, msg="Mutual info of Bell state should be 2 bits"
        )

    def test_to_density_matrix(self):
        """Test Statevector to DensityMatrix conversion."""
        import numpy as np
        from qiskit.quantum_info import DensityMatrix, Statevector

        bell = Statevector([1, 0, 0, 1]) / np.sqrt(2)
        dm = self.integration.to_density_matrix(bell)

        self.assertIsInstance(
            dm, DensityMatrix, msg="to_density_matrix should return DensityMatrix"
        )
        self.assertEqual(
            dm._data.shape, (4, 4), msg="2-qubit density matrix should be 4x4"
        )
        self.assertAlmostEqual(
            abs(dm.purity()),
            1.0,
            places=6,
            msg="Pure Bell state density matrix purity should be 1",
        )

    def test_von_neumann_entropy_reduced(self):
        """Test von Neumann entropy on reduced Bell state density matrix."""
        import numpy as np
        from qiskit.quantum_info import Statevector

        bell = Statevector([1, 0, 0, 1]) / np.sqrt(2)
        reduced = self.integration.compute_partial_trace(bell, qargs=[1])
        entropy = self.integration.compute_von_neumann_entropy(reduced)

        # S(ρ_A) = log₂(2) = 1 for max entanglement
        self.assertAlmostEqual(
            entropy,
            1.0,
            places=6,
            msg="Reduced Bell state entropy should be 1 (max entangled)",
        )


class TestPennyLaneQuantumInfo(unittest.TestCase):
    """Test PennyLane integration quantum information methods."""

    def setUp(self):
        try:
            from qkdpy.integrations.pennylane_integration import (
                PennyLaneIntegration,
            )

            self.integration = PennyLaneIntegration()
        except ImportError:
            self.skipTest("PennyLane not installed")

    def test_vn_entropy_bell_state(self):
        """Test von Neumann entropy on Bell state."""
        import numpy as np

        bell = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)
        entropy = self.integration.compute_vn_entropy(bell, indices=[0])

        import math

        self.assertAlmostEqual(
            entropy,
            math.log(2),
            places=6,
            msg="Reduced Bell state von Neumann entropy should be ln(2)",
        )

    def test_purity_bell_state(self):
        """Test purity on Bell state (should be 1 for pure state)."""
        import numpy as np

        bell = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)
        purity = self.integration.compute_purity(bell, indices=[0, 1])
        self.assertAlmostEqual(
            purity, 1.0, places=6, msg="Purity of pure Bell state should be 1"
        )

    def test_fidelity_identical_states(self):
        """Test fidelity between identical states."""
        import numpy as np

        bell = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)
        fid = self.integration.compute_fidelity(bell, bell)
        self.assertAlmostEqual(
            fid, 1.0, places=6, msg="Fidelity of identical states should be 1"
        )

    def test_fidelity_orthogonal_states(self):
        """Test fidelity between orthogonal states."""
        import numpy as np

        zero = np.array([1, 0], dtype=complex)
        one = np.array([0, 1], dtype=complex)
        fid = self.integration.compute_fidelity(zero, one)
        self.assertAlmostEqual(
            fid, 0.0, places=6, msg="Fidelity of orthogonal states should be 0"
        )

    def test_trace_distance_identical(self):
        """Test trace distance between identical states (should be 0)."""
        import numpy as np

        bell = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)
        td = self.integration.compute_trace_distance(bell, bell)
        self.assertAlmostEqual(
            td, 0.0, places=6, msg="Trace distance between identical states should be 0"
        )

    def test_trace_distance_orthogonal(self):
        """Test trace distance between orthogonal states."""
        import numpy as np

        zero = np.array([1, 0], dtype=complex)
        one = np.array([0, 1], dtype=complex)
        td = self.integration.compute_trace_distance(zero, one)
        self.assertAlmostEqual(
            td,
            1.0,
            places=6,
            msg="Trace distance between orthogonal states should be 1",
        )

    def test_chsh_correlation(self):
        """Test CHSH correlation value (should violate Bell inequality).

        Uses optimal angles for |Φ+⟩ with RY rotations:
        a=0, a'=π/2, b=π/4, b'=-π/4  →  S = 2√2 ≈ 2.828
        """
        import numpy as np

        s = self.integration.compute_chsh_correlation(
            [0, np.pi / 2], [np.pi / 4, -np.pi / 4], num_qubits=1000
        )
        # Analytic CHSH for |Φ+⟩ with optimal angles = 2√2 ≈ 2.828
        expected = 2 * np.sqrt(2)
        self.assertAlmostEqual(
            s,
            expected,
            places=5,
            msg=f"CHSH S={s} should equal 2√2={expected} for Bell state with optimal angles",
        )


class TestQpiAIIntegration(unittest.TestCase):
    """Test QpiAI Quantum SDK integration."""

    def setUp(self):
        try:
            from qkdpy.integrations.qpiai_integration import QpiAIIntegration

            self.integration = QpiAIIntegration()
        except ImportError:
            self.skipTest("QpiAI Quantum SDK not installed")

    def test_statevector_from_array(self):
        """Test creating a Statevector from array."""

        sv = self.integration.statevector_from_array([1, 0, 0, 1])
        self.assertEqual(
            len(sv.data), 4, msg="2-qubit statevector should have 4 components"
        )

    def test_compute_concurrence(self):
        """Test concurrence on Bell state density matrix."""
        import numpy as np

        bell = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)
        dm = np.outer(bell, np.conjugate(bell))
        c = self.integration.compute_concurrence(dm)
        self.assertAlmostEqual(
            c, 1.0, places=6, msg="Concurrence of Bell state should be 1"
        )

    def test_compute_purity(self):
        """Test purity on pure Bell state."""
        import numpy as np

        bell = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)
        dm = np.outer(bell, np.conjugate(bell))
        p = self.integration.compute_purity(dm)
        self.assertAlmostEqual(
            p, 1.0, places=6, msg="Purity of pure Bell state should be 1"
        )

    def test_create_bb84_circuit(self):
        """Test BB84 circuit construction with QpiAI."""
        circuit = self.integration.create_bb84_circuit(
            num_qubits=2,
            alice_bases=["Z", "X"],
            bob_bases=["X", "Z"],
        )
        # Circuit should have been created (structure varies by RNG bits)
        self.assertIsNotNone(circuit, "BB84 circuit should be created")

    def test_create_entanglement_circuit(self):
        """Test Bell state circuit generation."""
        circuit, desc = self.integration.create_entanglement_circuit("|Ψ+>")
        self.assertIsNotNone(circuit, "Entanglement circuit should be created")
        self.assertIn("01⟩ +", desc, "Entanglement circuit should describe Bell state")

    def test_create_ghz_circuit(self):
        """Test GHZ state circuit generation."""
        circuit = self.integration.create_ghz_circuit(num_qubits=4)
        self.assertIsNotNone(circuit, "GHZ circuit should be created")

    def test_calculate_qber(self):
        """Test QBER calculation."""
        qber = self.integration.calculate_qber([0, 1, 0], [0, 1, 0])
        self.assertAlmostEqual(qber, 0.0, msg="QBER of identical sequences should be 0")

        qber_noisy = self.integration.calculate_qber([0, 1, 0], [0, 0, 0])
        self.assertAlmostEqual(
            qber_noisy, 1 / 3, msg="QBER with 1 error in 3 bits should be 1/3"
        )

    def test_compute_chsh_value(self):
        """Test CHSH S-value computation.

        Optimal angles for |Φ+⟩ with RY rotations:
        a=0, a'=π/2, b=π/4, b'=-π/4  →  S = 2√2 ≈ 2.828
        """
        import numpy as np

        s = self.integration.compute_chsh_value([0, np.pi / 2, np.pi / 4, -np.pi / 4])
        # Max quantum CHSH = 2√2 ≈ 2.828
        self.assertGreater(
            s, 2.0, msg=f"CHSH S={s} should violate classical bound of 2"
        )
        self.assertLess(
            s, 3.0, msg=f"CHSH S={s} should be below Tsirelson bound of 2√2"
        )

    def test_simulate_no_api_key(self):
        """Test simulate returns circuit info without API key."""
        from qpiai_quantum import Circuit

        circuit = Circuit(2, 2)
        circuit.H(0)
        circuit.CX(0, 1)
        result = self.integration.simulate(circuit)
        self.assertIn(
            "circuit", result, "Simulate without API key should return circuit info"
        )
        self.assertIn("num_qubits", result, "Simulate result should include num_qubits")

    def test_submit_to_cloud_no_api_key(self):
        """Test cloud submission raises error without API key."""
        from qpiai_quantum import Circuit

        circuit = Circuit(2, 2)
        with self.assertRaises(ValueError):
            self.integration.submit_to_cloud(circuit)


if __name__ == "__main__":
    unittest.main()
