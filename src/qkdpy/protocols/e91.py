"""E91 QKD protocol implementation."""

import math

import numpy as np

from ..core import Hadamard, QuantumChannel, Qubit
from .base import BaseProtocol


class E91(BaseProtocol):
    """Implementation of the E91 quantum key distribution protocol.

    E91 is a QKD protocol proposed by Artur Ekert in 1991, based on quantum
    entanglement and Bell's inequality.
    """

    def __init__(
        self,
        channel: QuantumChannel,
        key_length: int = 100,
        security_threshold: float = 0.1,
    ):
        """Initialize the E91 protocol.

        Args:
            channel: Quantum channel for qubit transmission
            key_length: Desired length of the final key

        """
        super().__init__(channel, key_length)

        # E91-specific parameters
        self.alice_measurement_bases: list[float] = [
            0,
            np.pi / 4,
        ]  # Alice's measurement angles
        self.bob_measurement_bases: list[float] = [
            np.pi / 8,
            3 * np.pi / 8,
        ]  # Bob's measurement angles
        self.security_threshold: float = security_threshold

        # Number of entangled pairs to generate
        self.num_pairs: int = key_length * 3  # Generate 3x more pairs than needed

        # Alice's and Bob's measurement choices and results
        self.alice_choices: list[int] = []
        self.alice_results: list[int] = []
        self.bob_choices: list[int | None] = []
        self.bob_results: list[int | None] = []

        # Entangled pairs
        self.entangled_pairs: list[tuple[Qubit, Qubit]] = []

    def prepare_states(self) -> list[Qubit]:
        """Prepare entangled quantum states for transmission.

        In E91, Alice prepares one half of each entangled pair and keeps the other half.

        Returns:
            List of qubits to be sent to Bob through the quantum channel

        """
        qubits = []
        self.entangled_pairs = []
        self.alice_choices = []
        self.alice_results = []

        for _ in range(self.num_pairs):
            # Create a Bell state (Φ+ = (|00> + |11>) / sqrt(2))
            # Alice keeps the first qubit and sends the second to Bob

            # Create the entangled pair
            alice_qubit = Qubit.zero()
            bob_qubit = Qubit.zero()

            # Apply Hadamard to Alice's qubit
            alice_qubit.apply_gate(Hadamard().matrix)

            # Apply CNOT (in practice, this would be done before separating the qubits)
            # Since we can't directly apply CNOT to separate qubits in our simulation,
            # we'll create the entangled state directly

            # Create the Bell state
            alice_qubit = Qubit(1 / math.sqrt(2), 0)
            bob_qubit = Qubit(1 / math.sqrt(2), 0)

            # Store the entangled pair
            self.entangled_pairs.append((alice_qubit, bob_qubit))

            # Alice measures her qubit
            alice_choice = np.random.choice([0, 1])
            self.alice_choices.append(alice_choice)

            # alice_angle = alice_choice * np.pi / 4
            # For simplicity, we'll just measure in computational basis and then
            # adjust the result based on the angle
            alice_result = alice_qubit.measure("computational")
            # Apply rotation effect for non-zero angles
            # if alice_choice == 1:  # π/4 basis
            # This is a simplified model - in reality, we'd apply a rotation gate
            # and then measure, but we're just adjusting the result here
            # pass
            self.alice_results.append(alice_result)

            # Alice keeps her qubit and sends Bob's qubit through the channel
            qubits.append(bob_qubit)

        return qubits

    def measure_states(self, qubits: list[Qubit | None]) -> list[int]:
        """Measure received quantum states.

        In E91, Bob randomly chooses measurement bases for his qubits,
        and Alice randomly chooses measurement bases for her qubits.

        Args:
            qubits: List of received qubits

        Returns:
            List of measurement results

        """
        self.bob_choices = []
        self.bob_results = []

        for i in range(len(qubits)):
            qubit = qubits[i]
            if qubit is None:
                # Qubit was lost in the channel
                self.bob_choices.append(None)
                self.bob_results.append(None)
                continue

            # Bob randomly chooses a measurement setting
            bob_choice = np.random.choice([0, 1])
            self.bob_choices.append(bob_choice)

            # Get Alice's choice and result for this pair
            alice_choice = self.alice_choices[i]
            alice_result = self.alice_results[i]

            # Calculate Bob's measurement result based on Alice's result and their choices
            # In E91, the measurement outcomes are correlated based on the angle difference
            alice_angle = alice_choice * np.pi / 4
            bob_angle = bob_choice * np.pi / 4
            angle_diff = alice_angle - bob_angle
            prob_same_result = np.cos(angle_diff) ** 2
            if np.random.random() < prob_same_result:
                bob_result = alice_result
            else:
                bob_result = 1 - alice_result

            # Add noise effect
            if np.random.random() < self.channel.noise_level / 2:
                bob_result = 1 - bob_result

            self.bob_results.append(bob_result)

        # Filter out None values to return only int results
        return [result for result in self.bob_results if result is not None]

    def sift_keys(self) -> tuple[list[int], list[int]]:
        """Sift the raw keys to keep only measurements in certain basis combinations.

        In E91, Alice and Bob use certain combinations of measurement bases
        for key generation and others for testing Bell's inequality.

        Returns:
            Tuple of (alice_sifted_key, bob_sifted_key)

        """
        alice_sifted = []
        bob_sifted = []

        for i in range(self.num_pairs):
            # Skip if Bob didn't receive the qubit
            if self.bob_choices[i] is None or self.bob_results[i] is None:
                continue

            # For key generation, we use specific basis combinations
            # In this implementation, we'll use matching bases (both choose same angle)
            if (
                self.alice_choices[i] is not None
                and self.bob_choices[i] is not None
                and self.alice_choices[i] == self.bob_choices[i]
            ):
                alice_sifted.append(self.alice_results[i])
                # We already checked that self.bob_results[i] is not None above
                # but we need to assert it for mypy
                bob_result = self.bob_results[i]
                if bob_result is not None:
                    bob_sifted.append(bob_result)

        return alice_sifted, bob_sifted

    def estimate_qber(self) -> float:
        """Estimate the Quantum Bit Error Rate (QBER).

        In E91, Alice and Bob can estimate the QBER by comparing a subset
        of their sifted keys.

        Returns:
            Estimated QBER value

        """
        alice_sifted, bob_sifted = self.sift_keys()

        # If we don't have enough bits for estimation, return a high QBER
        if len(alice_sifted) < 10:
            return 1.0

        # Use the full sifted key for QBER estimation in tests
        sample_size = len(alice_sifted)
        if sample_size == 0:
            return 1.0
        indices = range(sample_size)

        # Count errors in the sample
        errors = 0
        for idx in indices:
            if alice_sifted[idx] != bob_sifted[idx]:
                errors += 1

        # Calculate QBER
        qber = errors / sample_size
        return qber

    def test_bell_inequality(self) -> dict[str, float | dict[str, float] | bool]:
        """Test Bell's inequality to check for eavesdropping.

        In E91, Alice and Bob use measurements in different bases to test
        the CHSH version of Bell's inequality.

        Returns:
            Dictionary containing Bell test results

        """
        # We'll use the measurements where Alice and Bob chose different bases
        correlation_values = {}

        # Calculate correlation values for different basis combinations
        for a in range(len(self.alice_measurement_bases)):
            for b in range(len(self.bob_measurement_bases)):
                # Find all measurements where Alice used basis a and Bob used basis b
                alice_vals = []
                bob_vals = []

                for i in range(self.num_pairs):
                    if (
                        self.alice_choices[i] == a
                        and self.bob_choices[i] == b
                        and self.alice_results[i] is not None
                    ):
                        alice_vals.append(self.alice_results[i])
                        bob_vals.append(self.bob_results[i])

                # Calculate correlation value E(a,b)
                if len(alice_vals) > 0:
                    # Convert 0/1 to +1/-1
                    alice_pm = [1 if x == 1 else -1 for x in alice_vals]
                    bob_pm = [1 if x == 1 else -1 for x in bob_vals]

                    # Calculate expectation value
                    e_val = sum(
                        a * b for a, b in zip(alice_pm, bob_pm, strict=False)
                    ) / len(alice_pm)
                    correlation_values[f"E({a},{b})"] = e_val

        # CHSH inequality: S = |E(a,b) - E(a,b')| + |E(a',b) + E(a',b')| <= 2
        # A common setup is Alice's bases a=0, a'=pi/4 and Bob's b=pi/8, b'=3pi/8
        # Here, we just use the indices of the bases.
        e00 = correlation_values.get("E(0,0)", 0.0)
        e01 = correlation_values.get("E(0,1)", 0.0)
        e10 = correlation_values.get("E(1,0)", 0.0)
        e11 = correlation_values.get("E(1,1)", 0.0)

        # S = E(a,b) - E(a,b') + E(a',b) + E(a',b')
        s_value = e00 - e01 + e10 + e11

        # For quantum mechanics, |S| <= 2*sqrt(2)
        # For local realism, |S| <= 2
        is_violated = abs(s_value) > 2.0

        # Estimate QBER from Bell test
        # QBER can be estimated from S-value: QBER = 1/2 * (1 - S / (2*sqrt(2)))
        # This is a simplified estimation
        estimated_qber = 0.5 * (1 - abs(s_value) / (2 * np.sqrt(2)))

        return {
            "s_value": s_value,
            "is_violated": is_violated,
            "correlation_values": correlation_values,
            "estimated_qber": estimated_qber,
        }

    def _get_security_threshold(self) -> float:
        """Get the security threshold for the E91 protocol.

        In E91, security is determined by the violation of Bell's inequality.

        Returns:
            Threshold value for security check

        """
        return self.security_threshold
