"""Realistic quantum detector model for QKD protocols."""

import numpy as np

from .qubit import Qubit


class QuantumDetector:
    """A realistic quantum detector model with physical properties.

    This class simulates a quantum detector with realistic properties such as:
    dark counts, detection efficiency, dead time, timing jitter, and afterpulsing.
    """

    def __init__(
        self,
        efficiency: float = 0.1,  # Detection efficiency (0.0 to 1.0)
        dark_count_rate: float = 1e-6,  # Dark count rate in Hz
        dead_time: float = 1e-6,  # Dead time in seconds
        timing_jitter: float = 1e-10,  # Timing jitter in seconds (std)
        afterpulse_probability: float = 0.01,  # Probability of afterpulsing
        reset_time: float = 1e-6,  # Time to reset after detection in seconds
    ):
        """Initialize the quantum detector.

        Args:
            efficiency: Detection efficiency (0.0 to 1.0)
            dark_count_rate: Rate of dark count events per second
            dead_time: Time after a detection during which detector is insensitive (s)
            timing_jitter: Standard deviation of timing measurement uncertainty (s)
            afterpulse_probability: Probability of afterpulsing events
            reset_time: Time needed to reset the detector after detection (s)

        """
        self.efficiency = max(0.0, min(1.0, efficiency))
        self.dark_count_rate = max(0.0, dark_count_rate)
        self.dead_time = max(0.0, dead_time)
        self.timing_jitter = max(0.0, timing_jitter)
        self.afterpulse_probability = max(0.0, min(1.0, afterpulse_probability))
        self.reset_time = max(0.0, reset_time)

        # Internal state tracking
        self.last_detection_time = -np.inf
        self.in_dead_time = False

        # Statistics
        self.total_photons_detected = 0
        self.dark_counts_detected = 0
        self.afterpulses_detected = 0
        self.effective_efficiency = efficiency

    def detect(
        self, photon_present: bool, timestamp: float, basis: str = "computational"
    ) -> tuple[int | None, float]:
        """Detect a photon with realistic behavior.

        Args:
            photon_present: Whether a photon is present at the detector input
            timestamp: Time of photon arrival
            basis: Measurement basis

        Returns:
            Tuple of (measurement_result, detection_time) where measurement_result
            is None if no detection occurs, otherwise 0 or 1
        """
        # Check if detector is in dead time
        if self.in_dead_time and (
            timestamp - self.last_detection_time < self.dead_time
        ):
            return None, timestamp

        # Calculate probability of detection based on efficiency
        detection_occurs = False
        measurement_result: int | None = None
        detection_time = timestamp

        # Check for real photon detection
        if photon_present:
            if np.random.random() < self.efficiency:
                detection_occurs = True
                # For simplicity, we'll consider the measurement result as 0 or 1
                # In a more complex implementation, we'd handle the quantum state properly
                measurement_result = np.random.choice([0, 1])

        # Check for dark count during this time interval
        # Calculate dark count probability based on time since last check
        if hasattr(self, "_last_dark_check_time"):
            time_since_check = timestamp - self._last_dark_check_time
        else:
            time_since_check = 1e-9  # Small time interval for first check

        # Update last check time
        self._last_dark_check_time = timestamp

        # Calculate probability of dark count
        p_dark = self.dark_count_rate * time_since_check
        if np.random.random() < p_dark:
            if not detection_occurs:  # Only count if no real photon was detected
                detection_occurs = True
                measurement_result = np.random.choice([0, 1])
                self.dark_counts_detected += 1
            else:
                # Both real detection and dark count - model as afterpulse
                if np.random.random() < self.afterpulse_probability:
                    self.afterpulses_detected += 1

        # Add timing jitter
        detection_time += np.random.normal(0, self.timing_jitter)

        if detection_occurs:
            self.total_photons_detected += 1
            self.last_detection_time = detection_time
            self.in_dead_time = True
        else:
            # No detection, so not in dead time anymore
            self.in_dead_time = False

        return measurement_result, detection_time

    def measure_state(
        self, qubit: Qubit, basis: str = "computational", timestamp: float = 0.0
    ) -> tuple[int | None, float]:
        """Measure a qubit state using the detector model.

        Args:
            qubit: The qubit to measure
            basis: Measurement basis ('computational', 'hadamard', 'circular')
            timestamp: Time of measurement

        Returns:
            Tuple of (measurement_result, detection_time)
        """
        # First measure in the specified basis (without collapsing)
        measurement_result_temp = qubit.measure(basis)

        # Use the detector model to determine if detection occurs
        # For this simulation, assume photon is present with probability based on state
        # In a real implementation, we'd consider the probability based on the state
        prob_detect = abs(qubit.state[measurement_result_temp]) ** 2

        photon_present = np.random.random() < prob_detect
        detection_result, detection_time = self.detect(photon_present, timestamp, basis)

        # Only collapse the state if detection occurred
        if detection_result is not None:
            qubit.collapse_state(detection_result, basis)

        return detection_result, detection_time

    def get_statistics(self) -> dict:
        """Get detector statistics.

        Returns:
            Dictionary with detector statistics
        """
        return {
            "total_photons_detected": self.total_photons_detected,
            "dark_counts_detected": self.dark_counts_detected,
            "afterpulses_detected": self.afterpulses_detected,
            "detection_efficiency": self.efficiency,
            "dead_time": self.dead_time,
            "timing_jitter": self.timing_jitter,
            "afterpulse_probability": self.afterpulse_probability,
        }

    def reset(self) -> None:
        """Reset detector statistics."""
        self.total_photons_detected = 0
        self.dark_counts_detected = 0
        self.afterpulses_detected = 0
        self.last_detection_time = -np.inf
        self.in_dead_time = False
        if hasattr(self, "_last_dark_check_time"):
            delattr(self, "_last_dark_check_time")


class DetectorArray:
    """Array of quantum detectors for multi-basis measurements."""

    def __init__(self, num_detectors: int = 2, **detector_kwargs):
        """Initialize an array of detectors.

        Args:
            num_detectors: Number of detectors in the array
            **detector_kwargs: Arguments to pass to individual detector constructors
        """
        self.detectors = [
            QuantumDetector(**detector_kwargs) for _ in range(num_detectors)
        ]

    def measure_in_basis(
        self, qubit: Qubit, basis: str = "computational", timestamp: float = 0.0
    ) -> int:
        """Measure a qubit in a specific basis using the detector array.

        Args:
            qubit: The qubit to measure
            basis: Measurement basis
            timestamp: Time of measurement

        Returns:
            Measurement result (0 or 1)
        """
        # For now, just use the first detector
        # In a real implementation, we'd use the appropriate detectors for the basis
        result, _ = self.detectors[0].measure_state(qubit, basis, timestamp)

        if result is None:
            # If no detection occurred, we might need some error handling or random assignment
            # For now, we'll assume a detection always occurs for protocol execution
            # This is a simplification - a real system would handle undetected photons
            result = np.random.choice([0, 1])

        return result

    def get_statistics(self) -> list[dict]:
        """Get statistics for all detectors.

        Returns:
            List of dictionaries with statistics for each detector
        """
        return [detector.get_statistics() for detector in self.detectors]
