"""Quantum circuit abstraction for composing quantum operations.

A Circuit represents a sequence of quantum gates and measurements applied to
a register of qubits. It provides a high-level interface for building quantum
programs, similar to Qiskit's QuantumCircuit or Cirq's Circuit.

Example:
    >>> from qkdpy.core import Circuit, Qubit
    >>> qc = Circuit(2)
    >>> qc.h(0)
    >>> qc.cx(0, 1)
    >>> qc.measure_all()
    >>> state = qc.simulate()
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from .density_matrix import DensityMatrix
from .gates import CNOT, CZ, SWAP, Hadamard, PauliX, PauliY, PauliZ, Rx, Ry, Rz, S, T
from .qubit import Qubit

if TYPE_CHECKING:
    from collections.abc import Sequence


class GateOperation:
    """A gate applied to specific qubits in a circuit."""

    def __init__(self, gate: np.ndarray, qubits: list[int]) -> None:
        self.gate = gate
        self.qubits = qubits


class MeasurementOperation:
    """A measurement operation on specific qubits."""

    def __init__(self, qubits: list[int] | None = None) -> None:
        self.qubits = qubits  # None means "all qubits"


class Circuit:
    """Quantum circuit for composing and simulating quantum operations.

    Attributes:
        num_qubits: Number of qubits in the circuit.
        operations: List of gate and measurement operations.
    """

    def __init__(self, num_qubits: int) -> None:
        """Initialize a quantum circuit.

        Args:
            num_qubits: Number of qubits in the circuit.
        """
        if num_qubits <= 0:
            raise ValueError("Number of qubits must be positive")

        self.num_qubits = num_qubits
        self.operations: list[GateOperation | MeasurementOperation] = []
        self._measure_all = False

    # --- Single-qubit gates ---

    def h(self, qubit: int) -> Circuit:
        """Apply Hadamard gate to a qubit.

        Args:
            qubit: Target qubit index.

        Returns:
            Self for method chaining.
        """
        self._validate_qubit(qubit)
        self.operations.append(GateOperation(Hadamard().matrix, [qubit]))
        return self

    def x(self, qubit: int) -> Circuit:
        """Apply Pauli-X (NOT) gate to a qubit."""
        self._validate_qubit(qubit)
        self.operations.append(GateOperation(PauliX().matrix, [qubit]))
        return self

    def y(self, qubit: int) -> Circuit:
        """Apply Pauli-Y gate to a qubit."""
        self._validate_qubit(qubit)
        self.operations.append(GateOperation(PauliY().matrix, [qubit]))
        return self

    def z(self, qubit: int) -> Circuit:
        """Apply Pauli-Z gate to a qubit."""
        self._validate_qubit(qubit)
        self.operations.append(GateOperation(PauliZ().matrix, [qubit]))
        return self

    def s(self, qubit: int) -> Circuit:
        """Apply S (phase) gate to a qubit."""
        self._validate_qubit(qubit)
        self.operations.append(GateOperation(S().matrix, [qubit]))
        return self

    def t(self, qubit: int) -> Circuit:
        """Apply T (π/8) gate to a qubit."""
        self._validate_qubit(qubit)
        self.operations.append(GateOperation(T().matrix, [qubit]))
        return self

    def rx(self, qubit: int, theta: float) -> Circuit:
        """Apply rotation around X-axis by angle theta."""
        self._validate_qubit(qubit)
        self.operations.append(GateOperation(Rx(theta).matrix, [qubit]))
        return self

    def ry(self, qubit: int, theta: float) -> Circuit:
        """Apply rotation around Y-axis by angle theta."""
        self._validate_qubit(qubit)
        self.operations.append(GateOperation(Ry(theta).matrix, [qubit]))
        return self

    def rz(self, qubit: int, theta: float) -> Circuit:
        """Apply rotation around Z-axis by angle theta."""
        self._validate_qubit(qubit)
        self.operations.append(GateOperation(Rz(theta).matrix, [qubit]))
        return self

    # --- Two-qubit gates ---

    def cx(self, control: int, target: int) -> Circuit:
        """Apply CNOT (controlled-X) gate.

        Args:
            control: Control qubit index.
            target: Target qubit index.

        Returns:
            Self for method chaining.
        """
        self._validate_qubit(control)
        self._validate_qubit(target)
        if control == target:
            raise ValueError("Control and target must be different qubits")
        self.operations.append(GateOperation(CNOT().matrix, [control, target]))
        return self

    def cz(self, control: int, target: int) -> Circuit:
        """Apply controlled-Z gate."""
        self._validate_qubit(control)
        self._validate_qubit(target)
        if control == target:
            raise ValueError("Control and target must be different qubits")
        self.operations.append(GateOperation(CZ().matrix, [control, target]))
        return self

    def swap(self, qubit1: int, qubit2: int) -> Circuit:
        """Apply SWAP gate."""
        self._validate_qubit(qubit1)
        self._validate_qubit(qubit2)
        if qubit1 == qubit2:
            raise ValueError("Qubits must be different")
        self.operations.append(GateOperation(SWAP().matrix, [qubit1, qubit2]))
        return self

    # --- Custom gates ---

    def custom_gate(self, gate: np.ndarray, qubits: list[int]) -> Circuit:
        """Apply a custom unitary gate.

        Args:
            gate: Unitary matrix (2^k × 2^k for k qubits).
            qubits: List of qubit indices the gate acts on.

        Returns:
            Self for method chaining.
        """
        expected_dim = 2 ** len(qubits)
        if gate.shape != (expected_dim, expected_dim):
            raise ValueError(
                f"Gate dimension {gate.shape} doesn't match "
                f"{len(qubits)} qubits (expected {expected_dim}×{expected_dim})"
            )
        for q in qubits:
            self._validate_qubit(q)
        self.operations.append(GateOperation(gate, qubits))
        return self

    # --- Measurements ---

    def measure(self, qubits: list[int] | None = None) -> Circuit:
        """Add measurement operation.

        Args:
            qubits: Qubits to measure. None means all qubits.

        Returns:
            Self for method chaining.
        """
        if qubits is not None:
            for q in qubits:
                self._validate_qubit(q)
        self.operations.append(MeasurementOperation(qubits))
        return self

    def measure_all(self) -> Circuit:
        """Mark that all qubits should be measured at the end."""
        self._measure_all = True
        return self

    # --- Circuit composition ---

    def compose(self, other: Circuit, qubits: list[int] | None = None) -> Circuit:
        """Compose this circuit with another circuit.

        Args:
            other: Circuit to append.
            qubits: Qubit mapping. If None, uses identity mapping.

        Returns:
            New circuit with both circuits applied sequentially.
        """
        if other.num_qubits > self.num_qubits:
            raise ValueError("Cannot compose: other circuit has more qubits")

        if qubits is None:
            qubits = list(range(other.num_qubits))

        result = Circuit(self.num_qubits)
        result.operations = self.operations.copy()

        for op in other.operations:
            if isinstance(op, GateOperation):
                mapped_qubits = [qubits[q] for q in op.qubits]
                result.operations.append(GateOperation(op.gate, mapped_qubits))
            else:
                result.operations.append(op)

        return result

    def __add__(self, other: Circuit) -> Circuit:
        """Operator + for circuit composition."""
        return self.compose(other)

    # --- Simulation ---

    def simulate(
        self,
        initial_state: Qubit | Sequence[Qubit] | None = None,
        use_density_matrix: bool = False,
    ) -> DensityMatrix | np.ndarray:
        """Simulate the circuit and return the final state.

        Args:
            initial_state: Initial state. If None, uses |0...0⟩.
            use_density_matrix: If True, return DensityMatrix; otherwise
                return statevector as numpy array.

        Returns:
            Final quantum state (statevector or density matrix).
        """
        # Initialize state
        if initial_state is None:
            state = np.zeros(2**self.num_qubits, dtype=complex)
            state[0] = 1.0
        elif isinstance(initial_state, Qubit):
            if self.num_qubits != 1:
                raise ValueError("Single qubit state provided but circuit has multiple qubits")
            state = initial_state.state
        else:
            # Tensor product of multiple qubits
            state = initial_state[0].state
            for qubit in initial_state[1:]:
                state = np.kron(state, qubit.state)

        # Apply operations
        for op in self.operations:
            if isinstance(op, GateOperation):
                state = self._apply_gate(state, op.gate, op.qubits)
            # Skip measurements for statevector simulation

        if use_density_matrix:
            return DensityMatrix.from_pure(state)
        return state

    def _apply_gate(
        self, state: np.ndarray, gate: np.ndarray, qubits: list[int]
    ) -> np.ndarray:
        """Apply a gate to specific qubits in the statevector.

        Args:
            state: Current statevector.
            gate: Gate matrix.
            qubits: Qubit indices the gate acts on.

        Returns:
            Updated statevector.
        """
        if len(qubits) == 1:
            # Single-qubit gate: use tensor product
            qubit = qubits[0]
            ops = [np.eye(2, dtype=complex)] * self.num_qubits
            ops[qubit] = gate
            full_gate = ops[0]
            for op in ops[1:]:
                full_gate = np.kron(full_gate, op)
            return full_gate @ state
        else:
            # Multi-qubit gate: need to construct the full operator
            # This is more complex for non-adjacent qubits
            dim = 2**self.num_qubits
            full_gate = np.zeros((dim, dim), dtype=complex)

            # Build the gate by iterating over all basis states
            for i in range(dim):
                # Extract the bits for the target qubits
                target_bits = 0
                for idx, q in enumerate(qubits):
                    bit = (i >> (self.num_qubits - 1 - q)) & 1
                    target_bits |= bit << (len(qubits) - 1 - idx)

                # Apply the gate to get new target bits
                for new_target_bits in range(2 ** len(qubits)):
                    amplitude = gate[new_target_bits, target_bits]
                    if abs(amplitude) < 1e-15:
                        continue

                    # Construct the new full state index
                    j = i
                    for idx, q in enumerate(qubits):
                        # Clear the old bit
                        j &= ~(1 << (self.num_qubits - 1 - q))
                        # Set the new bit
                        new_bit = (new_target_bits >> (len(qubits) - 1 - idx)) & 1
                        j |= new_bit << (self.num_qubits - 1 - q)

                    full_gate[j, i] += amplitude

            return full_gate @ state

    # --- Export ---

    def to_qasm(self) -> str:
        """Export circuit to OpenQASM 2.0 format.

        Returns:
            OpenQASM 2.0 string representation.
        """
        lines = [
            "OPENQASM 2.0;",
            'include "qelib1.inc";',
            f"qreg q[{self.num_qubits}];",
            f"creg c[{self.num_qubits}];",
        ]

        # Standard gates for comparison
        h_gate = Hadamard().matrix
        x_gate = PauliX().matrix
        y_gate = PauliY().matrix
        z_gate = PauliZ().matrix
        s_gate = S().matrix
        t_gate = T().matrix
        cnot_gate = CNOT().matrix
        cz_gate = CZ().matrix

        gate_names = {
            "h": h_gate,
            "x": x_gate,
            "y": y_gate,
            "z": z_gate,
            "s": s_gate,
            "t": t_gate,
        }

        for op in self.operations:
            if isinstance(op, GateOperation):
                if len(op.qubits) == 1:
                    q = op.qubits[0]
                    # Check if it's a standard gate using array comparison
                    matched = False
                    for name, std_gate in gate_names.items():
                        if np.array_equal(op.gate, std_gate):
                            lines.append(f"{name} q[{q}];")
                            matched = True
                            break
                    if not matched:
                        # Custom single-qubit gate - note it's custom
                        lines.append(f"// custom gate on q[{q}]")
                elif len(op.qubits) == 2:
                    ctrl, tgt = op.qubits
                    if np.array_equal(op.gate, cnot_gate):
                        lines.append(f"cx q[{ctrl}],q[{tgt}];")
                    elif np.array_equal(op.gate, cz_gate):
                        lines.append(f"cz q[{ctrl}],q[{tgt}];")
                    else:
                        lines.append(f"// custom 2-qubit gate on q[{ctrl}],q[{tgt}]")
            elif isinstance(op, MeasurementOperation):
                qubits = op.qubits if op.qubits else list(range(self.num_qubits))
                for q in qubits:
                    lines.append(f"measure q[{q}] -> c[{q}];")

        return "\n".join(lines)

    # --- Utility ---

    def depth(self) -> int:
        """Calculate circuit depth (longest path through the circuit).

        Returns:
            Number of time steps in the circuit.
        """
        if not self.operations:
            return 0

        # Track when each qubit is last used
        qubit_time = [0] * self.num_qubits

        for op in self.operations:
            if isinstance(op, GateOperation):
                # Gate acts on multiple qubits - find max time
                max_time = max(qubit_time[q] for q in op.qubits)
                # All involved qubits move to max_time + 1
                for q in op.qubits:
                    qubit_time[q] = max_time + 1
            else:
                # Measurement - acts on qubits
                qubits = op.qubits if op.qubits else list(range(self.num_qubits))
                max_time = max(qubit_time[q] for q in qubits)
                for q in qubits:
                    qubit_time[q] = max_time + 1

        return max(qubit_time)

    def count_ops(self) -> dict[str, int]:
        """Count the number of each type of gate.

        Returns:
            Dictionary mapping gate names to counts.
        """
        counts: dict[str, int] = {}
        for op in self.operations:
            if isinstance(op, GateOperation):
                # Identify gate type by checking against known gates
                if len(op.qubits) == 1:
                    if np.array_equal(op.gate, Hadamard().matrix):
                        name = "h"
                    elif np.array_equal(op.gate, PauliX().matrix):
                        name = "x"
                    elif np.array_equal(op.gate, PauliY().matrix):
                        name = "y"
                    elif np.array_equal(op.gate, PauliZ().matrix):
                        name = "z"
                    elif np.array_equal(op.gate, S().matrix):
                        name = "s"
                    elif np.array_equal(op.gate, T().matrix):
                        name = "t"
                    else:
                        name = "custom_1q"
                elif len(op.qubits) == 2:
                    if np.array_equal(op.gate, CNOT().matrix):
                        name = "cx"
                    elif np.array_equal(op.gate, CZ().matrix):
                        name = "cz"
                    elif np.array_equal(op.gate, SWAP().matrix):
                        name = "swap"
                    else:
                        name = "custom_2q"
                else:
                    name = f"custom_{len(op.qubits)}q"

                counts[name] = counts.get(name, 0) + 1
            else:
                counts["measure"] = counts.get("measure", 0) + 1

        return counts

    def _validate_qubit(self, qubit: int) -> None:
        """Validate qubit index."""
        if not 0 <= qubit < self.num_qubits:
            raise ValueError(
                f"Qubit index {qubit} out of range [0, {self.num_qubits})"
            )

    def __repr__(self) -> str:
        return f"Circuit(num_qubits={self.num_qubits}, depth={self.depth()})"
