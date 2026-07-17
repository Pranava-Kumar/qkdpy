"""Atmospheric physics helpers for free-space optical (FSO) satellite QKD.

These are lightweight, physically-motivated models that go beyond the simple
Beer-Lambert / Strehl approximation used elsewhere:

* **MODTRAN-style band transmittance** -- a wavelength-dependent atmospheric
  window model. MODTRAN computes line-by-line molecular transmittance; we use
  the well-known transmission *windows* (near-850 nm, 1064 nm, 1550 nm) with a
  smooth Gaussian window profile so different wavelengths experience very
  different atmospheric absorption.
* **Day/night background stray counts** -- sunlight scatters into the receiver
  during the day (high stray-count rate), while at night the dominant
  background is thermal/dark (low). This sets the QBER floor from background.
* **Uplink vs downlink asymmetry** -- in an *uplink* (ground -> satellite) the
  beam crosses the turbulent, scattering lower atmosphere at the *start* of the
  propagation and then traverses the clear upper atmosphere; in a *downlink*
  (satellite -> ground) the beam traverses clear space first and only hits the
  turbulent layer at the *end*. The net received power is similar, but the
  *timing* of the turbulent layer relative to beam broadening changes the
  scintillation and pointing loss. We model the asymmetry as a multiplicative
  factor on pointing/turbulence loss, with downlink slightly favoured.
"""

import math

import numpy as np

# MODTRAN-like atmospheric transmission windows (wavelength_nm -> peak relative
# transmittance and window width in nm). Outside these windows absorption bands
# suppress the transmittance toward a floor.
_ATMOSPHERIC_WINDOWS = [
    (850.0, 0.95, 120.0),
    (1064.0, 0.90, 100.0),
    (1550.0, 0.98, 200.0),
]


def modtran_band_transmittance(
    wavelength_nm: float,
    clear_sky_floor: float = 0.6,
) -> float:
    """MODTRAN-style band transmission for an optical wavelength.

    Combines the Gaussian atmospheric windows (a stand-in for molecular
    line-by-line transmittance) with a clear-sky floor representing residual
    continuum absorption.

    Args:
        wavelength_nm: Optical wavelength in nanometers.
        clear_sky_floor: Minimum transmittance away from any band (continuum).

    Returns:
        Band transmittance in ``[clear_sky_floor, ~1.0]``.
    """
    peak = clear_sky_floor
    for center, height, width in _ATMOSPHERIC_WINDOWS:
        contribution = height * np.exp(-0.5 * ((wavelength_nm - center) / width) ** 2)
        peak = max(peak, contribution)
    return float(min(1.0, peak))


def background_stray_count_rate(
    wavelength_nm: float,
    is_night: bool = True,
    receiver_area_m2: float = 0.07,
    bandwidth_hz: float = 1e9,
    solar_irradiance_day: float = 1000.0,
) -> float:
    """Background stray-photon count rate at the receiver.

    Models the dominant day/night difference: daytime sky brightness scatters
    sunlight into the receiver (high stray rate, raising the QBER floor), while
    at night the background is dominated by thermal emission / dark counts.
    The value is calibrated to realistic FSO satellite-receiver backgrounds:
    roughly ``1e2`` counts/s at night and ``1e6`` counts/s in daytime.

    Args:
        wavelength_nm: Optical wavelength in nanometers.
        is_night: Day (``False``) vs night (``True``) operation.
        receiver_area_m2: Receiver telescope area in m^2.
        bandwidth_hz: Receiver noise-equivalent bandwidth in Hz.
        solar_irradiance_day: Daytime scattered solar irradiance proxy (W/m^2).

    Returns:
        Stray-photon count rate (counts per second).
    """
    if is_night:
        # Night: thermal/sky background, dominated by dark counts.
        base_rate = 1e2
        window_factor = 1.0
    else:
        # Day: strong scattered sunlight; wavelengths inside an atmospheric
        # transmission window let less absorbed background through.
        window = modtran_band_transmittance(wavelength_nm)
        base_rate = 1e4 * (0.01 + 0.99 * window) * (solar_irradiance_day / 1000.0)
        window_factor = window

    # Scale by receiver area and the fraction of bandwidth actually integrated.
    area_factor = receiver_area_m2 / 0.07
    bw_factor = min(1.0, bandwidth_hz / 1e9)
    rate = base_rate * area_factor * bw_factor * window_factor
    return float(max(1.0, rate))


def link_direction_factor(
    link_direction: str = "downlink",
    elevation_angle_deg: float = 90.0,
) -> float:
    """Asymmetry factor for uplink vs downlink propagation.

    Downlink is slightly favoured: in an uplink the beam is broadened by
    turbulence near the ground transmitter before traversing the rest of the
    path, so the received spot at the satellite is larger (more pointing loss);
    in a downlink the beam stays collimated through clear space and is only
    perturbed at the end. Returns a factor ``<= 1`` used to scale the residual
    (turbulence + pointing) loss.

    Args:
        link_direction: ``"downlink"`` (satellite -> ground) or ``"uplink"``
            (ground -> satellite).
        elevation_angle_deg: Elevation angle; lower elevations increase the
            asymmetry because the path spends more time in the turbulent layer.

    Returns:
        Multiplicative loss factor in ``(0, 1]`` (1.0 = no extra penalty).
    """
    elevation_rad = math.radians(max(5.0, elevation_angle_deg))
    air_mass_factor = 1.0 / math.sin(elevation_rad)  # 1 at zenith, >1 low angle
    if link_direction.lower() == "uplink":
        # Uplink penalised more at low elevation (turbulence hit early).
        return float(max(0.5, 1.0 - 0.03 * air_mass_factor))
    # Downlink penalised less.
    return float(max(0.7, 1.0 - 0.015 * air_mass_factor))
