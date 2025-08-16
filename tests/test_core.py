"""Tests for core components of QKDpy."""

import unittest

import numpy as np

from qkdpy.core import (
    CNOT,
    CZ,
    SWAP,
    GateUtils,
    Hadamard,
    Measurement,
    PauliX,
    PauliY,
    PauliZ,
    QuantumChannel,
    Qubit,
    Rx,
    Ry,
    Rz,
    S,
    T,
)


class TestQubit(unittest.TestCase):
    """Test cases for the Qubit class."""

    def test_qubit_initialization(self):
        """Test qubit initialization with different states."""
        # Test |0> state
        q0 = Qubit.zero()
        self.assertAlmostEqual(q0.probabilities[0], 1.0)
        self.assertAlmostEqual(q0.probabilities[1], 0.0)

        # Test |1> state
        q1 = Qubit.one()
        self.assertAlmostEqual(q1.probabilities[0], 0.0)
        self.assertAlmostEqual(q1.probabilities[1], 1.0)

        # Test |+> state
        qp = Qubit.plus()
        self.assertAlmostEqual(qp.probabilities[0], 0.5)
        self.assertAlmostEqual(qp.probabilities[1], 0.5)

        # Test |-> state
        qm = Qubit.minus()
        self.assertAlmostEqual(qm.probabilities[0], 0.5)
        self.assertAlmostEqual(qm.probabilities[1], 0.5)

    def test_qubit_gates(self):
        """Test applying quantum gates to qubits."""
        # Test Pauli-X gate
        q = Qubit.zero()
        q.apply_gate(PauliX().matrix)
        self.assertAlmostEqual(q.probabilities[0], 0.0)
        self.assertAlmostEqual(q.probabilities[1], 1.0)

        # Test Hadamard gate
        q = Qubit.zero()
        q.apply_gate(Hadamard().matrix)
        self.assertAlmostEqual(q.probabilities[0], 0.5)
        self.assertAlmostEqual(q.probabilities[1], 0.5)

        # Test Pauli-Z gate
        q = Qubit.plus()
        q.apply_gate(PauliZ().matrix)
        self.assertAlmostEqual(q.probabilities[0], 0.5)
        self.assertAlmostEqual(q.probabilities[1], 0.5)

    def test_qubit_measurement(self):
        """Test measuring qubits in different bases."""
        # Test computational basis measurement
        q = Qubit.zero()
        result = q.measure("computational")
        self.assertEqual(result, 0)
        q.collapse_state(result, "computational")

        q = Qubit.one()
        result = q.measure("computational")
        self.assertEqual(result, 1)
        q.collapse_state(result, "computational")

        # Test Hadamard basis measurement
        q = Qubit.plus()
        result = q.measure("hadamard")
        self.assertEqual(result, 0)
        q.collapse_state(result, "hadamard")

        q = Qubit.minus()
        result = q.measure("hadamard")
        self.assertEqual(result, 1)
        q.collapse_state(result, "hadamard")

    def test_qubit_bloch_vector(self):
        """Test Bloch vector calculation."""
        # Test |0> state
        q = Qubit.zero()
        x, y, z = q.bloch_vector()
        self.assertAlmostEqual(x, 0.0)
        self.assertAlmostEqual(y, 0.0)
        self.assertAlmostEqual(z, 1.0)

        # Test |1> state
        q = Qubit.one()
        x, y, z = q.bloch_vector()
        self.assertAlmostEqual(x, 0.0)
        self.assertAlmostEqual(y, 0.0)
        self.assertAlmostEqual(z, -1.0)

        # Test |+> state
        q = Qubit.plus()
        x, y, z = q.bloch_vector()
        self.assertAlmostEqual(x, 1.0)
        self.assertAlmostEqual(y, 0.0)
        self.assertAlmostEqual(z, 0.0)

        # Test |-> state
        q = Qubit.minus()
        x, y, z = q.bloch_vector()
        self.assertAlmostEqual(x, -1.0)
        self.assertAlmostEqual(y, 0.0)
        self.assertAlmostEqual(z, 0.0)


class TestGateClasses(unittest.TestCase):
    """Test cases for the individual QuantumGate classes."""

    def test_pauli_gates(self):
        """Test Pauli gates."""
        # Test Pauli-X gate
        x_gate = PauliX().matrix
        self.assertTrue(GateUtils.is_unitary(x_gate))

        # Test Pauli-Y gate
        y_gate = PauliY().matrix
        self.assertTrue(GateUtils.is_unitary(y_gate))

        # Test Pauli-Z gate
        z_gate = PauliZ().matrix
        self.assertTrue(GateUtils.is_unitary(z_gate))

    def test_clifford_gates(self):
        """Test Clifford gates."""
        # Test Hadamard gate
        h_gate = Hadamard().matrix
        self.assertTrue(GateUtils.is_unitary(h_gate))

        # Test Phase gate
        s_gate = S().matrix
        self.assertTrue(GateUtils.is_unitary(s_gate))

        # Test π/8 gate
        t_gate = T().matrix
        self.assertTrue(GateUtils.is_unitary(t_gate))

    def test_rotation_gates(self):
        """Test rotation gates."""
        # Test X rotation
        rx_gate = Rx(np.pi / 4).matrix
        self.assertTrue(GateUtils.is_unitary(rx_gate))

        # Test Y rotation
        ry_gate = Ry(np.pi / 4).matrix
        self.assertTrue(GateUtils.is_unitary(ry_gate))

        # Test Z rotation
        rz_gate = Rz(np.pi / 4).matrix
        self.assertTrue(GateUtils.is_unitary(rz_gate))

    def test_two_qubit_gates(self):
        """Test two-qubit gates."""
        # Test CNOT gate
        cnot_gate = CNOT().matrix
        self.assertTrue(GateUtils.is_unitary(cnot_gate))

        # Test CZ gate
        cz_gate = CZ().matrix
        self.assertTrue(GateUtils.is_unitary(cz_gate))

        # Test SWAP gate
        swap_gate = SWAP().matrix
        self.assertTrue(GateUtils.is_unitary(swap_gate))

    def test_gate_composition(self):
        """Test gate composition."""
        # Test sequence composition
        h_gate = Hadamard().matrix
        x_gate = PauliX().matrix
        sequence = GateUtils.sequence(h_gate, x_gate)
        self.assertTrue(GateUtils.is_unitary(sequence))

        # Test tensor product
        tensor = GateUtils.tensor_product(h_gate, x_gate)
        self.assertEqual(tensor.shape, (4, 4))
        self.assertTrue(GateUtils.is_unitary(tensor))


class TestQuantumChannel(unittest.TestCase):
    """Test cases for the QuantumChannel class."""

    def test_channel_transmission(self):
        """Test qubit transmission through the channel."""
        # Test lossless channel
        channel = QuantumChannel(loss=0.0)
        q = Qubit.zero()
        received = channel.transmit(q)
        self.assertIsNotNone(received)
        self.assertEqual(received, q)

        # Test channel with loss
        channel = QuantumChannel(loss=1.0)
        q = Qubit.zero()
        received = channel.transmit(q)
        self.assertIsNone(received)

    def test_channel_noise(self):
        """Test noise models in the channel."""
        # Test depolarizing noise
        channel = QuantumChannel(loss=0.0, noise_model="depolarizing", noise_level=0.5)
        q = Qubit.zero()
        received = channel.transmit(q)
        self.assertIsNotNone(received)

        # Test bit flip noise
        channel = QuantumChannel(loss=0.0, noise_model="bit_flip", noise_level=0.5)
        q = Qubit.zero()
        received = channel.transmit(q)
        self.assertIsNotNone(received)

        # Test phase flip noise
        channel = QuantumChannel(loss=0.0, noise_model="phase_flip", noise_level=0.5)
        q = Qubit.zero()
        received = channel.transmit(q)
        self.assertIsNotNone(received)

        # Test amplitude damping noise
        channel = QuantumChannel(
            loss=0.0, noise_model="amplitude_damping", noise_level=0.5
        )
        q = Qubit.one()
        received = channel.transmit(q)
        self.assertIsNotNone(received)

    def test_eavesdropping(self):
        """Test eavesdropping attacks."""
        # Test intercept-resend attack
        channel = QuantumChannel(loss=0.0)
        channel.set_eavesdropper(QuantumChannel.intercept_resend_attack)

        q = Qubit.zero()
        received, detected = channel.intercept_resend_attack(q)
        self.assertIsNotNone(received)

        # Test entanglement attack
        channel = QuantumChannel(loss=0.0)
        channel.set_eavesdropper(QuantumChannel.entanglement_attack)

        q = Qubit.zero()
        received, detected = channel.entanglement_attack(q)
        self.assertIsNotNone(received)

    def test_channel_statistics(self):
        """Test channel statistics."""
        channel = QuantumChannel(loss=0.5, noise_model="depolarizing", noise_level=0.1)

        # Transmit a batch of qubits
        qubits = [Qubit.zero() for _ in range(100)]
        channel.transmit_batch(qubits)

        # Get statistics
        stats = channel.get_statistics()
        self.assertEqual(stats["transmitted"], 100)
        self.assertGreater(stats["lost"], 0)
        self.assertGreater(stats["received"], 0)
        self.assertGreaterEqual(stats["error_rate"], 0)


class TestMeasurement(unittest.TestCase):
    """Test cases for the Measurement class."""

    def test_measurement_in_basis(self):
        """Test measurement in different bases."""
        # Test computational basis
        q = Qubit.zero()
        result = Measurement.measure_in_basis(q, "computational")
        self.assertEqual(result, 0)
        q.collapse_state(result, "computational")

        # Test Hadamard basis
        q = Qubit.plus()
        result = Measurement.measure_in_basis(q, "hadamard")
        self.assertEqual(result, 0)
        q.collapse_state(result, "hadamard")

        # Test circular basis
        q = Qubit(1 / np.sqrt(2), 1j / np.sqrt(2))
        result = Measurement.measure_in_basis(q, "circular")
        self.assertEqual(result, 0)
        q.collapse_state(result, "circular")

    def test_measurement_in_random_basis(self):
        """Test measurement in random bases."""
        q = Qubit.zero()
        result, basis = Measurement.measure_in_random_basis(q)
        self.assertIn(result, [0, 1])
        self.assertIn(basis, ["computational", "hadamard"])
        q.collapse_state(result, basis)

    def test_state_fidelity(self):
        """Test state fidelity calculation."""
        q1 = Qubit.zero()
        q2 = Qubit.zero()
        fidelity = Measurement.measure_state_fidelity(q1, q2.state)
        self.assertAlmostEqual(fidelity, 1.0)

        q1 = Qubit.zero()
        q2 = Qubit.one()
        fidelity = Measurement.measure_state_fidelity(q1, q2.state)
        self.assertAlmostEqual(fidelity, 0.0)

    def test_bloch_coordinates(self):
        """Test Bloch coordinate measurement."""
        # Test |0> state
        q = Qubit.zero()
        x, y, z = Measurement.measure_bloch_coordinates(q)
        self.assertAlmostEqual(x, 0.0)
        self.assertAlmostEqual(y, 0.0)
        self.assertAlmostEqual(z, 1.0)

        # Test |1> state
        q = Qubit.one()
        x, y, z = Measurement.measure_bloch_coordinates(q)
        self.assertAlmostEqual(x, 0.0)
        self.assertAlmostEqual(y, 0.0)
        self.assertAlmostEqual(z, -1.0)

    def test_purity(self):
        """Test purity measurement."""
        # Test pure state
        q = Qubit.zero()
        purity = Measurement.measure_purity(q)
        self.assertAlmostEqual(purity, 1.0)

        # Test mixed state (by applying a random gate)
        q = Qubit.zero()
        q.apply_gate(GateUtils.random_unitary())
        purity = Measurement.measure_purity(q)
        self.assertAlmostEqual(purity, 1.0)

    def test_von_neumann_entropy(self):
        """Test von Neumann entropy measurement."""
        # Test pure state
        q = Qubit.zero()
        entropy = Measurement.measure_von_neumann_entropy(q)
        self.assertAlmostEqual(entropy, 0.0)

        # Test mixed state (by applying a random gate)
        q = Qubit.zero()
        q.apply_gate(GateUtils.random_unitary())
        entropy = Measurement.measure_von_neumann_entropy(q)
        self.assertAlmostEqual(entropy, 0.0)


if __name__ == "__main__":
    unittest.main()
