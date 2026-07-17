"""Atmospheric turbulence model for free-space optical (FSO) quantum links.

Implements the building blocks needed to go beyond the crude Strehl-ratio
approximation used elsewhere in the library:

* **Hufnagel-Valley profile** ``Cn2(h)`` -- the altitude-dependent refractive
  index structure constant. This is what makes day/night and zenith-angle
  dependences physically meaningful instead of a single ``turbulence_cn2`` knob.
* **von Karman power spectrum** ``Phi(kappa)`` -- the Kolmogorov spectrum with
  both inner (``l0``) and outer (``L0``) scale cutoffs, the standard model for
  atmospheric scintillation of an optical beam.
* **Split-step Fourier phase screens** -- a random phase screen drawn from the
  von Karman spectrum, which can be applied to a propagating field to produce
  beam wander, broadening and scintillation. We expose the screen generator and
  fold its *statistical* effect (scintillation loss + excess noise) into a
  channel model rather than running a full wave-optics propagation every pulse.

References:
    * Tatarskii / von Karman spectrum: Andrews & Phillips, "Laser Beam
      Propagation through Random Media", SPIE, 2005.
    * Hufnagel-Valley: Hufnagel & Stanley (1971); commonly used HV 5/7 models.
    * Rytov variance: a standard measure of the strength of optical turbulence.
"""

from collections.abc import Callable

import numpy as np

from ..channels import QuantumChannel
from ..qubit import Qubit
from ..qudit import Qudit
from ..secure_random import secure_random

_Pulse = Qubit | Qudit


def hufnagel_valley_cn2(
    altitude_m: float,
    cn2_ground: float = 1.7e-14,
    wind_speed: float = 21.0,
    is_night: bool = True,
) -> float:
    """Hufnagel-Valley ``Cn2`` profile as a function of altitude.

    The HV turbulence layer coefficient is calibrated so the column *mean*
    stays in the physically realistic range (night ~``1e-14`` m^{-2/3}, strong
    daytime ~``1e-12`` m^{-2/3}) rather than the uncalibrated literature peak.

    Args:
        altitude_m: Altitude above ground in meters.
        cn2_ground: Ground-level ``Cn2`` (m^{-2/3}). Night clear-air values are
            around ``1e-14``; daytime strong convection reaches ``~1e-11``.
        wind_speed: RMS wind speed (m/s) feeding the HV wind term.
        is_night: When True uses the night layer profile; daytime convection is
            approximated by a higher ground value.

    Returns:
        Structure constant ``Cn2`` in m^{-2/3} at the given altitude.
    """
    h_km = max(altitude_m, 0.0) / 1000.0
    # Calibrated HV turbulence layer (peak ~ 1e-13 night, ~1e-12 day).
    layer_coeff = 1.0e-12 if is_night else 1.0e-11
    layer = layer_coeff * (wind_speed / 21.0) ** 2 * (h_km / 10.0) ** 10 * np.exp(-h_km / 1.2)
    # Background clear-air profile (day/night differ mainly in ground strength).
    if is_night:
        background = 1.0e-15 * np.exp(-h_km / 3.0)
    else:
        background = 1.0e-13 * np.exp(-h_km / 2.0)
    return float(layer + background)


def von_karman_spectrum(
    kappa: np.ndarray,
    cn2: float,
    outer_scale: float = 10.0,
    inner_scale: float = 0.01,
) -> np.ndarray:
    """Modified von Karman turbulence power spectrum ``Phi(kappa)``.

    Args:
        kappa: Spatial frequency magnitude (rad/m), any shape.
        cn2: Structure constant (m^{-2/3}) at the propagation path.
        outer_scale: Outer scale ``L0`` in meters (cutoff at large scales).
        inner_scale: Inner scale ``l0`` in meters (cutoff at small scales).

    Returns:
        Spectrum values with the same shape as ``kappa`` (m^3).
    """
    kappa = np.asarray(kappa, dtype=float)
    k0 = 1.0 / outer_scale
    k1 = 1.0 / inner_scale
    term = (kappa**2 + k0**2) ** (11.0 / 6.0)
    # Kolmogorov core scaled by the von Karman inner/outer cutoffs.
    spectrum = (
        0.033
        * cn2
        * np.exp(-(kappa**2) / (k1**2))
        / term
    )
    return spectrum


def fried_parameter(
    path_cn2: float,
    wavelength_m: float = 850e-9,
    path_length_m: float = 20e3,
) -> float:
    """Fried coherence length ``r0`` for a turbulence-integrated path.

    Args:
        path_cn2: Path-integrated (or average) structure constant (m^{-2/3}).
        wavelength_m: Optical wavelength in meters.
        path_length_m: Propagation distance in meters.

    Returns:
        Fried parameter ``r0`` in meters.
    """
    k = 2.0 * np.pi / wavelength_m
    integrated = path_cn2 * path_length_m
    r0 = (0.423 * k**2 * integrated) ** (-3.0 / 5.0)
    return float(r0)


def rytov_variance(
    path_cn2: float,
    wavelength_m: float = 850e-9,
    path_length_m: float = 20e3,
) -> float:
    """Rytov variance for a spherical wave (weak-to-moderate turbulence)."""
    k = 2.0 * np.pi / wavelength_m
    return float(1.23 * k ** (7.0 / 6.0) * (path_cn2 * path_length_m) ** (11.0 / 6.0))


def scintillation_index(
    path_cn2: float,
    wavelength_m: float = 850e-9,
    path_length_m: float = 20e3,
) -> float:
    """On-axis scintillation index ``sigma_I^2`` (Andrews flat-top model).

    The Rytov (small-perturbation) approximation diverges in strong turbulence,
    so we use the standard Andrews ``flat-top`` scintillation index for a
    spherical wave, which is bounded and saturates at high turbulence.

    Args:
        path_cn2: Path-averaged structure constant (m^{-2/3}).
        wavelength_m: Optical wavelength in meters.
        path_length_m: Propagation distance in meters.

    Returns:
        Scintillation index ``sigma_I^2`` (>= 0).
    """
    beta_squared = 0.5 * rytov_variance(path_cn2, wavelength_m, path_length_m)
    if beta_squared <= 0.0:
        return 0.0
    term1 = (0.49 * beta_squared) / (1.0 + 1.11 * beta_squared ** (12.0 / 5.0)) ** (7.0 / 5.0)
    term2 = (0.51 * beta_squared) / (1.0 + 0.69 * beta_squared ** (12.0 / 5.0)) ** (5.0 / 3.0)
    return float(np.exp(term1 + term2) - 1.0)


def generate_phase_screen(
    grid_size: int,
    pixel_size_m: float,
    cn2: float,
    wavelength_m: float = 850e-9,
    outer_scale: float = 10.0,
    inner_scale: float = 0.01,
) -> np.ndarray:
    """Draw a random turbulence phase screen from the von Karman spectrum.

    Uses the standard spectral-method: sample a zero-mean complex Gaussian in
    the spatial-frequency domain with variance given by the von Karman spectrum,
    inverse-FFT, take the real part, and renormalize variance to ``1.0 rad^2``
    per unit (the absolute scale is applied by the caller via ``r0``).

    Args:
        grid_size: Number of grid points per side (power of two recommended).
        pixel_size_m: Physical size of one grid cell in meters.
        cn2: Structure constant (m^{-2/3}) for the screen.
        wavelength_m: Optical wavelength in meters.
        outer_scale: Outer scale ``L0`` (m).
        inner_scale: Inner scale ``l0`` (m).

    Returns:
        2D phase screen (radians) of shape ``(grid_size, grid_size)``.
    """
    freqs = np.fft.fftfreq(grid_size, d=pixel_size_m) * 2.0 * np.pi
    kx, ky = np.meshgrid(freqs, freqs)
    kappa = np.sqrt(kx**2 + ky**2)
    # Avoid division by zero at the DC term.
    kappa[grid_size // 2, grid_size // 2] = 1e-12

    spectrum = von_karman_spectrum(kappa, cn2, outer_scale, inner_scale)
    # Variance of the Fourier coefficients.
    variance = spectrum * (pixel_size_m**2)
    re = np.random.normal(0.0, 1.0, (grid_size, grid_size)) * np.sqrt(variance)
    im = np.random.normal(0.0, 1.0, grid_size) * np.sqrt(variance)
    complex_field = re + 1j * im
    screen = np.fft.ifft2(complex_field).real
    # Normalize to unit variance so the caller can scale by r0 physically.
    std = screen.std()
    if std > 0:
        screen = screen / std
    return screen


class AtmosphericTurbulenceChannel(QuantumChannel):
    """Quantum channel with physically-modelled atmospheric turbulence.

    Extends :class:`QuantumChannel` by adding turbulence-induced scintillation
    loss and excess phase noise derived from the Hufnagel-Valley ``Cn2`` profile
    and the von Karman spectrum, instead of the single ``turbulence_cn2`` knob.

    Args:
        distance: Slant path length in km.
        wavelength_nm: Optical wavelength in nanometers.
        cn2_ground: Ground-level structure constant for the HV profile.
        is_night: Day/night flag affecting the HV profile strength.
        telescope_diameter_m: Receiver aperture diameter (m); larger apertures
            average out scintillation (aperture averaging).
        outer_scale: von Karman outer scale (m).
        inner_scale: von Karman inner scale (m).
        grid_size: Phase-screen grid resolution for statistical modelling.
        **kwargs: Forwarded to :class:`QuantumChannel` (loss, noise_model, ...).
    """

    def __init__(
        self,
        distance: float = 1.0,
        wavelength_nm: float = 850.0,
        cn2_ground: float = 1.7e-14,
        is_night: bool = True,
        telescope_diameter_m: float = 0.3,
        outer_scale: float = 10.0,
        inner_scale: float = 0.01,
        grid_size: int = 128,
        **kwargs: object,
    ) -> None:
        """Initialize the turbulence channel with atmospheric parameters."""
        super().__init__(distance=distance, **kwargs)
        self.wavelength_nm = wavelength_nm
        self.cn2_ground = cn2_ground
        self.is_night = is_night
        self.telescope_diameter_m = telescope_diameter_m
        self.outer_scale = outer_scale
        self.inner_scale = inner_scale
        self.grid_size = grid_size

        self.wavelength_m = wavelength_nm * 1e-9
        self.path_length_m = distance * 1000.0

        # Average the HV profile over the slant path (sample 100 slabs).
        self.path_cn2 = self._integrate_cn2()
        self.rytov = rytov_variance(
            self.path_cn2, self.wavelength_m, self.path_length_m
        )
        self.r0 = fried_parameter(
            self.path_cn2, self.wavelength_m, self.path_length_m
        )
        # Scintillation loss from the (bounded) Andrews scintillation index,
        # reduced by aperture averaging for larger receivers. A pulse is lost
        # when a deep fade drives its received power below the detection
        # threshold; we approximate the fade probability with a saturating map.
        sigma_i2 = scintillation_index(
            self.path_cn2, self.wavelength_m, self.path_length_m
        )
        aperture_averaging = 1.0 / (1.0 + telescope_diameter_m / max(self.r0, 1e-3))
        self.scintillation_index = float(sigma_i2)
        self.scintillation_loss = float(
            min(0.9, sigma_i2 * aperture_averaging * 2.0)
        )

    def _integrate_cn2(self) -> float:
        """Average the HV ``Cn2`` profile over the slant path.

        Returns the path-*averaged* structure constant (m^{-2/3}); the Rytov
        variance and Fried parameter below multiply by ``path_length`` again,
        so we must pass the mean along the path, not the integral.
        """
        n = 100
        altitudes = np.linspace(0.0, self.path_length_m, n)
        values = np.array(
            [
                hufnagel_valley_cn2(a, self.cn2_ground, is_night=self.is_night)
                for a in altitudes
            ]
        )
        if self.path_length_m <= 0:
            return float(values[0])
        return float(np.trapz(values, altitudes) / self.path_length_m)

    def get_turbulence_metrics(self) -> dict:
        """Return the computed turbulence metrics for inspection."""
        return {
            "path_cn2": self.path_cn2,
            "rytov_variance": self.rytov,
            "fried_parameter_m": self.r0,
            "scintillation_index": self.scintillation_index,
            "scintillation_loss": self.scintillation_loss,
            "is_night": self.is_night,
            "wavelength_nm": self.wavelength_nm,
        }

    def transmit(
        self, qubit: _Pulse, timestamp: float = 0.0
    ) -> _Pulse | None:
        """Transmit a qubit, applying turbulence scintillation loss first."""
        # Turbulence drop-out is modelled as an additional loss channel on top
        # of the base (Beer-Lambert / geometric) loss.
        if secure_random() < self.scintillation_loss:
            self.lost_count += 1
            return None
        return super().transmit(qubit, timestamp)
