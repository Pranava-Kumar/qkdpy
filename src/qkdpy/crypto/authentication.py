"""Authentication utilities using quantum keys."""

import hashlib
import hmac

import numpy as np


class QuantumAuth:
    """Authentication using quantum keys.

    This class provides authentication methods that can be used with quantum keys
    to ensure the integrity and authenticity of messages.
    """

    @staticmethod
    def generate_mac(
        message: str, key: list[int], hash_algorithm: str = "sha256"
    ) -> str:
        """Generate a Message Authentication Code (MAC) for a message.

        Args:
            message: Message to authenticate
            key: Binary key for authentication
            hash_algorithm: Hash algorithm to use ('sha256', 'sha512', etc.)

        Returns:
            MAC as a hexadecimal string

        """
        # Convert the key to bytes
        key_bytes = bytes(
            int("".join(map(str, key)), 2).to_bytes(
                (len(key) + 7) // 8, byteorder="big"
            )
        )

        # Convert the message to bytes
        message_bytes = message.encode("utf-8")

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

        # Generate the MAC
        mac = hmac.new(key_bytes, message_bytes, hash_func).hexdigest()

        return mac

    @staticmethod
    def verify_mac(
        message: str, mac: str, key: list[int], hash_algorithm: str = "sha256"
    ) -> bool:
        """Verify a Message Authentication Code (MAC) for a message.

        Args:
            message: Message to verify
            mac: MAC to verify against
            key: Binary key for authentication
            hash_algorithm: Hash algorithm to use ('sha256', 'sha512', etc.)

        Returns:
            True if the MAC is valid, False otherwise

        """
        # Generate the MAC for the message
        generated_mac = QuantumAuth.generate_mac(message, key, hash_algorithm)

        # Compare the generated MAC with the provided MAC
        # Use hmac.compare_digest to prevent timing attacks
        return hmac.compare_digest(generated_mac, mac)

    @staticmethod
    def generate_authenticator(key: list[int], challenge: str = None) -> str:
        """Generate an authenticator for challenge-response authentication.

        Args:
            key: Binary key for authentication
            challenge: Challenge string (optional)

        Returns:
            Authenticator as a hexadecimal string

        """
        # If no challenge is provided, generate a random one
        if challenge is None:
            challenge = "".join(np.random.choice(list("0123456789abcdef"), size=16))

        # Convert the key to bytes
        key_bytes = bytes(
            int("".join(map(str, key)), 2).to_bytes(
                (len(key) + 7) // 8, byteorder="big"
            )
        )

        # Convert the challenge to bytes
        challenge_bytes = challenge.encode("utf-8")

        # Generate the authenticator using HMAC-SHA256
        authenticator = hmac.new(key_bytes, challenge_bytes, hashlib.sha256).hexdigest()

        return authenticator

    @staticmethod
    def verify_authenticator(
        key: list[int], challenge: str, authenticator: str
    ) -> bool:
        """Verify an authenticator for challenge-response authentication.

        Args:
            key: Binary key for authentication
            challenge: Challenge string
            authenticator: Authenticator to verify

        Returns:
            True if the authenticator is valid, False otherwise

        """
        # Generate the authenticator for the challenge
        generated_authenticator = QuantumAuth.generate_authenticator(key, challenge)

        # Compare the generated authenticator with the provided authenticator
        # Use hmac.compare_digest to prevent timing attacks
        return hmac.compare_digest(generated_authenticator, authenticator)

    @staticmethod
    def generate_key_fingerprint(key: list[int], hash_algorithm: str = "sha256") -> str:
        """Generate a fingerprint for a key.

        Args:
            key: Binary key to fingerprint
            hash_algorithm: Hash algorithm to use ('sha256', 'sha512', etc.)

        Returns:
            Key fingerprint as a hexadecimal string

        """
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

        # Generate the fingerprint
        fingerprint = hash_func(key_bytes).hexdigest()

        return fingerprint

    @staticmethod
    def generate_commitment(
        value: str, key: list[int], nonce: int = None
    ) -> dict[str, str]:
        """Generate a cryptographic commitment for a value.

        Args:
            value: Value to commit to
            key: Binary key for the commitment
            nonce: Nonce for the commitment (optional)

        Returns:
            Dictionary containing the commitment and nonce

        """
        # If no nonce is provided, generate a random one
        if nonce is None:
            nonce = np.random.randint(0, 2**32)

        # Convert the key to bytes
        key_bytes = bytes(
            int("".join(map(str, key)), 2).to_bytes(
                (len(key) + 7) // 8, byteorder="big"
            )
        )

        # Convert the value and nonce to bytes
        value_bytes = value.encode("utf-8")
        nonce_bytes = nonce.to_bytes(4, byteorder="big")

        # Generate the commitment using HMAC-SHA256
        commitment = hmac.new(
            key_bytes, value_bytes + nonce_bytes, hashlib.sha256
        ).hexdigest()

        return {"commitment": commitment, "nonce": str(nonce)}

    @staticmethod
    def verify_commitment(
        value: str, commitment: str, key: list[int], nonce: str
    ) -> bool:
        """Verify a cryptographic commitment for a value.

        Args:
            value: Value to verify
            commitment: Commitment to verify against
            key: Binary key for the commitment
            nonce: Nonce used for the commitment

        Returns:
            True if the commitment is valid, False otherwise

        """
        # Convert the nonce to an integer
        try:
            nonce_int = int(nonce)
        except ValueError:
            return False

        # Generate the commitment for the value
        generated_commitment = QuantumAuth.generate_commitment(value, key, nonce_int)[
            "commitment"
        ]

        # Compare the generated commitment with the provided commitment
        # Use hmac.compare_digest to prevent timing attacks
        return hmac.compare_digest(generated_commitment, commitment)
