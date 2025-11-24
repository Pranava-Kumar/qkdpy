"""Tests for advanced error correction methods."""

import unittest

import numpy as np

from qkdpy.key_management import AdvancedErrorCorrection


class TestAdvancedErrorCorrection(unittest.TestCase):
    """Test cases for the AdvancedErrorCorrection class."""

    def test_ldpc_error_correction(self):
        """Test LDPC error correction."""
        # Create test keys
        alice_key = [int(x) for x in np.random.randint(0, 2, 100)]
        bob_key = alice_key.copy()

        # Introduce some errors
        for _ in range(5):
            error_pos = np.random.randint(0, 100)
            bob_key[error_pos] = 1 - bob_key[error_pos]

        # Apply LDPC error correction
        corrected_alice, corrected_bob, success = (
            AdvancedErrorCorrection.low_density_parity_check(alice_key, bob_key)
        )

        # Check results
        self.assertEqual(len(corrected_alice), len(alice_key))
        self.assertEqual(len(corrected_bob), len(bob_key))

    def test_polar_code_error_correction(self):
        """Test polar code error correction."""
        # Create test keys
        alice_key = [int(x) for x in np.random.randint(0, 2, 100)]
        bob_key = alice_key.copy()

        # Introduce some errors
        for _ in range(5):
            error_pos = np.random.randint(0, 100)
            bob_key[error_pos] = 1 - bob_key[error_pos]

        # Apply polar code error correction
        corrected_alice, corrected_bob, success = (
            AdvancedErrorCorrection.polar_code_error_correction(alice_key, bob_key)
        )

        # Check results
        self.assertEqual(len(corrected_alice), len(alice_key))
        self.assertEqual(len(corrected_bob), len(bob_key))

    def test_turbo_code_error_correction(self):
        """Test turbo code error correction."""
        # Create test keys
        alice_key = [int(x) for x in np.random.randint(0, 2, 100)]
        bob_key = alice_key.copy()

        # Introduce some errors
        for _ in range(5):
            error_pos = np.random.randint(0, 100)
            bob_key[error_pos] = 1 - bob_key[error_pos]

        # Apply turbo code error correction
        corrected_alice, corrected_bob, success = (
            AdvancedErrorCorrection.turbo_code_error_correction(alice_key, bob_key)
        )

        # Check results
        self.assertEqual(len(corrected_alice), len(alice_key))
        self.assertEqual(len(corrected_bob), len(bob_key))

    def test_fountain_code_error_correction(self):
        """Test fountain code error correction."""
        # Create test keys
        alice_key = [int(x) for x in np.random.randint(0, 2, 100)]
        bob_key = alice_key.copy()

        # Introduce some errors
        for _ in range(5):
            error_pos = np.random.randint(0, 100)
            bob_key[error_pos] = 1 - bob_key[error_pos]

        # Apply fountain code error correction
        corrected_alice, corrected_bob, success = (
            AdvancedErrorCorrection.fountain_code_error_correction(alice_key, bob_key)
        )

        # Check results
        self.assertEqual(len(corrected_alice), len(alice_key))
        self.assertEqual(len(corrected_bob), len(bob_key))


if __name__ == "__main__":
    unittest.main()
