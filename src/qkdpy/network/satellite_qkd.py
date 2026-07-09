"""Satellite Quantum Key Distribution (SatQKD) Module.

This module provides simulation capabilities for satellite-based quantum
key distribution, implementing realistic free-space optical channel models,
atmospheric effects, and orbital mechanics for space-ground quantum links.

This module demonstrates the intersection of:
- Space Technology: Orbital mechanics, satellite-ground links
- Quantum Computing: QKD protocols adapted for space
- AI/ML: Predictive channel modeling and adaptive protocols
"""

import math
from dataclasses import dataclass
from enum import Enum
from typing import Any

import numpy as np

from ..core.channels import QuantumChannel
from ..utils.logging_config import get_logger
from .protocols import ChannelPredictor

logger = get_logger(__name__)


class OrbitType(Enum):
    """Satellite orbit types."""

    LEO = "leo"  # Low Earth Orbit (400-2000 km)
    MEO = "meo"  # Medium Earth Orbit (2000-35786 km)
    GEO = "geo"  # Geostationary Orbit (35786 km)


class AtmosphericCondition(Enum):
    """Atmospheric conditions affecting transmission."""

    CLEAR = "clear"
    HAZE = "haze"
    THIN_CLOUDS = "thin_clouds"
    TURBULENT = "turbulent"


@dataclass
class SatellitePosition:
    """Satellite orbital position."""

    altitude_km: float  # Altitude above Earth's surface
    latitude: float  # Degrees
    longitude: float  # Degrees
    elevation_angle: float  # Angle from ground station horizon
    slant_range_km: float  # Distance to ground station

    @classmethod
    def from_orbit(
        cls,
        altitude_km: float,
        ground_lat: float,
        ground_lon: float,
        sat_lat: float,
        sat_lon: float,
    ) -> "SatellitePosition":
        """Calculate satellite position relative to ground station."""
        # Earth's radius in km
        R_earth = 6371.0

        # Convert to radians
        lat1 = math.radians(ground_lat)
        lat2 = math.radians(sat_lat)
        dlon = math.radians(sat_lon - ground_lon)

        # Central angle using spherical law of cosines
        cos_gamma = math.sin(lat1) * math.sin(lat2) + math.cos(lat1) * math.cos(
            lat2
        ) * math.cos(dlon)
        # gamma used implicitly in slant_range via cos_gamma

        # Slant range calculation
        r_sat = R_earth + altitude_km
        slant_range = math.sqrt(R_earth**2 + r_sat**2 - 2 * R_earth * r_sat * cos_gamma)

        # Elevation angle
        sin_elev = (r_sat * cos_gamma - R_earth) / slant_range
        elevation = math.degrees(math.asin(max(-1, min(1, sin_elev))))

        return cls(
            altitude_km=altitude_km,
            latitude=sat_lat,
            longitude=sat_lon,
            elevation_angle=elevation,
            slant_range_km=slant_range,
        )


@dataclass
class AtmosphericProfile:
    """Atmospheric conditions along the optical path."""

    visibility_km: float = 23.0  # Horizontal visibility
    turbulence_cn2: float = 1e-14  # Refractive index structure constant
    aerosol_optical_depth: float = 0.1
    water_vapor_mm: float = 10.0  # Precipitable water vapor
    cloud_optical_depth: float = 0.0
    temperature_k: float = 288.0  # Ground temperature
    pressure_hpa: float = 1013.25  # Ground pressure


class FreeSpaceOpticalChannel(QuantumChannel):
    """Quantum channel model for free-space optical links.

    Implements realistic atmospheric effects including:
    - Geometric spreading loss
    - Atmospheric absorption and scattering
    - Turbulence-induced beam wandering and scintillation
    - Background noise from sky radiance
    """

    def __init__(
        self,
        satellite_position: SatellitePosition,
        atmosphere: AtmosphericProfile | None = None,
        wavelength_nm: float = 850.0,
        telescope_diameter_m: float = 0.3,
        pointing_error_urad: float = 1.0,
        **kwargs: Any,
    ) -> None:
        """Initialize free-space optical channel.

        Args:
            satellite_position: Satellite position data
            atmosphere: Atmospheric profile
            wavelength_nm: Wavelength of photons in nanometers
            telescope_diameter_m: Receiving telescope diameter
            pointing_error_urad: RMS pointing error in microradians
            **kwargs: Additional arguments for base QuantumChannel
        """
        self.satellite_position = satellite_position
        self.atmosphere = atmosphere or AtmosphericProfile()
        self.wavelength_nm = wavelength_nm
        self.wavelength_m = wavelength_nm * 1e-9
        self.telescope_diameter = telescope_diameter_m
        self.pointing_error = pointing_error_urad * 1e-6

        # Calculate total channel loss
        total_loss = self._calculate_total_loss()

        # Initialize base channel with calculated loss
        super().__init__(
            distance=satellite_position.slant_range_km,
            loss=total_loss,
            **kwargs,
        )

        logger.info(
            "FreeSpaceOpticalChannel initialized",
            slant_range_km=satellite_position.slant_range_km,
            elevation_deg=satellite_position.elevation_angle,
            total_loss_db=self._loss_to_db(total_loss),
        )

    def _loss_to_db(self, loss_fraction: float) -> float:
        """Convert loss fraction to dB."""
        if loss_fraction >= 1.0:
            return float("inf")
        if loss_fraction <= 0.0:
            return 0.0
        return -10 * math.log10(1 - loss_fraction)

    def _calculate_total_loss(self) -> float:
        """Calculate total channel loss from all effects."""
        # 1. Geometric spreading loss
        L = self.satellite_position.slant_range_km * 1000  # Convert to meters
        diffraction_angle = 1.22 * self.wavelength_m / self.telescope_diameter
        beam_radius_at_receiver = L * diffraction_angle
        geometric_efficiency = (
            self.telescope_diameter / (2 * beam_radius_at_receiver)
        ) ** 2
        geometric_efficiency = min(1.0, geometric_efficiency)

        # 2. Atmospheric transmittance (Beer-Lambert)
        # Effective atmospheric path using elevation angle
        elevation_rad = math.radians(max(5, self.satellite_position.elevation_angle))
        air_mass = 1 / math.sin(elevation_rad)  # Simplified plane-parallel

        # Rayleigh scattering coefficient at sea level (approx)
        rayleigh_coeff = 0.0116 * (550 / self.wavelength_nm) ** 4  # per km

        # Mie scattering from aerosols
        mie_coeff = self.atmosphere.aerosol_optical_depth / 8.0  # per km at zenith

        # Effective scattering path through atmosphere (~8 km scale height)
        atm_path_km = 8.0 * air_mass

        atmospheric_transmittance = math.exp(
            -(rayleigh_coeff + mie_coeff) * atm_path_km
        )

        # 3. Cloud attenuation
        cloud_transmittance = math.exp(-self.atmosphere.cloud_optical_depth)

        # 4. Pointing loss
        pointing_loss = math.exp(-2 * (self.pointing_error / diffraction_angle) ** 2)

        # 5. Turbulence effects (Strehl ratio approximation)
        r0 = self._fried_parameter()
        strehl = (
            math.exp(-((self.telescope_diameter / r0) ** (5 / 3))) if r0 > 0 else 0.1
        )
        strehl = max(0.1, min(1.0, strehl))

        # Total efficiency
        total_efficiency = (
            geometric_efficiency
            * atmospheric_transmittance
            * cloud_transmittance
            * pointing_loss
            * strehl
        )

        # Convert to loss fraction
        return 1.0 - max(0.0, min(1.0, total_efficiency))

    def _fried_parameter(self) -> float:
        """Calculate Fried parameter (r0) for atmospheric coherence.

        Returns:
            Fried parameter in meters
        """
        cn2 = self.atmosphere.turbulence_cn2
        k = 2 * math.pi / self.wavelength_m

        # Integrated path through turbulence (simplified)
        elevation_rad = math.radians(max(5, self.satellite_position.elevation_angle))
        sec_z = 1 / math.sin(elevation_rad)

        # Hufnagel-Valley turbulence profile integration (simplified)
        integrated_cn2 = cn2 * 1000 * sec_z  # Approximate

        r0 = (0.423 * k**2 * integrated_cn2) ** (-3 / 5)
        return max(0.01, r0)  # Minimum 1 cm

    def get_channel_metrics(self) -> dict[str, float]:
        """Get detailed channel metrics."""
        return {
            "slant_range_km": self.satellite_position.slant_range_km,
            "elevation_angle_deg": self.satellite_position.elevation_angle,
            "total_loss_db": self._loss_to_db(self.loss),
            "fried_parameter_cm": self._fried_parameter() * 100,
            "atmospheric_seeing_arcsec": 0.98
            * self.wavelength_m
            / self._fried_parameter()
            * 206265,
        }


class SatelliteQKD:
    """Satellite-based Quantum Key Distribution system.

    Simulates QKD between a satellite and ground station with:
    - Realistic orbital mechanics
    - Time-varying channel conditions
    - ML-based channel prediction for adaptive protocols
    """

    def __init__(
        self,
        orbit_type: OrbitType = OrbitType.LEO,
        altitude_km: float = 500.0,
        ground_station_lat: float = 0.0,
        ground_station_lon: float = 0.0,
        protocol: str = "BB84",
        channel_predictor: ChannelPredictor | None = None,
    ) -> None:
        """Initialize satellite QKD system.

        Args:
            orbit_type: Type of satellite orbit
            altitude_km: Satellite altitude in km
            ground_station_lat: Ground station latitude
            ground_station_lon: Ground station longitude
            protocol: QKD protocol to use
            channel_predictor: Optional ML predictor. Created lazily if None.
        """
        self.orbit_type = orbit_type
        self.altitude_km = altitude_km
        self.ground_station_lat = ground_station_lat
        self.ground_station_lon = ground_station_lon
        self.protocol_name = protocol

        # ML predictor for channel conditions
        self._channel_predictor: ChannelPredictor | None = channel_predictor
        self._pass_history: list[dict[str, Any]] = []

        logger.info(
            "SatelliteQKD initialized",
            orbit_type=orbit_type.value,
            altitude_km=altitude_km,
        )

    def simulate_pass(
        self,
        duration_seconds: float = 300.0,
        time_steps: int = 60,
        atmosphere: AtmosphericProfile | None = None,
    ) -> dict[str, Any]:
        """Simulate a satellite pass over the ground station.

        Args:
            duration_seconds: Pass duration in seconds
            time_steps: Number of simulation time steps
            atmosphere: Atmospheric conditions

        Returns:
            Pass simulation results
        """
        atmosphere = atmosphere or AtmosphericProfile()

        results = {
            "time_points": [],
            "elevation_angles": [],
            "channel_losses_db": [],
            "key_rates_bps": [],
            "qber_values": [],
            "total_key_bits": 0,
        }

        # Simulate pass trajectory (simplified circular arc)
        for i in range(time_steps):
            t = i / (time_steps - 1) if time_steps > 1 else 0

            # Elevation angle varies during pass — peak at middle of pass
            peak_elevation = 80.0
            min_elevation = 10.0
            elevation_angle = min_elevation + (
                peak_elevation - min_elevation
            ) * math.sin(math.pi * t)

            # Calculate satellite position for this time step
            sat_lat = self.ground_station_lat + 5 * math.cos(math.pi * t)
            sat_lon = self.ground_station_lon + 10 * (t - 0.5)

            position = SatellitePosition.from_orbit(
                self.altitude_km,
                self.ground_station_lat,
                self.ground_station_lon,
                sat_lat,
                sat_lon,
            )

            # Compute the per-step QBER *before* using it to derive key rate.
            # Higher elevation (closer to zenith) typically means lower QBER.
            qber = 0.02 + 0.01 * (1 - math.sin(math.radians(elevation_angle)))

            # Create channel for this position (atmospheric profile is constant
            # within a pass — only the geometric path changes with elevation).
            channel = FreeSpaceOpticalChannel(position, atmosphere)

            # Estimate key rate (simplified model): throughput gated by per-step
            # channel loss and qber.  Previously this used a hardcoded 2% QBER
            # regardless of the per-step qber, silently understating key-rate
            # variation across the pass.
            loss_db = channel._loss_to_db(channel.loss)
            detector_rate = 1e6  # 1 MHz source rate
            key_rate = detector_rate * (1 - channel.loss) * 0.5  # sifting factor
            key_rate = max(0.0, key_rate * (1.0 - qber))

            # Store results
            results["time_points"].append(i * duration_seconds / time_steps)
            results["elevation_angles"].append(position.elevation_angle)
            results["channel_losses_db"].append(loss_db)
            results["key_rates_bps"].append(key_rate)
            results["qber_values"].append(qber)

            results["total_key_bits"] += key_rate * (duration_seconds / time_steps)

        # Store for ML training
        self._pass_history.append(
            {
                "atmosphere": atmosphere,
                "total_key_bits": results["total_key_bits"],
                "peak_elevation": max(results["elevation_angles"]),
            }
        )

        logger.info(
            "Satellite pass simulated",
            total_key_bits=int(results["total_key_bits"]),
            peak_elevation=max(results["elevation_angles"]),
        )

        return results

    def train_channel_predictor(self) -> dict[str, Any]:
        """Train ML model to predict channel conditions.

        Uses historical pass data to train a predictor for
        optimal transmission windows.

        Returns:
            Training results
        """
        if len(self._pass_history) < 5:
            return {"error": "Need at least 5 passes for training"}

        # Prepare training data
        X = []
        y = []

        for pass_data in self._pass_history:
            atm = pass_data["atmosphere"]
            features = [
                atm.visibility_km,
                atm.turbulence_cn2 * 1e14,  # Scale for numerical stability
                atm.aerosol_optical_depth,
                atm.cloud_optical_depth,
                pass_data["peak_elevation"],
            ]
            X.append(features)
            y.append(pass_data["total_key_bits"])

        X = np.array(X)
        y = np.array(y)

        # Create and train efficient predictor if none was injected
        if self._channel_predictor is None:
            from ..ml.efficient_models import EfficientQKDPredictor

            self._channel_predictor = EfficientQKDPredictor(
                input_dim=5,
                max_memory_mb=128,
                enable_quantization=True,
            )

        results = self._channel_predictor.fit(X, y, epochs=50)

        logger.info(
            "Channel predictor trained",
            epochs=results["epochs_trained"],
            final_loss=results["final_train_loss"],
        )

        return results

    def predict_key_yield(
        self,
        atmosphere: AtmosphericProfile,
        peak_elevation: float = 80.0,
    ) -> float:
        """Predict key yield for given conditions using ML model.

        Args:
            atmosphere: Expected atmospheric conditions
            peak_elevation: Expected peak elevation angle

        Returns:
            Predicted total key bits
        """
        if self._channel_predictor is None or not self._channel_predictor.is_trained:
            logger.warning("Channel predictor not trained, using default estimate")
            return 1e6  # Default estimate

        features = np.array(
            [
                [
                    atmosphere.visibility_km,
                    atmosphere.turbulence_cn2 * 1e14,
                    atmosphere.aerosol_optical_depth,
                    atmosphere.cloud_optical_depth,
                    peak_elevation,
                ]
            ]
        )

        prediction = self._channel_predictor.predict(features)
        return float(prediction[0])

    def get_mission_summary(self) -> dict[str, Any]:
        """Get summary of satellite QKD mission capabilities.

        Returns:
            Mission capability summary
        """
        return {
            "orbit_type": self.orbit_type.value,
            "altitude_km": self.altitude_km,
            "ground_station": {
                "latitude": self.ground_station_lat,
                "longitude": self.ground_station_lon,
            },
            "protocol": self.protocol_name,
            "total_passes_simulated": len(self._pass_history),
            "ml_predictor_trained": (
                self._channel_predictor is not None
                and self._channel_predictor.is_trained
            ),
            "estimated_daily_key_bits": (
                sum(p["total_key_bits"] for p in self._pass_history[-10:])
                if self._pass_history
                else 0
            ),
        }


# Convenience function for quick satellite QKD simulation
def simulate_satellite_qkd(
    altitude_km: float = 500.0,
    ground_lat: float = 28.5,  # Cape Canaveral latitude
    ground_lon: float = -80.6,  # Cape Canaveral longitude
    num_passes: int = 5,
) -> dict[str, Any]:
    """Quick satellite QKD simulation.

    Args:
        altitude_km: Satellite altitude
        ground_lat: Ground station latitude
        ground_lon: Ground station longitude
        num_passes: Number of passes to simulate

    Returns:
        Simulation results
    """
    sat_qkd = SatelliteQKD(
        orbit_type=OrbitType.LEO,
        altitude_km=altitude_km,
        ground_station_lat=ground_lat,
        ground_station_lon=ground_lon,
    )

    all_results = []
    for _i in range(num_passes):
        # Vary atmospheric conditions
        atmosphere = AtmosphericProfile(
            visibility_km=15 + 10 * np.random.random(),
            turbulence_cn2=1e-14 * (0.5 + np.random.random()),
            aerosol_optical_depth=0.05 + 0.1 * np.random.random(),
        )

        results = sat_qkd.simulate_pass(atmosphere=atmosphere)
        all_results.append(results)

    # Train predictor if enough data
    if num_passes >= 5:
        sat_qkd.train_channel_predictor()

    return {
        "mission_summary": sat_qkd.get_mission_summary(),
        "pass_results": all_results,
        "total_key_bits": sum(r["total_key_bits"] for r in all_results),
    }
