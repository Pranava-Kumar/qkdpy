"""Continuous-variable QKD protocol implementation."""

import numpy as np

from ..core import QuantumChannel, Qubit
from .base import BaseProtocol


class CVQKD(BaseProtocol):
    """Implementation of a continuous-variable QKD protocol.

    This is a simplified simulation of CV-QKD, which uses continuous variables
    (such as the quadratures of light) instead of discrete variables (qubits).
    """

    def __init__(
        self,
        channel: QuantumChannel,
        key_length: int = 100,
        security_threshold: float = 0.1,
    ):
        """Initialize the CV-QKD protocol.

        Args:
            channel: Quantum channel for transmission
            key_length: Desired length of the final key
            security_threshold: Maximum excess noise level considered secure
        """
        super().__init__(channel, key_length)

        # CV-QKD-specific parameters
        self.security_threshold = security_threshold

        # Number of signals to send
        self.num_signals = key_length * 10  # Send 10x more signals than needed

        # Protocol parameters
        self.modulation_variance = 1.0  # Variance of the modulated signal
        self.homodyne_efficiency = 0.8  # Detection efficiency
        self.excess_noise = 0.01  # Excess noise in the channel

        # Alice's and Bob's data
        self.alice_bits = []
        self.alice_modulations = []
        self.bob_results = []
        self.bob_measurements = []

    def prepare_states(self) -> list[Qubit]:
        """Prepare quantum states for transmission (using qubits as a proxy).

        In CV-QKD, Alice prepares coherent states with Gaussian modulation.
        For this simulation, we'll use qubits with encoded classical information.

        Returns:
            List of qubits to be sent through the quantum channel
        """
        qubits = []
        self.alice_bits = []
        self.alice_modulations = []

        for _ in range(self.num_signals):
            # Alice generates a random bit (0 or 1)
            bit = int(np.random.randint(0, 2))
            self.alice_bits.append(bit)

            # Alice also generates a random modulation (Gaussian distributed)
            modulation = np.random.normal(0, np.sqrt(self.modulation_variance))
            self.alice_modulations.append(modulation)

            # Alice prepares a qubit based on the bit
            if bit == 0:
                qubit = Qubit.zero()
            else:
                qubit = Qubit.one()

            qubits.append(qubit)

        return qubits

    def measure_states(self, qubits: list[Qubit]) -> list[int]:
        """Measure received quantum states.

        In CV-QKD, Bob performs homodyne detection. For this simulation,
        we'll measure the qubits and add noise to simulate the continuous
        variable measurement.

        Args:
            qubits: List of received qubits

        Returns:
            List of measurement results (0 or 1)
        """
        self.bob_results = []
        self.bob_measurements = []

        for i, qubit in enumerate(qubits):
            if qubit is None:
                # Qubit was lost in the channel
                self.bob_results.append(None)
                self.bob_measurements.append(None)
                continue

            # Bob measures the qubit in the computational basis
            measurement = qubit.measure("computational")
            qubit.collapse_state(measurement, "computational")

            # Add noise to simulate continuous variable measurement
            # In a real implementation, this would be more complex
            noise = np.random.normal(0, np.sqrt(self.channel.noise_level))

            # Store both the discrete measurement (for protocol compatibility)
            # and the continuous measurement (for CV-QKD specific calculations)
            self.bob_results.append(measurement)

            # Create a noisy continuous measurement based on Alice's original modulation
            if i < len(self.alice_modulations):
                original_modulation = self.alice_modulations[i]
                # Add noise to the original modulation
                noisy_measurement = original_modulation + noise
            else:
                # Fallback if we don't have the original modulation
                noisy_measurement = float(measurement) + noise

            self.bob_measurements.append(noisy_measurement)

        return self.bob_results

    def sift_keys(self) -> tuple[list[int], list[int]]:
        """Sift the raw keys to keep only valid measurements.

        Returns:
            Tuple of (alice_sifted_key, bob_sifted_key)
        """
        alice_sifted = []
        bob_sifted = []

        for i in range(self.num_signals):
            # Skip if Bob didn't receive the signal
            if self.bob_results[i] is None:
                continue

            alice_sifted.append(int(self.alice_bits[i]))
            bob_sifted.append(int(self.bob_results[i]))

        return alice_sifted, bob_sifted

    def estimate_qber(self) -> float:
        """Estimate the error rate in the data.

        Returns:
            Estimated error rate
        """
        alice_sifted, bob_sifted = self.sift_keys()

        # If we don't have enough data for estimation, return a high error value
        if len(alice_sifted) < 10:
            return 1.0

        # Count errors in the sifted key (standard QBER calculation)
        errors = 0
        for i in range(len(alice_sifted)):
            if alice_sifted[i] != bob_sifted[i]:
                errors += 1

        # Calculate QBER
        qber = errors / len(alice_sifted) if len(alice_sifted) > 0 else 1.0

        return float(qber)

    def _get_security_threshold(self) -> float:
        """Get the security threshold for the CV-QKD protocol.

        Returns:
            Maximum error rate considered secure
        """
        return self.security_threshold

    def get_excess_noise(self) -> float:
        """Estimate the excess noise in the channel using continuous measurements.

        Returns:
            Estimated excess noise level
        """
        # Calculate the correlation between Alice's modulations and Bob's measurements
        valid_indices = [
            i for i in range(self.num_signals) if self.bob_measurements[i] is not None
        ]

        if len(valid_indices) < 10:
            return 1.0

        alice_mods = [self.alice_modulations[i] for i in valid_indices]
        bob_measurements = [self.bob_measurements[i] for i in valid_indices]

        # Calculate the correlation
        correlation = np.corrcoef(alice_mods, bob_measurements)[0, 1]

        # Convert correlation to an excess noise estimate
        excess_noise = max(0.0, min(1.0, 1.0 - correlation))

        return float(excess_noise)

    def get_key_rate(self) -> float:
        """Calculate the key generation rate.

        Returns:
            Key rate
        """
        if not self.is_complete:
            return 0.0

        # Simplified key rate calculation
        alice_sifted, _ = self.sift_keys()

        if len(alice_sifted) == 0:
            return 0.0

        # In this simplified version, we use the ratio of final key length to sifted key length
        key_rate = len(self.final_key) / len(alice_sifted)

        return key_rate
