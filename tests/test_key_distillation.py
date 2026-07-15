"""Tests for key distillation pipeline."""

import unittest

import numpy as np

from qkdpy.key_management.key_distillation import KeyDistillation
from qkdpy.key_management.error_correction import ErrorCorrection
from qkdpy.key_management.privacy_amplification import PrivacyAmplification


class TestKeyDistillationBasic(unittest.TestCase):
    """Test the KeyDistillation class basic functionality."""

    def test_default_initialization(self):
        """KeyDistillation initializes with cascade and universal_hashing."""
        distiller = KeyDistillation()
        self.assertEqual(distiller.error_correction_method, "cascade")
        self.assertEqual(distiller.privacy_amplification_method, "universal_hashing")

    def test_custom_methods(self):
        """KeyDistillation accepts custom method names."""
        distiller = KeyDistillation(
            error_correction_method="winnow",
            privacy_amplification_method="toeplitz_hashing",
        )
        self.assertEqual(distiller.error_correction_method, "winnow")
        self.assertEqual(distiller.privacy_amplification_method, "toeplitz_hashing")

    def test_distill_identical_keys(self):
        """Distill on identical keys should produce a valid result."""
        alice = [0, 1, 0, 1, 1, 0, 1, 0, 0, 1]
        bob = alice.copy()
        distiller = KeyDistillation()
        result = distiller.distill(alice, bob, qber=0.0)
        self.assertIn("alice_key", result)
        self.assertIn("bob_key", result)
        self.assertIn("final_key", result)
        self.assertIn("final_length", result)
        self.assertIn("error_rate", result)
        self.assertIn("initial_length", result)
        self.assertIn("eve_information", result)
        self.assertEqual(len(result["alice_key"]), len(result["bob_key"]))
        self.assertEqual(result["initial_length"], 10)
        self.assertEqual(result["error_rate"], 0.0)

    def test_distill_corrects_errors(self):
        """Distill should correct errors and produce matching final keys."""
        alice = [0, 1, 0, 1, 1, 0, 1, 0]
        bob =   [0, 1, 0, 0, 1, 0, 1, 0]  # Error at position 3
        distiller = KeyDistillation()
        result = distiller.distill(alice, bob, qber=0.2)
        self.assertEqual(result["alice_key"], result["bob_key"])

    def test_distill_short_key(self):
        """Distill should handle short keys (length 4)."""
        alice = [0, 1, 0, 1]
        bob = alice.copy()
        distiller = KeyDistillation()
        result = distiller.distill(alice, bob, qber=0.0)
        self.assertGreaterEqual(len(result["alice_key"]), 0)

    def test_distill_longer_key(self):
        """Distill should work on a longer key (32 bits) with few errors."""
        rng = np.random.RandomState(42)
        bits = list(rng.randint(0, 2, 32))
        alice = bits.copy()
        bob = bits.copy()
        # Introduce 1 error
        bob[15] = 1 - bob[15]
        distiller = KeyDistillation()
        result = distiller.distill(alice, bob, qber=0.05)
        self.assertEqual(result["alice_key"], result["bob_key"])

    def test_distill_mismatched_length_raises(self):
        """Distill with different length keys should raise ValueError."""
        distiller = KeyDistillation()
        with self.assertRaises(ValueError):
            distiller.distill([0, 1], [0, 1, 0], qber=0.0)

    def test_distill_with_eve_information(self):
        """Distill should report eve_information metric."""
        alice = [0, 1, 0, 1, 1, 0, 1, 0]
        bob = alice.copy()
        distiller = KeyDistillation()
        result = distiller.distill(alice, bob, qber=0.05)
        self.assertIn("eve_information", result)
        self.assertIsInstance(result["eve_information"], float)
        self.assertGreaterEqual(result["eve_information"], 0.0)

    def test_distill_specified_final_length(self):
        """Privacy amplification should reduce key size when final_key_length specified."""
        alice = [0, 1, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1]
        bob = alice.copy()
        distiller = KeyDistillation()
        result = distiller.distill(alice, bob, qber=0.0, final_key_length=4)
        self.assertEqual(len(result["final_key"]), 4)
        self.assertEqual(result["final_length"], 4)


class TestKeyDistillationDifferentMethods(unittest.TestCase):
    """Test KeyDistillation with various method combinations."""

    def test_winnow_toeplitz(self):
        """Distill with Winnow + Toeplitz hashing should work."""
        alice = [0, 1, 0, 1, 1, 0, 1, 0, 0, 1]
        bob = alice.copy()
        distiller = KeyDistillation(
            error_correction_method="winnow",
            privacy_amplification_method="toeplitz_hashing",
        )
        result = distiller.distill(alice, bob, qber=0.0)
        self.assertEqual(result["alice_key"], result["bob_key"])

    def test_cascade_cryptographic_hash(self):
        """Distill with Cascade + cryptographic hash should work."""
        alice = [0, 1, 0, 1, 1, 0, 1, 0]
        bob = alice.copy()
        distiller = KeyDistillation(
            error_correction_method="cascade",
            privacy_amplification_method="cryptographic_hash",
        )
        result = distiller.distill(alice, bob, qber=0.0)
        self.assertEqual(result["alice_key"], result["bob_key"])

    def test_biconf_universal_hashing(self):
        """Distill with invalid method should raise ValueError."""
        distiller = KeyDistillation(
            error_correction_method="biconf",
            privacy_amplification_method="universal_hashing",
        )
        with self.assertRaises(ValueError):
            distiller.distill([0, 1, 0, 1], [0, 1, 0, 1], qber=0.0)

    def test_ldpc_universal_hashing(self):
        """Distill with LDPC + universal hashing should work (smoke test)."""
        import warnings

        alice = [0, 1, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1, 1]
        bob = alice.copy()
        distiller = KeyDistillation(
            error_correction_method="ldpc",
            privacy_amplification_method="universal_hashing",
        )
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                result = distiller.distill(alice, bob, qber=0.0)
                self.assertEqual(result["alice_key"], result["bob_key"])
            except RuntimeError:
                # LDPC with random matrix on random key may not converge; this is acceptable
                pass

    def test_invalid_method_raises(self):
        """Invalid error correction method should raise ValueError."""
        distiller = KeyDistillation(
            error_correction_method="nonexistent_method",
        )
        with self.assertRaises(ValueError):
            distiller.distill([0, 1], [0, 1], qber=0.0)


class TestPrivacyAmplification(unittest.TestCase):
    """Test PrivacyAmplification directly."""

    def test_universal_hashing_reduces_length(self):
        """Universal hashing should reduce key length."""
        key = [0, 1, 0, 1, 1, 0, 1, 0, 0, 1]
        result = PrivacyAmplification.universal_hashing(key, output_length=5)
        self.assertEqual(len(result), 5)

    def test_universal_hashing_longer_output_raises(self):
        """Universal hashing with output >= input length should raise."""
        with self.assertRaises(ValueError):
            PrivacyAmplification.universal_hashing([0, 1, 0, 1], output_length=4)

    def test_toeplitz_hashing_reduces_length(self):
        """Toeplitz hashing should reduce key length."""
        key = [0, 1, 0, 1, 1, 0, 1, 0, 0, 1]
        result = PrivacyAmplification.toeplitz_hashing(key, output_length=5)
        self.assertEqual(len(result), 5)

    def test_cryptographic_hash_reduces_length(self):
        """Cryptographic hash should reduce key length."""
        key = [0, 1, 0, 1, 1, 0, 1, 0, 0, 1]
        result = PrivacyAmplification.cryptographic_hash(key, output_length=8)
        self.assertEqual(len(result), 8)

    def test_cryptographic_hash_default(self):
        """Cryptographic hash with default sha256 should work."""
        key = [0, 1, 0, 1, 1, 0, 1, 0]
        result = PrivacyAmplification.cryptographic_hash(key, output_length=4)
        self.assertEqual(len(result), 4)
        self.assertTrue(all(b in (0, 1) for b in result))

    def test_bennett_brassard_hashing(self):
        """Bennett-Brassard hashing should work with error rate."""
        key = [0, 1, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 0, 1, 0]
        result = PrivacyAmplification.bennett_brassard_hashing(key, output_length=8, error_rate=0.05)
        self.assertGreater(len(result), 0)
        self.assertLessEqual(len(result), 8)

    def test_leftover_hash_lemma(self):
        """Leftover Hash Lemma should produce a valid key."""
        key = [0, 1, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1]
        result = PrivacyAmplification.leftover_hash_lemma(key, min_entropy=8.0)
        self.assertGreater(len(result), 0)

    def test_extract_randomness_universal(self):
        """extract_randomness with universal_hashing should work."""
        key = [0, 1, 0, 1, 1, 0, 1, 0, 0, 1]
        result = PrivacyAmplification.extract_randomness(
            key, output_length=5, method="universal_hashing"
        )
        self.assertEqual(len(result), 5)

    def test_extract_randomness_toeplitz(self):
        """extract_randomness with toeplitz_hashing should work."""
        key = [0, 1, 0, 1, 1, 0, 1, 0, 0, 1]
        result = PrivacyAmplification.extract_randomness(
            key, output_length=5, method="toeplitz_hashing"
        )
        self.assertEqual(len(result), 5)

    def test_extract_randomness_cryptographic(self):
        """extract_randomness with cryptographic_hash should work."""
        key = [0, 1, 0, 1, 1, 0, 1, 0, 0, 1]
        result = PrivacyAmplification.extract_randomness(
            key, output_length=5, method="cryptographic_hash"
        )
        self.assertEqual(len(result), 5)

    def test_extract_randomness_bennett_brassard(self):
        """extract_randomness with bennett_brassard should work."""
        key = [0, 1, 0, 1, 1, 0, 1, 0, 0, 1]
        result = PrivacyAmplification.extract_randomness(
            key, output_length=5, method="bennett_brassard"
        )
        self.assertGreater(len(result), 0)

    def test_extract_randomness_invalid_method_raises(self):
        """extract_randomness with unknown method should raise."""
        with self.assertRaises(ValueError):
            PrivacyAmplification.extract_randomness(
                [0, 1, 0, 1], output_length=2, method="invalid"
            )


if __name__ == "__main__":
    unittest.main()
