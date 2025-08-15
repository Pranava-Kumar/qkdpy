"""High-Dimensional Quantum Key Distribution (HD-QKD) protocol implementation."""

import numpy as np

from ..core import QuantumChannel, Qubit
from .base import BaseProtocol


class HDQKD(BaseProtocol):
    """Implementation of High-Dimensional Quantum Key Distribution protocol.

    HD-QKD uses qudits (d-dimensional quantum systems) instead of qubits,
    allowing for more information per photon and enhanced security.
    """

    def __init__(
        self,
        channel: QuantumChannel,
        key_length: int = 100,
        dimension: int = 4,
        security_threshold: float = 0.15,
    ):
        """Initialize the HD-QKD protocol.

        Args:
            channel: Quantum channel for qudit transmission
            key_length: Desired length of the final key
            dimension: Dimension of the qudit system (d)
            security_threshold: Maximum QBER value considered secure
        """
        super().__init__(channel, key_length)

        # HD-QKD-specific parameters
        self.dimension = dimension
        self.security_threshold = security_threshold

        # Number of qudits to send (more than needed to account for sifting)
        self.num_qudits = key_length * 3

        # Alice's random symbols and bases
        self.alice_symbols = []
        self.alice_bases = []

        # Bob's measurement results and bases
        self.bob_results = []
        self.bob_bases = []

        # MUBs (Mutually Unbiased Bases) for the dimension
        self.mubs = self._generate_mubs(dimension)

    def _generate_mubs(self, d: int) -> list[np.ndarray]:
        """Generate Mutually Unbiased Bases for a d-dimensional system.

        Args:
            d: Dimension of the system

        Returns:
            List of d+1 MUBs, each as a dxd matrix
        """
        if d == 2:
            # For qubits, we have 3 MUBs (X, Y, Z)
            return [
                np.array([[1, 0], [0, 1]]),  # Computational basis
                np.array([[1, 1], [1, -1]]) / np.sqrt(2),  # Hadamard basis
                np.array([[1, -1j], [1, 1j]]) / np.sqrt(2),  # Circular basis
            ]
        else:
            # For higher dimensions, we would need a more complex implementation
            # This is a simplified placeholder
            mubs = []
            for _i in range(d + 1):
                # Generate a random unitary matrix for each basis
                # In a real implementation, these would be mathematically constructed MUBs
                H = np.random.randn(d, d) + 1j * np.random.randn(d, d)
                Q, R = np.linalg.qr(H)
                mubs.append(Q)
            return mubs

    def prepare_states(self) -> list[Qubit]:
        """Prepare quantum states for transmission in HD-QKD.

        In HD-QKD, Alice randomly chooses symbols from {0, 1, ..., d-1} and bases.

        Returns:
            List of qubits encoded with HD information
        """
        qubits = []
        self.alice_symbols = []
        self.alice_bases = []

        for _ in range(self.num_qudits):
            # Alice randomly chooses a symbol (0 to d-1)
            symbol = np.random.randint(0, self.dimension)
            self.alice_symbols.append(symbol)

            # Alice randomly chooses a basis (0 to d)
            basis_idx = np.random.randint(0, len(self.mubs))
            self.alice_bases.append(basis_idx)

            # For simulation purposes, we'll encode the symbol in the computational basis
            # This is a simplified representation - a full HD-QKD implementation
            # would require qudit simulation capabilities
            if symbol == 0:
                qubit = Qubit.zero()
            elif symbol == 1:
                qubit = Qubit.one()
            else:
                # For higher dimensions, we'll use superposition states
                # This is a simplification for the current qubit-based framework
                alpha = np.cos(np.pi * symbol / self.dimension)
                beta = np.sin(np.pi * symbol / self.dimension) * np.exp(
                    1j * np.pi * symbol / self.dimension
                )
                qubit = Qubit(alpha, beta)

            qubits.append(qubit)

        return qubits

    def measure_states(self, qubits: list[Qubit]) -> list[int]:
        """Measure received quantum states in HD-QKD.

        Args:
            qubits: List of received qubits

        Returns:
            List of measurement results
        """
        self.bob_results = []
        self.bob_bases = []

        for qubit in qubits:
            if qubit is None:
                # Qubit was lost in the channel
                self.bob_results.append(None)
                self.bob_bases.append(None)
                continue

            # Bob randomly chooses a basis
            basis_idx = np.random.randint(0, len(self.mubs))
            self.bob_bases.append(basis_idx)

            # For simulation, we'll measure in computational basis and map to symbols
            # A full implementation would use the appropriate measurement operators
            prob_0, prob_1 = qubit.probabilities
            if prob_0 > prob_1:
                result = 0
            else:
                result = 1

            # Map to higher dimensions probabilistically
            if self.dimension > 2:
                result = int(np.random.randint(0, self.dimension))

            self.bob_results.append(result)

        return self.bob_results

    def sift_keys(self) -> tuple[list[int], list[int]]:
        """Sift the raw keys to keep only measurements in matching bases.

        Returns:
            Tuple of (alice_sifted_key, bob_sifted_key)
        """
        alice_sifted = []
        bob_sifted = []

        for i in range(self.num_qudits):
            # Skip if Bob didn't receive the qubit
            if self.bob_bases[i] is None:
                continue

            # Check if Alice and Bob used the same basis
            if self.alice_bases[i] == self.bob_bases[i]:
                alice_sifted.append(int(self.alice_symbols[i]))
                bob_sifted.append(int(self.bob_results[i]))

        return alice_sifted, bob_sifted

    def estimate_qber(self) -> float:
        """Estimate the Quantum Bit Error Rate (QBER) for HD-QKD.

        Returns:
            Estimated QBER value
        """
        alice_sifted, bob_sifted = self.sift_keys()

        # If we don't have enough bits for estimation, return a high QBER
        if len(alice_sifted) < 10:
            return 1.0

        # Count errors in the sifted key
        errors = 0
        for i in range(len(alice_sifted)):
            if alice_sifted[i] != bob_sifted[i]:
                errors += 1

        # Calculate QBER
        qber = errors / len(alice_sifted) if len(alice_sifted) > 0 else 1.0
        return qber

    def _get_security_threshold(self) -> float:
        """Get the security threshold for the HD-QKD protocol.

        Returns:
            Maximum QBER value considered secure
        """
        return self.security_threshold

    def get_dimension_efficiency(self) -> float:
        """Calculate the efficiency gain from using higher dimensions.

        Returns:
            Efficiency factor compared to qubit-based protocols
        """
        # In HD-QKD, we can encode log2(d) bits per photon instead of 1
        return np.log2(self.dimension)

    def get_basis_distribution(self) -> dict:
        """Analyze the distribution of measurement bases.

        Returns:
            Dictionary with basis distribution statistics
        """
        alice_basis_counts = {}
        bob_basis_counts = {}

        # Count Alice's basis choices
        for basis in self.alice_bases:
            if basis is not None:
                alice_basis_counts[basis] = alice_basis_counts.get(basis, 0) + 1

        # Count Bob's basis choices
        for basis in self.bob_bases:
            if basis is not None:
                bob_basis_counts[basis] = bob_basis_counts.get(basis, 0) + 1

        return {
            "alice_bases": alice_basis_counts,
            "bob_bases": bob_basis_counts,
            "total_qudits": self.num_qudits,
            "dimension": self.dimension,
        }
