"""Tests for advanced privacy amplification methods."""

import unittest

import numpy as np

from qkdpy.key_management import AdvancedPrivacyAmplification


class TestAdvancedPrivacyAmplification(unittest.TestCase):
    """Test cases for the AdvancedPrivacyAmplification class."""

    def test_xor_extract(self):
        """Test XOR-based randomness extraction."""
        # Create a test key
        key = [int(x) for x in np.random.randint(0, 2, 100)]

        # Apply XOR extraction
        extracted = AdvancedPrivacyAmplification.xor_extract(key)

        # Check that the output is shorter than the input
        self.assertLess(len(extracted), len(key))

        # Check that all output bits are valid
        for bit in extracted:
            self.assertIn(bit, [0, 1])

    def test_aes_hash_extract(self):
        """Test AES-based hash extraction."""
        # Create a test key
        key = [int(x) for x in np.random.randint(0, 2, 100)]
        output_length = 50

        # Apply AES hash extraction
        extracted = AdvancedPrivacyAmplification.aes_hash_extract(key, output_length)

        # Check the output length
        self.assertEqual(len(extracted), output_length)

        # Check that all output bits are valid
        for bit in extracted:
            self.assertIn(bit, [0, 1])

    def test_randomness_extractor(self):
        """Test different randomness extraction methods."""
        # Create a test key
        key = [int(x) for x in np.random.randint(0, 2, 100)]
        output_length = 50

        # Test XOR method
        extracted_xor = AdvancedPrivacyAmplification.randomness_extractor(
            key, output_length, "xor"
        )
        self.assertEqual(
            len(extracted_xor), len(AdvancedPrivacyAmplification.xor_extract(key))
        )

        # Test AES method
        extracted_aes = AdvancedPrivacyAmplification.randomness_extractor(
            key, output_length, "aes"
        )
        self.assertEqual(len(extracted_aes), output_length)

        # Test universal method
        extracted_universal = AdvancedPrivacyAmplification.randomness_extractor(
            key, output_length, "universal"
        )
        self.assertEqual(len(extracted_universal), output_length)

    def test_strong_extractor(self):
        """Test strong randomness extractor."""
        # Create a test key
        key = [int(x) for x in np.random.randint(0, 2, 100)]
        output_length = 30
        min_entropy = 50.0

        # Apply strong extractor
        extracted = AdvancedPrivacyAmplification.strong_extractor(
            key, output_length, min_entropy
        )

        # Check the output length
        self.assertLessEqual(len(extracted), output_length)

        # Check that all output bits are valid
        for bit in extracted:
            self.assertIn(bit, [0, 1])

    def test_seeded_extractor(self):
        """Test seeded randomness extractor."""
        # Create a test key and seed
        key = [int(x) for x in np.random.randint(0, 2, 100)]
        seed = [int(x) for x in np.random.randint(0, 2, 50)]
        output_length = 30

        # Apply seeded extractor
        extracted = AdvancedPrivacyAmplification.seeded_extractor(
            key, seed, output_length
        )

        # Check the output length
        self.assertLessEqual(len(extracted), output_length)

        # Check that all output bits are valid
        for bit in extracted:
            self.assertIn(bit, [0, 1])


if __name__ == "__main__":
    unittest.main()
