"""Cryptographically secure random number generation utilities.

This module provides CSPRNG-based replacements for common random operations
to ensure the library is suitable for production cryptographic use.
"""

import secrets
from typing import Any

import numpy as np


class SecureRandom:
    """Cryptographically secure random number generator using Python's secrets module."""

    def __init__(self):
        """Initialize the secure random generator."""
        # Create a numpy Generator with secure seed for numpy operations
        secure_seed = secrets.randbits(128)
        self._np_rng = np.random.Generator(np.random.PCG64(secure_seed))

    def randint(self, low: int, high: int) -> int:
        """Generate a cryptographically secure random integer.

        Args:
            low: Lower bound (inclusive)
            high: Upper bound (exclusive)

        Returns:
            Random integer in range [low, high)
        """
        return secrets.randbelow(high - low) + low

    def choice(self, items: list[Any] | np.ndarray) -> Any:
        """Cryptographically secure choice from a sequence.

        Args:
            items: Sequence to choose from

        Returns:
            Randomly chosen element
        """
        if isinstance(items, np.ndarray):
            items = items.tolist()
        return secrets.choice(items)

    def random(self) -> float:
        """Generate a cryptographically secure random float in [0.0, 1.0).

        Returns:
            Random float
        """
        # Generate 53 bits of randomness for double precision
        return secrets.randbits(53) / (1 << 53)

    def normal(self, mean: float = 0.0, std: float = 1.0) -> float:
        """Generate a cryptographically secure normally distributed random number.

        Uses Box-Muller transform with secure uniform random source.

        Args:
            mean: Mean of the distribution
            std: Standard deviation

        Returns:
            Random number from normal distribution
        """
        # Box-Muller transform
        u1 = self.random()
        u2 = self.random()
        z0 = np.sqrt(-2.0 * np.log(u1)) * np.cos(2.0 * np.pi * u2)
        return mean + std * z0

    def bits(self, num_bits: int) -> list[int]:
        """Generate cryptographically secure random bits.

        Args:
            num_bits: Number of bits to generate

        Returns:
            List of random bits (0 or 1)
        """
        num_bytes = (num_bits + 7) // 8
        random_bytes = secrets.token_bytes(num_bytes)
        bits = []
        for byte in random_bytes:
            for i in range(8):
                if len(bits) < num_bits:
                    bits.append((byte >> (7 - i)) & 1)
        return bits[:num_bits]


# Global instance for convenience
_secure_rng = SecureRandom()


# Convenience functions that mirror numpy.random API
def secure_randint(low: int, high: int) -> int:
    """Generate a cryptographically secure random integer.

    Args:
        low: Lower bound (inclusive)
        high: Upper bound (exclusive)

    Returns:
        Random integer in range [low, high)
    """
    return _secure_rng.randint(low, high)


def secure_choice(items: list[Any] | np.ndarray) -> Any:
    """Cryptographically secure choice from a sequence.

    Args:
        items: Sequence to choose from

    Returns:
        Randomly chosen element
    """
    return _secure_rng.choice(items)


def secure_random() -> float:
    """Generate a cryptographically secure random float in [0.0, 1.0).

    Returns:
        Random float
    """
    return _secure_rng.random()


def secure_normal(mean: float = 0.0, std: float = 1.0) -> float:
    """Generate a cryptographically secure normally distributed random number.

    Args:
        mean: Mean of the distribution
        std: Standard deviation

    Returns:
        Random number from normal distribution
    """
    return _secure_rng.normal(mean, std)


def secure_bits(num_bits: int) -> list[int]:
    """Generate cryptographically secure random bits.

    Args:
        num_bits: Number of bits to generate

    Returns:
        List of random bits (0 or 1)
    """
    return _secure_rng.bits(num_bits)


def secure_weighted_choice(
    items: list[Any] | np.ndarray, probabilities: list[float] | np.ndarray
) -> Any:
    """Cryptographically secure weighted choice.

    Args:
        items: Sequence to choose from
        probabilities: Probabilities for each item

    Returns:
        Randomly chosen element based on probabilities
    """
    if isinstance(items, np.ndarray):
        items = items.tolist()
    if isinstance(probabilities, np.ndarray):
        probabilities = probabilities.tolist()

    # Verify probabilities sum to roughly 1.0
    total_prob = sum(probabilities)
    if abs(total_prob - 1.0) > 1e-6:
        # Normalize if needed
        probabilities = [p / total_prob for p in probabilities]

    # Cumulative distribution
    cum_probs = []
    current_sum = 0.0
    for p in probabilities:
        current_sum += p
        cum_probs.append(current_sum)

    # Secure random float
    r = _secure_rng.random()

    # Find index
    for i, cp in enumerate(cum_probs):
        if r < cp:
            return items[i]

    return items[-1]


def reseed_secure_rng():
    """Reseed the global secure RNG instance.

    This should be called if you want to ensure fresh entropy,
    though it's generally not necessary as secrets module is self-seeding.
    """
    global _secure_rng
    _secure_rng = SecureRandom()
