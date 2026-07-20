"""Tests for quantum circuit module."""

import numpy as np
import pytest

from qkdpy.core import Circuit, Qubit


class TestCircuit:
    """Test Circuit class."""

    def test_init(self):
        """Test circuit initialization."""
        qc = Circuit(3)
        assert qc.num_qubits == 3
        assert len(qc.operations) == 0

    def test_init_invalid(self):
        """Test circuit initialization with invalid qubit count."""
        with pytest.raises(ValueError, match="positive"):
            Circuit(0)

    def test_single_qubit_gates(self):
        """Test single-qubit gate methods."""
        qc = Circuit(1)
        qc.h(0).x(0).y(0).z(0).s(0).t(0)
        assert len(qc.operations) == 6

    def test_rotation_gates(self):
        """Test rotation gates."""
        qc = Circuit(1)
        qc.rx(0, np.pi / 4).ry(0, np.pi / 2).rz(0, np.pi)
        assert len(qc.operations) == 3

    def test_two_qubit_gates(self):
        """Test two-qubit gates."""
        qc = Circuit(2)
        qc.cx(0, 1).cz(0, 1).swap(0, 1)
        assert len(qc.operations) == 3

    def test_invalid_qubit_index(self):
        """Test invalid qubit index raises error."""
        qc = Circuit(2)
        with pytest.raises(ValueError, match="out of range"):
            qc.h(2)

    def test_cx_same_qubit(self):
        """Test CNOT with same control and target raises error."""
        qc = Circuit(2)
        with pytest.raises(ValueError, match="different qubits"):
            qc.cx(0, 0)

    def test_swap_same_qubit(self):
        """Test SWAP with same qubits raises error."""
        qc = Circuit(2)
        with pytest.raises(ValueError, match="different"):
            qc.swap(0, 0)

    def test_custom_gate(self):
        """Test custom gate application."""
        qc = Circuit(2)
        # Custom 2-qubit gate (CNOT)
        cnot = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]])
        qc.custom_gate(cnot, [0, 1])
        assert len(qc.operations) == 1

    def test_custom_gate_invalid_dim(self):
        """Test custom gate with wrong dimension."""
        qc = Circuit(2)
        wrong_dim = np.eye(3)
        with pytest.raises(ValueError, match="dimension"):
            qc.custom_gate(wrong_dim, [0, 1])

    def test_measure(self):
        """Test measurement operation."""
        qc = Circuit(2)
        qc.h(0)
        qc.measure([0])
        assert len(qc.operations) == 2

    def test_measure_all(self):
        """Test measure_all flag."""
        qc = Circuit(2)
        qc.h(0).measure_all()
        assert qc._measure_all

    def test_compose(self):
        """Test circuit composition."""
        qc1 = Circuit(2)
        qc1.h(0)

        qc2 = Circuit(2)
        qc2.cx(0, 1)

        qc3 = qc1.compose(qc2)
        assert qc3.num_qubits == 2
        assert len(qc3.operations) == 2

    def test_compose_qubit_mapping(self):
        """Test circuit composition with qubit mapping."""
        qc1 = Circuit(3)
        qc1.h(0)

        qc2 = Circuit(2)
        qc2.cx(0, 1)

        qc3 = qc1.compose(qc2, qubits=[1, 2])
        assert qc3.num_qubits == 3
        # Should have h(0) and cx(1, 2)
        assert len(qc3.operations) == 2

    def test_compose_invalid(self):
        """Test composition with larger circuit raises error."""
        qc1 = Circuit(2)
        qc2 = Circuit(3)
        with pytest.raises(ValueError, match="more qubits"):
            qc1.compose(qc2)

    def test_add_operator(self):
        """Test + operator for composition."""
        qc1 = Circuit(2)
        qc1.h(0)

        qc2 = Circuit(2)
        qc2.cx(0, 1)

        qc3 = qc1 + qc2
        assert len(qc3.operations) == 2

    def test_simulate_bell_state(self):
        """Test simulating Bell state circuit."""
        qc = Circuit(2)
        qc.h(0)
        qc.cx(0, 1)

        state = qc.simulate()
        # Bell state |Φ+⟩ = (|00⟩ + |11⟩)/√2
        expected = np.array([1, 0, 0, 1]) / np.sqrt(2)
        assert np.allclose(state, expected)

    def test_simulate_ghz_state(self):
        """Test simulating GHZ state."""
        qc = Circuit(3)
        qc.h(0)
        qc.cx(0, 1)
        qc.cx(0, 2)

        state = qc.simulate()
        # GHZ state (|000⟩ + |111⟩)/√2
        expected = np.zeros(8, dtype=complex)
        expected[0] = 1 / np.sqrt(2)
        expected[7] = 1 / np.sqrt(2)
        assert np.allclose(state, expected)

    def test_simulate_with_initial_state(self):
        """Test simulation with custom initial state."""
        qc = Circuit(1)
        qc.x(0)  # Flip |0⟩ to |1⟩

        # Start with |0⟩
        state = qc.simulate(initial_state=Qubit.zero())
        # Should be |1⟩ after X gate
        assert np.allclose(state, [0, 1])

    def test_simulate_density_matrix(self):
        """Test simulation returning density matrix."""
        qc = Circuit(1)
        qc.h(0)

        rho = qc.simulate(use_density_matrix=True)
        # |+⟩⟨+| = [[0.5, 0.5], [0.5, 0.5]]
        expected = np.array([[0.5, 0.5], [0.5, 0.5]])
        assert np.allclose(rho.matrix, expected)

    def test_depth_empty(self):
        """Test depth of empty circuit."""
        qc = Circuit(2)
        assert qc.depth() == 0

    def test_depth_sequential(self):
        """Test depth of sequential gates."""
        qc = Circuit(1)
        qc.h(0).x(0).z(0)
        assert qc.depth() == 3

    def test_depth_parallel(self):
        """Test depth with parallel gates."""
        qc = Circuit(3)
        qc.h(0).h(1).h(2)
        # All H gates act on different qubits, so depth is 1
        assert qc.depth() == 1

    def test_depth_mixed(self):
        """Test depth with mixed parallel and sequential gates."""
        qc = Circuit(3)
        qc.h(0).h(1)  # Depth 1 (parallel)
        qc.cx(0, 1)  # Depth 2 (depends on both)
        qc.h(2)  # Depth 2 (parallel with cx)
        assert qc.depth() == 2

    def test_count_ops_empty(self):
        """Test counting ops in empty circuit."""
        qc = Circuit(2)
        counts = qc.count_ops()
        assert counts == {}

    def test_count_ops(self):
        """Test counting gate operations."""
        qc = Circuit(2)
        qc.h(0).h(1).cx(0, 1).measure([0])

        counts = qc.count_ops()
        assert counts["h"] == 2
        assert counts["cx"] == 1
        assert counts["measure"] == 1

    def test_to_qasm_basic(self):
        """Test OpenQASM export."""
        qc = Circuit(2)
        qc.h(0).cx(0, 1)
        qc.measure_all()

        qasm = qc.to_qasm()
        assert "OPENQASM 2.0" in qasm
        assert "qreg q[2]" in qasm
        assert "h q[0]" in qasm
        assert "cx q[0],q[1]" in qasm

    def test_method_chaining(self):
        """Test that gate methods return self for chaining."""
        qc = Circuit(2)
        result = qc.h(0).cx(0, 1).measure([0])
        assert result is qc
        assert len(qc.operations) == 3

    def test_repr(self):
        """Test string representation."""
        qc = Circuit(3)
        qc.h(0).cx(0, 1)
        s = repr(qc)
        assert "num_qubits=3" in s
        assert "depth=2" in s

    def test_x_gate_simulation(self):
        """Test X gate flips |0⟩ to |1⟩."""
        qc = Circuit(1)
        qc.x(0)
        state = qc.simulate()
        assert np.allclose(state, [0, 1])

    def test_hadamard_simulation(self):
        """Test Hadamard creates superposition."""
        qc = Circuit(1)
        qc.h(0)
        state = qc.simulate()
        expected = np.array([1, 1]) / np.sqrt(2)
        assert np.allclose(state, expected)

    def test_multi_qubit_gate_non_adjacent(self):
        """Test multi-qubit gate on non-adjacent qubits."""
        qc = Circuit(3)
        # CNOT with control=0, target=2 (non-adjacent)
        qc.cx(0, 2)

        # Simulate: should flip qubit 2 when qubit 0 is |1⟩
        # Start with |100⟩ (qubit 0 is |1⟩, qubits 1,2 are |0⟩)
        initial = [Qubit.one(), Qubit.zero(), Qubit.zero()]
        state = qc.simulate(initial_state=initial)

        # After CNOT(0,2): qubit 0 controls, qubit 2 flips if qubit 0 is |1⟩
        # |100⟩ → |101⟩ (qubit 2 flips from |0⟩ to |1⟩)
        # In our convention, qubit 0 is the most significant bit
        # |101⟩ in binary (qubits 0,1,2) = 1*4 + 0*2 + 1*1 = 5
        expected = np.zeros(8, dtype=complex)
        expected[5] = 1.0  # |101⟩
        assert np.allclose(state, expected)
