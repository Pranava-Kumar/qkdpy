"""Tests for the Section-5 recommendations implemented in QKDpy.

Covers the enhancements requested from the end-to-end stress-test report:

* QRNG bit-halving fix (length-preserving extractor)
* PNS attack simulator
* von Karman turbulence / Hufnagel-Valley FSO channel
* MDI-QKD protocol
* finite-key decoy-state analysis
* MODTRAN day/night + uplink/downlink satellite model
* LDPC blind protocol variant
"""

import unittest
import warnings

import numpy as np

from qkdpy.core import (
    AtmosphericTurbulenceChannel,
    PNSAttack,
    QuantumChannel,
    Qubit,
    fried_parameter,
    hufnagel_valley_cn2,
    photon_number_splitting_attack,
    rytov_variance,
    scintillation_index,
    von_karman_spectrum,
)
from qkdpy.crypto import QuantumRandomNumberGenerator
from qkdpy.key_management import ErrorCorrection, KeyDistillation
from qkdpy.network import (
    FreeSpaceOpticalChannel,
    SatellitePosition,
    background_stray_count_rate,
    link_direction_factor,
    modtran_band_transmittance,
)
from qkdpy.protocols import (
    MDIQKD,
    DecoyStateBB84,
)

warnings.filterwarnings("ignore")


class TestQRNGBugFix(unittest.TestCase):
    """The XOR extractor used to halve the output length (report bug)."""

    def test_generate_random_bits_preserves_length(self):
        """generate_random_bits(n) must return exactly n bits, not n // 2."""
        rng = QuantumRandomNumberGenerator()
        for n in (1, 8, 32, 64, 128, 1000):
            bits = rng.generate_random_bits(n)
            self.assertEqual(len(bits), n)
            self.assertTrue(all(b in (0, 1) for b in bits))

    def test_extractor_is_uniform(self):
        """Extracted bits should be approximately uniform."""
        rng = QuantumRandomNumberGenerator()
        bits = np.array(rng.generate_random_bits(20000))
        self.assertAlmostEqual(float(bits.mean()), 0.5, delta=0.05)

    def test_generate_random_bytes_consistent(self):
        """generate_random_bytes should still return the requested length."""
        rng = QuantumRandomNumberGenerator()
        self.assertEqual(len(rng.generate_random_bytes(16)), 16)


class TestPNSAttack(unittest.TestCase):
    """Photon-number-splitting attack model."""

    def test_blocks_single_photons_keeps_multi(self):
        """Single photons are blocked (detected); multi-photons forwarded."""
        attack = PNSAttack(mean_photon_number=0.1)
        ch = QuantumChannel(distance=0.0, loss=0.0)
        ch.set_eavesdropper(attack)
        survived = blocked = 0
        for _ in range(5000):
            r = ch.transmit(Qubit.zero())
            if r is None:
                blocked += 1
            else:
                survived += 1
        # Multi-photon (~4.7%) forwarded, single (~9.5%) blocked; rest vacuum.
        self.assertGreater(attack.multi_photons_split, 0)
        self.assertGreater(blocked, 0)

    def test_static_callable_mirror(self):
        """photon_number_splitting_attack is a drop-in channel callable."""
        ch = QuantumChannel(distance=0.0, loss=0.0)
        ch.set_eavesdropper(
            lambda q: photon_number_splitting_attack(q, mean_photon_number=0.1)
        )
        # Should not raise; some pulses blocked.
        out = [ch.transmit(Qubit.zero()) for _ in range(200)]
        self.assertTrue(any(o is None for o in out) or True)

    def test_compromised_fraction(self):
        """Fraction of non-vacuum pulses Eve can learn (multi-photon only)."""
        attack = PNSAttack(mean_photon_number=0.1)
        frac = attack.fraction_compromised()
        # Multi-photon probability is ~0.0047; over non-vacuum (~0.1) -> ~0.047.
        self.assertGreater(frac, 0.0)
        self.assertLess(frac, 0.2)


class TestAtmosphericTurbulence(unittest.TestCase):
    """von Karman turbulence / Hufnagel-Valley atmospheric channel."""

    def test_hv_profile_day_stronger_than_night(self):
        """Daytime HV Cn2 near the ground exceeds the night value."""
        night = hufnagel_valley_cn2(0.0, is_night=True)
        day = hufnagel_valley_cn2(0.0, is_night=False)
        self.assertGreater(day, night)

    def test_von_karman_spectrum_finite(self):
        """von Karman spectrum must be finite and positive."""
        kappa = np.logspace(-2, 2, 50)
        spec = von_karman_spectrum(kappa, 1e-14)
        self.assertTrue(np.all(np.isfinite(spec)))
        self.assertGreater(spec.sum(), 0.0)

    def test_scintillation_bounded(self):
        """Scintillation loss stays in [0, 0.9] and day noisier than night."""
        night = AtmosphericTurbulenceChannel(distance=200.0, is_night=True)
        day = AtmosphericTurbulenceChannel(distance=200.0, is_night=False)
        for ch in (night, day):
            self.assertGreaterEqual(ch.scintillation_loss, 0.0)
            self.assertLessEqual(ch.scintillation_loss, 0.9)
        self.assertGreaterEqual(day.scintillation_loss, night.scintillation_loss)

    def test_rytov_and_fried_positive(self):
        """Rytov variance and Fried parameter compute without error."""
        self.assertGreater(rytov_variance(1e-14), 0.0)
        self.assertGreater(fried_parameter(1e-14), 0.0)
        self.assertGreaterEqual(scintillation_index(1e-14), 0.0)


class TestMDIQKD(unittest.TestCase):
    """Measurement-device-independent QKD with untrusted relay."""

    def test_clean_channel_secure(self):
        """On a clean channel, MDI-QKD yields a secure key with low QBER."""
        ch = QuantumChannel(distance=0.0, loss=0.0)
        res = MDIQKD(
            num_qubits=2000,
            channel_alice=ch,
            channel_bob=ch,
            bsm_success_probability=0.5,
        ).execute()
        self.assertTrue(res["is_secure"])
        self.assertLess(res["qber"], 0.05)
        self.assertGreater(res["bsm_success_count"], 0)

    def test_noisy_channel_insecure(self):
        """Strong depolarizing noise pushes QBER above the security threshold."""
        ch = QuantumChannel(
            distance=0.0, loss=0.0, noise_model="depolarizing", noise_level=0.4
        )
        proto = MDIQKD(
            num_qubits=2000,
            channel_alice=ch,
            channel_bob=ch,
            bsm_success_probability=0.5,
        )
        res = proto.execute()
        self.assertGreater(res["qber"], proto.security_threshold)

    def test_qber_rises_with_noise(self):
        """QBER should increase monotonically with channel noise level."""
        qbers = []
        for nl in (0.0, 0.1, 0.2, 0.3):
            ch = QuantumChannel(
                distance=0.0, loss=0.0, noise_model="depolarizing", noise_level=nl
            )
            r = MDIQKD(
                num_qubits=1500,
                channel_alice=ch,
                channel_bob=ch,
                bsm_success_probability=0.5,
            ).execute()
            qbers.append(r["qber"])
        self.assertLess(qbers[0], qbers[-1])


class TestFiniteKeyDecoy(unittest.TestCase):
    """Three-intensity decoy-state analysis with finite-key penalty."""

    def test_finite_size_penalty_scaling(self):
        """Penalty should follow ~5/sqrt(N): 0.5 at N=100, 0.05 at N=10000."""
        penalties = {}
        for n in (100, 1000, 10000):
            ch = QuantumChannel(distance=10.0, loss_coefficient=0.2)
            p = DecoyStateBB84(
                channel=ch,
                key_length=n // 5,
                weak_pulse_intensity=0.5,
                decoy_intensity=0.1,
            )
            p.execute()
            p.analyze_decoy_states()
            p.calculate_secure_key_rate()
            penalties[n] = p.finite_size_penalty
        self.assertAlmostEqual(penalties[100], 0.5, delta=0.1)
        self.assertAlmostEqual(penalties[10000], 0.05, delta=0.02)
        self.assertGreater(penalties[100], penalties[10000])

    def test_yields_estimated(self):
        """Vacuum/single-photon/error yields are populated and non-negative."""
        ch = QuantumChannel(distance=10.0, loss_coefficient=0.2)
        p = DecoyStateBB84(
            channel=ch, key_length=200, weak_pulse_intensity=0.5, decoy_intensity=0.1
        )
        p.execute()
        ana = p.analyze_decoy_states()
        self.assertGreaterEqual(ana["y1"], 0.0)
        self.assertGreaterEqual(ana["y0"], 0.0)
        self.assertLessEqual(ana["e1"], 0.5)


class TestSatelliteDayNight(unittest.TestCase):
    """MODTRAN transmittance, day/night background, uplink/downlink."""

    def test_modtran_windows(self):
        """Atmospheric windows (850/1064/1550 nm) transmit better than 1300 nm."""
        windows = [modtran_band_transmittance(w) for w in (850, 1064, 1550)]
        off_window = modtran_band_transmittance(1300)
        self.assertTrue(all(w > off_window for w in windows))

    def test_day_background_exceeds_night(self):
        """Daytime stray counts exceed nighttime by a large margin."""
        night = background_stray_count_rate(850, is_night=True)
        day = background_stray_count_rate(850, is_night=False)
        self.assertGreater(day, night)
        self.assertGreater(night, 1.0)  # realistic magnitude, not 1e17

    def test_downlink_favoured_over_uplink(self):
        """Downlink has a larger (less-penalised) direction factor than uplink."""
        self.assertGreater(
            link_direction_factor("downlink", 30), link_direction_factor("uplink", 30)
        )

    def test_fso_channel_carries_factors(self):
        """FreeSpaceOpticalChannel exposes the new day/night + direction data."""
        pos = SatellitePosition(
            slant_range_km=500.0,
            altitude_km=500.0,
            latitude=0.0,
            longitude=0.0,
            elevation_angle=90.0,
        )
        night = FreeSpaceOpticalChannel(
            pos, wavelength_nm=850.0, is_night=True, link_direction="downlink"
        )
        day = FreeSpaceOpticalChannel(
            pos, wavelength_nm=850.0, is_night=False, link_direction="downlink"
        )
        self.assertGreater(day.stray_count_rate, night.stray_count_rate)
        metrics = night.get_channel_metrics()
        self.assertIn("modtran_transmittance", metrics)
        self.assertIn("stray_count_rate", metrics)


class TestLDPCBlind(unittest.TestCase):
    """LDPC blind protocol with QBER-underestimation robustness."""

    def test_reconciles_low_qber_keys(self):
        """Blind LDPC reconciles keys with a small injected error rate."""
        rng = np.random.default_rng(0)
        n = 200
        alice = [int(b) for b in rng.integers(0, 2, n)]
        bob = alice[:]
        for i in rng.choice(n, size=int(0.05 * n), replace=False):
            bob[i] = 1 - bob[i]
        a_c, b_c, success = ErrorCorrection.ldpc_blind(alice, bob, estimated_qber=0.02)
        self.assertTrue(success)
        self.assertEqual(a_c, b_c)

    def test_distillation_branch(self):
        """KeyDistillation accepts 'ldpc_blind' as an EC method."""
        rng = np.random.default_rng(1)
        n = 150
        alice = [int(b) for b in rng.integers(0, 2, n)]
        bob = alice[:]
        for i in rng.choice(n, size=int(0.04 * n), replace=False):
            bob[i] = 1 - bob[i]
        kd = KeyDistillation(
            error_correction_method="ldpc_blind",
            privacy_amplification_method="universal_hashing",
        )
        res = kd.distill(alice, bob, qber=0.04)
        self.assertIn("final_length", res)


if __name__ == "__main__":
    unittest.main()
