"""Tests for extended core components of QKDpy."""

import unittest

import numpy as np

from qkdpy.core import ExtendedQuantumChannel, MultiQubitState, Qubit


class TestMultiQubitState(unittest.TestCase):
    """Test cases for the MultiQubitState class."""

    def test_multiqubit_initialization(self):
        """Test multi-qubit state initialization."""
        # Test with valid state vectors
        state1 = np.array([1.0, 0.0])  # 1 qubit
        mqs1 = MultiQubitState(state1)
        self.assertEqual(mqs1.num_qubits, 1)

        state2 = np.array([1.0, 0.0, 0.0, 0.0])  # 2 qubits
        mqs2 = MultiQubitState(state2)
        self.assertEqual(mqs2.num_qubits, 2)

        # Test normalization
        state3 = np.array([2.0, 0.0, 0.0, 0.0])  # Should be normalized
        mqs3 = MultiQubitState(state3)
        self.assertAlmostEqual(np.linalg.norm(mqs3.state), 1.0)

    def test_multiqubit_from_qubits(self):
        """Test creating multi-qubit state from individual qubits."""
        q0 = Qubit.zero()
        q1 = Qubit.one()

        # Test with two qubits
        mqs = MultiQubitState.from_qubits([q0, q1])
        self.assertEqual(mqs.num_qubits, 2)
        expected_state = np.kron(q0.state, q1.state)
        np.testing.assert_array_almost_equal(mqs.state, expected_state)

    def test_multiqubit_special_states(self):
        """Test special multi-qubit states."""
        # Test |00...0> state
        mqs_zeros = MultiQubitState.zeros(3)
        self.assertEqual(mqs_zeros.num_qubits, 3)
        self.assertAlmostEqual(mqs_zeros.state[0], 1.0)
        self.assertAlmostEqual(np.sum(np.abs(mqs_zeros.state[1:]) ** 2), 0.0)

        # Test GHZ state
        mqs_ghz = MultiQubitState.ghz(3)
        self.assertEqual(mqs_ghz.num_qubits, 3)
        self.assertAlmostEqual(mqs_ghz.state[0], 1 / np.sqrt(2))
        self.assertAlmostEqual(mqs_ghz.state[-1], 1 / np.sqrt(2))

    def test_multiqubit_probabilities(self):
        """Test probability calculations."""
        # Test with a simple 2-qubit state
        state = np.array([0.5, 0.5, 0.5, 0.5])
        mqs = MultiQubitState(state)

        probs = mqs.probabilities
        self.assertEqual(len(probs), 4)
        for prob in probs:
            self.assertAlmostEqual(prob, 0.25)

    def test_multiqubit_fidelity(self):
        """Test fidelity calculation."""
        # Test identical states
        state1 = np.array([1.0, 0.0, 0.0, 0.0])
        mqs1 = MultiQubitState(state1)
        mqs2 = MultiQubitState(state1)
        self.assertAlmostEqual(mqs1.fidelity(mqs2), 1.0)

        # Test orthogonal states
        state2 = np.array([0.0, 0.0, 0.0, 1.0])
        mqs3 = MultiQubitState(state2)
        self.assertAlmostEqual(mqs1.fidelity(mqs3), 0.0)


class TestExtendedQuantumChannel(unittest.TestCase):
    """Test cases for the ExtendedQuantumChannel class."""

    def test_extended_channel_initialization(self):
        """Test extended quantum channel initialization."""
        # Test with default parameters
        channel = ExtendedQuantumChannel()
        self.assertEqual(channel.loss, 0.0)
        self.assertEqual(channel.noise_model, "depolarizing")
        self.assertEqual(channel.noise_level, 0.0)

        # Test with custom parameters
        channel = ExtendedQuantumChannel(
            loss=0.1, noise_model="phase_damping", noise_level=0.05
        )
        self.assertEqual(channel.loss, 0.1)
        self.assertEqual(channel.noise_model, "phase_damping")
        self.assertEqual(channel.noise_level, 0.05)

    def test_extended_channel_phase_damping(self):
        """Test phase damping noise model."""
        channel = ExtendedQuantumChannel(
            loss=0.0, noise_model="phase_damping", noise_level=0.5
        )

        qubit = Qubit.plus()
        received = channel.transmit(qubit)
        self.assertIsNotNone(received)

    def test_extended_channel_generalized_amplitude_damping(self):
        """Test generalized amplitude damping noise model."""
        channel = ExtendedQuantumChannel(
            loss=0.0, noise_model="generalized_amplitude_damping", noise_level=0.5
        )

        qubit = Qubit.one()
        received = channel.transmit(qubit)
        self.assertIsNotNone(received)

    def test_extended_channel_statistics(self):
        """Test extended channel statistics."""
        channel = ExtendedQuantumChannel(loss=0.5, noise_level=0.1)

        # Transmit a batch of qubits
        qubits = [Qubit.zero() for _ in range(100)]
        for qubit in qubits:
            channel.transmit(qubit)

        # Get statistics
        stats = channel.get_statistics()
        self.assertEqual(stats["transmitted"], 100)
        self.assertGreater(stats["lost"], 0)
        self.assertGreater(stats["received"], 0)


if __name__ == "__main__":
    unittest.main()
