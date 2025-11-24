from qkdpy.core.security_analysis import (
    AttackType,
    QBERAnalysis,
    SecurityAnalyzer,
    SideChannelAnalyzer,
)


class TestSecurityAnalysisCoverage:
    """Tests to improve coverage of security_analysis.py."""

    def setup_method(self):
        self.analyzer = SecurityAnalyzer()
        self.qber_analyzer = QBERAnalysis()
        self.side_channel_analyzer = SideChannelAnalyzer()

    def test_perform_security_analysis_various_protocols(self):
        """Test security analysis for different protocols."""
        protocols = [
            ("BB84", 0.05),
            ("SARG04", 0.10),
            ("E91", 0.05),
            ("B92", 0.15),
            ("six-state", 0.10),
            ("cv_qkd", 0.10),
            ("HD-QKD", 0.10),
            ("decoy-state-bb84", 0.05),
            ("unknown-protocol", 0.05),
        ]

        for protocol, qber in protocols:
            result = self.analyzer.perform_security_analysis(
                protocol_name=protocol,
                qber=qber,
                key_rate=1000.0,
                channel_loss=0.2,
                mean_photon_number=0.1,
                num_decoy_states=2,
            )
            assert result["protocol"] == protocol
            assert "is_secure" in result
            assert "security_level" in result
            assert 1 <= result["security_level"] <= 5

    def test_perform_security_analysis_high_qber(self):
        """Test security analysis with high QBER (insecure)."""
        result = self.analyzer.perform_security_analysis(
            protocol_name="BB84",
            qber=0.20,  # Above 11% threshold
            key_rate=1000.0,
            channel_loss=0.2,
            mean_photon_number=0.1,
        )
        assert not result["is_secure"]
        assert result["security_level"] == 1
        assert result["corrected_key_rate"] == 0.0

    def test_simulate_all_attacks(self):
        """Test simulation of all defined attack types."""
        for attack_type in AttackType:
            result = self.analyzer.simulate_attack(
                attack_type=attack_type,
                protocol_name="BB84",
                original_qber=0.02,
                channel_loss=10.0,
                mean_photon_number=0.5,
            )
            assert result["attack_type"] == attack_type.value
            assert result["new_qber"] >= 0.02
            assert "security_compromise_level" in result

    def test_qber_analysis_trends(self):
        """Test QBER trend analysis."""
        # Increasing trend
        qber_increasing = [0.01, 0.02, 0.03, 0.04, 0.05]
        result = self.qber_analyzer.analyze_qber_trends(qber_increasing)
        assert result["trend_direction"] == "increasing"

        # Decreasing trend
        qber_decreasing = [0.05, 0.04, 0.03, 0.02, 0.01]
        result = self.qber_analyzer.analyze_qber_trends(qber_decreasing)
        assert result["trend_direction"] == "decreasing"

        # Stable trend
        qber_stable = [0.02, 0.02, 0.02, 0.02, 0.02]
        result = self.qber_analyzer.analyze_qber_trends(qber_stable)
        assert (
            result["trend_direction"] == "stable"
            or abs(result["qber_trend_slope"]) < 0.001
        )

        # Insufficient data
        assert "error" in self.qber_analyzer.analyze_qber_trends([0.01])

    def test_qber_anomalies(self):
        """Test QBER anomaly detection."""
        # One spike
        qber_values = [0.02, 0.02, 0.02, 0.10, 0.02, 0.02]
        result = self.qber_analyzer.analyze_qber_trends(qber_values)
        assert result["num_anomalies"] > 0
        assert 3 in result["anomalies_detected"]  # Index of 0.10

        # No anomalies (constant)
        qber_constant = [0.02] * 10
        result = self.qber_analyzer.analyze_qber_trends(qber_constant)
        assert result["num_anomalies"] == 0

    def test_side_channel_analysis(self):
        """Test side channel analysis."""
        # Timing data with variance
        detector_timing = [
            (0.0, True),
            (1.0, True),
            (2.0, True),
            (3.0, True),  # Regular
            (4.1, True),
            (5.2, True),  # Irregular
        ]

        # Settings with variance
        detector_settings = [
            {"bias_voltage": 50.0, "temp": 20.0},
            {"bias_voltage": 50.1, "temp": 20.1},
            {"bias_voltage": 49.9, "temp": 19.9},
            {"bias_voltage": 55.0, "temp": 25.0},  # Outlier
        ]

        result = self.side_channel_analyzer.analyze_detector_side_channels(
            detector_timing, detector_settings
        )

        assert "timing_analysis" in result
        assert "setting_analysis" in result
        assert "vulnerabilities" in result
        assert "recommendations" in result

        # Check empty inputs
        assert (
            "error"
            in self.side_channel_analyzer.analyze_detector_side_channels([], [])[
                "timing_analysis"
            ]
        )
        assert "error" in self.side_channel_analyzer._analyze_detector_settings([])

    def test_calculate_compromise_level(self):
        """Test compromise level calculation logic."""
        # BB84 threshold is 0.11
        assert self.analyzer._calculate_compromise_level(0.05, "BB84") == "none"
        assert (
            self.analyzer._calculate_compromise_level(0.10, "BB84") == "minor"
        )  # 0.10 > 0.11*0.7 (0.077)
        assert (
            self.analyzer._calculate_compromise_level(0.12, "BB84") == "moderate"
        )  # 0.12 > 0.11
        assert (
            self.analyzer._calculate_compromise_level(0.20, "BB84") == "severe"
        )  # 0.20 > 0.11*1.5 (0.165)

    def test_calculate_corrected_key_rate_edge_cases(self):
        """Test edge cases for key rate calculation."""
        # QBER > 0.5
        rate = self.analyzer._calculate_corrected_key_rate(1000, 0.6, "BB84")
        assert rate == 0.0

        # Zero QBER
        rate = self.analyzer._calculate_corrected_key_rate(1000, 0.0, "BB84")
        # h2(0) = 0, mutual_ab = 1, mutual_ae = 0 -> rate = 1000 * 1 * 0.5 = 500
        assert rate == 500.0
