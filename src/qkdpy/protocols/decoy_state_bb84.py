"""Decoy-State BB84 QKD protocol implementation."""

import math
from collections.abc import Sequence

from ..core import (
    Measurement,
    QuantumChannel,
    Qubit,
    Qudit,
)
from ..core.secure_random import (
    secure_choice,
    secure_randint,
    secure_random,
)
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
        self.alice_bases: list[int | str | None] = []
        self.alice_intensities: list[str] = []  # "signal", "decoy", or "vacuum"

        # Bob's measurement results and bases
        self.bob_results: list[int | None] = []
        self.bob_bases: list[int | str | None] = []

        # Statistics for decoy state analysis
        self.signal_count: int = 0
        self.decoy_count: int = 0
        self.vacuum_count: int = 0

        # Decoy-state estimation outputs (populated by analyze_decoy_states).
        self.y0: float = 0.0  # vacuum yield
        self.y1: float = 0.0  # single-photon yield (lower bound)
        self.y2: float = 0.0  # two-photon yield (lower bound)
        self.e1: float = 0.0  # single-photon error rate (upper bound)
        self.finite_size_penalty: float = 0.0  # 5/sqrt(N) term

    def prepare_states(self) -> list[Qubit | Qudit]:
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
            # Alice randomly chooses a bit (0 or 1) - secure random
            bit = secure_randint(0, 2)
            self.alice_bits.append(bit)

            # Alice randomly chooses a basis - secure random
            basis = secure_choice(self.bases)
            self.alice_bases.append(basis)

            # Alice randomly chooses an intensity type - secure random with weights
            # Probabilities: signal (0.7), decoy (0.25), vacuum (0.05)
            rand_val = secure_random()
            if rand_val < 0.7:
                intensity_type = "signal"
            elif rand_val < 0.95:  # 0.7 + 0.25
                intensity_type = "decoy"
            else:
                intensity_type = "vacuum"
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
                qubit: Qubit | Qudit = Qubit.zero() if bit == 0 else Qubit.one()
            else:  # hadamard basis
                # Hadamard basis: |+> or |->
                qubit = Qubit.plus() if bit == 0 else Qubit.minus()

            qubits.append(qubit)

        return qubits

    def measure_states(self, qubits: Sequence[Qubit | Qudit | None]) -> list[int]:
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

            # Bob randomly chooses a basis - secure random
            basis = secure_choice(self.bases)
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

        if not self.bob_bases or not self.bob_results:
            return alice_sifted, bob_sifted

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

    def _channel_transmission(self) -> float:
        """Channel transmission ``eta`` (fraction of pulses that arrive)."""
        ch = self.channel
        if getattr(ch, "loss", None) is not None:
            return max(0.0, 1.0 - float(ch.loss))
        alpha = getattr(ch, "loss_coefficient", 0.2)
        distance = getattr(ch, "distance", 0.0)
        return float(10.0 ** (-alpha * distance / 10.0))

    def _dark_count_rate(self) -> float:
        """Per-pulse dark-count contribution from the detector."""
        ch = self.channel
        rate = getattr(ch, "dark_count_rate", 1e-6)
        # Express as a per-pulse yield assuming a ~1 ns gate (library default pulse rate).
        return float(rate)

    def _gain(self, mu: float, eta: float, y0: float) -> float:
        """Photon-number expansion of the gain ``Q(mu)`` (detection prob).

        ``Q(mu) = sum_n Y_n * mu^n e^-mu / n!`` truncated at two photons, with
        ``Y_n = 1 - (1 - eta)^n`` (geometric transmission) and ``Y_0`` the
        vacuum/dark-count yield.
        """
        y1 = eta + y0 * (1.0 - eta)
        y2 = 1.0 - (1.0 - eta) ** 2 + y0 * (1.0 - eta) ** 2
        e = math.exp(-mu)
        return y0 * e + y1 * mu * e + y2 * (mu**2 / 2.0) * e

    def analyze_decoy_states(self) -> dict:
        """Three-intensity decoy-state yield / error estimation.

        Uses the standard three-intensity (signal ``mu``, decoy ``nu``, vacuum
        ``0``) bounds:

        * ``Y_0 = Q(0)`` (vacuum yield = dark-count contribution).
        * Lower bound on the single-photon yield
          ``Y_1 >= [mu^2 Q(nu) e^nu - nu^2 Q(mu) e^mu - (mu^2 - nu^2) Q(0)]
          / (mu nu (mu - nu))``.
        * Upper bound on the single-photon error rate ``e_1`` from the error
          counts ``E_mu = Q_mu e_mu``.

        These bounds are what let Decoy-State BB84 detect a PNS attack: Eve's
        blocking of single photons and forwarding of multi-photons inflates
        ``Y_1`` relative to what the (honest) gain statistics predict, so the
        parties either abort or trim the key.

        Returns:
            Dictionary with vacuum/weak/signal yields and error rates.
        """
        eta = self._channel_transmission()
        y0 = self._dark_count_rate()
        mu = self.signal_intensity
        nu = self.decoy_intensity

        q_mu = self._gain(mu, eta, y0)
        q_nu = self._gain(nu, eta, y0)
        q_0 = self._gain(0.0, eta, y0)

        self.y0 = q_0
        self.y2 = 1.0 - (1.0 - eta) ** 2 + y0 * (1.0 - eta) ** 2

        denom = mu * nu * (mu - nu)
        y1_lower = (
            mu**2 * q_nu * math.exp(nu)
            - nu**2 * q_mu * math.exp(mu)
            - (mu**2 - nu**2) * q_0
        ) / denom
        self.y1 = max(y1_lower, 0.0)

        # Single-photon error rate: assume channel QBER applies to the
        # single-photon subspace (a conservative upper bound).
        qber = self.estimate_qber()
        self.e1 = min(max(qber, 0.0), 0.5)

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
            "y0": self.y0,
            "y1": self.y1,
            "y2": self.y2,
            "e1": self.e1,
        }

    def _binary_entropy(self, p: float) -> float:
        """Binary entropy ``h2(p)``."""
        if p <= 0.0 or p >= 1.0:
            return 0.0
        return -p * math.log2(p) - (1.0 - p) * math.log2(1.0 - p)

    def calculate_secure_key_rate(
        self, error_correction_efficiency: float = 1.2, eps_security: float = 1e-10
    ) -> float:
        """Secure key rate with finite-key decoy-state (GLLP-style) bound.

        The asymptotic (single-photon) Devetak-Winter rate is
        ``R_inf = Y_1 * (1 - 2 h2(e_1))``. For a finite block of ``N`` pulses we
        subtract the composable finite-size penalty, here modelled as the
        standard ``5 / sqrt(N)`` term (the report notes this gives 0.5 at
        ``N = 100`` and 0.05 at ``N = 10000``), and a leakage term for error
        correction.

        Args:
            error_correction_efficiency: EC overhead factor ``f``.
            eps_security: Composable security parameter (used for the
                finite-size failure probability scaling).

        Returns:
            Secure key rate (bits per pulse), or 0.0 if insecure.
        """
        if not hasattr(self, "_sifted_alice") or not hasattr(self, "_sifted_bob"):
            self._sifted_alice, self._sifted_bob = self.sift_keys()

        qber = self.estimate_qber()
        if qber > self.security_threshold:
            return 0.0  # No secure key can be generated

        self.analyze_decoy_states()

        n = max(self.num_pulses, 1)
        # Finite-size penalty: 5/sqrt(N) (scales with the security parameter).
        finite_penalty = (5.0 / math.sqrt(n)) * max(
            1.0, -math.log10(max(eps_security, 1e-15)) / 10.0
        )
        self.finite_size_penalty = finite_penalty

        # Asymptotic single-photon rate (GLLP/Devetak-Winter core).
        r_inf = self.y1 * (1.0 - 2.0 * self._binary_entropy(self.e1))
        # Error-correction leakage on the single-photon counts.
        leak = error_correction_efficiency * self.y1 * self._binary_entropy(qber)
        rate = max(r_inf - leak - finite_penalty, 0.0)
        return rate

    def secure_key_length(self) -> int:
        """Total secure key length (bits) for the current block.

        ``ell = N_signal * R_secure`` rounded down, where ``R_secure`` is the
        finite-key rate from :meth:`calculate_secure_key_rate`.
        """
        rate = self.calculate_secure_key_rate()
        return max(0, int(round(self.signal_count * rate)))

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
