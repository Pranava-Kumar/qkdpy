"""Realistic photon source models for QKD protocols."""

from enum import Enum

import numpy as np


class PhotonSourceState(Enum):
    """Enum for different photon source states."""

    VACUUM = 0
    SINGLE_PHOTON = 1
    MULTI_PHOTON = 2  # Multiple photons in the same mode


class PhotonSource:
    """Base class for realistic photon sources in QKD systems."""

    def __init__(
        self,
        name: str = "Photon Source",
        pulse_rate: float = 1e9,  # 1 GHz pulse rate
        wavelength: float = 1550e-9,  # 1550 nm telecom wavelength
        timing_jitter: float = 1e-12,  # 1 ps timing jitter (std)
        power: float = 1e-6,  # 1 µW average power
        efficiency: float = 0.1,  # 10% coupling efficiency
    ):
        """Initialize a basic photon source.

        Args:
            name: Name of the photon source
            pulse_rate: Rate of photon pulse generation (Hz)
            wavelength: Wavelength of the photons (m)
            timing_jitter: Standard deviation of timing jitter (s)
            power: Average optical power in watts
            efficiency: Coupling efficiency to the quantum channel
        """
        self.name = name
        self.pulse_rate = pulse_rate
        self.wavelength = wavelength
        self.timing_jitter = timing_jitter
        self.power = power
        self.efficiency = efficiency
        self.photon_energy = self._calculate_photon_energy()

    def _calculate_photon_energy(self) -> float:
        """Calculate the energy of a single photon.

        Returns:
            Energy of a single photon in Joules
        """
        h = 6.626e-34  # Planck constant
        c = 299792458  # Speed of light
        return h * c / self.wavelength

    def generate_photon_pulse(self, time: float) -> tuple[bool, float]:
        """Generate a photon pulse at the specified time.

        Args:
            time: Time of pulse generation

        Returns:
            Tuple of (photon_present, actual_time_with_jitter)
        """
        # Add timing jitter
        actual_time = time + np.random.normal(0, self.timing_jitter)

        # Determine if a photon is generated based on power/energy
        # For now, assume a simple model where photons are regularly generated
        photon_present = np.random.random() < self.efficiency

        return photon_present, actual_time


class WeakCoherentSource(PhotonSource):
    """Model for weak coherent photon sources used in QKD."""

    def __init__(
        self,
        name: str = "Weak Coherent Source",
        pulse_rate: float = 1e9,
        wavelength: float = 1550e-9,
        mean_photon_number: float = 0.1,
        timing_jitter: float = 1e-12,
        power: float = 1e-6,
        efficiency: float = 0.1,
    ):
        """Initialize a weak coherent source.

        Args:
            name: Name of the photon source
            pulse_rate: Rate of photon pulse generation (Hz)
            wavelength: Wavelength of the photons (m)
            mean_photon_number: Average number of photons per pulse
            timing_jitter: Standard deviation of timing jitter (s)
            power: Average optical power in watts
            efficiency: Coupling efficiency to the quantum channel
        """
        super().__init__(name, pulse_rate, wavelength, timing_jitter, power, efficiency)
        self.mean_photon_number = mean_photon_number

    def generate_photon_pulse(self, time: float) -> tuple[PhotonSourceState, float]:
        """Generate a photon pulse from the weak coherent source.

        Args:
            time: Time of pulse generation

        Returns:
            Tuple of (photon_state, actual_time_with_jitter)
        """
        # Add timing jitter
        actual_time = time + np.random.normal(0, self.timing_jitter)

        # Generate photon number according to Poisson distribution
        photon_count = np.random.poisson(self.mean_photon_number)

        if photon_count == 0:
            return PhotonSourceState.VACUUM, actual_time
        elif photon_count == 1:
            return PhotonSourceState.SINGLE_PHOTON, actual_time
        else:
            return PhotonSourceState.MULTI_PHOTON, actual_time

    def get_photon_statistics(self, num_pulses: int = 1000) -> dict[str, float]:
        """Get photon statistics for the source.

        Args:
            num_pulses: Number of pulses to simulate

        Returns:
            Dictionary with photon statistics
        """
        vacuum_count = 0
        single_photon_count = 0
        multi_photon_count = 0

        for _ in range(num_pulses):
            state, _ = self.generate_photon_pulse(0.0)
            if state == PhotonSourceState.VACUUM:
                vacuum_count += 1
            elif state == PhotonSourceState.SINGLE_PHOTON:
                single_photon_count += 1
            else:
                multi_photon_count += 1

        return {
            "vacuum_probability": vacuum_count / num_pulses,
            "single_photon_probability": single_photon_count / num_pulses,
            "multi_photon_probability": multi_photon_count / num_pulses,
            "mean_photon_number": self.mean_photon_number,
            "g2_factor": self.mean_photon_number,  # For coherent state
        }


class DecoyStateSource(PhotonSource):
    """Model for decoy state photon sources used to enhance security."""

    def __init__(
        self,
        name: str = "Decoy State Source",
        pulse_rate: float = 1e9,
        wavelength: float = 1550e-9,
        signal_mean_photon_number: float = 0.5,
        decoy_mean_photon_numbers: list[float] | None = None,
        timing_jitter: float = 1e-12,
        power: float = 1e-6,
        efficiency: float = 0.1,
        decoy_probability: float = 0.1,  # 10% decoy state pulses
        random_number_generator: np.random.Generator = None,
    ):
        """Initialize a decoy state source.

        Args:
            name: Name of the photon source
            pulse_rate: Rate of photon pulse generation (Hz)
            wavelength: Wavelength of the photons (m)
            signal_mean_photon_number: Average photons for signal pulses
            decoy_mean_photon_numbers: List of average photons for decoy pulses
            timing_jitter: Standard deviation of timing jitter (s)
            power: Average optical power in watts
            efficiency: Coupling efficiency to the quantum channel
            decoy_probability: Probability of sending a decoy pulse
            random_number_generator: Random number generator instance
        """
        super().__init__(name, pulse_rate, wavelength, timing_jitter, power, efficiency)

        self.signal_mean_photon_number = signal_mean_photon_number
        self.decoy_mean_photon_numbers = decoy_mean_photon_numbers or [0.1, 0.01]
        self.decoy_probability = decoy_probability
        self.rng = random_number_generator or np.random.default_rng()

    def generate_signal_pulse(
        self, time: float
    ) -> tuple[PhotonSourceState, float, str]:
        """Generate a signal photon pulse.

        Args:
            time: Time of pulse generation

        Returns:
            Tuple of (photon_state, actual_time_with_jitter, pulse_type)
        """
        actual_time = time + np.random.normal(0, self.timing_jitter)
        photon_count = np.random.poisson(self.signal_mean_photon_number)

        if photon_count == 0:
            state = PhotonSourceState.VACUUM
        elif photon_count == 1:
            state = PhotonSourceState.SINGLE_PHOTON
        else:
            state = PhotonSourceState.MULTI_PHOTON

        return state, actual_time, "signal"

    def generate_decoy_pulse(self, time: float) -> tuple[PhotonSourceState, float, str]:
        """Generate a decoy photon pulse.

        Args:
            time: Time of pulse generation

        Returns:
            Tuple of (photon_state, actual_time_with_jitter, pulse_type)
        """
        actual_time = time + np.random.normal(0, self.timing_jitter)

        # Randomly select a decoy intensity
        decoy_intensity = self.rng.choice(self.decoy_mean_photon_numbers)
        photon_count = self.rng.poisson(decoy_intensity)

        if photon_count == 0:
            state = PhotonSourceState.VACUUM
        elif photon_count == 1:
            state = PhotonSourceState.SINGLE_PHOTON
        else:
            state = PhotonSourceState.MULTI_PHOTON

        return state, actual_time, f"decoy_{decoy_intensity}"

    def generate_photon_pulse(
        self, time: float
    ) -> tuple[PhotonSourceState, float, str]:
        """Generate a photon pulse, randomly selecting signal or decoy state.

        Args:
            time: Time of pulse generation

        Returns:
            Tuple of (photon_state, actual_time_with_jitter, pulse_type)
        """
        if np.random.random() < self.decoy_probability:
            # Generate decoy pulse
            return self.generate_decoy_pulse(time)
        else:
            # Generate signal pulse
            return self.generate_signal_pulse(time)

    def get_pulse_type_statistics(self, num_pulses: int = 1000) -> dict[str, float]:
        """Get statistics about pulse types generated.

        Args:
            num_pulses: Number of pulses to simulate

        Returns:
            Dictionary with pulse type statistics
        """
        signal_count = 0
        decoy_counts = [0] * len(self.decoy_mean_photon_numbers)

        for _ in range(num_pulses):
            if np.random.random() < self.decoy_probability:
                # Determine which decoy type
                idx = np.random.randint(len(self.decoy_mean_photon_numbers))
                decoy_counts[idx] += 1
            else:
                signal_count += 1

        return {
            "signal_probability": signal_count / num_pulses,
            "decoy_probability": sum(decoy_counts) / num_pulses,
            "decoy_probabilities_by_type": [
                count / num_pulses for count in decoy_counts
            ],
        }


class ParametricDownConversionSource(PhotonSource):
    """Model for parametric down conversion photon pair sources."""

    def __init__(
        self,
        name: str = "PDC Source",
        pulse_rate: float = 1e8,  # Typically lower rate for PDC
        wavelength: float = 1550e-9,
        pair_generation_rate: float = 1e6,  # Pairs per second
        timing_jitter: float = 2e-12,  # Higher timing jitter for PDC
        efficiency: float = 0.05,  # Lower efficiency for PDC
        heralding_efficiency: float = 0.15,  # Efficiency of heralding
        spectral_width: float = 1e12,  # Spectral width (FWHM) in Hz
    ):
        """Initialize a parametric down conversion source.

        Args:
            name: Name of the photon source
            pulse_rate: Rate of pump pulses (Hz)
            wavelength: Wavelength of the down-converted photons (m)
            pair_generation_rate: Rate of photon pair generation (pairs/s)
            timing_jitter: Standard deviation of timing jitter (s)
            efficiency: Overall efficiency of the source
            heralding_efficiency: Efficiency of detecting one photon to herald the other
            spectral_width: Spectral width of the photons (FWHM) in Hz
        """
        # Calculate mean photon number based on pair generation rate
        mean_photon_number = pair_generation_rate / pulse_rate
        super().__init__(
            name,
            pulse_rate,
            wavelength,
            timing_jitter,
            power=mean_photon_number * self._calculate_photon_energy() * pulse_rate,
            efficiency=efficiency,
        )

        self.pair_generation_rate = pair_generation_rate
        self.heralding_efficiency = heralding_efficiency
        self.spectral_width = spectral_width
        self.heralding_probability = (
            mean_photon_number  # Probability of pair generation per pulse
        )

    def generate_photon_pulse(
        self, time: float
    ) -> tuple[bool, float, dict[str, float]]:
        """Generate a photon pulse from the PDC source.

        Args:
            time: Time of pulse generation

        Returns:
            Tuple of (photon_present, actual_time_with_jitter, additional_info)
        """
        actual_time = time + np.random.normal(0, self.timing_jitter)

        # Determine if a pair is generated
        pair_generated = np.random.random() < self.heralding_probability

        additional_info = {}
        photon_present = False

        if pair_generated:
            # Determine if the heralding photon is detected
            herald_detected = np.random.random() < self.heralding_efficiency

            if herald_detected:
                # The signal photon is available with coupling efficiency
                photon_present = np.random.random() < self.efficiency
                additional_info = {
                    "pair_generated": True,
                    "herald_detected": True,
                    "photon_present": photon_present,
                }
            else:
                additional_info = {
                    "pair_generated": True,
                    "herald_detected": False,
                    "photon_present": False,
                }
        else:
            additional_info = {
                "pair_generated": False,
                "herald_detected": False,
                "photon_present": False,
            }

        return photon_present, actual_time, additional_info


class PhotonSourceManager:
    """Manager for coordinating multiple photon sources in QKD protocols."""

    def __init__(self):
        """Initialize the photon source manager."""
        self.sources: dict[str, PhotonSource] = {}
        self.active_source: str | None = None

    def add_source(self, source_id: str, source: PhotonSource) -> None:
        """Add a photon source to the manager.

        Args:
            source_id: Unique identifier for the source
            source: PhotonSource instance to add
        """
        self.sources[source_id] = source

    def set_active_source(self, source_id: str) -> None:
        """Set the active photon source.

        Args:
            source_id: ID of the source to make active
        """
        if source_id not in self.sources:
            raise ValueError(f"Source {source_id} not found")
        self.active_source = source_id

    def generate_sequence(
        self, duration: float, source_id: str = None, timestamps: list[float] = None
    ) -> list[tuple[any, float]]:
        """Generate a sequence of photon pulses.

        Args:
            duration: Duration of sequence in seconds
            source_id: ID of source to use (default: active source)
            timestamps: Specific timestamps for pulse generation (optional)

        Returns:
            List of (photon_state, time) tuples
        """
        if source_id is None:
            if self.active_source is None:
                raise ValueError("No active source and no source specified")
            source_id = self.active_source

        if source_id not in self.sources:
            raise ValueError(f"Source {source_id} not found")

        source = self.sources[source_id]

        if timestamps is not None:
            # Generate pulses at specific timestamps
            results = []
            for time in timestamps:
                if hasattr(source, "generate_signal_pulse") and hasattr(
                    source, "generate_decoy_pulse"
                ):
                    # Special handling for decoy state source
                    result = source.generate_photon_pulse(time)
                    results.append(result)
                else:
                    photon_state, actual_time = source.generate_photon_pulse(time)
                    results.append((photon_state, actual_time))
        else:
            # Generate pulses at regular intervals
            num_pulses = int(duration * source.pulse_rate)
            pulse_interval = 1.0 / source.pulse_rate

            results = []
            for i in range(num_pulses):
                time = i * pulse_interval
                if hasattr(source, "generate_signal_pulse") and hasattr(
                    source, "generate_decoy_pulse"
                ):
                    # Special handling for decoy state source
                    result = source.generate_photon_pulse(time)
                    results.append(result)
                else:
                    photon_state, actual_time = source.generate_photon_pulse(time)
                    results.append((photon_state, actual_time))

        return results
