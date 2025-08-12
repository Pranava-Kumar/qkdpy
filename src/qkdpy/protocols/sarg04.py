"""SARG04 QKD protocol implementation."""

import numpy as np

from ..core import Measurement, QuantumChannel, Qubit
from .base import BaseProtocol


class SARG04(BaseProtocol):
    """Implementation of the SARG04 quantum key distribution protocol.

    SARG04 is a variant of BB84 proposed by Scarani, Acín, Ribordy, and Gisin in 2004.
    It is more robust to certain types of eavesdropping attacks than BB84.
    """

    def __init__(self, channel: QuantumChannel, key_length: int = 100):
        """Initialize the SARG04 protocol.

        Args:
            channel: Quantum channel for qubit transmission
            key_length: Desired length of the final key

        """
        super().__init__(channel, key_length)

        # SARG04-specific parameters
        self.bases = ["computational", "hadamard"]
        self.security_threshold = 0.11  # Similar to BB84

        # Number of qubits to send (we'll send more than needed to account for sifting)
        self.num_qubits = key_length * 3  # Send 3x more qubits than needed

        # Alice's random bits and bases
        self.alice_bits = []
        self.alice_bases = []

        # Bob's measurement results and bases
        self.bob_results = []
        self.bob_bases = []

        # SARG04 specific: Bob's measurement guesses
        self.bob_guesses = []

    def prepare_states(self) -> list[Qubit]:
        """Prepare quantum states for transmission.

        In SARG04, Alice randomly chooses bits and bases, and prepares qubits
        in the corresponding states, similar to BB84.

        Returns:
            List of qubits to be sent through the quantum channel

        """
        qubits = []
        self.alice_bits = []
        self.alice_bases = []

        for _ in range(self.num_qubits):
            # Alice randomly chooses a bit (0 or 1)
            bit = int(np.random.randint(0, 2))
            self.alice_bits.append(bit)

            # Alice randomly chooses a basis
            basis = np.random.choice(self.bases)
            self.alice_bases.append(basis)

            # Prepare the qubit in the appropriate state
            if basis == "computational":
                # Computational basis: |0> or |1>
                qubit = Qubit.zero() if bit == 0 else Qubit.one()
            else:  # hadamard basis
                # Hadamard basis: |+> or |->
                qubit = Qubit.plus() if bit == 0 else Qubit.minus()

            qubits.append(qubit)

        return qubits

    def measure_states(self, qubits: list[Qubit]) -> list[int]:
        """Measure received quantum states.

        In SARG04, Bob randomly chooses bases to measure in, and then makes
        a guess about which state Alice sent.

        Args:
            qubits: List of received qubits

        Returns:
            List of measurement results

        """
        self.bob_results = []
        self.bob_bases = []
        self.bob_guesses = []

        for qubit in qubits:
            if qubit is None:
                # Qubit was lost in the channel
                self.bob_results.append(None)
                self.bob_bases.append(None)
                self.bob_guesses.append(None)
                continue

            # Bob randomly chooses a basis
            basis = np.random.choice(self.bases)
            self.bob_bases.append(basis)

            # Measure in the chosen basis
            result = Measurement.measure_in_basis(qubit, basis)
            self.bob_results.append(result)

            # SARG04 specific: Bob makes a guess about which state Alice sent
            # If Bob measured in the computational basis and got 0, he guesses Alice sent |0> or |+>
            # If Bob measured in the computational basis and got 1, he guesses Alice sent |1> or |->
            # If Bob measured in the Hadamard basis and got 0, he guesses Alice sent |0> or |+>
            # If Bob measured in the Hadamard basis and got 1, he guesses Alice sent |1> or |->

            # Bob randomly chooses one of the two possible states
            guess = int(np.random.randint(0, 2))
            self.bob_guesses.append(guess)

        return self.bob_results

    def sift_keys(self) -> tuple[list[int], list[int]]:
        """Sift the raw keys to keep only measurements in certain conditions.

        In SARG04, Alice and Bob keep bits where Bob's guess is inconsistent
        with his measurement basis, but consistent with Alice's basis.

        Returns:
            Tuple of (alice_sifted_key, bob_sifted_key)

        """
        alice_sifted = []
        bob_sifted = []

        for i in range(self.num_qubits):
            # Skip if Bob didn't receive the qubit
            if self.bob_bases[i] is None:
                continue

            # In SARG04, we keep bits where Bob's guess is inconsistent with his measurement basis
            # but consistent with Alice's basis

            # Bob's guess corresponds to a state in the opposite basis
            # For example, if Bob measured in the computational basis and his guess is 0,
            # he's guessing Alice sent |+> (which is in the Hadamard basis)

            # We need to check if Alice's basis matches Bob's guess
            alice_basis_index = 0 if self.alice_bases[i] == "computational" else 1
            bob_guess_basis = 1 - (0 if self.bob_bases[i] == "computational" else 1)

            if alice_basis_index == bob_guess_basis:
                alice_sifted.append(int(self.alice_bits[i]))

                # Bob's bit is determined by his guess
                bob_sifted.append(int(self.bob_guesses[i]))

        return alice_sifted, bob_sifted

    def estimate_qber(self) -> float:
        """Estimate the Quantum Bit Error Rate (QBER).

        In SARG04, Alice and Bob publicly compare a subset of their sifted keys
        to estimate the error rate.

        Returns:
            Estimated QBER value

        """
        alice_sifted, bob_sifted = self.sift_keys()

        # If we don't have enough bits for estimation, return a high QBER
        if len(alice_sifted) < 10:
            return 1.0

        # Use a random subset of the sifted key for QBER estimation
        sample_size = max(1, int(len(alice_sifted) * 0.2))

        # Randomly select indices for the sample
        indices = np.random.choice(len(alice_sifted), size=sample_size, replace=False)

        # Count errors in the sample
        errors = 0
        for idx in indices:
            if alice_sifted[idx] != bob_sifted[idx]:
                errors += 1

        # Calculate QBER
        qber = errors / sample_size
        return qber

    def _get_security_threshold(self) -> float:
        """Get the security threshold for the SARG04 protocol.

        Returns:
            Maximum QBER value considered secure

        """
        return self.security_threshold

    def get_sifting_efficiency(self) -> float:
        """Calculate the sifting efficiency of the protocol.

        Returns:
            Fraction of received qubits that are included in the sifted key

        """
        alice_sifted, _ = self.sift_keys()

        received_count = sum(1 for basis in self.bob_bases if basis is not None)

        return len(alice_sifted) / received_count if received_count > 0 else 0
