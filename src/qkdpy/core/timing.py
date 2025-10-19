"""Timing and synchronization models for QKD protocols."""

import time

import numpy as np


class TimingSynchronizer:
    """A realistic timing synchronization model for QKD systems."""

    def __init__(
        self,
        clock_frequency: float = 1e9,  # 1 GHz clock
        timing_jitter: float = 1e-12,  # 1 ps timing jitter (std)
        synchronization_accuracy: float = 1e-9,  # 1 ns synchronization accuracy
        max_drift_rate: float = 1e-6,  # 1 ppm drift rate
    ):
        """Initialize timing synchronizer.

        Args:
            clock_frequency: System clock frequency in Hz
            timing_jitter: Standard deviation of timing jitter in seconds
            synchronization_accuracy: Accuracy of synchronization in seconds
            max_drift_rate: Maximum clock drift rate (fraction per second)
        """
        self.clock_frequency = clock_frequency
        self.timing_jitter = timing_jitter
        self.synchronization_accuracy = synchronization_accuracy
        self.max_drift_rate = max_drift_rate

        # Initialize clock states
        self.alice_clock_offset = 0.0  # Alice's clock offset from reference
        self.bob_clock_offset = 0.0  # Bob's clock offset from reference
        self.alice_clock_drift = np.random.uniform(-max_drift_rate, max_drift_rate)
        self.bob_clock_drift = np.random.uniform(-max_drift_rate, max_drift_rate)

        # Reference time (for simulation purposes)
        self.reference_time = time.time()

        # Timing statistics
        self.timing_measurements: list[dict] = []

    def synchronize_clocks(self, synchronization_time: float) -> dict[str, float]:
        """Perform clock synchronization between Alice and Bob.

        Args:
            synchronization_time: Time of synchronization attempt

        Returns:
            Dictionary with synchronization results
        """
        # Add timing jitter to synchronization
        sync_error = np.random.normal(0, self.synchronization_accuracy)

        # Update clock offsets based on synchronization
        self.alice_clock_offset = sync_error / 2  # Assume equal adjustment
        self.bob_clock_offset = -sync_error / 2

        # Record synchronization result
        sync_result = {
            "synchronization_time": synchronization_time,
            "synchronization_error": abs(sync_error),
            "alice_offset_after_sync": self.alice_clock_offset,
            "bob_offset_after_sync": self.bob_clock_offset,
        }

        return sync_result

    def get_alice_time(self, reference_time: float) -> float:
        """Get Alice's local time based on reference time and drift.

        Args:
            reference_time: Reference time

        Returns:
            Alice's local time
        """
        # Calculate elapsed time since reference
        elapsed = reference_time - self.reference_time

        # Apply clock drift and offset
        drift = elapsed * self.alice_clock_drift
        alice_time = reference_time + self.alice_clock_offset + drift

        # Add timing jitter
        alice_time += np.random.normal(0, self.timing_jitter)

        return alice_time

    def get_bob_time(self, reference_time: float) -> float:
        """Get Bob's local time based on reference time and drift.

        Args:
            reference_time: Reference time

        Returns:
            Bob's local time
        """
        # Calculate elapsed time since reference
        elapsed = reference_time - self.reference_time

        # Apply clock drift and offset
        drift = elapsed * self.bob_clock_drift
        bob_time = reference_time + self.bob_clock_offset + drift

        # Add timing jitter
        bob_time += np.random.normal(0, self.timing_jitter)

        return bob_time

    def calculate_time_difference(self, reference_time: float) -> float:
        """Calculate the time difference between Alice and Bob's clocks.

        Args:
            reference_time: Reference time for calculation

        Returns:
            Time difference (Alice's time - Bob's time)
        """
        alice_time = self.get_alice_time(reference_time)
        bob_time = self.get_bob_time(reference_time)
        return alice_time - bob_time

    def update_clock_drift(self) -> None:
        """Update clock drift values (to simulate gradual changes)."""
        # Small random walk for drift values
        drift_change = np.random.normal(0, self.max_drift_rate * 0.01)  # Small changes
        self.alice_clock_drift = np.clip(
            self.alice_clock_drift + drift_change,
            -self.max_drift_rate,
            self.max_drift_rate,
        )

        drift_change = np.random.normal(0, self.max_drift_rate * 0.01)
        self.bob_clock_drift = np.clip(
            self.bob_clock_drift + drift_change,
            -self.max_drift_rate,
            self.max_drift_rate,
        )


class PhotonTimingModel:
    """Model for photon timing in QKD systems."""

    def __init__(
        self,
        fiber_length: float,  # in meters
        speed_of_light_factor: float = 0.2,  # Fraction of c in fiber (typically ~0.2)
        detector_timing_resolution: float = 5e-12,  # 5 ps resolution
        source_jitter: float = 2e-12,  # 2 ps source jitter
    ):
        """Initialize photon timing model.

        Args:
            fiber_length: Length of optical fiber in meters
            speed_of_light_factor: Effective speed as fraction of c in fiber
            detector_timing_resolution: Timing resolution of detectors in seconds
            source_jitter: Jitter from photon source in seconds
        """
        self.fiber_length = fiber_length
        self.speed_of_light_factor = speed_of_light_factor
        self.detector_timing_resolution = detector_timing_resolution
        self.source_jitter = source_jitter

        # Speed of light in fiber (m/s)
        self.v_fiber = 299792458 * speed_of_light_factor

        # Propagation time for photons
        self.propagation_time = fiber_length / self.v_fiber

    def emit_photon(self, emission_time: float) -> float:
        """Simulate photon emission with timing jitter.

        Args:
            emission_time: Desired emission time

        Returns:
            Actual emission time with jitter
        """
        actual_emission = emission_time + np.random.normal(0, self.source_jitter)
        return actual_emission

    def detect_photon(self, arrival_time: float) -> float:
        """Simulate photon detection with timing resolution.

        Args:
            arrival_time: Actual arrival time of photon

        Returns:
            Measured arrival time with resolution effects
        """
        # Detector adds timing uncertainty
        measured_time = arrival_time + np.random.normal(
            0, self.detector_timing_resolution
        )
        return measured_time

    def photon_transit_time(self) -> float:
        """Get the transit time for a photon through the fiber.

        Returns:
            Photon transit time in seconds
        """
        return self.propagation_time


class QBERTimingAnalysis:
    """Analyze timing-dependent QBER in QKD systems."""

    def __init__(
        self,
        timing_window: float = 1e-9,  # 1 ns coincidence window
        max_temporal_drift: float = 1e-12,  # 1 ps max drift per photon
    ):
        """Initialize timing-dependent QBER analysis.

        Args:
            timing_window: Time window for matching photon pairs (s)
            max_temporal_drift: Maximum temporal drift per photon (s)
        """
        self.timing_window = timing_window
        self.max_temporal_drift = max_temporal_drift

    def calculate_temporal_qber(
        self,
        alice_times: list[float],
        bob_times: list[float],
        expected_delay: float = 0.0,
    ) -> float:
        """Calculate QBER based on timing mismatches.

        Args:
            alice_times: List of photon emission times from Alice
            bob_times: List of photon detection times at Bob
            expected_delay: Expected delay between Alice and Bob

        Returns:
            Estimated QBER due to timing mismatches
        """
        if len(alice_times) != len(bob_times):
            raise ValueError("Alice and Bob time lists must have the same length")

        mismatches = 0
        total_pairs = len(alice_times)

        for i in range(total_pairs):
            # Calculate time difference accounting for expected delay
            time_diff = abs((bob_times[i] - alice_times[i]) - expected_delay)

            # If outside timing window, consider as mismatch
            if time_diff > self.timing_window:
                mismatches += 1

        return mismatches / total_pairs if total_pairs > 0 else 0.0

    def update_with_drift(
        self, drift_rate: float, time_elapsed: float  # s/s  # s
    ) -> float:
        """Update timing window based on clock drift.

        Args:
            drift_rate: Rate of temporal drift (s/s)
            time_elapsed: Time since last synchronization (s)

        Returns:
            Adjusted timing window to account for drift
        """
        additional_uncertainty = abs(drift_rate) * time_elapsed
        return self.timing_window + additional_uncertainty


class ProtocolTimingManager:
    """Manage timing aspects of QKD protocols."""

    def __init__(
        self,
        synchronizer: TimingSynchronizer,
        photon_model: PhotonTimingModel,
        qber_analyzer: QBERTimingAnalysis,
    ):
        """Initialize protocol timing manager.

        Args:
            synchronizer: Timing synchronizer instance
            photon_model: Photon timing model instance
            qber_analyzer: QBER timing analysis instance
        """
        self.synchronizer = synchronizer
        self.photon_model = photon_model
        self.qber_analyzer = qber_analyzer

        # Event timing records
        self.emission_times: list[float] = []
        self.detection_times: list[float] = []

    def send_photon_sequence(
        self,
        start_time: float,
        pulse_interval: float,
        num_photons: int,
        basis_sequence: list[str],
    ) -> tuple[list[float], list[str]]:
        """Simulate sending a sequence of photons with proper timing.

        Args:
            start_time: Start time for sequence
            pulse_interval: Interval between pulses
            num_photons: Number of photons to send
            basis_sequence: Sequence of bases to encode

        Returns:
            Tuple of (emission_times, basis_sequence)
        """
        emission_times = []

        for i in range(num_photons):
            # Calculate scheduled emission time
            scheduled_time = start_time + i * pulse_interval

            # Apply emission jitter
            actual_emission = self.photon_model.emit_photon(scheduled_time)
            emission_times.append(actual_emission)

            # Update clock drifts over time
            self.synchronizer.update_clock_drift()

        return emission_times, basis_sequence

    def receive_photon_sequence(
        self,
        emission_times: list[float],
        expected_delay: float,
        basis_sequence: list[str],
    ) -> tuple[list[float], list[str], float]:
        """Simulate receiving a sequence of photons with proper timing.

        Args:
            emission_times: List of photon emission times from Alice
            expected_delay: Expected delay for photons
            basis_sequence: Sequence of bases that were encoded

        Returns:
            Tuple of (detection_times, measurement_bases, timing_qber)
        """
        detection_times = []
        measurement_bases = []

        for i, emit_time in enumerate(emission_times):
            # Calculate when photon should arrive
            arrival_time = emit_time + self.photon_model.photon_transit_time()

            # Simulate detection with resolution
            detection_time = self.photon_model.detect_photon(arrival_time)
            detection_times.append(detection_time)

            # Bob might choose a different basis due to timing effects
            measurement_bases.append(basis_sequence[i])

        # Calculate timing-dependent QBER
        timing_qber = self.qber_analyzer.calculate_temporal_qber(
            emission_times, detection_times, expected_delay
        )

        return detection_times, measurement_bases, timing_qber

    def get_timing_stats(self) -> dict:
        """Get statistics about timing performance.

        Returns:
            Dictionary with timing statistics
        """
        return {
            "propagation_time": self.photon_model.propagation_time,
            "timing_window": self.qber_analyzer.timing_window,
            "source_jitter": self.photon_model.source_jitter,
            "detector_resolution": self.photon_model.detector_timing_resolution,
            "current_alice_drift": self.synchronizer.alice_clock_drift,
            "current_bob_drift": self.synchronizer.bob_clock_drift,
        }
