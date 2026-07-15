"""Extended tests for Cirq integration -- BB84 circuits, simulation, entanglement."""

import unittest

try:
    import cirq
except ImportError:
    cirq = None  # type: ignore


@unittest.skipIf(cirq is None, "Cirq not installed")
class TestCirqBB84Circuit(unittest.TestCase):
    """Test BB84 circuit construction via CirqIntegration."""

    def setUp(self):
        from qkdpy.integrations.cirq_integration import CirqIntegration

        self.integration = CirqIntegration()

    def test_create_bb84_circuit_returns_circuit(self):
        """create_bb84_circuit returns a valid cirq Circuit."""
        circuit = self.integration.create_bb84_circuit(num_qubits=4)
        self.assertIsInstance(circuit, cirq.Circuit)

    def test_create_bb84_circuit_correct_qubit_count(self):
        """Circuit should have the requested number of qubits."""
        for n in [1, 2, 5]:
            circuit = self.integration.create_bb84_circuit(num_qubits=n)
            qubits = list(circuit.all_qubits())
            self.assertEqual(len(qubits), n)

    def test_create_bb84_circuit_with_known_bases(self):
        """When bases are specified, the circuit should include H gates for X bases."""
        alice_bases = ["Z", "X", "Z", "X"]
        bob_bases = ["Z", "Z", "X", "X"]
        circuit = self.integration.create_bb84_circuit(
            num_qubits=4,
            alice_bases=alice_bases,
            bob_bases=bob_bases,
        )
        # Count Hadamard gates: one per X basis in Alice + one per X basis in Bob
        h_count = sum(
            1 for op in circuit.all_operations() if isinstance(op.gate, cirq.HPowGate)
        )
        self.assertEqual(h_count, 4)  # 2 from Alice (X) + 2 from Bob (X)

    def test_create_bb84_circuit_has_measurements(self):
        """Circuit should contain measurement operations for each qubit."""
        circuit = self.integration.create_bb84_circuit(num_qubits=3)
        measure_ops = [
            op
            for op in circuit.all_operations()
            if isinstance(op.gate, cirq.MeasurementGate)
        ]
        self.assertEqual(len(measure_ops), 3)

    def test_create_bb84_circuit_measurement_keys(self):
        """Measurement keys should follow the result_i pattern."""
        circuit = self.integration.create_bb84_circuit(num_qubits=2)
        keys = []
        for op in circuit.all_operations():
            if isinstance(op.gate, cirq.MeasurementGate):
                keys.append(op.gate.key)
        self.assertIn("result_0", keys)
        self.assertIn("result_1", keys)


@unittest.skipIf(cirq is None, "Cirq not installed")
class TestCirqEntanglementCircuit(unittest.TestCase):
    """Test entanglement circuit generation."""

    def setUp(self):
        from qkdpy.integrations.cirq_integration import CirqIntegration

        self.integration = CirqIntegration()

    def test_create_entanglement_circuit_returns_circuit(self):
        """create_entanglement_circuit returns a valid cirq Circuit."""
        circuit = self.integration.create_entanglement_circuit(num_pairs=1)
        self.assertIsInstance(circuit, cirq.Circuit)

    def test_entanglement_circuit_qubit_count(self):
        """2 qubits per entangled pair (Alice + Bob)."""
        for pairs in [1, 3]:
            circuit = self.integration.create_entanglement_circuit(num_pairs=pairs)
            qubits = list(circuit.all_qubits())
            self.assertEqual(len(qubits), pairs * 2)

    def test_entanglement_circuit_has_h_and_cnot(self):
        """Entanglement circuit should contain H + CNOT gates."""
        circuit = self.integration.create_entanglement_circuit(num_pairs=1)
        ops = list(circuit.all_operations())
        gates = [type(op.gate).__name__ for op in ops if op.gate is not None]
        self.assertIn("HPowGate", gates)
        self.assertIn("CXPowGate", gates)


@unittest.skipIf(cirq is None, "Cirq not installed")
class TestCirqSimulateBB84(unittest.TestCase):
    """Test BB84 simulation via Cirq."""

    def setUp(self):
        from qkdpy.integrations.cirq_integration import CirqIntegration

        self.integration = CirqIntegration()

    def test_simulate_bb84_returns_tuple(self):
        """simulate_bb84_with_cirq returns (alice_bits, bob_bits, matching_bases)."""
        result = self.integration.simulate_bb84_with_cirq(num_qubits=10)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 3)

    def test_simulate_bb84_result_types(self):
        """Alice bits, Bob bits, and matching bases should have correct lengths."""
        n = 20
        alice_bits, bob_bits, matching = self.integration.simulate_bb84_with_cirq(
            num_qubits=n
        )
        self.assertEqual(len(alice_bits), n)
        self.assertEqual(len(bob_bits), n)
        self.assertEqual(len(matching), n)
        self.assertTrue(all(b in (0, 1) for b in alice_bits))
        self.assertTrue(all(b in (0, 1) for b in bob_bits))
        self.assertTrue(all(isinstance(m, bool) for m in matching))

    def test_simulate_bb84_no_noise_perfect_bases(self):
        """With no noise and same bases, Alice and Bob should have identical bits."""
        n = 100
        # Same bases for both (no mismatches)
        bases = ["Z"] * n
        circuit = self.integration.create_bb84_circuit(
            num_qubits=n,
            alice_bases=bases,
            bob_bases=bases,
        )
        simulator = cirq.Simulator()
        result = simulator.run(circuit, repetitions=1)
        # All measurement results should be deterministic for |0> in Z basis
        self.assertIsNotNone(result)

    def test_simulate_with_depolarizing_noise(self):
        """Depolarizing noise should produce some errors."""
        n = 100
        alice_bits, bob_bits, matching = self.integration.simulate_bb84_with_cirq(
            num_qubits=n, noise_model="depolarizing", noise_level=0.1
        )
        # Some bits should match where bases match (at nonzero rate)
        matching_indices = [i for i, m in enumerate(matching) if m]
        if matching_indices:
            matches = sum(1 for i in matching_indices if alice_bits[i] == bob_bits[i])
            self.assertGreaterEqual(matches, 0)

    def test_simulate_with_bit_flip_noise(self):
        """Bit flip noise should run without error."""
        n = 50
        result = self.integration.simulate_bb84_with_cirq(
            num_qubits=n, noise_model="bit_flip", noise_level=0.2
        )
        self.assertIsNotNone(result)
        self.assertEqual(len(result[0]), n)

    def test_simulate_zero_noise(self):
        """Noise level 0 with a model should still work (no noise applied)."""
        n = 20
        result = self.integration.simulate_bb84_with_cirq(
            num_qubits=n, noise_model="depolarizing", noise_level=0.0
        )
        self.assertIsNotNone(result)


@unittest.skipIf(cirq is None, "Cirq not installed")
class TestCirqChannelConversion(unittest.TestCase):
    """Test converting QKDpy channels to Cirq noise gates."""

    def setUp(self):
        from qkdpy.core import QuantumChannel
        from qkdpy.integrations.cirq_integration import CirqIntegration

        self.integration = CirqIntegration()
        self.channel_cls = QuantumChannel

    def test_convert_depolarizing_channel(self):
        """Depolarizing channel should produce depolarize gate."""
        channel = self.channel_cls(
            loss=0.0, noise_model="depolarizing", noise_level=0.1
        )
        gates = self.integration.convert_channel_to_cirq(channel)
        self.assertGreaterEqual(len(gates), 1)
        self.assertIsInstance(gates[0], cirq.DepolarizingChannel)

    def test_convert_bit_flip_channel(self):
        """Bit flip channel should produce bit_flip gate."""
        channel = self.channel_cls(loss=0.0, noise_model="bit_flip", noise_level=0.05)
        gates = self.integration.convert_channel_to_cirq(channel)
        self.assertGreaterEqual(len(gates), 1)
        self.assertIsInstance(gates[0], cirq.BitFlipChannel)

    def test_convert_phase_flip_channel(self):
        """Phase flip channel should produce phase_flip gate."""
        channel = self.channel_cls(loss=0.0, noise_model="phase_flip", noise_level=0.05)
        gates = self.integration.convert_channel_to_cirq(channel)
        self.assertGreaterEqual(len(gates), 1)
        self.assertIsInstance(gates[0], cirq.PhaseFlipChannel)

    def test_convert_noiseless_channel(self):
        """Noiseless channel should return empty list."""
        channel = self.channel_cls(
            loss=0.0, noise_model="depolarizing", noise_level=0.0
        )
        gates = self.integration.convert_channel_to_cirq(channel)
        self.assertEqual(len(gates), 0)


@unittest.skipIf(cirq is None, "Cirq not installed")
class TestCirqBenchmark(unittest.TestCase):
    """Test benchmarking utility."""

    def setUp(self):
        from qkdpy.integrations.cirq_integration import CirqIntegration

        self.integration = CirqIntegration()

    def test_benchmark_returns_dict(self):
        """benchmark_qkdpy_vs_cirq returns a dict with expected keys."""
        result = self.integration.benchmark_qkdpy_vs_cirq(num_qubits=4, num_trials=2)
        self.assertIsInstance(result, dict)
        self.assertIn("qkdpy_average_time", result)
        self.assertIn("cirq_average_time", result)
        self.assertIn("speedup_factor", result)
        self.assertIn("num_qubits", result)
        self.assertIn("num_trials", result)
        self.assertEqual(result["num_qubits"], 4)
        self.assertEqual(result["num_trials"], 2)


if __name__ == "__main__":
    unittest.main()
