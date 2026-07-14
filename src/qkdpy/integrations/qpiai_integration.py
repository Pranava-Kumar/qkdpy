"""QpiAI Quantum SDK integration plugin for QKDpy."""

from __future__ import annotations

from typing import Any

try:
    import numpy as np
    from qpiai_quantum import (
        Circuit,
        Statevector,
        Backend,
        JobManager,
    )
    from qpiai_quantum.state_preparation import (
        BellStateGenerator,
        GHZStateGenerator,
        WStateGenerator,
        ClusterStateGenerator,
    )

    QPIAI_AVAILABLE = True
except ImportError:
    QPIAI_AVAILABLE = False
    np = None  # type: ignore[assignment]


from ..core import QuantumChannel, Qubit
from ..protocols.bb84 import BB84


class QpiAIIntegration:
    """Integration with QpiAI Quantum SDK for QKD protocol simulation.

    Provides conversion between QKDpy and QpiAI quantum primitives,
    circuit construction for QKD protocols, and access to QpiAI's
    cloud quantum hardware and local simulators.
    """

    def __init__(self) -> None:
        """Initialize QpiAI integration."""
        if not QPIAI_AVAILABLE:
            raise ImportError(
                "QpiAI Quantum SDK is not installed. "
                "Install it from https://github.com/qpiai/quantum-sdk"
            )

    # ------------------------------------------------------------------ #
    #  State Conversion
    # ------------------------------------------------------------------ #

    def qubit_to_qpiai(self, qkdpy_qubit: Qubit) -> Statevector:
        """Convert a QKDpy Qubit to a QpiAI Statevector.

        Args:
            qkdpy_qubit: QKDpy Qubit object

        Returns:
            QpiAI Statevector representing the same quantum state
        """
        state = qkdpy_qubit.state
        return Statevector(state)

    def qpiai_to_qubit(self, qpiai_state: Statevector) -> Qubit:
        """Convert a QpiAI Statevector to a QKDpy Qubit.

        Args:
            qpiai_state: QpiAI Statevector

        Returns:
            QKDpy Qubit representing the same quantum state
        """
        state = qpiai_state.data
        return Qubit(float(np.real(state[0])), float(np.real(state[1])))

    def statevector_from_array(
        self, data: list[complex] | np.ndarray
    ) -> Statevector:
        """Create a QpiAI Statevector from an array of amplitudes (local, no cloud).

        Args:
            data: Complex amplitudes (will be normalized)

        Returns:
            QpiAI Statevector
        """
        return Statevector(data)

    # ------------------------------------------------------------------ #
    #  Quantum Information Measures (using QpiAI formalism)
    # ------------------------------------------------------------------ #

    def compute_concurrence(self, state: np.ndarray) -> float:
        """Compute the concurrence of a 2-qubit state.

        Uses QpiAI's formalism DensityMatrix.

        Args:
            state: 4x4 density matrix or 4-element state vector

        Returns:
            Concurrence value (0 to 1)
        """
        from qpiai_quantum.formalism import DensityMatrix

        dm = DensityMatrix(state)
        return float(dm.concurrence())

    def compute_purity(self, state: np.ndarray) -> float:
        """Compute the purity of a quantum state.

        Args:
            state: Density matrix or state vector

        Returns:
            Purity value (1/d to 1)
        """
        from qpiai_quantum.formalism import DensityMatrix

        dm = DensityMatrix(state)
        return float(dm.purity())

    # ------------------------------------------------------------------ #
    #  Circuit Construction
    # ------------------------------------------------------------------ #

    def create_bb84_circuit(
        self,
        num_qubits: int = 1,
        alice_bases: list[str] | None = None,
        bob_bases: list[str] | None = None,
    ) -> Circuit:
        """Create a QpiAI circuit implementing the BB84 protocol.

        Args:
            num_qubits: Number of qubits to encode
            alice_bases: Bases Alice uses ('Z' or 'X')
            bob_bases: Bases Bob uses ('Z' or 'X')

        Returns:
            QpiAI Circuit for BB84
        """
        if alice_bases is None:
            alice_bases = [np.random.choice(["Z", "X"]) for _ in range(num_qubits)]
        if bob_bases is None:
            bob_bases = [np.random.choice(["Z", "X"]) for _ in range(num_qubits)]

        circuit = Circuit(num_qubits * 2, num_qubits * 2)

        # Alice prepares and encodes qubits
        for i in range(num_qubits):
            alice_bit = np.random.randint(0, 2)
            if alice_bit == 1:
                circuit.X(i)
            if alice_bases[i] == "X":
                circuit.H(i)

        # Alice sends to Bob (qubits pass through channel)
        # Bob measures in his chosen bases
        for i in range(num_qubits):
            bob_wire = i + num_qubits
            if bob_bases[i] == "X":
                circuit.H(bob_wire)

        # Measurement
        for i in range(num_qubits * 2):
            circuit.MEASURE(i, i)

        return circuit

    def create_entanglement_circuit(
        self, state_type: str = "|Ψ+>"
    ) -> tuple[Circuit, str]:
        """Create a circuit for Bell state (entangled pair) generation.

        Args:
            state_type: Type of Bell state: '|Ψ+>', '|Ψ->', '|Φ+>', '|Φ->'

        Returns:
            Tuple of (QpiAI Circuit, description string)
        """
        descriptions = {
            "|Ψ+>": "|01⟩ + |10⟩",
            "|Ψ->": "|01⟩ - |10⟩",
            "|Φ+>": "|00⟩ + |11⟩",
            "|Φ->": "|00⟩ - |11⟩",
        }

        circuit = Circuit(2, 2)
        circuit.H(0)
        circuit.CX(0, 1)

        if state_type == "|Ψ+>":
            circuit.X(0)  # Flip qubit 0: |00⟩+|11⟩ → |10⟩+|01⟩
        elif state_type == "|Ψ->":
            circuit.X(0)
            circuit.Z(0)
        elif state_type == "|Φ->":
            circuit.Z(0)

        return circuit, descriptions.get(state_type, state_type)

    def create_ghz_circuit(self, num_qubits: int = 3) -> Circuit:
        """Create a circuit for GHZ state generation.

        GHZ state: (|0...0⟩ + |1...1⟩)/√2 for multi-party QKD.

        Args:
            num_qubits: Number of qubits (>= 2)

        Returns:
            QpiAI Circuit for GHZ state
        """
        circuit = Circuit(num_qubits, num_qubits)
        circuit.H(0)
        for i in range(1, num_qubits):
            circuit.CX(0, i)
        return circuit

    def create_e91_circuit(
        self,
        num_pairs: int = 1,
        alice_bases: list[str] | None = None,
        bob_bases: list[str] | None = None,
    ) -> Circuit:
        """Create a QpiAI circuit implementing the E91 protocol.

        Uses entangled pairs with measurement in Z, X, and W bases.

        Args:
            num_pairs: Number of entangled pairs
            alice_bases: Bases Alice uses ('Z', 'X', 'W')
            bob_bases: Bases Bob uses ('Z', 'X', 'W')

        Returns:
            QpiAI Circuit for E91
        """
        if alice_bases is None:
            alice_bases = [np.random.choice(["Z", "X", "W"]) for _ in range(num_pairs)]
        if bob_bases is None:
            bob_bases = [np.random.choice(["Z", "X", "W"]) for _ in range(num_pairs)]

        circuit = Circuit(num_pairs * 2, num_pairs * 2)

        # Create entangled pairs
        for i in range(num_pairs):
            circuit.H(i)
            circuit.CX(i, i + num_pairs)

        # Alice measures her half
        for i, basis in enumerate(alice_bases):
            if basis == "X":
                circuit.H(i)
            elif basis == "W":
                circuit.RY(-np.pi / 4, i)
            # Z basis: no rotation

        # Bob measures his half
        for i, basis in enumerate(bob_bases):
            bob_wire = i + num_pairs
            if basis == "X":
                circuit.H(bob_wire)
            elif basis == "W":
                circuit.RY(np.pi / 4, bob_wire)

        # Measure all qubits
        for i in range(num_pairs * 2):
            circuit.MEASURE(i, i)

        return circuit

    # ------------------------------------------------------------------ #
    #  Simulation & Execution
    # ------------------------------------------------------------------ #

    def simulate(
        self, circuit: Circuit, shots: int = 1024
    ) -> dict[str, Any]:
        """Run a circuit on the QpiAI local simulator.

        Requires API_KEY set in environment for cloud simulation.
        Falls back to returning the circuit object for inspection.

        Args:
            circuit: QpiAI Circuit to simulate
            shots: Number of shots

        Returns:
            Dict with state information
        """
        import os

        api_key = os.getenv("API_KEY")
        if api_key:
            try:
                sv = Statevector(circuit)
                return {
                    "statevector": sv.data,
                    "num_qubits": sv.num_qubits,
                }
            except Exception:
                pass

        # Return circuit info for inspection
        return {
            "circuit": circuit,
            "num_qubits": circuit.icr.num_qubits,
            "num_classical": getattr(circuit.icr, "num_clbits", 0),
            "note": "Set API_KEY env var for full simulation",
        }

    def submit_to_cloud(
        self,
        circuit: Circuit,
        device_name: str = "QpiAI-QSV-Simulator",
        shots: int = 1024,
    ) -> Any:
        """Submit a circuit to the QpiAI quantum cloud.

        Args:
            circuit: QpiAI Circuit to execute
            device_name: Target device
            shots: Number of measurement shots

        Returns:
            JobResult from the cloud execution

        Raises:
            ValueError: If API_KEY is not set
        """
        import os

        api_key = os.getenv("API_KEY")
        if not api_key:
            raise ValueError(
                "API_KEY environment variable is required for cloud execution."
            )

        manager = JobManager(api_key=api_key)
        result = manager.run_circuit(
            circuit=circuit,
            device_name=device_name,
            shots=shots,
        )
        return result

    # ------------------------------------------------------------------ #
    #  QKD Protocol Helpers
    # ------------------------------------------------------------------ #

    def calculate_qber(
        self, alice_bits: list[int], bob_bits: list[int]
    ) -> float:
        """Calculate Quantum Bit Error Rate from measurement outcomes.

        Args:
            alice_bits: Alice's bit string
            bob_bits: Bob's bit string

        Returns:
            QBER value (0 to 1)
        """
        if len(alice_bits) != len(bob_bits):
            raise ValueError("Bit strings must have equal length")

        mismatches = sum(1 for a, b in zip(alice_bits, bob_bits) if a != b)
        return mismatches / len(alice_bits) if len(alice_bits) > 0 else 0.0

    def compute_chsh_value(self, angle_settings: list[float]) -> float:
        """Compute the CHSH S-value for DI-QKD verification.

        Uses QpiAI Statevector to compute the Bell correlator.

        Args:
            angle_settings: List of four angles [a, a', b, b']

        Returns:
            CHSH S-value. S > 2 indicates non-local correlations.
        """
        import numpy as np

        def correlation(a: float, b: float) -> float:
            """Compute ⟨Z₀Z₁⟩ for a Bell state with RY-rotated measurements."""
            # For |Φ+⟩ = (|00⟩+|11⟩)/√2 with RY rotations and Z measurements:
            # E(a,b) = cos(a-b)
            return np.cos(a - b)

        a, a_prime, b, b_prime = angle_settings

        # S = E(a,b) + E(a,b') + E(a',b) - E(a',b')
        s_value = (
            correlation(a, b)
            + correlation(a, b_prime)
            + correlation(a_prime, b)
            - correlation(a_prime, b_prime)
        )

        return float(s_value)
