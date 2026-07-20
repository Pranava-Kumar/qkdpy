"""Secret key rate calculations for QKD protocols.

This module computes the asymptotic secret key rate for various QKD protocols
under different channel conditions. The secret key rate is the fundamental
metric for comparing QKD protocols and optimizing system parameters.

The key rate formulas are based on information-theoretic security proofs:
- BB84: Shor-Preskill bound (2000)
- Decoy-state BB84: God-Lütkenhaus analysis (2002)
- E91: Entanglement-based protocol
- SARG04: Modified BB84 with improved photon-number resistance

Example:
    >>> from qkdpy.protocols import SecretKeyRate
    >>> rate = SecretKeyRate.bb84(
    ...     distance_km=50,
    ...     channel_loss_db_km=0.2,
    ...     detector_efficiency=0.6,
    ...     dark_count_prob=1e-6,
    ... )
    >>> print(f"Key rate: {rate:.2e} bits/pulse")
"""

from __future__ import annotations

from dataclasses import dataclass
from math import exp, log2
from typing import Any


@dataclass
class ChannelParameters:
    """Physical channel and detector parameters.

    Attributes:
        distance_km: Fiber distance in kilometers.
        channel_loss_db_km: Fiber attenuation in dB/km (typical: 0.2 for SMF at 1550nm).
        detector_efficiency: Detector quantum efficiency η ∈ [0, 1].
        dark_count_prob: Probability of dark count per pulse.
        misalignment_error: Optical misalignment error (typically 0.01-0.05).
        internal_loss: Internal optical loss (0 = perfect, 1 = total loss).
    """

    distance_km: float
    channel_loss_db_km: float = 0.2
    detector_efficiency: float = 0.6
    dark_count_prob: float = 1e-6
    misalignment_error: float = 0.03
    internal_loss: float = 0.0

    @property
    def transmittance(self) -> float:
        """Channel transmittance T = 10^(-αL/10).

        Returns:
            Transmittance in [0, 1].
        """
        return 10 ** (-self.channel_loss_db_km * self.distance_km / 10)

    @property
    def total_efficiency(self) -> float:
        """Overall system efficiency η_total = η_det × T × (1 - loss_int).

        Returns:
            Total efficiency in [0, 1].
        """
        return self.detector_efficiency * self.transmittance * (1 - self.internal_loss)

    @property
    def qber(self) -> float:
        """Quantum bit error rate (QBER) estimate.

        The QBER is dominated by:
        1. Misalignment errors (deterministic)
        2. Dark counts (stochastic, depends on signal strength)

        For a rough estimate, we use:
            e ≈ e_misalign + e_dark

        where e_dark = p_dark / (2 × η_total) for weak signals.

        Returns:
            Estimated QBER in [0, 1].
        """
        e_misalign = self.misalignment_error
        # Dark count contribution (simplified)
        if self.total_efficiency > 0:
            e_dark = self.dark_count_prob / (2 * self.total_efficiency)
        else:
            e_dark = 0.5  # Maximum error if no signal
        return min(e_misalign + e_dark, 0.5)


@dataclass
class DecoyStateParameters(ChannelParameters):
    """Extended parameters for decoy-state protocols.

    Attributes:
        mean_photon_number: Mean photon number μ of the signal state.
        decoy_intensity: Mean photon number ν of the decoy state (ν < μ).
        fraction_signal: Fraction of pulses sent as signal (1 - fraction_decoy).
        fraction_decoy: Fraction of pulses sent as decoy.
    """

    mean_photon_number: float = 0.5
    decoy_intensity: float = 0.1
    fraction_signal: float = 0.5
    fraction_decoy: float = 0.5


class SecretKeyRate:
    """Compute secret key rates for QKD protocols."""

    @staticmethod
    def _binary_entropy(x: float) -> float:
        """Binary entropy function h(x) = -x log₂(x) - (1-x) log₂(1-x).

        Args:
            x: Value in [0, 1].

        Returns:
            Binary entropy in bits.
        """
        if x <= 0 or x >= 1:
            return 0.0
        return -x * log2(x) - (1 - x) * log2(1 - x)

    @staticmethod
    def bb84(params: ChannelParameters | None = None, **kwargs: Any) -> float:
        """Compute secret key rate for BB84 protocol.

        The asymptotic key rate for BB84 is:
            R = q × [1 - 2 × h(e)]

        where:
        - q = 1/2 (basis reconciliation efficiency for BB84)
        - e = QBER
        - h(e) = binary entropy

        This is the Shor-Preskill bound (2000).

        Args:
            params: Channel parameters (or None to use kwargs).
            **kwargs: Channel parameters (used if params is None).

        Returns:
            Secret key rate in bits per pulse.
        """
        if params is None:
            params = ChannelParameters(**kwargs)

        e = params.qber
        eta = params.total_efficiency

        # Basis reconciliation efficiency (BB84 uses 2 bases, so q = 1/2)
        q = 0.5

        # Secret key rate formula
        if e >= 0.11:  # BB84 security threshold
            return 0.0

        h_e = SecretKeyRate._binary_entropy(e)
        rate = q * eta * (1 - 2 * h_e)

        return max(0.0, rate)

    @staticmethod
    def decoy_bb84(params: DecoyStateParameters | None = None, **kwargs: Any) -> float:
        """Compute secret key rate for decoy-state BB84.

        Decoy-state protocols use multiple intensity levels to detect
        photon-number-splitting (PNS) attacks. The key rate is:

            R = q × {P_1 × [1 - h(e_1)] - P_signal × f(e) × h(e)}

        where:
        - P_1 = probability of single-photon pulse
        - e_1 = error rate of single-photon component
        - P_signal = probability of signal pulse
        - f(e) = error correction efficiency (typically 1.16)
        - e = overall QBER

        This is the God-Lütkenhaus analysis (2002).

        Args:
            params: Decoy-state parameters (or None to use kwargs).
            **kwargs: Decoy-state parameters (used if params is None).

        Returns:
            Secret key rate in bits per pulse.
        """
        if params is None:
            params = DecoyStateParameters(**kwargs)

        mu = params.mean_photon_number
        eta = params.total_efficiency
        e = params.qber
        p_signal = params.fraction_signal

        # Photon number distribution (Poisson)
        p_1 = mu * exp(-mu)
        p_2 = (mu**2 / 2) * exp(-mu)

        # Single-photon yield (lower bound)
        # Using simplified decoy-state analysis
        y_1_lower = max(0, eta - p_2 * eta**2 / p_1)

        # Single-photon error rate (upper bound)
        e_1_upper = min(0.5, (e * eta - p_2 * eta**2 * 0.5 / p_1) / (y_1_lower * p_1))

        # Error correction efficiency (Shannon limit is 1.0, practical is ~1.16)
        f_ec = 1.16

        # Key rate
        if e >= 0.11:  # Security threshold
            return 0.0

        h_e = SecretKeyRate._binary_entropy(e)
        h_e1 = SecretKeyRate._binary_entropy(e_1_upper)

        # Secret key rate per pulse
        rate = p_signal * (p_1 * y_1_lower * (1 - h_e1) - eta * f_ec * h_e)

        return max(0.0, rate)

    @staticmethod
    def e91(params: ChannelParameters | None = None, **kwargs: Any) -> float:
        """Compute secret key rate for E91 (entanglement-based) protocol.

        The E91 protocol uses entangled photon pairs. The key rate is:

            R = q × [1 - h(e)]

        where:
        - q = 1/4 (E91 uses 3 bases for Alice and Bob)
        - e = QBER

        The security threshold for E91 is higher than BB84 due to the
        additional basis choices.

        Args:
            params: Channel parameters (or None to use kwargs).
            **kwargs: Channel parameters (used if params is None).

        Returns:
            Secret key rate in bits per pulse.
        """
        if params is None:
            params = ChannelParameters(**kwargs)

        e = params.qber
        eta = params.total_efficiency

        # Basis reconciliation efficiency (E91 uses 3 bases each, so q = 1/4)
        q = 0.25

        # Security threshold for E91 is ~7.1%
        if e >= 0.071:
            return 0.0

        h_e = SecretKeyRate._binary_entropy(e)
        rate = q * eta * (1 - h_e)

        return max(0.0, rate)

    @staticmethod
    def sarg04(params: ChannelParameters | None = None, **kwargs: Any) -> float:
        """Compute secret key rate for SARG04 protocol.

        SARG04 is a variant of BB84 that uses different state preparation.
        It has better resistance to photon-number-splitting attacks.

        The key rate is similar to BB84 but with different security threshold:

            R = q × [1 - h(e)]

        where:
        - q = 1/2 (same as BB84)
        - e = QBER

        The security threshold for SARG04 is ~14.6% (higher than BB84's 11%).

        Args:
            params: Channel parameters (or None to use kwargs).
            **kwargs: Channel parameters (used if params is None).

        Returns:
            Secret key rate in bits per pulse.
        """
        if params is None:
            params = ChannelParameters(**kwargs)

        e = params.qber
        eta = params.total_efficiency

        q = 0.5

        # Security threshold for SARG04 is ~14.6%
        if e >= 0.146:
            return 0.0

        h_e = SecretKeyRate._binary_entropy(e)
        rate = q * eta * (1 - h_e)

        return max(0.0, rate)

    @staticmethod
    def max_distance(
        protocol: str = "bb84",
        channel_loss_db_km: float = 0.2,
        detector_efficiency: float = 0.6,
        dark_count_prob: float = 1e-6,
        misalignment_error: float = 0.03,
        threshold_rate: float = 1e-10,
        **kwargs: Any,
    ) -> float:
        """Find maximum secure distance for a given protocol.

        Uses binary search to find the distance at which the key rate
        drops below a threshold.

        Args:
            protocol: Protocol name ("bb84", "decoy_bb84", "e91", "sarg04").
            channel_loss_db_km: Fiber attenuation in dB/km.
            detector_efficiency: Detector efficiency.
            dark_count_prob: Dark count probability.
            misalignment_error: Misalignment error.
            threshold_rate: Minimum acceptable key rate (default: 1e-10).
            **kwargs: Additional parameters for decoy-state protocols.

        Returns:
            Maximum distance in km.
        """
        # Binary search for max distance
        d_min = 0.0
        d_max = 500.0  # km
        tolerance = 0.1  # km

        while d_max - d_min > tolerance:
            d_mid = (d_min + d_max) / 2

            params = ChannelParameters(
                distance_km=d_mid,
                channel_loss_db_km=channel_loss_db_km,
                detector_efficiency=detector_efficiency,
                dark_count_prob=dark_count_prob,
                misalignment_error=misalignment_error,
            )

            if protocol == "bb84":
                rate = SecretKeyRate.bb84(params)
            elif protocol == "decoy_bb84":
                decoy_params = DecoyStateParameters(
                    distance_km=d_mid,
                    channel_loss_db_km=channel_loss_db_km,
                    detector_efficiency=detector_efficiency,
                    dark_count_prob=dark_count_prob,
                    misalignment_error=misalignment_error,
                    **kwargs,
                )
                rate = SecretKeyRate.decoy_bb84(decoy_params)
            elif protocol == "e91":
                rate = SecretKeyRate.e91(params)
            elif protocol == "sarg04":
                rate = SecretKeyRate.sarg04(params)
            else:
                raise ValueError(f"Unknown protocol: {protocol}")

            if rate > threshold_rate:
                d_min = d_mid
            else:
                d_max = d_mid

        return d_min
