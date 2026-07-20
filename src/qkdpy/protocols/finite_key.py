"""Finite-key security analysis for QKD protocols.

Real QKD operates on finite blocks (10⁶–10⁹ pulses), not asymptotic limits.
The security proof changes — you need composable security with explicit
failure probability ε.

This module implements finite-key analysis for BB84 and related protocols,
providing:
- Secure key length calculation with finite-size effects
- Privacy amplification overhead estimation
- Security parameter tuning
- Composable security framework

References:
- Tomamichel et al., "The Finite Blocklength Regime for QKD" (2012)
- Leverrier et al., "Finite-size analysis of continuous-variable QKD" (2013)
- Scarani et al., "The security of practical QKD" (2009)
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class FiniteKeyParameters:
    """Parameters for finite-key security analysis.

    Attributes:
        n_pulses: Total number of transmitted pulses.
        observed_qber: Observed quantum bit error rate.
        security_parameter: Desired security parameter ε (failure probability).
        protocol: Protocol name ("BB84", "E91", "SARG04", etc.).
        basis_efficiency: Basis reconciliation efficiency (0.5 for BB84).
        error_correction_efficiency: Error correction efficiency f (typically 1.16).
        smooth_min_entropy_rate: Smooth min-entropy rate (optional, computed if None).
    """

    n_pulses: int
    observed_qber: float
    security_parameter: float = 1e-10
    protocol: str = "BB84"
    basis_efficiency: float = 0.5
    error_correction_efficiency: float = 1.16
    smooth_min_entropy_rate: float | None = None


class FiniteKeyAnalysis:
    """Finite-key security analysis for QKD protocols."""

    @staticmethod
    def _binary_entropy(x: float) -> float:
        """Binary entropy function h(x) = -x log₂(x) - (1-x) log₂(1-x)."""
        if x <= 0 or x >= 1:
            return 0.0
        return -x * math.log2(x) - (1 - x) * math.log2(1 - x)

    @staticmethod
    def _devetak_winter_rate(qber: float, protocol: str) -> float:
        """Compute asymptotic Devetak-Winter key rate.

        Args:
            qber: Quantum bit error rate.
            protocol: Protocol name.

        Returns:
            Asymptotic key rate in bits per pulse.
        """
        if protocol == "BB84":
            # BB84: R = q * (1 - 2*h(e))
            q = 0.5  # Basis efficiency
            h_e = FiniteKeyAnalysis._binary_entropy(qber)
            return q * (1 - 2 * h_e)
        elif protocol == "E91":
            # E91: R = q * (1 - h(e))
            q = 0.25  # Basis efficiency (3 bases each)
            h_e = FiniteKeyAnalysis._binary_entropy(qber)
            return q * (1 - h_e)
        elif protocol == "SARG04":
            # SARG04: Similar to BB84 but with different threshold
            q = 0.5
            h_e = FiniteKeyAnalysis._binary_entropy(qber)
            return q * (1 - h_e)
        else:
            raise ValueError(f"Unknown protocol: {protocol}")

    @staticmethod
    def _smooth_min_entropy_rate(
        qber: float,
        n_pulses: int,
        security_parameter: float,
        protocol: str,
    ) -> float:
        """Compute smooth min-entropy rate with finite-size corrections.

        The smooth min-entropy accounts for statistical fluctuations in
        finite samples. For BB84:

            H_min^ε ≈ 1 - 2*h(e + Δ)

        where Δ is the statistical deviation:

            Δ = sqrt((2 * log(1/ε) + log(2/ε)) / (n * q))

        Args:
            qber: Observed QBER.
            n_pulses: Number of pulses.
            security_parameter: Security parameter ε.
            protocol: Protocol name.

        Returns:
            Smooth min-entropy rate.
        """
        if protocol == "BB84":
            q = 0.5  # Basis efficiency

            # Statistical deviation (finite-size effect)
            log_eps = math.log(1 / security_parameter)
            delta = math.sqrt((2 * log_eps + math.log(2 / security_parameter)) / (n_pulses * q))

            # Deviation-corrected QBER
            qber_dev = min(qber + delta, 0.5)

            # Smooth min-entropy rate
            h_e = FiniteKeyAnalysis._binary_entropy(qber_dev)
            return 1 - 2 * h_e
        else:
            # For other protocols, use similar approach
            log_eps = math.log(1 / security_parameter)
            delta = math.sqrt((2 * log_eps) / n_pulses)
            qber_dev = min(qber + delta, 0.5)
            h_e = FiniteKeyAnalysis._binary_entropy(qber_dev)
            return 1 - h_e

    @staticmethod
    def key_length(params: FiniteKeyParameters | None = None, **kwargs) -> int:
        """Compute secure key length with finite-size effects.

        The secure key length is:

            ℓ = n * q * (H_min^ε - f * h(e)) - 2 * log(1/ε)

        where:
        - n: number of pulses
        - q: basis efficiency
        - H_min^ε: smooth min-entropy rate
        - f: error correction efficiency
        - h(e): binary entropy of QBER
        - ε: security parameter

        Args:
            params: Finite-key parameters (or None to use kwargs).
            **kwargs: Parameters (used if params is None).

        Returns:
            Secure key length in bits.
        """
        if params is None:
            params = FiniteKeyParameters(**kwargs)

        n = params.n_pulses
        e = params.observed_qber
        eps = params.security_parameter
        q = params.basis_efficiency
        f = params.error_correction_efficiency

        # Edge case: zero pulses
        if n == 0:
            return 0

        # Compute smooth min-entropy rate
        if params.smooth_min_entropy_rate is not None:
            h_min = params.smooth_min_entropy_rate
        else:
            h_min = FiniteKeyAnalysis._smooth_min_entropy_rate(
                e, n, eps, params.protocol
            )

        # Error correction overhead
        h_e = FiniteKeyAnalysis._binary_entropy(e)

        # Key length formula
        key_length = n * q * (h_min - f * h_e) - 2 * math.log(1 / eps)

        return max(0, int(key_length))

    @staticmethod
    def pa_overhead(params: FiniteKeyParameters | None = None, **kwargs) -> float:
        """Compute privacy amplification overhead.

        The overhead is the fraction of the raw key consumed by privacy
        amplification to remove Eve's information.

        Args:
            params: Finite-key parameters (or None to use kwargs).
            **kwargs: Parameters (used if params is None).

        Returns:
            Privacy amplification overhead as a fraction in [0, 1].
        """
        if params is None:
            params = FiniteKeyParameters(**kwargs)

        raw_key_length = int(params.n_pulses * params.basis_efficiency)
        secure_key_length = FiniteKeyAnalysis.key_length(params)

        if raw_key_length == 0:
            return 1.0

        return 1 - secure_key_length / raw_key_length

    @staticmethod
    def max_secure_distance(
        protocol: str = "BB84",
        n_pulses: int = 10**8,
        security_parameter: float = 1e-10,
        channel_loss_db_km: float = 0.2,
        detector_efficiency: float = 0.6,
        dark_count_prob: float = 1e-6,
        misalignment_error: float = 0.03,
        threshold_key_length: int = 1,
    ) -> float:
        """Find maximum distance for finite-key secure communication.

        Uses binary search to find the distance at which the secure key
        length drops below a threshold.

        Args:
            protocol: Protocol name.
            n_pulses: Number of pulses.
            security_parameter: Security parameter ε.
            channel_loss_db_km: Fiber attenuation in dB/km.
            detector_efficiency: Detector efficiency.
            dark_count_prob: Dark count probability.
            misalignment_error: Misalignment error.
            threshold_key_length: Minimum acceptable key length.

        Returns:
            Maximum distance in km.
        """
        from .key_rate import ChannelParameters

        # Binary search for max distance
        d_min = 0.0
        d_max = 500.0  # km
        tolerance = 0.1  # km

        while d_max - d_min > tolerance:
            d_mid = (d_min + d_max) / 2

            # Compute QBER at this distance
            channel_params = ChannelParameters(
                distance_km=d_mid,
                channel_loss_db_km=channel_loss_db_km,
                detector_efficiency=detector_efficiency,
                dark_count_prob=dark_count_prob,
                misalignment_error=misalignment_error,
            )

            qber = channel_params.qber

            # Compute finite-key secure key length
            finite_params = FiniteKeyParameters(
                n_pulses=n_pulses,
                observed_qber=qber,
                security_parameter=security_parameter,
                protocol=protocol,
            )

            key_length = FiniteKeyAnalysis.key_length(finite_params)

            if key_length >= threshold_key_length:
                d_min = d_mid
            else:
                d_max = d_mid

        return d_min

    @staticmethod
    def compare_asymptotic_vs_finite(
        params: FiniteKeyParameters | None = None, **kwargs
    ) -> dict[str, float]:
        """Compare asymptotic and finite-key secure key lengths.

        Args:
            params: Finite-key parameters (or None to use kwargs).
            **kwargs: Parameters (used if params is None).

        Returns:
            Dictionary with:
            - 'asymptotic': asymptotic key length (bits)
            - 'finite': finite-key length (bits)
            - 'ratio': finite / asymptotic ratio
            - 'overhead': finite-size overhead (fraction)
        """
        if params is None:
            params = FiniteKeyParameters(**kwargs)

        # Asymptotic key length
        asymptotic_rate = FiniteKeyAnalysis._devetak_winter_rate(
            params.observed_qber, params.protocol
        )
        asymptotic_length = int(
            params.n_pulses * params.basis_efficiency * asymptotic_rate
        )

        # Finite-key length
        finite_length = FiniteKeyAnalysis.key_length(params)

        # Comparison
        ratio = finite_length / asymptotic_length if asymptotic_length > 0 else 0
        overhead = 1 - ratio

        return {
            "asymptotic": asymptotic_length,
            "finite": finite_length,
            "ratio": ratio,
            "overhead": overhead,
        }
