"""Tests for finite-key security analysis."""

import pytest

from qkdpy.protocols import (
    FiniteKeyAnalysis,
    FiniteKeyParameters,
)


class TestFiniteKeyParameters:
    """Test FiniteKeyParameters dataclass."""

    def test_init_defaults(self):
        """Test default parameter values."""
        params = FiniteKeyParameters(
            n_pulses=10**8,
            observed_qber=0.05,
        )
        assert params.security_parameter == 1e-10
        assert params.protocol == "BB84"
        assert params.basis_efficiency == 0.5
        assert params.error_correction_efficiency == 1.16
        assert params.smooth_min_entropy_rate is None

    def test_init_custom(self):
        """Test custom parameter values."""
        params = FiniteKeyParameters(
            n_pulses=10**9,
            observed_qber=0.03,
            security_parameter=1e-12,
            protocol="E91",
        )
        assert params.n_pulses == 10**9
        assert params.observed_qber == 0.03
        assert params.security_parameter == 1e-12
        assert params.protocol == "E91"


class TestFiniteKeyAnalysis:
    """Test FiniteKeyAnalysis class."""

    def test_key_length_short_distance(self):
        """Test key length at short distance with low QBER."""
        params = FiniteKeyParameters(
            n_pulses=10**8,
            observed_qber=0.01,
            security_parameter=1e-10,
        )
        key_len = FiniteKeyAnalysis.key_length(params)
        assert key_len > 0

    def test_key_length_high_qber(self):
        """Test that high QBER yields zero or very short key."""
        params = FiniteKeyParameters(
            n_pulses=10**8,
            observed_qber=0.15,  # Above BB84 threshold
            security_parameter=1e-10,
        )
        key_len = FiniteKeyAnalysis.key_length(params)
        # Should be very small or zero
        assert key_len < 1000

    def test_key_length_increases_with_pulses(self):
        """Test that more pulses yield longer key."""
        params_short = FiniteKeyParameters(
            n_pulses=10**6,
            observed_qber=0.05,
        )
        params_long = FiniteKeyParameters(
            n_pulses=10**8,
            observed_qber=0.05,
        )

        key_short = FiniteKeyAnalysis.key_length(params_short)
        key_long = FiniteKeyAnalysis.key_length(params_long)

        assert key_long > key_short

    def test_key_length_decreases_with_qber(self):
        """Test that higher QBER yields shorter key."""
        params_low = FiniteKeyParameters(
            n_pulses=10**8,
            observed_qber=0.02,
        )
        params_high = FiniteKeyParameters(
            n_pulses=10**8,
            observed_qber=0.08,
        )

        key_low = FiniteKeyAnalysis.key_length(params_low)
        key_high = FiniteKeyAnalysis.key_length(params_high)

        assert key_low > key_high

    def test_key_length_security_parameter(self):
        """Test that stricter security parameter yields shorter key."""
        params_relaxed = FiniteKeyParameters(
            n_pulses=10**8,
            observed_qber=0.05,
            security_parameter=1e-6,
        )
        params_strict = FiniteKeyParameters(
            n_pulses=10**8,
            observed_qber=0.05,
            security_parameter=1e-15,
        )

        key_relaxed = FiniteKeyAnalysis.key_length(params_relaxed)
        key_strict = FiniteKeyAnalysis.key_length(params_strict)

        assert key_relaxed > key_strict

    def test_pa_overhead_low_qber(self):
        """Test privacy amplification overhead at low QBER."""
        params = FiniteKeyParameters(
            n_pulses=10**8,
            observed_qber=0.01,
        )
        overhead = FiniteKeyAnalysis.pa_overhead(params)
        assert 0 <= overhead <= 1

    def test_pa_overhead_high_qber(self):
        """Test that overhead increases with QBER."""
        params_low = FiniteKeyParameters(
            n_pulses=10**8,
            observed_qber=0.02,
        )
        params_high = FiniteKeyParameters(
            n_pulses=10**8,
            observed_qber=0.08,
        )

        overhead_low = FiniteKeyAnalysis.pa_overhead(params_low)
        overhead_high = FiniteKeyAnalysis.pa_overhead(params_high)

        assert overhead_high > overhead_low

    def test_max_secure_distance_bb84(self):
        """Test maximum distance for BB84 with finite-key analysis."""
        max_dist = FiniteKeyAnalysis.max_secure_distance(
            protocol="BB84",
            n_pulses=10**8,
            security_parameter=1e-10,
            channel_loss_db_km=0.2,
            detector_efficiency=0.6,
            dark_count_prob=1e-6,
            misalignment_error=0.03,
        )
        # Should be reasonable distance
        assert 50 < max_dist < 300

    def test_max_secure_distance_increases_with_pulses(self):
        """Test that more pulses allow longer distance."""
        max_dist_short = FiniteKeyAnalysis.max_secure_distance(
            n_pulses=10**6,
            detector_efficiency=0.6,
        )
        max_dist_long = FiniteKeyAnalysis.max_secure_distance(
            n_pulses=10**9,
            detector_efficiency=0.6,
        )

        assert max_dist_long > max_dist_short

    def test_compare_asymptotic_vs_finite(self):
        """Test comparison between asymptotic and finite-key."""
        params = FiniteKeyParameters(
            n_pulses=10**8,
            observed_qber=0.05,
        )

        comparison = FiniteKeyAnalysis.compare_asymptotic_vs_finite(params)

        assert "asymptotic" in comparison
        assert "finite" in comparison
        assert "ratio" in comparison
        assert "overhead" in comparison

        # Finite should be less than or equal to asymptotic
        assert comparison["finite"] <= comparison["asymptotic"]

        # Ratio should be in [0, 1]
        assert 0 <= comparison["ratio"] <= 1

        # Overhead should be in [0, 1]
        assert 0 <= comparison["overhead"] <= 1

    def test_different_protocols(self):
        """Test key length for different protocols."""
        protocols = ["BB84", "E91", "SARG04"]

        for protocol in protocols:
            params = FiniteKeyParameters(
                n_pulses=10**8,
                observed_qber=0.05,
                protocol=protocol,
            )
            key_len = FiniteKeyAnalysis.key_length(params)
            assert key_len >= 0

    def test_kwargs_interface(self):
        """Test that kwargs interface works."""
        key_len = FiniteKeyAnalysis.key_length(
            n_pulses=10**8,
            observed_qber=0.05,
            security_parameter=1e-10,
        )
        assert key_len >= 0

    def test_smooth_min_entropy_rate(self):
        """Test smooth min-entropy rate calculation."""
        rate = FiniteKeyAnalysis._smooth_min_entropy_rate(
            qber=0.05,
            n_pulses=10**8,
            security_parameter=1e-10,
            protocol="BB84",
        )
        # Should be in reasonable range
        assert 0 <= rate <= 1

    def test_devetak_winter_rate(self):
        """Test Devetak-Winter rate calculation."""
        rate_bb84 = FiniteKeyAnalysis._devetak_winter_rate(0.05, "BB84")
        rate_e91 = FiniteKeyAnalysis._devetak_winter_rate(0.05, "E91")

        assert rate_bb84 > 0
        assert rate_e91 > 0

    def test_binary_entropy(self):
        """Test binary entropy function."""
        assert FiniteKeyAnalysis._binary_entropy(0.0) == 0.0
        assert FiniteKeyAnalysis._binary_entropy(1.0) == 0.0
        assert FiniteKeyAnalysis._binary_entropy(0.5) == pytest.approx(1.0)

    def test_finite_size_effects(self):
        """Test that finite-size effects are present."""
        # Compare with large pulse count (approaches asymptotic)
        params_large = FiniteKeyParameters(
            n_pulses=10**12,
            observed_qber=0.05,
        )

        # Compare with moderate pulse count
        params_moderate = FiniteKeyParameters(
            n_pulses=10**8,
            observed_qber=0.05,
        )

        comparison_large = FiniteKeyAnalysis.compare_asymptotic_vs_finite(params_large)
        comparison_moderate = FiniteKeyAnalysis.compare_asymptotic_vs_finite(params_moderate)

        # Larger pulse count should have smaller overhead (closer to asymptotic)
        assert comparison_large["overhead"] < comparison_moderate["overhead"]

    def test_zero_pulses(self):
        """Test behavior with zero pulses."""
        params = FiniteKeyParameters(
            n_pulses=0,
            observed_qber=0.05,
        )
        key_len = FiniteKeyAnalysis.key_length(params)
        assert key_len == 0

    def test_zero_qber(self):
        """Test behavior with zero QBER."""
        params = FiniteKeyParameters(
            n_pulses=10**8,
            observed_qber=0.0,
        )
        key_len = FiniteKeyAnalysis.key_length(params)
        # Should get maximum possible key length
        assert key_len > 0
