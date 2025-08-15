"""Quantum random number generation utilities."""

import os
import secrets
import time

import numpy as np

from ..core import QuantumChannel
from ..protocols import BB84


class QuantumRandomNumberGenerator:
    """Generates cryptographically secure random numbers using quantum principles."""

    def __init__(self, channel: QuantumChannel | None = None):
        """Initialize the quantum random number generator.

        Args:
            channel: Quantum channel for QKD-based randomness (optional)
        """
        self.channel = channel
        self.entropy_pool: list[int] = []
        self.bits_generated = 0
        self.last_calibration = time.time()

    def generate_random_bits(self, num_bits: int) -> list[int]:
        """Generate cryptographically secure random bits.

        Args:
            num_bits: Number of random bits to generate

        Returns:
            List of random bits
        """
        # For a real quantum RNG, we would use quantum measurements
        # Since we're simulating, we'll use a combination of sources

        # 1. Use quantum key generation if a channel is provided
        if self.channel is not None:
            try:
                # Generate a short key using BB84 for additional entropy
                qkd = BB84(self.channel, key_length=min(128, num_bits))
                results = qkd.execute()

                if results["is_secure"] and len(results["final_key"]) > 0:
                    # Add the quantum-generated key to our entropy pool
                    self.entropy_pool.extend(results["final_key"])
            except Exception:
                # If QKD fails, continue with other methods
                pass

        # 2. Use OS-provided randomness
        os_random_bytes = secrets.token_bytes((num_bits + 7) // 8)
        os_random_bits = []
        for byte in os_random_bytes:
            for i in range(8):
                os_random_bits.append((byte >> (7 - i)) & 1)
        self.entropy_pool.extend(os_random_bits[:num_bits])

        # 3. Use numpy random with additional entropy
        if len(self.entropy_pool) < num_bits:
            # Add some additional entropy from system time and process ID
            additional_entropy = (
                int(time.time() * 1000000) ^ os.getpid() ^ secrets.randbelow(2**32)
            )
            np.random.seed(additional_entropy)

            numpy_random_bits = [
                int(np.random.randint(0, 2))
                for _ in range(num_bits - len(self.entropy_pool))
            ]
            self.entropy_pool.extend(numpy_random_bits)

        # 4. Apply a randomness extractor to ensure quality
        if len(self.entropy_pool) >= num_bits:
            # Use a simple XOR-based extractor
            extracted_bits = self._xor_extractor(self.entropy_pool[:num_bits])
            self.entropy_pool = self.entropy_pool[num_bits:]
        else:
            # If we don't have enough bits, generate more
            needed_bits = num_bits - len(self.entropy_pool)
            additional_bits = [int(np.random.randint(0, 2)) for _ in range(needed_bits)]
            all_bits = self.entropy_pool + additional_bits
            extracted_bits = self._xor_extractor(all_bits)
            self.entropy_pool = []

        self.bits_generated += len(extracted_bits)
        return extracted_bits[:num_bits]

    def generate_random_bytes(self, num_bytes: int) -> bytes:
        """Generate cryptographically secure random bytes.

        Args:
            num_bytes: Number of random bytes to generate

        Returns:
            Random bytes
        """
        # Generate 8 times as many bits as bytes
        random_bits = self.generate_random_bits(num_bytes * 8)

        # Convert bits to bytes
        random_bytes = bytearray()
        for i in range(0, len(random_bits), 8):
            if i + 8 <= len(random_bits):
                byte_bits = random_bits[i : i + 8]
                byte_value = sum(bit << (7 - j) for j, bit in enumerate(byte_bits))
                random_bytes.append(byte_value)

        return bytes(random_bytes)

    def generate_random_int(self, min_val: int, max_val: int) -> int:
        """Generate a cryptographically secure random integer in a range.

        Args:
            min_val: Minimum value (inclusive)
            max_val: Maximum value (inclusive)

        Returns:
            Random integer in the specified range
        """
        if min_val > max_val:
            raise ValueError("min_val must be less than or equal to max_val")

        if min_val == max_val:
            return min_val

        # Calculate the range
        range_size = max_val - min_val + 1

        # Determine how many bits we need
        num_bits = int(np.ceil(np.log2(range_size)))

        # Generate random bits and convert to integer
        while True:
            random_bits = self.generate_random_bits(num_bits)
            random_int = sum(bit << i for i, bit in enumerate(reversed(random_bits)))

            # If the result is within our desired range, return it
            if random_int < range_size:
                return min_val + random_int

    def generate_random_string(self, length: int, charset: str = "alphanumeric") -> str:
        """Generate a cryptographically secure random string.

        Args:
            length: Length of the string to generate
            charset: Character set to use ('alphanumeric', 'hex', 'binary', or custom)

        Returns:
            Random string
        """
        # Define character sets
        charsets = {
            "alphanumeric": "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789",
            "hex": "0123456789abcdef",
            "binary": "01",
        }

        # Select the character set
        chars = charsets.get(charset, charset)

        # Generate random indices
        random_string = ""
        for _ in range(length):
            index = self.generate_random_int(0, len(chars) - 1)
            random_string += chars[index]

        return random_string

    def _xor_extractor(self, bits: list[int]) -> list[int]:
        """Simple XOR-based randomness extractor.

        Args:
            bits: Input bits to extract from

        Returns:
            Extracted random bits
        """
        if len(bits) < 2:
            return bits

        # Apply pairwise XOR to reduce bias
        extracted = []
        for i in range(0, len(bits) - 1, 2):
            extracted.append(bits[i] ^ bits[i + 1])

        return extracted

    def add_entropy(self, entropy_source: list[int]) -> None:
        """Add external entropy to the pool.

        Args:
            entropy_source: List of random bits to add to the entropy pool
        """
        self.entropy_pool.extend(entropy_source)

    def get_entropy_level(self) -> float:
        """Estimate the entropy level in the pool.

        Returns:
            Estimated entropy level (0.0 to 1.0)
        """
        if len(self.entropy_pool) == 0:
            return 0.0

        # Simple entropy estimation based on bit balance
        ones = sum(self.entropy_pool)
        zeros = len(self.entropy_pool) - ones
        balance = abs(ones - zeros) / len(self.entropy_pool)

        # Return 1.0 - balance as a simple entropy measure
        return 1.0 - balance

    def calibrate(self) -> bool:
        """Calibrate the random number generator.

        Returns:
            True if calibration successful, False otherwise
        """
        try:
            # Add entropy from various sources
            timestamp_entropy = [int(b) for b in bin(int(time.time() * 1000000))[2:]]
            self.add_entropy(timestamp_entropy)

            # Add OS-provided entropy
            os_entropy = [int(b) for b in bin(secrets.randbelow(2**32))[2:]]
            self.add_entropy(os_entropy)

            self.last_calibration = time.time()
            return True
        except Exception:
            return False

    def get_statistics(self) -> dict:
        """Get statistics about the random number generator.

        Returns:
            Dictionary with generator statistics
        """
        return {
            "bits_generated": self.bits_generated,
            "entropy_pool_size": len(self.entropy_pool),
            "entropy_level": self.get_entropy_level(),
            "last_calibration": self.last_calibration,
            "time_since_calibration": time.time() - self.last_calibration,
        }
