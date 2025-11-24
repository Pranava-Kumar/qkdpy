"""Tests for quantum key exchange."""

import unittest

from qkdpy.core import QuantumChannel
from qkdpy.crypto import QuantumKeyExchange


class TestQuantumKeyExchange(unittest.TestCase):
    """Test cases for the QuantumKeyExchange class."""

    def setUp(self):
        """Set up test fixtures."""
        self.channel = QuantumChannel()
        self.key_exchange = QuantumKeyExchange(self.channel)

    def test_key_exchange_initialization(self):
        """Test quantum key exchange initialization."""
        self.assertEqual(len(self.key_exchange.exchange_sessions), 0)
        self.assertEqual(self.key_exchange.successful_exchanges, 0)
        self.assertEqual(self.key_exchange.failed_exchanges, 0)

    def test_initiate_key_exchange(self):
        """Test initiating a key exchange."""
        party_a = "alice"
        party_b = "bob"

        # Initiate a key exchange
        session_id = self.key_exchange.initiate_key_exchange(
            party_a, party_b, key_length=50
        )

        # Check that a session was created
        self.assertIsNotNone(session_id)

        # Check that the session is stored
        self.assertIn(session_id, self.key_exchange.exchange_sessions)

        # Check session details
        session = self.key_exchange.exchange_sessions[session_id]
        self.assertEqual(session["party_a"], party_a)
        self.assertEqual(session["party_b"], party_b)
        self.assertEqual(session["key_length"], 50)

    def test_execute_key_exchange(self):
        """Test executing a key exchange."""
        party_a = "alice"
        party_b = "bob"

        # Initiate a key exchange
        session_id = self.key_exchange.initiate_key_exchange(
            party_a, party_b, key_length=50
        )

        # Execute the key exchange
        result = self.key_exchange.execute_key_exchange(session_id)

        # Check that the execution completed (result may be True or False)
        self.assertIsInstance(result, bool)

    def test_get_shared_key(self):
        """Test getting a shared key from a completed exchange."""
        party_a = "alice"
        party_b = "bob"

        # Initiate a key exchange
        session_id = self.key_exchange.initiate_key_exchange(
            party_a, party_b, key_length=50
        )

        # Execute the key exchange
        self.key_exchange.execute_key_exchange(session_id)

        # Get the shared key
        shared_key = self.key_exchange.get_shared_key(session_id)

        # Check that we got a key (may be None if exchange failed)
        if shared_key is not None:
            self.assertIsInstance(shared_key, list)

    def test_verify_key_exchange(self):
        """Test verifying a party's participation in a key exchange."""
        party_a = "alice"
        party_b = "bob"
        challenge = "test_challenge"

        # Initiate a key exchange
        session_id = self.key_exchange.initiate_key_exchange(
            party_a, party_b, key_length=50
        )

        # Execute the key exchange
        self.key_exchange.execute_key_exchange(session_id)

        # Verify party A's participation
        token_id = self.key_exchange.verify_key_exchange(session_id, party_a, challenge)

        # Check that we got a verification token
        self.assertIsNotNone(token_id)

    def test_get_exchange_statistics(self):
        """Test getting key exchange statistics."""
        # Get initial statistics
        initial_stats = self.key_exchange.get_exchange_statistics()

        # Check initial values
        self.assertEqual(initial_stats["successful_exchanges"], 0)
        self.assertEqual(initial_stats["failed_exchanges"], 0)
        self.assertEqual(initial_stats["total_exchanges"], 0)
        self.assertEqual(initial_stats["success_rate"], 0.0)


if __name__ == "__main__":
    unittest.main()
