"""Tests for error correction methods."""

import unittest
import warnings

import numpy as np

from qkdpy.key_management.error_correction import ErrorCorrection


class TestErrorCorrectionCascade(unittest.TestCase):
    """Test the Cascade error correction protocol."""

    def test_cascade_identical_keys_unchanged(self):
        """Cascade on identical keys should return them unchanged."""
        key = [0, 1, 0, 1, 1, 0, 1, 0]
        corrected_a, corrected_b = ErrorCorrection.cascade(key, key, iterations=2)
        self.assertEqual(corrected_a, key)
        self.assertEqual(corrected_b, key)

    def test_cascade_corrects_single_error(self):
        """Cascade should correct a single bit error."""
        alice = [0, 1, 0, 1, 1, 0, 1, 0]
        bob = [0, 1, 0, 0, 1, 0, 1, 0]  # error at index 3
        corrected_a, corrected_b = ErrorCorrection.cascade(
            alice, bob, iterations=4, random_permute=False
        )
        self.assertEqual(corrected_a, alice)
        self.assertEqual(corrected_b, corrected_a)

    def test_cascade_corrects_multiple_errors(self):
        """Cascade should correct multiple bit errors."""
        alice = [0, 1, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1]
        bob = [0, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 0, 1, 0, 1, 1]  # errors at 2, 6
        corrected_a, corrected_b = ErrorCorrection.cascade(
            alice, bob, iterations=4, random_permute=False
        )
        self.assertEqual(corrected_a, corrected_b)

    def test_cascade_mismatched_lengths_raises(self):
        """Cascade on different length keys should raise ValueError."""
        with self.assertRaises(ValueError):
            ErrorCorrection.cascade([0, 1], [0, 1, 0])

    def test_cascade_random_permutation(self):
        """Cascade with random permutation should converge."""
        alice = [0, 1, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1]
        bob = [0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1]  # error at 4
        corrected_a, corrected_b = ErrorCorrection.cascade(
            alice, bob, iterations=4, random_permute=True
        )
        self.assertEqual(corrected_a, corrected_b)

    def test_cascade_empty_keys(self):
        """Cascade on empty keys should return empty lists."""
        corrected_a, corrected_b = ErrorCorrection.cascade([], [])
        self.assertEqual(corrected_a, [])
        self.assertEqual(corrected_b, [])

    def test_cascade_custom_block_sizes(self):
        """Cascade with custom block sizes should work."""
        alice = [0, 1, 0, 1, 1, 0, 1, 0]
        bob = [0, 1, 0, 0, 1, 0, 1, 0]
        corrected_a, corrected_b = ErrorCorrection.cascade(
            alice, bob, block_sizes=[2, 4], iterations=2, random_permute=False
        )
        self.assertEqual(corrected_a, corrected_b)

    def test_cascade_longer_key(self):
        """Cascade should work on longer keys (64 bits)."""
        alice = [
            0,
            1,
            0,
            1,
            1,
            0,
            1,
            0,
            1,
            1,
            0,
            0,
            1,
            0,
            1,
            1,
            0,
            1,
            0,
            1,
            1,
            0,
            1,
            0,
            1,
            1,
            0,
            0,
            1,
            0,
            1,
            1,
            0,
            1,
            0,
            1,
            1,
            0,
            1,
            0,
            1,
            1,
            0,
            0,
            1,
            0,
            1,
            1,
            0,
            1,
            0,
            1,
            1,
            0,
            1,
            0,
            1,
            1,
            0,
            0,
            1,
            0,
            1,
            1,
        ]
        bob = alice.copy()
        bob[5] = 1 - bob[5]
        bob[23] = 1 - bob[23]
        bob[47] = 1 - bob[47]
        corrected_a, corrected_b = ErrorCorrection.cascade(
            alice, bob, iterations=4, random_permute=False
        )
        self.assertEqual(corrected_a, corrected_b)


class TestErrorCorrectionWinnow(unittest.TestCase):
    """Test the Winnow error correction protocol."""

    def test_winnow_identical_keys(self):
        """Winnow on identical keys should return them unchanged."""
        key = [0, 1, 0, 1, 1, 0, 1, 0]
        corrected_a, corrected_b = ErrorCorrection.winnow(
            key, key, iterations=2, random_permute=False
        )
        self.assertEqual(corrected_a, key)

    def test_winnow_corrects_single_error(self):
        """Winnow should correct single bit errors."""
        alice = [0, 1, 0, 1, 1, 0, 1, 0]
        bob = [0, 1, 0, 0, 1, 0, 1, 0]  # error at 3
        corrected_a, corrected_b = ErrorCorrection.winnow(
            alice, bob, iterations=4, random_permute=False
        )
        self.assertEqual(corrected_a, corrected_b)

    def test_winnow_empty_keys(self):
        """Winnow on empty keys should return empty lists."""
        corrected_a, corrected_b = ErrorCorrection.winnow([], [])
        self.assertEqual(corrected_a, [])
        self.assertEqual(corrected_b, [])

    def test_winnow_mismatched_length_raises(self):
        """Winnow on different length keys should raise ValueError."""
        with self.assertRaises(ValueError):
            ErrorCorrection.winnow([0, 1], [0, 1, 0])


class TestErrorCorrectionBiconf(unittest.TestCase):
    """Test the BICONF error correction protocol."""

    def test_biconf_identical_keys(self):
        """BICONF on identical keys should return them unchanged."""
        key = [0, 1, 0, 1, 1, 0, 1, 0]
        corrected_a, corrected_b = ErrorCorrection.biconf(key, key)
        self.assertEqual(corrected_a, key)
        self.assertEqual(corrected_b, key)

    def test_biconf_corrects_errors(self):
        """BICONF should correct errors in keys."""
        alice = [0, 1, 0, 1, 1, 0, 1, 0]
        bob = [0, 1, 0, 0, 1, 0, 1, 0]  # error at 3
        corrected_a, corrected_b = ErrorCorrection.biconf(
            alice, bob, max_iterations=5, error_rate_estimate=0.2
        )
        self.assertEqual(corrected_a, corrected_b)

    def test_biconf_mismatched_length_raises(self):
        """BICONF on different length keys should raise ValueError."""
        with self.assertRaises(ValueError):
            ErrorCorrection.biconf([0, 1], [0, 1, 0])


class TestErrorCorrectionLDPC(unittest.TestCase):
    """Test the LDPC error correction.

    Note: The LDPC implementation uses random matrices and may not always converge.
    We test basic functionality and edge cases.
    """

    def test_ldpc_identical_keys(self):
        """LDPC on identical keys should return them unchanged."""
        alice = [0, 1, 0, 1, 1, 0, 1, 0]
        bob = alice.copy()
        # Suppress runtime warnings from numpy operations
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            corrected_a, corrected_b = ErrorCorrection.ldpc(
                alice, bob, max_iterations=10
            )
        self.assertEqual(corrected_a, alice)

    def test_ldpc_empty_keys(self):
        """LDPC on empty keys should not crash."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            corrected_a, corrected_b = ErrorCorrection.ldpc([], [])
        self.assertEqual(corrected_a, [])
        self.assertEqual(corrected_b, [])

    def test_ldpc_mismatched_length_raises(self):
        """LDPC on different length keys should raise ValueError."""
        with self.assertRaises(ValueError):
            ErrorCorrection.ldpc([0, 1], [0, 1, 0])

    def test_ldpc_custom_matrix(self):
        """LDPC with a provided parity check matrix."""
        n = 8
        m = 4
        H = np.zeros((m, n), dtype=int)
        # Create a simple parity check matrix
        for j in range(m):
            for i in range(j * 2, j * 2 + 2):
                if i < n:
                    H[j, i] = 1
        alice = [0, 1, 0, 1, 1, 0, 1, 0]
        bob = alice.copy()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            corrected_a, corrected_b = ErrorCorrection.ldpc(
                alice, bob, parity_check_matrix=H, max_iterations=10
            )
        self.assertEqual(len(corrected_a), len(alice))
        self.assertEqual(len(corrected_b), len(bob))


class TestErrorCorrectionHelpers(unittest.TestCase):
    """Test helper functions in ErrorCorrection."""

    def test_hamming_distance_identical(self):
        """Hamming distance of a key with itself should be 0."""
        key = [0, 1, 0, 1, 1, 0]
        self.assertEqual(ErrorCorrection.hamming_distance(key, key), 0)

    def test_hamming_distance_different(self):
        """Hamming distance should count differing positions."""
        a = [0, 1, 0, 1, 1, 0]
        b = [0, 1, 1, 1, 0, 0]  # differs at index 2 and 4
        self.assertEqual(ErrorCorrection.hamming_distance(a, b), 2)

    def test_hamming_distance_empty(self):
        """Hamming distance of empty keys should be 0."""
        self.assertEqual(ErrorCorrection.hamming_distance([], []), 0)

    def test_hamming_distance_mismatched_length_raises(self):
        """Hamming distance with different lengths should raise."""
        with self.assertRaises(ValueError):
            ErrorCorrection.hamming_distance([0], [0, 1])

    def test_error_rate_identical(self):
        """Error rate of identical keys should be 0."""
        self.assertEqual(ErrorCorrection.error_rate([0, 1, 0], [0, 1, 0]), 0.0)

    def test_error_rate_all_different(self):
        """Error rate of completely different keys should be 1.0."""
        self.assertEqual(ErrorCorrection.error_rate([0, 0, 0], [1, 1, 1]), 1.0)

    def test_error_rate_partial(self):
        """Error rate should be fraction of differing bits."""
        a = [0, 1, 0, 1]
        b = [0, 1, 1, 0]  # 2 of 4 differ
        self.assertAlmostEqual(ErrorCorrection.error_rate(a, b), 0.5)

    def test_error_rate_empty(self):
        """Error rate of empty keys should be 0."""
        self.assertEqual(ErrorCorrection.error_rate([], []), 0.0)

    def test_low_density_parity_check_identical(self):
        """low_density_parity_check should handle identical keys (long enough for LDPC)."""
        key = [0, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1, 1]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            corrected_a, corrected_b, iters = ErrorCorrection.low_density_parity_check(
                key, key, code_rate=0.5, max_iterations=5
            )
        self.assertEqual(corrected_a, key)
        self.assertEqual(corrected_b, key)


if __name__ == "__main__":
    unittest.main()
