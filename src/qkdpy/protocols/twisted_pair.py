"""Twisted Pair QKD protocol implementation."""

import numpy as np

from ..core import QuantumChannel, Qubit
from .base import BaseProtocol


class TwistedPairQKD(BaseProtocol):
    """Implementation of a twisted pair QKD protocol.

    This is a conceptual protocol that combines multiple QKD techniques
    for enhanced security and robustness.
    """

    def __init__(
        self,
        channel: QuantumChannel,
        key_length: int = 100,
        security_threshold: float = 0.11,
    ):
        """Initialize the Twisted Pair QKD protocol.

        Args:
            channel: Quantum channel for qubit transmission
            key_length: Desired length of the final key
            security_threshold: Maximum QBER value considered secure
        """
        super().__init__(channel, key_length)

        # Twisted Pair QKD-specific parameters
        self.security_threshold = security_threshold

        # Number of qubits to send
        self.num_qubits = key_length * 3  # Send 3x more qubits than needed

        # Protocol parameters
        self.bases = ["computational", "hadamard", "circular"]
        self.twist_factor = 2  # Number of twists in the protocol

        # Alice's and Bob's data
        self.alice_bits = []
        self.alice_bases = []
        self.bob_results = []
        self.bob_bases = []
        self.twist_indices = []

    def prepare_states(self) -> list[Qubit]:
        """Prepare quantum states for transmission with twisted encoding.

        Returns:
            List of qubits to be sent through the quantum channel
        """
        qubits = []
        self.alice_bits = []
        self.alice_bases = []
        self.twist_indices = []

        for i in range(self.num_qubits):
            # Alice randomly chooses a bit (0 or 1)
            bit = int(np.random.randint(0, 2))
            self.alice_bits.append(bit)

            # Alice randomly chooses a basis
            basis = np.random.choice(self.bases)
            self.alice_bases.append(basis)

            # Apply twisting - every twist_factor qubits, we apply a twist
            if i % self.twist_factor == 0:
                self.twist_indices.append(i)

            # Prepare the qubit in the appropriate state
            if basis == "computational":
                # Computational basis: |0> or |1>
                qubit = Qubit.zero() if bit == 0 else Qubit.one()
            elif basis == "hadamard":
                # Hadamard basis: |+> or |->
                qubit = Qubit.plus() if bit == 0 else Qubit.minus()
            else:  # circular basis
                # Circular basis: |+i> or |-i>
                if bit == 0:
                    qubit = Qubit(1 / np.sqrt(2), 1j / np.sqrt(2))
                else:
                    qubit = Qubit(1 / np.sqrt(2), -1j / np.sqrt(2))

            qubits.append(qubit)

        return qubits

    def measure_states(self, qubits: list[Qubit]) -> list[int]:
        """Measure received quantum states with twisted decoding.

        Args:
            qubits: List of received qubits

        Returns:
            List of measurement results
        """
        self.bob_results = []
        self.bob_bases = []

        for i, qubit in enumerate(qubits):
            if qubit is None:
                # Qubit was lost in the channel
                self.bob_results.append(None)
                self.bob_bases.append(None)
                continue

            # Bob randomly chooses a basis
            basis = np.random.choice(self.bases)
            self.bob_bases.append(basis)

            # Apply twisting effect if this is a twist index
            if i in self.twist_indices:
                # In a real implementation, this would apply a specific
                # transformation based on the twist
                pass

            # Measure in the chosen basis
            from ..core import Measurement

            result = Measurement.measure_in_basis(qubit, basis)
            self.bob_results.append(result)

        return self.bob_results

    def sift_keys(self) -> tuple[list[int], list[int]]:
        """Sift the raw keys to keep only measurements in matching bases.

        Returns:
            Tuple of (alice_sifted_key, bob_sifted_key)
        """
        alice_sifted = []
        bob_sifted = []

        for i in range(self.num_qubits):
            # Skip if Bob didn't receive the qubit
            if self.bob_bases[i] is None:
                continue

            # Check if Alice and Bob used the same basis
            if self.alice_bases[i] == self.bob_bases[i]:
                alice_sifted.append(int(self.alice_bits[i]))
                bob_sifted.append(int(self.bob_results[i]))

        return alice_sifted, bob_sifted

    def estimate_qber(self) -> float:
        """Estimate the Quantum Bit Error Rate (QBER).

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
        """Get the security threshold for the Twisted Pair QKD protocol.

        Returns:
            Maximum QBER value considered secure
        """
        return self.security_threshold

    def get_twist_efficiency(self) -> float:
        """Calculate the efficiency of the twisting mechanism.

        Returns:
            Fraction of qubits that were twisted
        """
        return len(self.twist_indices) / self.num_qubits if self.num_qubits > 0 else 0

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
            "total_qubits": self.num_qubits,
        }
