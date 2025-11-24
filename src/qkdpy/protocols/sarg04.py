"""SARG04 QKD protocol implementation."""

import numpy as np

from ..core import Measurement, QuantumChannel, Qubit
from ..core.secure_random import secure_choice, secure_randint
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
        # SARG04 efficiency is ~25%, so we need ~4x raw bits. Adding buffer.
        self.num_qubits = key_length * 6  # Send 6x more qubits than needed

        # Alice's random bits and bases
        self.alice_bits: list[int] = []
        self.alice_bases: list[str | None] = []

        # Bob's measurement results and bases
        self.bob_results: list[int | None] = []
        self.bob_bases: list[str | None] = []

        # SARG04 specific: Bob's measurement guesses
        self.bob_guesses: list[int | None] = []

    def prepare_states(self) -> list[Qubit]:
        """Prepare quantum states for transmission.

        In SARG04, Alice prepares states like BB84 but also selects a 'partner' state
        to form a non-orthogonal set for announcement.

        Mapping:
        - Bit 0: |0> (Z) or |+> (X)
        - Bit 1: |1> (Z) or |-> (X)

        Announcement Pairs (one sent, one partner with opposite bit):
        - If sending |0> (Bit 0), partner is |-> (Bit 1). Set: {|0>, |->}
        - If sending |1> (Bit 1), partner is |+> (Bit 0). Set: {|1>, |+>}
        - If sending |+> (Bit 0), partner is |1> (Bit 1). Set: {|+>, |1>}
        - If sending |-> (Bit 1), partner is |0> (Bit 0). Set: {|->, |0>}

        Returns:
            List of qubits to be sent through the quantum channel
        """
        qubits = []
        self.alice_bits = []
        self.alice_bases = []
        self.announced_sets: list[tuple[str, str]] = (
            []
        )  # Stores the two states in the set (e.g., ("0", "-"))

        for _ in range(self.num_qubits):
            # Alice randomly chooses a bit (0 or 1)
            bit = secure_randint(0, 2)
            self.alice_bits.append(bit)

            # Alice randomly chooses a basis
            basis = secure_choice(self.bases)
            self.alice_bases.append(basis)

            # Prepare state and select partner
            qubit = None
            partner_state = ""
            sent_state_str = ""

            if basis == "computational":
                if bit == 0:
                    qubit = Qubit.zero()
                    sent_state_str = "0"
                    partner_state = "-"  # |0> paired with |->
                else:
                    qubit = Qubit.one()
                    sent_state_str = "1"
                    partner_state = "+"  # |1> paired with |+>
            else:  # hadamard
                if bit == 0:
                    qubit = Qubit.plus()
                    sent_state_str = "+"
                    partner_state = "1"  # |+> paired with |1>
                else:
                    qubit = Qubit.minus()
                    sent_state_str = "-"
                    partner_state = "0"  # |-> paired with |0>

            qubits.append(qubit)

            # Randomize order in announcement to hide which one was sent
            if secure_randint(0, 2) == 0:
                self.announced_sets.append((sent_state_str, partner_state))
            else:
                self.announced_sets.append((partner_state, sent_state_str))

        return qubits

    def measure_states(self, qubits: list[Qubit | None]) -> list[int]:
        """Measure received quantum states.

        Bob measures in a random basis.

        Args:
            qubits: List of received qubits

        Returns:
            List of measurement results
        """
        self.bob_results = []
        self.bob_bases = []

        for qubit in qubits:
            if qubit is None:
                self.bob_results.append(None)
                self.bob_bases.append(None)
                continue

            # Bob randomly chooses a basis
            basis = secure_choice(self.bases)
            self.bob_bases.append(basis)

            # Measure in the chosen basis
            result = Measurement.measure_in_basis(qubit, basis)
            qubit.collapse_state(result, basis)
            self.bob_results.append(result)

        # Filter out None values to return only int results
        return [result for result in self.bob_results if result is not None]

    def sift_keys(self) -> tuple[list[int], list[int]]:
        """Sift the raw keys based on SARG04 logic.

        Bob keeps the bit if his measurement result is orthogonal to one of the
        states in the announced set. This allows him to infer the *other* state
        was the one sent.

        Returns:
            Tuple of (alice_sifted_key, bob_sifted_key)
        """
        alice_sifted = []
        bob_sifted = []

        for i in range(self.num_qubits):
            # Skip if Bob didn't receive the qubit
            if self.bob_bases[i] is None or self.bob_results[i] is None:
                continue

            s1, s2 = self.announced_sets[i]
            bob_basis = self.bob_bases[i]
            bob_result = self.bob_results[i]

            # Determine Bob's measured state string
            measured_state = ""
            if bob_basis == "computational":
                measured_state = "0" if bob_result == 0 else "1"
            else:
                measured_state = "+" if bob_result == 0 else "-"

            # Check orthogonality
            # Orthogonal pairs: (0, 1), (+, -)
            is_ortho_s1 = self._are_orthogonal(measured_state, s1)
            is_ortho_s2 = self._are_orthogonal(measured_state, s2)

            inferred_bit = -1

            if is_ortho_s1 and not is_ortho_s2:
                # Orthogonal to s1, so must be s2
                inferred_bit = self._get_bit_from_state(s2)
            elif is_ortho_s2 and not is_ortho_s1:
                # Orthogonal to s2, so must be s1
                inferred_bit = self._get_bit_from_state(s1)
            else:
                # Inconclusive (orthogonal to neither or both - both impossible for these sets)
                continue

            # If we have a conclusive result, keep the bit
            alice_sifted.append(self.alice_bits[i])
            bob_sifted.append(inferred_bit)

        return alice_sifted, bob_sifted

    def _are_orthogonal(self, state1: str, state2: str) -> bool:
        """Check if two state strings are orthogonal."""
        if state1 == "0" and state2 == "1":
            return True
        if state1 == "1" and state2 == "0":
            return True
        if state1 == "+" and state2 == "-":
            return True
        if state1 == "-" and state2 == "+":
            return True
        return False

    def _get_bit_from_state(self, state: str) -> int:
        """Get the bit encoded by a state string."""
        if state in ["0", "+"]:
            return 0
        if state in ["1", "-"]:
            return 1
        raise ValueError(f"Unknown state: {state}")

    def estimate_qber(self) -> float:
        """Estimate the Quantum Bit Error Rate (QBER)."""
        alice_sifted, bob_sifted = self.sift_keys()

        if len(alice_sifted) < 10:
            return 1.0

        sample_size = max(1, int(len(alice_sifted) * 0.2))
        indices = np.random.choice(len(alice_sifted), size=sample_size, replace=False)

        errors = 0
        for idx in indices:
            if alice_sifted[idx] != bob_sifted[idx]:
                errors += 1

        return errors / sample_size

    def _get_security_threshold(self) -> float:
        return self.security_threshold

    def get_sifting_efficiency(self) -> float:
        alice_sifted, _ = self.sift_keys()
        received_count = sum(1 for basis in self.bob_bases if basis is not None)
        return len(alice_sifted) / received_count if received_count > 0 else 0
