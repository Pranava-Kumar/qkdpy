"""Device-independent QKD protocol implementation."""

import numpy as np

from ..core import QuantumChannel, Qubit
from ..core.measurements import Measurement
from .base import BaseProtocol


class DeviceIndependentQKD(BaseProtocol):
    """Implementation of a device-independent QKD protocol.

    This is a simplified simulation of device-independent QKD, which aims to
    provide security even against attacks on the devices used in the protocol.
    """

    def __init__(
        self,
        channel: QuantumChannel,
        key_length: int = 100,
        security_threshold: float = 0.8,
    ):
        """Initialize the device-independent QKD protocol.

        Args:
            channel: Quantum channel for qubit transmission
            key_length: Desired length of the final key
            security_threshold: Minimum Bell inequality violation for security
        """
        super().__init__(channel, key_length)

        # DI-QKD-specific parameters
        self.security_threshold = security_threshold

        # Number of entangled pairs to generate
        self.num_pairs = key_length * 4  # Generate 4x more pairs than needed

        # Measurement settings for Alice and Bob
        self.alice_settings = [0, np.pi / 4]  # Alice's measurement angles
        self.bob_settings = [np.pi / 8, 3 * np.pi / 8]  # Bob's measurement angles

        # Alice's and Bob's measurement choices and results
        self.alice_choices: list[int] = []
        self.alice_results: list[int] = []
        self.bob_choices: list[int | None] = []
        self.bob_results: list[int | None] = []

    def prepare_states(self) -> list[Qubit]:
        """Prepare entangled quantum states for transmission.

        In DI-QKD, Alice prepares one half of each entangled pair and keeps
        the other half.

        Returns:
            List of qubits to be sent to Bob through the quantum channel
        """
        qubits = []

        for _ in range(self.num_pairs):
            # Create a Bell state (Φ+ = (|00> + |11>) / sqrt(2))
            # Alice keeps the first qubit and sends the second to Bob
            # alice_qubit = Qubit(1/np.sqrt(2), 0)  # Simplified representation (not used)
            bob_qubit = Qubit(1 / np.sqrt(2), 0)  # Simplified representation

            # In a real implementation, we would create proper entangled states
            # For this simulation, we'll just send one qubit of each pair
            qubits.append(bob_qubit)

        return qubits

    def measure_states(self, qubits: list[Qubit | None]) -> list[int]:
        """Measure received quantum states.

        In DI-QKD, Bob randomly chooses measurement settings.

        Args:
            qubits: List of received qubits (may contain None for lost qubits)

        Returns:
            List of measurement results
        """
        self.bob_choices = []
        self.bob_results = []

        # Alice's random choices (in a real implementation, Alice would also make choices)
        self.alice_choices = [int(np.random.choice([0, 1])) for _ in range(len(qubits))]
        self.alice_results = [int(np.random.choice([0, 1])) for _ in range(len(qubits))]

        for qubit in qubits:
            if qubit is None:
                # Qubit was lost in the channel
                self.bob_choices.append(None)
                self.bob_results.append(None)
                continue

            # Bob randomly chooses a measurement setting
            bob_choice = int(np.random.choice([0, 1]))
            self.bob_choices.append(bob_choice)

            # Measure the qubit
            # In a real implementation, we would apply the appropriate rotation based on the setting
            result = Measurement.measure_in_basis(qubit, "computational")

            # Add noise effect
            if np.random.random() < self.channel.noise_level:
                result = 1 - result

            self.bob_results.append(result)

        # Filter out None values to return only int results
        return [result for result in self.bob_results if result is not None]

    def sift_keys(self) -> tuple[list[int], list[int]]:
        """Sift the raw keys to keep only measurements in certain setting combinations.

        Returns:
            Tuple of (alice_sifted_key, bob_sifted_key)
        """
        alice_sifted = []
        bob_sifted = []

        for i in range(self.num_pairs):
            # Skip if Bob didn't receive the qubit
            if self.bob_choices[i] is None or self.bob_results[i] is None:
                continue

            # For key generation, we use specific combinations of measurement settings
            # In this simplified implementation, we'll use matching settings
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

        In DI-QKD, Alice and Bob can estimate the QBER by comparing a subset
        of their sifted keys.

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

    def test_bell_inequality(self) -> dict:
        """Test Bell's inequality to verify entanglement and device independence.

        Returns:
            Dictionary containing Bell test results
        """
        # Calculate correlation values for different setting combinations
        correlations = {}

        # For each combination of Alice and Bob's settings
        for a in range(len(self.alice_settings)):
            for b in range(len(self.bob_settings)):
                # Find all measurements where Alice used setting a and Bob used setting b
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
                    correlations[f"E({a},{b})"] = e_val

        # CHSH inequality: S = |E(a,b) - E(a,b')| + |E(a',b) + E(a',b')| <= 2
        # For quantum mechanics, |S| <= 2*sqrt(2) ≈ 2.828
        # For local realism, |S| <= 2

        # Extract correlation values (use 0 if not available)
        e00 = correlations.get("E(0,0)", 0.0)
        e01 = correlations.get("E(0,1)", 0.0)
        e10 = correlations.get("E(1,0)", 0.0)
        e11 = correlations.get("E(1,1)", 0.0)

        # Calculate S value
        s_value = abs(e00 - e01) + abs(e10 + e11)

        # Check if Bell's inequality is violated
        is_violated = s_value > 2.0

        # Estimate QBER from Bell test
        # In DI-QKD, the QBER can be estimated from the Bell violation
        # This is a simplified estimation
        estimated_qber = max(0.0, min(1.0, 0.5 * (1 - s_value / (2 * np.sqrt(2)))))

        return {
            "s_value": s_value,
            "is_violated": is_violated,
            "correlations": correlations,
            "estimated_qber": estimated_qber,
        }

    def _get_security_threshold(self) -> float:
        """Get the security threshold for the DI-QKD protocol.

        In device-independent QKD, security is determined by the violation
        of Bell's inequality beyond a certain threshold.

        Returns:
            Minimum Bell inequality violation for security

        """
        return self.security_threshold
