import numpy as np

from qkdpy.core.secure_random import (
    secure_bits,
    secure_choice,
    secure_normal,
    secure_randint,
    secure_random,
    secure_weighted_choice,
)


class TestCSPRNGUsage:
    """Tests to verify correct usage and properties of CSPRNG functions."""

    def test_independence_from_numpy_seed(self):
        """Verify that secure_random functions are NOT affected by np.random.seed."""
        # Set a fixed seed
        np.random.seed(42)

        # Generate values
        val1_random = secure_random()
        _ = secure_randint(0, 1000)
        _ = secure_choice([1, 2, 3, 4, 5])

        # Reset the same seed
        np.random.seed(42)

        # Generate values again - they should be DIFFERENT (with high probability)
        # Note: There is a tiny probability of collision, but for float it's negligible.
        # For randint/choice, we might need multiple trials to be sure, but let's check float first.

        val2_random = secure_random()

        # Check that they are different
        assert (
            val1_random != val2_random
        ), "secure_random() should not be deterministic with np.random.seed"

    def test_secure_randint_range(self):
        """Verify secure_randint respects the range."""
        min_val = 10
        max_val = 20
        for _ in range(100):
            val = secure_randint(min_val, max_val)
            assert min_val <= val < max_val

    def test_secure_choice_distribution(self):
        """Verify secure_choice can pick any element."""
        options = [1, 2, 3]
        counts = {1: 0, 2: 0, 3: 0}
        for _ in range(300):
            val = secure_choice(options)
            counts[val] += 1

        # All options should be picked at least once
        assert all(c > 0 for c in counts.values())

    def test_secure_weighted_choice_distribution(self):
        """Verify secure_weighted_choice respects probabilities approximately."""
        options = [0, 1]
        weights = [0.8, 0.2]
        counts = {0: 0, 1: 0}
        num_trials = 1000

        for _ in range(num_trials):
            val = secure_weighted_choice(options, weights)
            counts[val] += 1

        # Check if distribution is roughly correct (allow some variance)
        # 0 should be around 800, 1 around 200
        assert 700 < counts[0] < 900
        assert 100 < counts[1] < 300

    def test_secure_bits_length(self):
        """Verify secure_bits returns correct number of bits."""
        length = 50
        bits = secure_bits(length)
        assert len(bits) == length
        assert all(b in [0, 1] for b in bits)

    def test_secure_normal_stats(self):
        """Verify secure_normal produces values with roughly correct mean/std."""
        mean = 10.0
        std = 2.0
        values = [secure_normal(mean, std) for _ in range(1000)]

        calc_mean = np.mean(values)
        calc_std = np.std(values)

        # Allow some margin of error
        assert abs(calc_mean - mean) < 0.5
        assert abs(calc_std - std) < 0.5
