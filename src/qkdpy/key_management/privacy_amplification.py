"""Privacy amplification methods for QKD protocols."""

import hashlib

import numpy as np


class PrivacyAmplification:
    """Provides various privacy amplification methods for QKD protocols.

    This class implements different privacy amplification algorithms that can be used
    to reduce Eve's information about the final key.
    """

    @staticmethod
    def universal_hashing(
        key: list[int], output_length: int, seed: int = None
    ) -> list[int]:
        """Privacy amplification using universal hashing.

        Args:
            key: Binary key to be amplified
            output_length: Desired length of the output key
            seed: Seed for the random hash function

        Returns:
            Shortened, more secure key

        """
        if output_length >= len(key):
            raise ValueError("Output length must be less than input key length")

        if output_length <= 0:
            return []

        # Set the seed for reproducibility
        if seed is not None:
            np.random.seed(seed)

        # Convert the key to a binary string
        key_str = "".join(map(str, key))

        # Generate a random binary matrix for the hash function
        hash_matrix = np.random.randint(0, 2, size=(output_length, len(key)))

        # Apply the hash function
        result = []
        for i in range(output_length):
            # Compute the dot product modulo 2
            bit = sum(hash_matrix[i][j] * int(key_str[j]) for j in range(len(key))) % 2
            result.append(int(bit))

        return result

    @staticmethod
    def toeplitz_hashing(
        key: list[int], output_length: int, seed: int = None
    ) -> list[int]:
        """Privacy amplification using Toeplitz matrix hashing.

        Args:
            key: Binary key to be amplified
            output_length: Desired length of the output key
            seed: Seed for the random hash function

        Returns:
            Shortened, more secure key

        """
        if output_length >= len(key):
            raise ValueError("Output length must be less than input key length")

        if output_length <= 0:
            return []

        # Set the seed for reproducibility
        if seed is not None:
            np.random.seed(seed)

        # Convert the key to a binary string
        key_str = "".join(map(str, key))

        # Generate a random binary vector for the first row of the Toeplitz matrix
        first_row = np.random.randint(0, 2, size=len(key))

        # Generate a random binary vector for the first column of the Toeplitz matrix (excluding the first element)
        first_col = np.random.randint(0, 2, size=output_length)

        # Construct the Toeplitz matrix
        toeplitz = np.zeros((output_length, len(key)), dtype=int)
        for i in range(output_length):
            for j in range(len(key)):
                if i <= j:
                    toeplitz[i, j] = first_row[j - i]
                else:
                    toeplitz[i, j] = first_col[i - j]

        # Apply the hash function
        result = []
        for i in range(output_length):
            # Compute the dot product modulo 2
            bit = sum(toeplitz[i][j] * int(key_str[j]) for j in range(len(key))) % 2
            result.append(int(bit))

        return result

    @staticmethod
    def cryptographic_hash(
        key: list[int], output_length: int, hash_algorithm: str = "sha256"
    ) -> list[int]:
        """Privacy amplification using cryptographic hash functions.

        Args:
            key: Binary key to be amplified
            output_length: Desired length of the output key
            hash_algorithm: Hash algorithm to use ('sha256', 'sha512', etc.)

        Returns:
            Shortened, more secure key

        """
        if output_length <= 0:
            return []

        # Convert the key to bytes
        key_bytes = bytes(
            int("".join(map(str, key)), 2).to_bytes(
                (len(key) + 7) // 8, byteorder="big"
            )
        )

        # Choose the hash function
        if hash_algorithm == "sha256":
            hash_func = hashlib.sha256
        elif hash_algorithm == "sha512":
            hash_func = hashlib.sha512
        elif hash_algorithm == "sha1":
            hash_func = hashlib.sha1
        elif hash_algorithm == "md5":
            hash_func = hashlib.md5
        else:
            raise ValueError(f"Unsupported hash algorithm: {hash_algorithm}")

        # Apply the hash function
        hashed = hash_func(key_bytes).digest()

        # Convert the hash to a binary string
        hash_bits = "".join(format(byte, "08b") for byte in hashed)

        # Truncate to the desired length
        result = [int(bit) for bit in hash_bits[:output_length]]

        return result

    @staticmethod
    def bennett_brassard_hashing(
        key: list[int], output_length: int, error_rate: float = 0.0
    ) -> list[int]:
        """Privacy amplification using the Bennett-Brassard method.

        Args:
            key: Binary key to be amplified
            output_length: Desired length of the output key
            error_rate: Estimated error rate in the key

        Returns:
            Shortened, more secure key

        """
        if output_length >= len(key):
            raise ValueError("Output length must be less than input key length")

        if output_length <= 0:
            return []

        # Calculate the number of bits to keep
        # According to the Bennett-Brassard method, we keep r = n - s - t bits
        # where n is the original key length, s is a security parameter, and t is
        # an estimate of the information leaked to Eve
        n = len(key)
        s = 10  # Security parameter
        t = int(n * (error_rate + 0.1))  # Estimate of information leaked to Eve

        r = max(1, n - s - t)  # Ensure at least 1 bit remains

        # If the requested output length is greater than r, use r instead
        r = min(r, output_length)

        # Use universal hashing with the calculated output length
        return PrivacyAmplification.universal_hashing(key, r)

    @staticmethod
    def leftover_hash_lemma(
        key: list[int], min_entropy: float, security_parameter: float = 1e-9
    ) -> list[int]:
        """Privacy amplification using the Leftover Hash Lemma.

        Args:
            key: Binary key to be amplified
            min_entropy: Minimum entropy of the input key
            security_parameter: Desired security parameter

        Returns:
            Shortened, more secure key

        """
        # Calculate the output length according to the Leftover Hash Lemma
        # l = H_min(X) - 2 * log(1/ε)
        # where H_min(X) is the min-entropy of X and ε is the security parameter
        output_length = int(min_entropy - 2 * np.log2(1 / security_parameter))

        # Ensure the output length is at least 1
        output_length = max(1, output_length)

        # Ensure the output length is less than the input key length
        output_length = min(output_length, len(key) - 1)

        # Use universal hashing with the calculated output length
        return PrivacyAmplification.universal_hashing(key, output_length)

    @staticmethod
    def extract_randomness(
        key: list[int], output_length: int, method: str = "universal_hashing"
    ) -> list[int]:
        """Extract randomness from a key using various methods.

        Args:
            key: Binary key to extract randomness from
            output_length: Desired length of the output key
            method: Method to use for randomness extraction

        Returns:
            Random bits extracted from the key

        """
        if method == "universal_hashing":
            return PrivacyAmplification.universal_hashing(key, output_length)
        elif method == "toeplitz_hashing":
            return PrivacyAmplification.toeplitz_hashing(key, output_length)
        elif method == "cryptographic_hash":
            return PrivacyAmplification.cryptographic_hash(key, output_length)
        elif method == "bennett_brassard":
            return PrivacyAmplification.bennett_brassard_hashing(key, output_length)
        else:
            raise ValueError(f"Unknown randomness extraction method: {method}")
