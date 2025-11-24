"""Tests for quantum authentication."""

import unittest

from qkdpy.core import QuantumChannel
from qkdpy.crypto import QuantumAuthenticator


class TestQuantumAuthenticator(unittest.TestCase):
    """Test cases for the QuantumAuthenticator class."""

    def setUp(self):
        """Set up test fixtures."""
        self.channel = QuantumChannel()
        self.authenticator = QuantumAuthenticator(self.channel)

    def test_authenticator_initialization(self):
        """Test quantum authenticator initialization."""
        self.assertEqual(len(self.authenticator.authenticated_parties), 0)
        self.assertEqual(len(self.authenticator.auth_tokens), 0)

    def test_register_party(self):
        """Test registering a party for authentication."""
        party_id = "alice"

        # Register a party
        result = self.authenticator.register_party(party_id, shared_key_length=50)

        # Check that registration was successful
        self.assertTrue(result)

        # Check that the party is registered
        self.assertIn(party_id, self.authenticator.authenticated_parties)

    def test_authenticate_party(self):
        """Test authenticating a registered party."""
        party_id = "alice"

        # Register a party
        self.authenticator.register_party(party_id, shared_key_length=50)

        # Authenticate the party
        token_id = self.authenticator.authenticate_party(party_id)

        # Check that we got a token
        self.assertIsNotNone(token_id)

        # Check that the token is stored
        self.assertIn(token_id, self.authenticator.auth_tokens)

    def test_verify_authentication(self):
        """Test verifying an authentication token."""
        party_id = "alice"
        challenge = "test_challenge"

        # Register a party
        self.authenticator.register_party(party_id, shared_key_length=50)

        # Authenticate the party
        token_id = self.authenticator.authenticate_party(party_id, challenge)

        # Verify the authentication
        result = self.authenticator.verify_authentication(party_id, token_id, challenge)

        # Check that verification was successful
        self.assertTrue(result)

    def test_generate_quantum_signature(self):
        """Test generating a quantum digital signature."""
        party_id = "alice"
        message = "test message"

        # Register a party
        self.authenticator.register_party(party_id, shared_key_length=50)

        # Generate a signature
        signature_result = self.authenticator.generate_quantum_signature(
            party_id, message
        )

        # Check that we got a signature
        self.assertIsNotNone(signature_result)
        self.assertIsInstance(signature_result, tuple)
        self.assertEqual(len(signature_result), 2)

    def test_verify_quantum_signature(self):
        """Test verifying a quantum digital signature."""
        party_id = "alice"
        message = "test message"

        # Register a party
        self.authenticator.register_party(party_id, shared_key_length=50)

        # Generate a signature
        signature, timestamp = self.authenticator.generate_quantum_signature(
            party_id, message
        )

        # Verify the signature
        result = self.authenticator.verify_quantum_signature(
            party_id, message, signature, timestamp
        )

        # Check that verification was successful
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
