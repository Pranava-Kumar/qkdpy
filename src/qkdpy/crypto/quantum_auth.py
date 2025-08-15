"""Quantum authentication and digital signature schemes."""

import hashlib
import hmac
import time

import numpy as np

from ..core import QuantumChannel
from ..protocols import BB84


class QuantumAuthenticator:
    """Provides quantum-based authentication mechanisms."""

    def __init__(self, channel: QuantumChannel):
        """Initialize the quantum authenticator.

        Args:
            channel: Quantum channel for authentication protocol
        """
        self.channel = channel
        self.authenticated_parties: dict[str, dict] = {}
        self.auth_tokens: dict[str, dict] = {}

    def register_party(self, party_id: str, shared_key_length: int = 128) -> bool:
        """Register a party for quantum authentication.

        Args:
            party_id: Unique identifier for the party
            shared_key_length: Length of the shared key to generate

        Returns:
            True if registration successful, False otherwise
        """
        try:
            # Generate a shared key using QKD
            qkd = BB84(self.channel, key_length=shared_key_length)
            results = qkd.execute()

            if not results["is_secure"] or len(results["final_key"]) == 0:
                return False

            # Store the shared key
            self.authenticated_parties[party_id] = {
                "shared_key": results["final_key"],
                "registered": time.time(),
                "last_auth": None,
            }

            return True
        except Exception as e:
            print(f"Error registering party: {e}")
            return False

    def authenticate_party(
        self, party_id: str, challenge: str | None = None
    ) -> str | None:
        """Authenticate a registered party.

        Args:
            party_id: Unique identifier for the party
            challenge: Challenge string (optional)

        Returns:
            Authentication token if successful, None otherwise
        """
        if party_id not in self.authenticated_parties:
            return None

        # If no challenge provided, generate a random one
        if challenge is None:
            challenge = "".join(np.random.choice(list("0123456789abcdef"), size=16))

        # Get the shared key
        shared_key = self.authenticated_parties[party_id]["shared_key"]

        # Convert the key to bytes
        key_bytes = bytes(
            int("".join(map(str, shared_key)), 2).to_bytes(
                (len(shared_key) + 7) // 8, byteorder="big"
            )
        )

        # Convert the challenge to bytes
        challenge_bytes = challenge.encode("utf-8")

        # Generate the authentication token using HMAC-SHA256
        auth_token = hmac.new(key_bytes, challenge_bytes, hashlib.sha256).hexdigest()

        # Store the authentication token
        token_id = f"token_{int(time.time() * 1000000)}_{np.random.randint(10000)}"
        self.auth_tokens[token_id] = {
            "party_id": party_id,
            "challenge": challenge,
            "token": auth_token,
            "timestamp": time.time(),
        }

        # Update last authentication time
        self.authenticated_parties[party_id]["last_auth"] = time.time()

        return token_id

    def verify_authentication(
        self, party_id: str, token_id: str, challenge: str
    ) -> bool:
        """Verify an authentication token.

        Args:
            party_id: Unique identifier for the party
            token_id: Authentication token identifier
            challenge: Challenge string

        Returns:
            True if authentication is valid, False otherwise
        """
        # Check if the party is registered
        if party_id not in self.authenticated_parties:
            return False

        # Check if the token exists
        if token_id not in self.auth_tokens:
            return False

        # Check if the token belongs to the party
        if self.auth_tokens[token_id]["party_id"] != party_id:
            return False

        # Check if the challenge matches
        if self.auth_tokens[token_id]["challenge"] != challenge:
            return False

        # Check if the token is still valid (5 minutes expiration)
        if time.time() - self.auth_tokens[token_id]["timestamp"] > 300:
            # Remove expired token
            del self.auth_tokens[token_id]
            return False

        # Get the shared key
        shared_key = self.authenticated_parties[party_id]["shared_key"]

        # Convert the key to bytes
        key_bytes = bytes(
            int("".join(map(str, shared_key)), 2).to_bytes(
                (len(shared_key) + 7) // 8, byteorder="big"
            )
        )

        # Convert the challenge to bytes
        challenge_bytes = challenge.encode("utf-8")

        # Generate the expected authentication token
        expected_token = hmac.new(
            key_bytes, challenge_bytes, hashlib.sha256
        ).hexdigest()

        # Compare with the provided token
        is_valid = hmac.compare_digest(
            expected_token, self.auth_tokens[token_id]["token"]
        )

        return is_valid

    def generate_quantum_signature(
        self, party_id: str, message: str
    ) -> tuple[str, str] | None:
        """Generate a quantum digital signature for a message.

        Args:
            party_id: Unique identifier for the signing party
            message: Message to sign

        Returns:
            Tuple of (signature, timestamp) if successful, None otherwise
        """
        if party_id not in self.authenticated_parties:
            return None

        # Get the shared key
        shared_key = self.authenticated_parties[party_id]["shared_key"]

        # Convert the key to bytes
        key_bytes = bytes(
            int("".join(map(str, shared_key)), 2).to_bytes(
                (len(shared_key) + 7) // 8, byteorder="big"
            )
        )

        # Convert the message to bytes
        message_bytes = message.encode("utf-8")

        # Generate the signature using HMAC-SHA256
        signature = hmac.new(key_bytes, message_bytes, hashlib.sha256).hexdigest()
        timestamp = str(int(time.time()))

        return (signature, timestamp)

    def verify_quantum_signature(
        self, party_id: str, message: str, signature: str, timestamp: str
    ) -> bool:
        """Verify a quantum digital signature.

        Args:
            party_id: Unique identifier for the signing party
            message: Message that was signed
            signature: Signature to verify
            timestamp: Timestamp of the signature

        Returns:
            True if signature is valid, False otherwise
        """
        # Check if the party is registered
        if party_id not in self.authenticated_parties:
            return False

        # Check if the signature is still valid (1 hour expiration)
        try:
            signature_time = int(timestamp)
            if time.time() - signature_time > 3600:
                return False
        except ValueError:
            return False

        # Get the shared key
        shared_key = self.authenticated_parties[party_id]["shared_key"]

        # Convert the key to bytes
        key_bytes = bytes(
            int("".join(map(str, shared_key)), 2).to_bytes(
                (len(shared_key) + 7) // 8, byteorder="big"
            )
        )

        # Convert the message to bytes
        message_bytes = message.encode("utf-8")

        # Generate the expected signature
        expected_signature = hmac.new(
            key_bytes, message_bytes, hashlib.sha256
        ).hexdigest()

        # Compare with the provided signature
        return hmac.compare_digest(expected_signature, signature)

    def get_party_info(self, party_id: str) -> dict | None:
        """Get information about an authenticated party.

        Args:
            party_id: Unique identifier for the party

        Returns:
            Dictionary with party information, None if not found
        """
        if party_id in self.authenticated_parties:
            party_info = self.authenticated_parties[party_id].copy()
            # Remove the shared key from the returned information
            del party_info["shared_key"]
            return party_info
        return None

    def remove_party(self, party_id: str) -> bool:
        """Remove an authenticated party.

        Args:
            party_id: Unique identifier for the party

        Returns:
            True if successful, False otherwise
        """
        if party_id in self.authenticated_parties:
            del self.authenticated_parties[party_id]

            # Remove any tokens associated with this party
            tokens_to_remove = [
                token_id
                for token_id, token_info in self.auth_tokens.items()
                if token_info["party_id"] == party_id
            ]
            for token_id in tokens_to_remove:
                del self.auth_tokens[token_id]

            return True
        return False
