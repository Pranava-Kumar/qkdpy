"""Tests for quantum random number generator."""

import unittest

from qkdpy.core import QuantumChannel
from qkdpy.crypto import QuantumRandomNumberGenerator


class TestQuantumRandomNumberGenerator(unittest.TestCase):
    """Test cases for the QuantumRandomNumberGenerator class."""

    def setUp(self):
        """Set up test fixtures."""
        self.channel = QuantumChannel()
        self.qrng = QuantumRandomNumberGenerator(self.channel)

    def test_qrng_initialization(self):
        """Test quantum random number generator initialization."""
        self.assertIsInstance(self.qrng.entropy_pool, list)
        self.assertEqual(self.qrng.bits_generated, 0)

    def test_generate_random_bits(self):
        """Test generating random bits."""
        num_bits = 100

        # Generate random bits
        random_bits = self.qrng.generate_random_bits(num_bits)

        # Check the output
        self.assertGreater(len(random_bits), 0)
        self.assertLessEqual(len(random_bits), num_bits)

        # Check that all bits are valid
        for bit in random_bits:
            self.assertIn(bit, [0, 1])

    def test_generate_random_bytes(self):
        """Test generating random bytes."""
        num_bytes = 50

        # Generate random bytes
        random_bytes = self.qrng.generate_random_bytes(num_bytes)

        # Check the output
        self.assertGreater(len(random_bytes), 0)
        self.assertLessEqual(len(random_bytes), num_bytes)
        self.assertIsInstance(random_bytes, bytes)

    def test_generate_random_int(self):
        """Test generating random integers."""
        min_val = 10
        max_val = 100

        # Generate random integers
        for _ in range(10):
            random_int = self.qrng.generate_random_int(min_val, max_val)

            # Check the output
            self.assertGreaterEqual(random_int, min_val)
            self.assertLessEqual(random_int, max_val)

    def test_generate_random_string(self):
        """Test generating random strings."""
        length = 20

        # Test alphanumeric string
        random_string = self.qrng.generate_random_string(length, "alphanumeric")
        self.assertEqual(len(random_string), length)

        # Test hex string
        random_hex = self.qrng.generate_random_string(length, "hex")
        self.assertEqual(len(random_hex), length)

        # Test binary string
        random_binary = self.qrng.generate_random_string(length, "binary")
        self.assertEqual(len(random_binary), length)

        # Check that binary string contains only 0s and 1s
        for char in random_binary:
            self.assertIn(char, ["0", "1"])

    def test_add_entropy(self):
        """Test adding entropy to the pool."""
        initial_pool_size = len(self.qrng.entropy_pool)
        entropy_source = [1, 0, 1, 1, 0, 0, 1, 0]

        # Add entropy
        self.qrng.add_entropy(entropy_source)

        # Check that entropy was added
        self.assertEqual(
            len(self.qrng.entropy_pool), initial_pool_size + len(entropy_source)
        )

    def test_get_entropy_level(self):
        """Test getting entropy level."""
        # Add some entropy
        self.qrng.add_entropy([1, 0, 1, 0, 1, 0, 1, 0])

        # Get entropy level
        entropy_level = self.qrng.get_entropy_level()

        # Check that we get a valid entropy level
        self.assertGreaterEqual(entropy_level, 0.0)
        self.assertLessEqual(entropy_level, 1.0)

    def test_get_statistics(self):
        """Test getting generator statistics."""
        # Generate some random bits
        self.qrng.generate_random_bits(100)

        # Get statistics
        stats = self.qrng.get_statistics()

        # Check the statistics
        self.assertIn("bits_generated", stats)
        self.assertIn("entropy_pool_size", stats)
        self.assertIn("entropy_level", stats)
        self.assertIn("last_calibration", stats)
        self.assertIn("time_since_calibration", stats)


if __name__ == "__main__":
    unittest.main()
