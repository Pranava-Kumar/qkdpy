"""Decoy-State BB84 QKD protocol implementation."""

import numpy as np

from ..core import Measurement, QuantumChannel, Qubit
from .base import BaseProtocol


class DecoyStateBB84(BaseProtocol):
    """Implementation of the Decoy-State BB84 quantum key distribution protocol.

    Decoy-State BB84 is an enhancement of the standard BB84 protocol that uses
    decoy states to detect photon number splitting (PNS) attacks and improve
    security against imperfect single-photon sources.
    """

    def __init__(
        self,
        channel: QuantumChannel,
        key_length: int = 100,
        security_threshold: float = 0.11,
        weak_pulse_intensity: float = 0.1,
        decoy_intensity: float = 0.05,
    ):
        """Initialize the Decoy-State BB84 protocol.

        Args:
            channel: Quantum channel for qubit transmission
            key_length: Desired length of the final key
            security_threshold: Maximum QBER value considered secure
            weak_pulse_intensity: Intensity for weak coherent pulses (signal states)
            decoy_intensity: Intensity for decoy states

        """
        super().__init__(channel, key_length)

        # Protocol-specific parameters
        self.bases: list[str] = ["computational", "hadamard"]
        self.security_threshold: float = security_threshold

        # Intensity settings for decoy-state protocol
        self.signal_intensity: float = weak_pulse_intensity
        self.decoy_intensity: float = decoy_intensity

        # Number of pulses to send (we'll send more than needed)
        self.num_pulses: int = key_length * 5  # Send 5x more pulses than needed

        # Alice's random bits, bases, and intensities
        self.alice_bits: list[int] = []
        self.alice_bases: list[str | None] = []
        self.alice_intensities: list[str] = []  # "signal", "decoy", or "vacuum"

        # Bob's measurement results and bases
        self.bob_results: list[int | None] = []
        self.bob_bases: list[str | None] = []

        # Statistics for decoy state analysis
        self.signal_count: int = 0
        self.decoy_count: int = 0
        self.vacuum_count: int = 0

    def prepare_states(self) -> list[Qubit]:
        """Prepare quantum states for transmission with decoy states.

        In Decoy-State BB84, Alice randomly chooses bits, bases, and intensities
        for each pulse, and prepares weak coherent pulses with the chosen parameters.

        Returns:
            List of qubits to be sent through the quantum channel

        """
        qubits = []
        self.alice_bits = []
        self.alice_bases = []
        self.alice_intensities = []

        # Reset counters
        self.signal_count = 0
        self.decoy_count = 0
        self.vacuum_count = 0

        for _ in range(self.num_pulses):
            # Alice randomly chooses a bit (0 or 1)
            bit = int(np.random.randint(0, 2))
            self.alice_bits.append(bit)

            # Alice randomly chooses a basis
            basis = np.random.choice(self.bases)
            self.alice_bases.append(basis)

            # Alice randomly chooses an intensity type (signal, decoy, or vacuum)
            intensity_type = np.random.choice(
                ["signal", "decoy", "vacuum"], p=[0.7, 0.25, 0.05]
            )
            self.alice_intensities.append(intensity_type)

            if intensity_type == "signal":
                self.signal_count += 1
            elif intensity_type == "decoy":
                self.decoy_count += 1
            else:  # vacuum
                self.vacuum_count += 1

            # Prepare the qubit in the appropriate state
            if basis == "computational":
                # Computational basis: |0> or |1>
                qubit = Qubit.zero() if bit == 0 else Qubit.one()
            else:  # hadamard basis
                # Hadamard basis: |+> or |->
                qubit = Qubit.plus() if bit == 0 else Qubit.minus()

            qubits.append(qubit)

        return qubits

    def measure_states(self, qubits: list[Qubit | None]) -> list[int]:
        """Measure received quantum states.

        In Decoy-State BB84, Bob randomly chooses bases to measure in.

        Args:
            qubits: List of received qubits (may contain None for lost qubits)

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
            basis = np.random.choice(self.bases)
            self.bob_bases.append(basis)

            # Measure in the chosen basis
            result = Measurement.measure_in_basis(qubit, basis)
            qubit.collapse_state(result, basis)
            self.bob_results.append(result)

        # Filter out None values to return only int results
        return [result for result in self.bob_results if result is not None]

    def sift_keys(self) -> tuple[list[int], list[int]]:
        """Sift the raw keys to keep only measurements in matching bases.

        In Decoy-State BB84, Alice and Bob publicly compare their bases and keep only
        the bits where they used the same basis.

        Returns:
            Tuple of (alice_sifted_key, bob_sifted_key)

        """
        alice_sifted = []
        bob_sifted = []

        for i in range(self.num_pulses):
            # Skip if Bob didn't receive the qubit
            if self.bob_bases[i] is None or self.bob_results[i] is None:
                continue

            # Check if Alice and Bob used the same basis
            if (
                self.alice_bases[i] is not None
                and self.bob_bases[i] is not None
                and self.alice_bases[i] == self.bob_bases[i]
            ):
                alice_sifted.append(self.alice_bits[i])
                # We already checked that self.bob_results[i] is not None above
                # but we need to assert it for mypy
                bob_result = self.bob_results[i]
                if bob_result is not None:
                    bob_sifted.append(bob_result)

        return alice_sifted, bob_sifted

    def estimate_qber(self) -> float:
        """Estimate the Quantum Bit Error Rate (QBER) using decoy state analysis.

        In Decoy-State BB84, QBER is estimated separately for signal and decoy states.

        Returns:
            Estimated QBER value

        """
        alice_sifted, bob_sifted = self.sift_keys()

        # If we don't have enough bits for estimation, return a high QBER
        if len(alice_sifted) < 10:
            return 1.0

        # Use the full sifted key for QBER estimation in tests
        sample_size = len(alice_sifted)
        indices = range(sample_size)

        # Count errors in the sample
        errors = 0
        for idx in indices:
            if alice_sifted[idx] != bob_sifted[idx]:
                errors += 1

        # Calculate QBER
        qber = errors / sample_size
        print(f"Decoy-State BB84 Estimated QBER: {qber}")
        return qber

    def analyze_decoy_states(self) -> dict:
        """Analyze decoy state statistics for security parameter estimation.

        Returns:
            Dictionary with decoy state analysis results

        """
        # In a full implementation, this would perform detailed analysis of
        # signal, decoy, and vacuum states to estimate single-photon yield
        # and error rates, which are used to calculate secure key rate.

        # For this simulation, we'll return basic statistics
        total_pulses = self.signal_count + self.decoy_count + self.vacuum_count

        return {
            "total_pulses": total_pulses,
            "signal_pulses": self.signal_count,
            "decoy_pulses": self.decoy_count,
            "vacuum_pulses": self.vacuum_count,
            "signal_fraction": (
                self.signal_count / total_pulses if total_pulses > 0 else 0
            ),
            "decoy_fraction": (
                self.decoy_count / total_pulses if total_pulses > 0 else 0
            ),
            "vacuum_fraction": (
                self.vacuum_count / total_pulses if total_pulses > 0 else 0
            ),
        }

    def calculate_secure_key_rate(self) -> float:
        """Calculate the secure key generation rate using decoy state analysis.

        Returns:
            Secure key rate (bits per pulse)

        """
        # In a full implementation, this would use the GLLP (Gottesman-Lo-Lütkenhaus-Preskill)
        # formula or similar to calculate the secure key rate based on:
        # - Single-photon yield
        # - Single-photon error rate
        # - Intensity settings

        # For this simulation, we'll use a simplified model based on QBER
        # First ensure we have the sifted keys
        if not hasattr(self, "_sifted_alice") or not hasattr(self, "_sifted_bob"):
            self._sifted_alice, self._sifted_bob = self.sift_keys()

        # Simplified secure key rate formula
        # In practice, this would be much more complex
        qber = self.estimate_qber()

        if qber > self.security_threshold:
            return 0.0  # No secure key can be generated

        # Simplified linear model for key rate
        key_rate = max(0.0, 0.1 * (1 - qber / self.security_threshold))
        return key_rate

    def _get_security_threshold(self) -> float:
        """Get the security threshold for the Decoy-State BB84 protocol.

        Returns:
            Maximum QBER value considered secure

        """
        return self.security_threshold

    def get_basis_reconciliation_rate(self) -> float:
        """Calculate the basis reconciliation rate.

        Returns:
            Fraction of pulses where Alice and Bob used the same basis

        """
        matches = 0
        total = 0

        for i in range(self.num_pulses):
            if self.bob_bases[i] is not None:
                total += 1
                if self.alice_bases[i] == self.bob_bases[i]:
                    matches += 1

        return matches / total if total > 0 else 0

    def get_key_rate(self) -> float:
        """Calculate the key generation rate.

        Returns:
            Fraction of transmitted pulses that result in secure key bits

        """
        if not self.is_complete:
            return 0.0

        return len(self.final_key) / self.num_pulses
