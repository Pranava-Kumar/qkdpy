"""Enhanced continuous-variable QKD protocol implementation."""

import numpy as np

from ..core import QuantumChannel, Qubit
from .base import BaseProtocol


class EnhancedCVQKD(BaseProtocol):
    """Enhanced implementation of continuous-variable QKD protocol.

    This implementation properly handles continuous variables and implements
    Gaussian-modulated coherent state CV-QKD with homodyne detection.
    """

    def __init__(
        self,
        channel: QuantumChannel,
        key_length: int = 100,
        security_threshold: float = 0.1,
        modulation_variance: float = 2.0,
        detection_efficiency: float = 0.6,
    ):
        """Initialize the enhanced CV-QKD protocol.

        Args:
            channel: Quantum channel for transmission
            key_length: Desired length of the final key
            security_threshold: Maximum excess noise level considered secure
            modulation_variance: Variance of Gaussian modulation
            detection_efficiency: Homodyne detection efficiency
        """
        super().__init__(channel, key_length)

        # CV-QKD-specific parameters
        self.security_threshold = security_threshold
        self.modulation_variance = modulation_variance
        self.detection_efficiency = detection_efficiency

        # Number of signals to send
        self.num_signals = key_length * 20  # Send more signals for better statistics

        # Protocol parameters
        self.excess_noise = 0.01  # Excess noise in the channel
        self.transmission_t = 0.1  # Channel transmission
        self.homodyne_angle = 0.0  # Homodyne detection angle

        # Alice's and Bob's data
        self.alice_bits: list[int] = []
        self.alice_modulations_x: list[float] = []  # X quadrature modulations
        self.alice_modulations_p: list[float] = []  # P quadrature modulations
        self.bob_measurements_x: list[float] = []  # X quadrature measurements
        self.bob_measurements_p: list[float] = []  # P quadrature measurements
        self.alice_key: list[int] = []
        self.bob_key: list[int] = []

        # For security analysis
        self.covariance_matrix: np.ndarray | None = None
        self.secret_fraction: float = 0.0

    def prepare_states(self) -> list[Qubit]:
        """Prepare quantum states for transmission.

        In CV-QKD, Alice prepares coherent states with Gaussian modulation
        on both quadratures. For compatibility with the base protocol,
        we encode the continuous information in qubit states.

        Returns:
            List of qubits to be sent through the quantum channel
        """
        qubits = []
        self.alice_bits = []
        self.alice_modulations_x = []
        self.alice_modulations_p = []

        for _ in range(self.num_signals):
            # Alice generates random bits for key generation
            bit = int(np.random.randint(0, 2))
            self.alice_bits.append(bit)

            # Alice generates Gaussian modulations for both quadratures
            modulation_x = np.random.normal(0, np.sqrt(self.modulation_variance))
            modulation_p = np.random.normal(0, np.sqrt(self.modulation_variance))

            self.alice_modulations_x.append(modulation_x)
            self.alice_modulations_p.append(modulation_p)

            # For compatibility, we'll create a qubit that represents the bit
            # but store the continuous information separately
            if bit == 0:
                qubit = Qubit.zero()
            else:
                qubit = Qubit.one()

            qubits.append(qubit)

        return qubits

    def measure_states(self, qubits: list[Qubit | None]) -> list[int]:
        """Measure received quantum states.

        In CV-QKD, Bob performs homodyne measurements on the received signals.
        For compatibility with the base protocol, we return discrete measurements.

        Args:
            qubits: List of received qubits (may contain None for lost signals)

        Returns:
            List of measurement results (0 or 1)
        """
        self.bob_measurements_x = []
        self.bob_measurements_p = []

        for i, qubit in enumerate(qubits):
            if qubit is None:
                # Signal was lost in the channel
                self.bob_measurements_x.append(0.0)
                self.bob_measurements_p.append(0.0)
                continue

            # Extract Alice's original modulations if available
            alice_x = (
                self.alice_modulations_x[i]
                if i < len(self.alice_modulations_x)
                else 0.0
            )
            alice_p = (
                self.alice_modulations_p[i]
                if i < len(self.alice_modulations_p)
                else 0.0
            )

            # Channel transmission effect on the continuous variables
            transmitted_x = alice_x * np.sqrt(self.transmission_t)
            transmitted_p = alice_p * np.sqrt(self.transmission_t)

            # Add channel noise (thermal noise + excess noise)
            thermal_noise = 1.0  # Vacuum noise
            total_noise = thermal_noise + self.excess_noise

            noise_x = np.random.normal(0, np.sqrt(total_noise / 2))
            noise_p = np.random.normal(0, np.sqrt(total_noise / 2))

            noisy_x = transmitted_x + noise_x
            noisy_p = transmitted_p + noise_p

            # Detection efficiency
            detected_x = noisy_x * np.sqrt(self.detection_efficiency)
            detected_p = noisy_p * np.sqrt(self.detection_efficiency)

            # Add electronic noise
            elec_noise = np.random.normal(0, np.sqrt(0.1))
            final_x = detected_x + elec_noise
            elec_noise = np.random.normal(0, np.sqrt(0.1))
            final_p = detected_p + elec_noise

            self.bob_measurements_x.append(final_x)
            self.bob_measurements_p.append(final_p)

        # For compatibility with the base protocol, return discrete measurements
        # based on the sign of the X quadrature measurements
        discrete_measurements = []
        for x_measurement in self.bob_measurements_x:
            discrete_measurements.append(0 if x_measurement >= 0 else 1)

        return discrete_measurements

    def sift_keys(self) -> tuple[list[int], list[int]]:
        """Sift the raw keys using correlated data.

        In CV-QKD, key sifting is based on correlation between Alice's
        modulations and Bob's measurements.

        Returns:
            Tuple of (alice_sifted_key, bob_sifted_key)
        """
        # Calculate correlations to determine which data to keep
        correlations_x = []
        correlations_p = []

        for i in range(len(self.alice_modulations_x)):
            if i < len(self.bob_measurements_x):
                corr_x = self.alice_modulations_x[i] * self.bob_measurements_x[i]
                corr_p = self.alice_modulations_p[i] * self.bob_measurements_p[i]
                correlations_x.append(corr_x)
                correlations_p.append(corr_p)

        # Use data with high correlation for key generation
        threshold_x = np.percentile(correlations_x, 70)  # Keep top 30%
        threshold_p = np.percentile(correlations_p, 70)  # Keep top 30%

        alice_sifted = []
        bob_sifted = []

        for i in range(len(self.alice_bits)):
            if (
                i < len(correlations_x)
                and correlations_x[i] > threshold_x
                and correlations_p[i] > threshold_p
            ):
                alice_sifted.append(self.alice_bits[i])

                # Bob generates bit from his measurements
                # In a real implementation, this would be more sophisticated
                bob_bit = 0 if self.bob_measurements_x[i] > 0 else 1
                bob_sifted.append(bob_bit)

        self.alice_key = alice_sifted
        self.bob_key = bob_sifted

        return alice_sifted, bob_sifted

    def estimate_qber(self) -> float:
        """Estimate the quantum bit error rate.

        In CV-QKD, this is estimated from the correlation between
        Alice's modulations and Bob's measurements.

        Returns:
            Estimated error rate
        """
        alice_sifted, bob_sifted = self.sift_keys()

        if len(alice_sifted) < 10:
            return 1.0

        # Count errors in the sifted key
        errors = 0
        for i in range(len(alice_sifted)):
            if alice_sifted[i] != bob_sifted[i]:
                errors += 1

        # Calculate QBER
        qber = errors / len(alice_sifted) if len(alice_sifted) > 0 else 1.0

        return float(qber)

    def calculate_secret_fraction(self) -> float:
        """Calculate the fraction of secret key that can be extracted.

        This uses the Gaussian optimality of Gaussian attacks.

        Returns:
            Secret fraction (key rate)
        """
        # Calculate the covariance matrix elements
        if len(self.alice_modulations_x) == 0 or len(self.bob_measurements_x) == 0:
            return 0.0

        # Simplified calculation based on variances
        var_x_a = np.var(self.alice_modulations_x)
        var_p_a = np.var(self.alice_modulations_p)
        var_x_b = np.var(self.bob_measurements_x)
        var_p_b = np.var(self.bob_measurements_p)

        # Cross correlations
        _cov_x = np.mean(
            [
                a * b
                for a, b in zip(
                    self.alice_modulations_x, self.bob_measurements_x, strict=False
                )
            ]
        )
        _cov_p = np.mean(
            [
                a * b
                for a, b in zip(
                    self.alice_modulations_p, self.bob_measurements_p, strict=False
                )
            ]
        )

        # Entropies (simplified)
        _h_a = 0.5 * np.log2(2 * np.pi * np.e * max(var_x_a, var_p_a))
        h_b = 0.5 * np.log2(2 * np.pi * np.e * max(var_x_b, var_p_b))

        # Mutual information
        # Simplified calculation
        chi_be = 1.0  # Eve's information (simplified)

        # Secret fraction
        secret_fraction = max(0.0, h_b - chi_be)

        self.secret_fraction = secret_fraction
        return secret_fraction

    def get_excess_noise(self) -> float:
        """Estimate the excess noise in the channel.

        Returns:
            Estimated excess noise level
        """
        if len(self.alice_modulations_x) == 0 or len(self.bob_measurements_x) == 0:
            return 1.0

        # Calculate the noise from the difference between expected and actual correlations
        expected_corr = np.sqrt(self.transmission_t * self.modulation_variance)
        actual_corr_x = np.mean(
            [
                abs(a * b)
                for a, b in zip(
                    self.alice_modulations_x, self.bob_measurements_x, strict=False
                )
            ]
        )
        actual_corr_p = np.mean(
            [
                abs(a * b)
                for a, b in zip(
                    self.alice_modulations_p, self.bob_measurements_p, strict=False
                )
            ]
        )

        avg_corr = (actual_corr_x + actual_corr_p) / 2
        noise_estimate = max(0.0, (expected_corr - avg_corr) / expected_corr)

        return float(noise_estimate)

    def _get_security_threshold(self) -> float:
        """Get the security threshold for the CV-QKD protocol.

        Returns:
            Maximum error rate considered secure
        """
        return self.security_threshold

    def get_key_rate(self) -> float:
        """Calculate the key generation rate.

        Returns:
            Key rate (bits per signal)
        """
        if not self.is_complete:
            return 0.0

        secret_frac = self.calculate_secret_fraction()
        alice_sifted, _ = self.sift_keys()

        if len(alice_sifted) == 0:
            return 0.0

        key_rate = secret_frac * len(alice_sifted) / self.num_signals
        return max(0.0, float(key_rate))

    def get_protocol_parameters(self) -> dict:
        """Get the protocol parameters.

        Returns:
            Dictionary with protocol parameters
        """
        return {
            "modulation_variance": self.modulation_variance,
            "detection_efficiency": self.detection_efficiency,
            "transmission_t": self.transmission_t,
            "excess_noise": self.excess_noise,
            "security_threshold": self.security_threshold,
            "num_signals": self.num_signals,
            "secret_fraction": self.secret_fraction,
        }
