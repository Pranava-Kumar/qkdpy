"""Security analysis tools for QKD protocols."""

from enum import Enum
from typing import Any

import numpy as np


class AttackType(Enum):
    """Types of attacks that can be simulated in QKD protocols."""

    INTERCEPT_RESEND = "intercept-resend"
    PHASE_CLONE = "phase-cloning"
    BEAM_SPLITTING = "beam-splitting"
    FAKED_STATE = "faked-state"
    TIME_SHIFT = "time-shift"
    SPLIT_AND_DELAY = "split-and-delay"
    COLLECTOR = "collector"


class SecurityAnalyzer:
    """Comprehensive security analysis tools for QKD protocols."""

    def __init__(self):
        """Initialize the security analyzer."""
        self.attack_results: list[dict[str, Any]] = []

    def perform_security_analysis(
        self,
        protocol_name: str,
        qber: float,
        key_rate: float,
        channel_loss: float,
        mean_photon_number: float,
        num_decoy_states: int = 0,
    ) -> dict[str, Any]:
        """Perform comprehensive security analysis for a QKD protocol.

        Args:
            protocol_name: Name of the QKD protocol
            qber: Quantum Bit Error Rate
            key_rate: Raw key generation rate
            channel_loss: Channel loss in dB
            mean_photon_number: Mean photon number per pulse
            num_decoy_states: Number of decoy states used (0 for no decoys)

        Returns:
            Dictionary with comprehensive security analysis
        """
        # Calculate various security metrics
        security_threshold = self._get_protocol_security_threshold(protocol_name)
        is_secure = qber < security_threshold

        # Calculate key rate after error correction and privacy amplification
        corrected_key_rate = self._calculate_corrected_key_rate(
            key_rate, qber, protocol_name
        )

        # Calculate security parameters
        sifted_key_rate = key_rate * 0.5  # Rough estimate: ~50% sifted in BB84

        # Estimate security parameters based on protocol
        security_params = self._estimate_security_parameters(
            protocol_name, qber, channel_loss, mean_photon_number, num_decoy_states
        )

        # Perform attack vulnerability analysis
        vulnerabilities = self._analyze_attack_vulnerabilities(
            protocol_name, qber, channel_loss, mean_photon_number, num_decoy_states
        )

        # Calculate security level
        security_level = self._calculate_security_level(
            is_secure, qber, security_threshold, vulnerabilities
        )

        return {
            "protocol": protocol_name,
            "qber": qber,
            "threshold": security_threshold,
            "is_secure": is_secure,
            "raw_key_rate": key_rate,
            "corrected_key_rate": corrected_key_rate,
            "sifted_key_rate": sifted_key_rate,
            "security_level": security_level,
            "security_parameters": security_params,
            "vulnerabilities": vulnerabilities,
            "analysis_timestamp": np.datetime64("now"),
        }

    def _get_protocol_security_threshold(self, protocol_name: str) -> float:
        """Get the security threshold for a specific protocol.

        Args:
            protocol_name: Name of the QKD protocol

        Returns:
            Security threshold QBER value
        """
        thresholds = {
            "BB84": 0.11,
            "SARG04": 0.146,
            "E91": 0.071,  # For maximally entangled states
            "B92": 0.25,
            "six-state": 0.127,
            "cv_qkd": 0.5,  # For continuous variable (more tolerant to noise)
            "HD-QKD": 0.15,  # Higher for high-dimensional protocols
            "decoy-state-bb84": 0.12,
        }
        return thresholds.get(protocol_name.lower(), 0.11)

    def _calculate_corrected_key_rate(
        self, raw_rate: float, qber: float, protocol_name: str
    ) -> float:
        """Calculate corrected key rate after privacy amplification.

        Args:
            raw_rate: Raw key generation rate
            qber: Quantum Bit Error Rate
            protocol_name: Name of the protocol

        Returns:
            Corrected key rate after privacy amplification
        """

        def h2(x):
            """Binary entropy function."""
            return -x * np.log2(x) - (1 - x) * np.log2(1 - x) if 0 < x < 1 else 0

        if qber > 0.5:
            return 0.0  # No secure key possible

        # Calculate mutual information between Alice and Bob
        mutual_ab = 1 - h2(qber)

        # Calculate upper bound on mutual information between Alice and Eve
        # For BB84: I(A:E) <= h2(qber)
        mutual_ae = h2(qber)

        # Calculate final key rate after privacy amplification
        # R >= R_raw * (mutual_ab - mutual_ae)
        corrected_rate = raw_rate * max(0, mutual_ab - mutual_ae)

        # Apply protocol-specific efficiency factors
        efficiency_factors = {
            "BB84": 0.5,  # Sifting factor
            "SARG04": 0.25,
            "E91": 0.25,
            "B92": 0.5,
            "six-state": 0.33,
            "cv_qkd": 0.7,  # Higher for CV protocols
            "HD-QKD": 0.5,  # Depends on dimension
            "decoy-state-bb84": 0.5,
        }

        efficiency = efficiency_factors.get(protocol_name.lower(), 0.5)
        return corrected_rate * efficiency

    def _estimate_security_parameters(
        self,
        protocol_name: str,
        qber: float,
        channel_loss: float,
        mean_photon_number: float,
        num_decoy_states: int,
    ) -> dict[str, float]:
        """Estimate key security parameters.

        Args:
            protocol_name: Name of the protocol
            qber: Quantum Bit Error Rate
            channel_loss: Channel loss in dB
            mean_photon_number: Mean photon number per pulse
            num_decoy_states: Number of decoy states

        Returns:
            Dictionary with security parameters
        """
        # Calculate various security metrics
        visibility = 1 - 2 * qber if qber < 0.5 else 0
        error_rate_db = -10 * np.log10(qber) if qber > 0 else float("inf")

        # Calculate probability of multi-photon pulses (for weak coherent sources)
        prob_multi = (
            1
            - np.exp(-mean_photon_number)
            - mean_photon_number * np.exp(-mean_photon_number)
        )

        # Calculate decoy-state effectiveness
        decoy_effectiveness = min(1.0, num_decoy_states * 0.2)  # Simplified

        # Calculate expected key rate based on channel parameters
        transmittance = 10 ** (-channel_loss / 10.0)
        expected_rate = (
            transmittance * np.exp(-mean_photon_number) * mean_photon_number
        )  # Single photon rate

        return {
            "visibility": visibility,
            "error_rate_db": error_rate_db,
            "probability_multi_photon": prob_multi,
            "decoy_effectiveness": decoy_effectiveness,
            "expected_single_photon_rate": expected_rate,
            "photon_count_statistics": self._analyze_photon_statistics(
                mean_photon_number
            ),
        }

    def _analyze_photon_statistics(self, mean_photon_number: float) -> dict[str, float]:
        """Analyze photon number statistics.

        Args:
            mean_photon_number: Mean photon number per pulse

        Returns:
            Dictionary with photon statistics
        """
        prob_vacuum = np.exp(-mean_photon_number)
        prob_single = mean_photon_number * np.exp(-mean_photon_number)
        prob_multi = 1 - prob_vacuum - prob_single

        return {
            "prob_vacuum": prob_vacuum,
            "prob_single": prob_single,
            "prob_multi": prob_multi,
        }

    def _analyze_attack_vulnerabilities(
        self,
        protocol_name: str,
        qber: float,
        channel_loss: float,
        mean_photon_number: float,
        num_decoy_states: int,
    ) -> dict[AttackType, dict[str, float]]:
        """Analyze vulnerabilities to different types of attacks.

        Args:
            protocol_name: Name of the protocol
            qber: Quantum Bit Error Rate
            channel_loss: Channel loss in dB
            mean_photon_number: Mean photon number per pulse
            num_decoy_states: Number of decoy states

        Returns:
            Dictionary mapping attack types to vulnerability assessments
        """
        vulnerabilities = {}

        # Intercept-Resend Attack
        ir_success_prob = 0.25  # Basic intercept-resend success probability
        ir_detected = qber > 0.125  # Detection threshold
        vulnerabilities[AttackType.INTERCEPT_RESEND] = {
            "success_probability": ir_success_prob,
            "detectability": float(ir_detected),
            "impact": 0.25,
        }

        # Photon Number Splitting (PNS) / Beam Splitting Attack
        # More vulnerable with higher mean photon number and no decoy states
        pns_vuln = min(1.0, mean_photon_number * 2.0)  # Higher for multi-photon
        if num_decoy_states > 0:
            pns_vuln *= 0.1  # Decoy states significantly reduce PNS vulnerability
        vulnerabilities[AttackType.BEAM_SPLITTING] = {
            "vulnerability_level": pns_vuln,
            "detectability": 0.0,  # PNS is hard to detect
            "impact": pns_vuln,
        }

        # Phase-Clone Attack
        pc_vuln = min(0.5, qber * 2)  # More effective at higher QBER
        vulnerabilities[AttackType.PHASE_CLONE] = {
            "vulnerability_level": pc_vuln,
            "detectability": 0.3,
            "impact": pc_vuln * 0.6,
        }

        # Faked-State Attack
        # More relevant for protocols using phase encoding
        fs_vuln = 0.1 if protocol_name in ["BB84", "decoy-state-bb84"] else 0.05
        vulnerabilities[AttackType.FAKED_STATE] = {
            "vulnerability_level": fs_vuln,
            "detectability": 0.8,  # Usually detectable
            "impact": fs_vuln * 0.8,
        }

        # Time-Shift Attack
        # Depends on detector characteristics (simplified)
        ts_vuln = 0.15 * (channel_loss / 20.0)  # Higher loss = higher vulnerability
        vulnerabilities[AttackType.TIME_SHIFT] = {
            "vulnerability_level": ts_vuln,
            "detectability": 0.6,
            "impact": ts_vuln * 0.5,
        }

        return vulnerabilities

    def _calculate_security_level(
        self,
        is_secure: bool,
        qber: float,
        threshold: float,
        vulnerabilities: dict[AttackType, dict[str, float]],
    ) -> int:
        """Calculate overall security level (1-5 scale).

        Args:
            is_secure: Whether the protocol is secure based on QBER
            qber: Quantum Bit Error Rate
            threshold: Security threshold
            vulnerabilities: Vulnerability analysis results

        Returns:
            Security level from 1 (insecure) to 5 (very secure)
        """
        if not is_secure:
            return 1  # Not secure based on QBER

        # Calculate security score based on how far QBER is from threshold
        safety_margin = (threshold - qber) / threshold
        safety_score = min(2.0, max(0.0, safety_margin * 3.0))  # Scale 0-2

        # Calculate vulnerability score (lower is better)
        max_vulnerability = (
            max(v["vulnerability_level"] for v in vulnerabilities.values())
            if vulnerabilities
            else 0
        )
        vulnerability_score = 2 * (1 - max_vulnerability)  # Scale 0-2

        # Calculate protocol robustness score
        robustness_score = 1.0  # Base score

        total_score = safety_score + vulnerability_score + robustness_score
        return max(1, min(5, int(np.ceil(total_score))))

    def simulate_attack(
        self,
        attack_type: AttackType,
        protocol_name: str,
        original_qber: float,
        channel_loss: float,
        mean_photon_number: float,
    ) -> dict[str, Any]:
        """Simulate the effects of a specific attack on the protocol.

        Args:
            attack_type: Type of attack to simulate
            protocol_name: Name of the protocol
            original_qber: Original QBER without attack
            channel_loss: Channel loss in dB
            mean_photon_number: Mean photon number per pulse

        Returns:
            Dictionary with attack simulation results
        """
        # Calculate the impact of the attack
        if attack_type == AttackType.INTERCEPT_RESEND:
            # Intercept-resend adds 25% error rate on top of existing errors
            new_qber = min(0.5, original_qber + 0.25)
            info_gained = 0.5  # Eve gains 50% of information
            detection_prob = 0.75 if original_qber < 0.1 else 0.95

        elif attack_type == AttackType.BEAM_SPLITTING:
            # PNS attack - more effective with higher mean photon number
            pns_effect = 0.3 * min(
                1.0, mean_photon_number - 0.1
            )  # Only effective if > 0.1
            new_qber = min(0.5, original_qber + pns_effect * 0.1)
            info_gained = min(
                1.0, mean_photon_number * 0.8
            )  # More info with more photons
            detection_prob = 0.05  # PNS is hard to detect

        elif attack_type == AttackType.PHASE_CLONE:
            # Phase cloning attack - adds error and lets Eve gain information
            new_qber = min(0.5, original_qber + 0.15)
            info_gained = 0.4
            detection_prob = 0.3

        elif attack_type == AttackType.FAKED_STATE:
            # Faked state attack on detectors
            new_qber = min(0.5, original_qber + 0.05)
            info_gained = 0.6
            detection_prob = 0.9  # Usually detectable

        elif attack_type == AttackType.TIME_SHIFT:
            # Time shift attack exploiting detector dead time
            ts_effect = 0.08 * (channel_loss / 10.0)  # More effective at higher loss
            new_qber = min(0.5, original_qber + ts_effect)
            info_gained = 0.35
            detection_prob = 0.6

        else:
            # Default values for other attacks
            new_qber = original_qber + 0.1
            info_gained = 0.2
            detection_prob = 0.4

        # Calculate impact on key rate
        key_rate_reduction = info_gained * 0.5  # Simplified model

        result = {
            "attack_type": attack_type.value,
            "original_qber": original_qber,
            "new_qber": new_qber,
            "qber_increase": new_qber - original_qber,
            "information_gained_by_eve": info_gained,
            "detection_probability": detection_prob,
            "key_rate_reduction_factor": key_rate_reduction,
            "effective_key_rate": max(0, 1 - key_rate_reduction),
            "security_compromise_level": self._calculate_compromise_level(
                new_qber, protocol_name
            ),
        }

        self.attack_results.append(result)
        return result

    def _calculate_compromise_level(self, qber: float, protocol_name: str) -> str:
        """Calculate the level of security compromise.

        Args:
            qber: QBER value
            protocol_name: Name of the protocol

        Returns:
            Security compromise level as a string
        """
        threshold = self._get_protocol_security_threshold(protocol_name)

        if qber > threshold * 1.5:
            return "severe"
        elif qber > threshold:
            return "moderate"
        elif qber > threshold * 0.7:
            return "minor"
        else:
            return "none"


class QBERAnalysis:
    """Analysis tools specifically for QBER (Quantum Bit Error Rate)."""

    def __init__(self):
        """Initialize QBER analysis tools."""
        pass

    def analyze_qber_trends(
        self,
        qber_values: list[float],
        time_intervals: list[float] = None,
        window_size: int = 10,
    ) -> dict[str, Any]:
        """Analyze trends in QBER values over time.

        Args:
            qber_values: List of QBER values over time
            time_intervals: Optional time intervals for each QBER value
            window_size: Size of sliding window for trend analysis

        Returns:
            Dictionary with QBER trend analysis
        """
        if len(qber_values) < 2:
            return {"error": "Need at least 2 QBER values for trend analysis"}

        # Calculate basic statistics
        mean_qber = float(np.mean(qber_values))
        std_qber = float(np.std(qber_values))
        min_qber = float(np.min(qber_values))
        max_qber = float(np.max(qber_values))

        # Calculate trends
        if len(qber_values) >= 2:
            recent_values = (
                qber_values[-window_size:]
                if len(qber_values) >= window_size
                else qber_values
            )
            if len(recent_values) >= 2:
                # Linear trend over recent values
                x = np.arange(len(recent_values))
                slope, _ = np.polyfit(x, recent_values, 1)
                trend_direction = (
                    "increasing"
                    if slope > 0.001
                    else "decreasing" if slope < -0.001 else "stable"
                )
            else:
                slope = 0
                trend_direction = "insufficient_data"
        else:
            slope = 0
            trend_direction = "insufficient_data"

        # Detect anomalies
        anomalies = self._detect_qber_anomalies(qber_values)

        return {
            "mean_qber": mean_qber,
            "std_qber": std_qber,
            "min_qber": min_qber,
            "max_qber": max_qber,
            "qber_trend_slope": float(slope),
            "trend_direction": trend_direction,
            "anomalies_detected": anomalies,
            "num_anomalies": len(anomalies),
            "qber_stability": self._calculate_stability_score(qber_values),
        }

    def _detect_qber_anomalies(self, qber_values: list[float]) -> list[int]:
        """Detect anomalous QBER values using statistical methods.

        Args:
            qber_values: List of QBER values

        Returns:
            List of indices where anomalies were detected
        """
        if len(qber_values) < 3:
            return []

        anomalies = []
        mean_qber = np.mean(qber_values)
        std_qber = np.std(qber_values)

        if std_qber == 0:
            return []  # All values are the same

        # Use 2-sigma as threshold for anomaly detection
        threshold = 2 * std_qber

        for i, qber in enumerate(qber_values):
            if abs(qber - mean_qber) > threshold:
                anomalies.append(i)

        return anomalies

    def _calculate_stability_score(self, qber_values: list[float]) -> float:
        """Calculate a stability score for QBER values.

        Args:
            qber_values: List of QBER values

        Returns:
            Stability score between 0 (unstable) and 1 (stable)
        """
        if len(qber_values) < 2:
            return 0.5  # Unknown stability

        # Calculate coefficient of variation
        mean_qber = np.mean(qber_values)
        std_qber = np.std(qber_values)

        if mean_qber == 0:
            return 0.0 if std_qber > 0 else 1.0

        cv = std_qber / mean_qber if mean_qber > 0 else float("inf")

        # Convert to stability score (inverse relationship)
        # Lower CV = more stable
        stability_score = 1.0 / (1.0 + cv)  # Maps to [0, 1]

        return min(1.0, max(0.0, stability_score))


class SideChannelAnalyzer:
    """Analyzer for side-channel attacks in QKD systems."""

    def __init__(self):
        """Initialize side-channel analyzer."""
        pass

    def analyze_detector_side_channels(
        self,
        detector_timing: list[tuple[float, bool]],
        detector_settings: list[dict[str, float]],
    ) -> dict[str, Any]:
        """Analyze potential side-channel vulnerabilities in detectors.

        Args:
            detector_timing: List of (timestamp, detection_occurred) tuples
            detector_settings: List of detector configuration parameters

        Returns:
            Dictionary with side-channel analysis
        """
        # Analyze timing correlations
        timing_analysis = self._analyze_detector_timing(detector_timing)

        # Analyze setting correlations
        setting_analysis = self._analyze_detector_settings(detector_settings)

        # Identify potential vulnerabilities
        vulnerabilities = self._identify_detector_vulnerabilities(
            timing_analysis, setting_analysis
        )

        return {
            "timing_analysis": timing_analysis,
            "setting_analysis": setting_analysis,
            "vulnerabilities": vulnerabilities,
            "recommendations": self._generate_detector_recommendations(vulnerabilities),
        }

    def _analyze_detector_timing(
        self, detector_timing: list[tuple[float, bool]]
    ) -> dict[str, Any]:
        """Analyze detector timing for side-channel vulnerabilities.

        Args:
            detector_timing: List of (timestamp, detection_occurred) tuples

        Returns:
            Dictionary with timing analysis
        """
        if not detector_timing:
            return {"error": "No timing data provided"}

        # Calculate detection rate
        detections = [detected for _, detected in detector_timing if detected]
        detection_rate = sum(detections) / len(detections) if detections else 0.0

        # Analyze timing patterns
        intervals = []
        last_detection_time = None
        for timestamp, detected in detector_timing:
            if detected:
                if last_detection_time is not None:
                    intervals.append(timestamp - last_detection_time)
                last_detection_time = timestamp

        timing_variance = float(np.var(intervals)) if intervals else 0.0
        mean_interval = float(np.mean(intervals)) if intervals else float("inf")

        return {
            "detection_rate": detection_rate,
            "mean_interval": mean_interval,
            "timing_variance": timing_variance,
            "possible_timing_attacks": timing_variance > 1e-12,  # Arbitrary threshold
            "number_of_intervals": len(intervals),
        }

    def _analyze_detector_settings(
        self, detector_settings: list[dict[str, float]]
    ) -> dict[str, Any]:
        """Analyze detector settings for correlations.

        Args:
            detector_settings: List of detector configuration parameters

        Returns:
            Dictionary with setting analysis
        """
        if not detector_settings:
            return {"error": "No detector settings provided"}

        # Check for correlations between settings and outcomes
        keys = set()
        for setting in detector_settings:
            keys.update(setting.keys())

        correlations = {}
        for key in keys:
            values = [setting.get(key, 0) for setting in detector_settings]
            # Calculate variance as a simple measure of setting stability
            correlations[key] = {
                "mean": float(np.mean(values)),
                "std": float(np.std(values)),
                "min": float(np.min(values)),
                "max": float(np.max(values)),
                "possible_vulnerability": np.std(values)
                > 0.1,  # If settings vary significantly
            }

        return {
            "parameter_correlations": correlations,
            "number_of_settings": len(detector_settings),
        }

    def _identify_detector_vulnerabilities(
        self, timing_analysis: dict[str, Any], setting_analysis: dict[str, Any]
    ) -> list[str]:
        """Identify potential detector side-channel vulnerabilities.

        Args:
            timing_analysis: Results from timing analysis
            setting_analysis: Results from setting analysis

        Returns:
            List of identified vulnerabilities
        """
        vulnerabilities = []

        # Check for timing-based vulnerabilities
        if timing_analysis.get("possible_timing_attacks", False):
            vulnerabilities.append("timing_correlation")

        # Check for setting-based vulnerabilities
        param_correlations = setting_analysis.get("parameter_correlations", {})
        for param, stats in param_correlations.items():
            if stats.get("possible_vulnerability", False):
                vulnerabilities.append(f"setting_correlation_{param}")

        return vulnerabilities

    def _generate_detector_recommendations(
        self, vulnerabilities: list[str]
    ) -> list[str]:
        """Generate recommendations based on identified vulnerabilities.

        Args:
            vulnerabilities: List of identified vulnerabilities

        Returns:
            List of recommendations
        """
        recommendations = []

        if "timing_correlation" in vulnerabilities:
            recommendations.append(
                "Implement randomized detector timing or add temporal jitter"
            )

        for vuln in vulnerabilities:
            if vuln.startswith("setting_correlation_"):
                param = vuln.replace("setting_correlation_", "")
                recommendations.append(
                    f"Stabilize {param} parameter or add randomization"
                )

        if not vulnerabilities:
            recommendations.append(
                "No significant detector side-channel vulnerabilities detected"
            )

        return recommendations
