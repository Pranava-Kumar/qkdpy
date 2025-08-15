"""Enhanced security features for QKD protocols."""

import hashlib
import hmac
import secrets

import numpy as np


class QuantumAuthentication:
    """Quantum authentication protocols for enhanced security."""

    @staticmethod
    def generate_message_authentication_code(
        key: list[int], message: bytes, algorithm: str = "sha256"
    ) -> str:
        """Generate a message authentication code using a quantum key.

        Args:
            key: Quantum key as a list of bits
            message: Message to authenticate
            algorithm: Hash algorithm to use

        Returns:
            Hexadecimal representation of the MAC
        """
        # Convert key to bytes
        key_bytes = bytes(
            [int("".join(map(str, key[i : i + 8])), 2) for i in range(0, len(key), 8)]
        )

        # Pad or truncate key to 32 bytes for HMAC
        if len(key_bytes) < 32:
            key_bytes = key_bytes.ljust(32, b"\x00")
        elif len(key_bytes) > 32:
            key_bytes = key_bytes[:32]

        # Generate MAC
        mac = hmac.new(key_bytes, message, getattr(hashlib, algorithm))
        return mac.hexdigest()

    @staticmethod
    def verify_message_authentication_code(
        key: list[int], message: bytes, mac: str, algorithm: str = "sha256"
    ) -> bool:
        """Verify a message authentication code.

        Args:
            key: Quantum key as a list of bits
            message: Message to verify
            mac: Message authentication code to verify
            algorithm: Hash algorithm to use

        Returns:
            True if MAC is valid, False otherwise
        """
        computed_mac = QuantumAuthentication.generate_message_authentication_code(
            key, message, algorithm
        )
        return hmac.compare_digest(computed_mac, mac)


class QuantumKeyValidation:
    """Validation mechanisms for quantum keys."""

    @staticmethod
    def statistical_randomness_test(key: list[int]) -> dict:
        """Perform statistical randomness tests on a quantum key.

        Args:
            key: Quantum key as a list of bits

        Returns:
            Dictionary with test results
        """
        if not key:
            return {"error": "Empty key"}

        # Convert to numpy array for easier manipulation
        bits = np.array(key)

        # Frequency test
        ones_count = np.sum(bits)
        zeros_count = len(bits) - ones_count
        frequency_p_value = 1 - abs(ones_count - zeros_count) / len(bits)

        # Runs test (simplified)
        runs_count = 1
        for i in range(1, len(bits)):
            if bits[i] != bits[i - 1]:
                runs_count += 1

        expected_runs = len(bits) / 2 + 1
        runs_p_value = 1 - abs(runs_count - expected_runs) / expected_runs

        # Longest run test (simplified)
        max_run_length = 1
        current_run_length = 1
        for i in range(1, len(bits)):
            if bits[i] == bits[i - 1]:
                current_run_length += 1
                max_run_length = max(max_run_length, current_run_length)
            else:
                current_run_length = 1

        # Return results
        return {
            "frequency_test_p_value": frequency_p_value,
            "runs_test_p_value": runs_p_value,
            "longest_run_length": max_run_length,
            "key_length": len(key),
            "ones_proportion": ones_count / len(bits),
        }

    @staticmethod
    def entropy_test(key: list[int]) -> float:
        """Calculate the entropy of a quantum key.

        Args:
            key: Quantum key as a list of bits

        Returns:
            Entropy value (0 to 1, where 1 is maximum entropy)
        """
        if not key:
            return 0.0

        # Convert to string for easier processing
        key_str = "".join(map(str, key))

        # Calculate frequency of 0s and 1s
        ones_count = key_str.count("1")
        zeros_count = len(key_str) - ones_count

        # Calculate probabilities
        p0 = zeros_count / len(key_str)
        p1 = ones_count / len(key_str)

        # Calculate entropy
        def entropy_term(p):
            return -p * np.log2(p) if p > 0 else 0

        entropy = entropy_term(p0) + entropy_term(p1)

        # Normalize to 0-1 range
        return entropy / 1.0  # Maximum entropy for binary is 1

    @staticmethod
    def correlation_test(key: list[int], lag: int = 1) -> float:
        """Test for correlations in the key at a specific lag.

        Args:
            key: Quantum key as a list of bits
            lag: Lag for correlation test

        Returns:
            Correlation coefficient (-1 to 1)
        """
        if len(key) <= lag:
            return 0.0

        # Convert to numpy array
        bits = np.array(key)

        # Calculate correlation
        x = bits[:-lag]
        y = bits[lag:]

        # Pearson correlation coefficient
        correlation = np.corrcoef(x, y)[0, 1] if len(x) > 1 else 0.0

        return correlation if not np.isnan(correlation) else 0.0


class QuantumSideChannelProtection:
    """Protection against side-channel attacks in QKD implementations."""

    @staticmethod
    def constant_time_compare(key1: list[int], key2: list[int]) -> bool:
        """Compare two keys in constant time to prevent timing attacks.

        Args:
            key1: First key
            key2: Second key

        Returns:
            True if keys are equal, False otherwise
        """
        if len(key1) != len(key2):
            return False

        result = 0
        for i in range(len(key1)):
            result |= key1[i] ^ key2[i]

        return result == 0

    @staticmethod
    def secure_key_splitting(key: list[int], num_parts: int) -> list[list[int]]:
        """Split a key into multiple parts using XOR secret sharing.

        Args:
            key: Key to split
            num_parts: Number of parts to split into

        Returns:
            List of key parts
        """
        if num_parts < 2:
            raise ValueError("Must split into at least 2 parts")

        # Generate random parts
        parts = []
        for _ in range(num_parts - 1):
            part = [secrets.randbelow(2) for _ in range(len(key))]
            parts.append(part)

        # Compute the last part so that XOR of all parts equals the original key
        last_part = key.copy()
        for part in parts:
            for j in range(len(key)):
                last_part[j] ^= part[j]

        parts.append(last_part)

        return parts

    @staticmethod
    def reconstruct_key(parts: list[list[int]]) -> list[int]:
        """Reconstruct a key from its parts.

        Args:
            parts: List of key parts

        Returns:
            Reconstructed key
        """
        if not parts:
            raise ValueError("No parts provided")

        # XOR all parts to get the original key
        key = [0] * len(parts[0])
        for part in parts:
            for j in range(len(key)):
                key[j] ^= part[j]

        return key
