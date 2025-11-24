"""Tests for quantum key manager."""

import unittest

from qkdpy.core import QuantumChannel
from qkdpy.key_management import QuantumKeyManager


class TestQuantumKeyManager(unittest.TestCase):
    """Test cases for the QuantumKeyManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.channel = QuantumChannel()
        self.key_manager = QuantumKeyManager(self.channel)

    def test_key_manager_initialization(self):
        """Test quantum key manager initialization."""
        self.assertEqual(len(self.key_manager.key_store), 0)
        self.assertEqual(len(self.key_manager.active_sessions), 0)
        self.assertEqual(self.key_manager.key_generation_rate, 0.0)
        self.assertEqual(self.key_manager.total_keys_generated, 0)

    def test_generate_key(self):
        """Test key generation."""
        session_id = "test_session"

        # Generate a key
        key_id = self.key_manager.generate_key(session_id, key_length=50)

        # Check that a key was generated
        self.assertIsNotNone(key_id)

        # Check that the key is stored
        self.assertIn(key_id, self.key_manager.key_store)

        # Check that the session is tracked
        self.assertIn(session_id, self.key_manager.active_sessions)
        self.assertIn(key_id, self.key_manager.active_sessions[session_id]["keys"])

    def test_get_key(self):
        """Test retrieving a key."""
        session_id = "test_session"

        # Generate a key
        key_id = self.key_manager.generate_key(session_id, key_length=50)

        # Retrieve the key
        key = self.key_manager.get_key(key_id)

        # Check that we got a valid key
        self.assertIsNotNone(key)
        self.assertIsInstance(key, list)
        self.assertGreater(len(key), 0)

    def test_delete_key(self):
        """Test deleting a key."""
        session_id = "test_session"

        # Generate a key
        key_id = self.key_manager.generate_key(session_id, key_length=50)

        # Delete the key
        result = self.key_manager.delete_key(key_id)

        # Check that the deletion was successful
        self.assertTrue(result)

        # Check that the key is no longer in the store
        self.assertNotIn(key_id, self.key_manager.key_store)

        # Check that the key is no longer in the session
        self.assertNotIn(key_id, self.key_manager.active_sessions[session_id]["keys"])

    def test_get_session_keys(self):
        """Test getting all keys for a session."""
        session_id = "test_session"

        # Generate multiple keys for the same session
        key_id1 = self.key_manager.generate_key(session_id, key_length=50)
        key_id2 = self.key_manager.generate_key(session_id, key_length=50)

        # Get all session keys
        session_keys = self.key_manager.get_session_keys(session_id)

        # Check that we got the right keys
        self.assertEqual(len(session_keys), 2)
        self.assertIn(key_id1, session_keys)
        self.assertIn(key_id2, session_keys)

    def test_get_key_statistics(self):
        """Test getting key statistics."""
        session_id = "test_session"

        # Generate a few keys
        self.key_manager.generate_key(session_id, key_length=50)
        self.key_manager.generate_key(session_id, key_length=50)

        # Get statistics
        stats = self.key_manager.get_key_statistics()

        # Check the statistics
        self.assertEqual(stats["total_keys"], 2)
        self.assertEqual(stats["total_sessions"], 1)
        self.assertGreaterEqual(stats["total_keys_generated"], 2)


if __name__ == "__main__":
    unittest.main()
