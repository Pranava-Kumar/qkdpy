"""Satellite / atmospheric optics mapping for the qpiai-qkd companion.

Wraps the real qkdpy physics modules so a researcher can go from a QpiAI
protocol run to the free-space link figures that bound its performance: slant
range, Fried parameter, Rytov variance, scintillation, and total link loss.

Models used (all in qkdpy core/network):
  * ``core.atmospheric.turbulence`` — Hufnagel-Valley Cn2, Fried parameter,
    Rytov variance, scintillation index.
  * ``network.atmospheric_physics`` — MODTRAN band transmittance, stray-light
    count rate, up/down-link direction factor.
  * ``network.satellite_qkd.FreeSpaceOpticalChannel`` — end-to-end link loss.

These are *physical models with stated assumptions* (single-scattering,
Kolmogorov turbulence, clear-sky MODTRAN band). They estimate expected loss;
they do NOT guarantee a secret-key rate and should not be read as one. SAE
deployments must validate against measured link budgets.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

import numpy as np

from qkdpy.core.atmospheric.turbulence import (
    fried_parameter,
    hufnagel_valley_cn2,
    rytov_variance,
    scintillation_index,
)
from qkdpy.network.atmospheric_physics import (
    background_stray_count_rate,
    link_direction_factor,
    modtran_band_transmittance,
)


@dataclass
class LinkPhysics:
    """JSON-serialisable free-space QKD link physics summary."""

    wavelength_nm: float
    slant_range_km: float
    cn2: float
    fried_parameter_m: float
    rytov_variance: float
    scintillation_index: float
    modtran_transmittance: float
    stray_count_rate_hz: float
    direction_factor: float
    total_link_loss_db: float = 0.0
    notes: list[str] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(self.__dict__, indent=2, sort_keys=True)


def map_satellite_link(
    wavelength_nm: float,
    slant_range_km: float,
    telescope_diameter_m: float,
    is_night: bool = True,
    link_direction: str = "down",
    cn2_ground: float = 1.7e-14,
    wind_speed: float = 21.0,
) -> LinkPhysics:
    """Compute the physics summary for a free-space QKD link.

    Args:
        wavelength_nm: Optical wavelength (e.g. 1550 nm or 850 nm).
        slant_range_km: Ground-station to satellite distance (km).
        telescope_diameter_m: Aperture diameter (m).
        is_night: Day/night profile selection for turbulence & stray light.
        link_direction: ``"down"`` or ``"up"`` (affects beam geometry).
        cn2_ground: Ground-level turbulence strength (m^-2/3).
        wind_speed: RMS wind speed feeding the HV wind term (m/s).

    Returns:
        A :class:`LinkPhysics` summary.
    """
    notes: list[str] = []
    wavelength_m = wavelength_nm * 1e-9
    path_length_m = slant_range_km * 1000.0
    # Representative point Cn2 at the path midpoint; the turbulence functions
    # treat path_cn2 as the path-integrated structure constant.
    cn2 = hufnagel_valley_cn2(
        altitude_m=path_length_m / 2.0,
        cn2_ground=cn2_ground,
        wind_speed=wind_speed,
        is_night=is_night,
    )
    r0 = fried_parameter(path_cn2=cn2, wavelength_m=wavelength_m, path_length_m=path_length_m)
    sigma_r2 = rytov_variance(
        path_cn2=cn2, wavelength_m=wavelength_m, path_length_m=path_length_m
    )
    sigma_i = scintillation_index(
        path_cn2=cn2, wavelength_m=wavelength_m, path_length_m=path_length_m
    )
    transmit = modtran_band_transmittance(wavelength_nm)
    stray = background_stray_count_rate(wavelength_nm, is_night=is_night)
    direction = link_direction_factor(link_direction=link_direction, elevation_angle_deg=90.0)

    # Diffraction-limited beam spreading penalty vs the aperture: a larger
    # aperture spreads the beam less, so a small aperture is a *loss*.
    # Fraunhofer spot diameter ~ 1.22 * lambda * L / D, i.e. loss grows as the
    # beam diverges for smaller D. Use a reference 1 m aperture as the floor.
    diffraction_penalty_db = float(
        10.0 * np.log10(max(1.0 / max(telescope_diameter_m, 1e-3), 1.0))
    )
    # Honest, simple end-to-end estimate: transmittance and link-direction are
    # multiplicative sub-unity factors (each a positive loss), plus a turbulence
    # power penalty proportional to Rytov variance.
    turbulence_penalty_db = float(10.0 * np.log10(max(sigma_r2, 1e-6) + 1.0))
    total_loss_db = float(
        -10.0 * np.log10(max(transmit, 1e-9))
        - 10.0 * np.log10(max(direction, 1e-9))
        + turbulence_penalty_db
        + diffraction_penalty_db
    )
    notes.append(
        "Single-scattering/Kolmogorov model; clear-sky MODTRAN band. "
        "Estimate of expected loss, not a guaranteed key rate."
    )
    return LinkPhysics(
        wavelength_nm=wavelength_nm,
        slant_range_km=slant_range_km,
        cn2=cn2,
        fried_parameter_m=r0,
        rytov_variance=float(sigma_r2),
        scintillation_index=float(sigma_i),
        modtran_transmittance=transmit,
        stray_count_rate_hz=stray,
        direction_factor=direction,
        total_link_loss_db=total_loss_db,
        notes=notes,
    )
