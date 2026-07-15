"""Tests for advanced cryptographic utilities."""

import unittest

from qkdpy.crypto.advanced_crypto import (
    QuantumCommitment,
    QuantumHash,
    QuantumZeroKnowledge,
)


class TestQuantumHash(unittest.TestCase):
    """Test the QuantumHash class."""

    def test_sha3_256_hash_returns_bytes(self):
        """sha3_256_hash returns bytes."""
        result = QuantumHash.sha3_256_hash(b"test data")
        self.assertIsInstance(result, bytes)
        self.assertEqual(len(result), 32)  # 256 bits = 32 bytes

    def test_sha3_256_hash_deterministic(self):
        """sha3_256_hash should produce the same output for the same input."""
        h1 = QuantumHash.sha3_256_hash(b"hello")
        h2 = QuantumHash.sha3_256_hash(b"hello")
        self.assertEqual(h1, h2)

    def test_sha3_256_hash_different_inputs(self):
        """Different inputs should produce different hashes."""
        h1 = QuantumHash.sha3_256_hash(b"hello")
        h2 = QuantumHash.sha3_256_hash(b"world")
        self.assertNotEqual(h1, h2)

    def test_sha3_256_hash_empty(self):
        """Empty input should still produce a 32-byte hash."""
        result = QuantumHash.sha3_256_hash(b"")
        self.assertEqual(len(result), 32)

    def test_shake_256_hash_default_length(self):
        """shake_256_hash returns bytes of requested length."""
        result = QuantumHash.shake_256_hash(b"test", length=16)
        self.assertIsInstance(result, bytes)
        self.assertEqual(len(result), 16)

    def test_shake_256_hash_deterministic(self):
        """shake_256_hash should be deterministic."""
        h1 = QuantumHash.shake_256_hash(b"test", length=10)
        h2 = QuantumHash.shake_256_hash(b"test", length=10)
        self.assertEqual(h1, h2)

    def test_quantum_hash_returns_bit_list(self):
        """quantum_hash returns a list of bits (0/1 values)."""
        bits = [0, 1, 0, 1, 1, 0, 1, 0]
        result = QuantumHash.quantum_hash(bits)
        self.assertIsInstance(result, list)
        self.assertTrue(all(b in (0, 1) for b in result))

    def test_quantum_hash_deterministic(self):
        """quantum_hash should be deterministic for the same input."""
        bits = [0, 1, 0, 1, 1, 0, 1, 0]
        h1 = QuantumHash.quantum_hash(bits)
        h2 = QuantumHash.quantum_hash(bits)
        self.assertEqual(h1, h2)

    def test_quantum_hash_short_input(self):
        """quantum_hash should handle very short inputs."""
        result = QuantumHash.quantum_hash([0])
        self.assertIsInstance(result, list)
        self.assertTrue(all(b in (0, 1) for b in result))

    def test_quantum_hash_empty_returns_256_bits(self):
        """quantum_hash of empty list should return 256 bits (SHA3-256 of empty)."""
        result = QuantumHash.quantum_hash([])
        self.assertEqual(len(result), 256)

    def test_quantum_hash_long_input(self):
        """quantum_hash should handle longer bit strings."""
        bits = [0, 1] * 64  # 128 bits
        result = QuantumHash.quantum_hash(bits)
        self.assertGreater(len(result), 0)
        self.assertTrue(all(b in (0, 1) for b in result))


class TestQuantumCommitment(unittest.TestCase):
    """Test the QuantumCommitment class."""

    def setUp(self):
        self.scheme = QuantumCommitment()

    def test_commit_returns_tuple(self):
        """commit returns a tuple of (commitment_id, opening_key)."""
        commitment_id, opening_key = self.scheme.commit("secret message")
        self.assertIsInstance(commitment_id, str)
        self.assertIsInstance(opening_key, str)

    def test_open_valid_commitment(self):
        """A valid opening should return the commitment info."""
        commitment_id, opening_key = self.scheme.commit("my secret message")
        info = self.scheme.open_commitment(commitment_id, opening_key)
        self.assertIsNotNone(info)
        self.assertEqual(info["value"], "my secret message")

    def test_open_wrong_key(self):
        """Wrong opening key should return None."""
        commitment_id, _ = self.scheme.commit("my secret message")
        info = self.scheme.open_commitment(commitment_id, "wrong_key")
        self.assertIsNone(info)

    def test_open_nonexistent_commitment(self):
        """Opening a nonexistent commitment should return None."""
        info = self.scheme.open_commitment("nonexistent", "some_key")
        self.assertIsNone(info)

    def test_open_commitment_with_salt(self):
        """Commitment with explicit salt should work."""
        commitment_id, opening_key = self.scheme.commit("value", salt="fixed_salt")
        info = self.scheme.open_commitment(commitment_id, opening_key)
        self.assertIsNotNone(info)

    def test_verify_valid_commitment(self):
        """verify_commitment with correct details should return True."""
        commitment_id, opening_key = self.scheme.commit("test_value", salt="test_salt")
        is_valid = self.scheme.verify_commitment(
            commitment_id, "test_value", "test_salt", opening_key
        )
        self.assertTrue(is_valid)

    def test_verify_wrong_value(self):
        """verify_commitment with wrong value should return False."""
        commitment_id, opening_key = self.scheme.commit("real_value", salt="salt")
        is_valid = self.scheme.verify_commitment(
            commitment_id, "wrong_value", "salt", opening_key
        )
        self.assertFalse(is_valid)

    def test_verify_wrong_key(self):
        """verify_commitment with wrong opening key should return False."""
        commitment_id, opening_key = self.scheme.commit("real_value", salt="salt")
        is_valid = self.scheme.verify_commitment(
            commitment_id, "real_value", "salt", "wrong_key"
        )
        self.assertFalse(is_valid)

    def test_commit_deterministic(self):
        """Commitments should use secure randomness (not trivially deterministic)."""
        c1_id, _ = self.scheme.commit("same message")
        c2_id, _ = self.scheme.commit("same message")
        # Same message should produce different commitment IDs due to random nonce
        self.assertNotEqual(c1_id, c2_id)

    def test_get_commitment_info(self):
        """get_commitment_info returns info without sensitive fields."""
        commitment_id, opening_key = self.scheme.commit("secret_value")
        info = self.scheme.get_commitment_info(commitment_id)
        self.assertIsNotNone(info)
        self.assertIn("commitment", info)
        self.assertNotIn("opening_key", info)
        self.assertNotIn("value", info)

    def test_get_commitment_info_nonexistent(self):
        """get_commitment_info for nonexistent ID returns None."""
        info = self.scheme.get_commitment_info("nonexistent")
        self.assertIsNone(info)


class TestQuantumZeroKnowledge(unittest.TestCase):
    """Test the QuantumZeroKnowledge class."""

    def test_schnorr_proof_returns_tuple(self):
        """schnorr_proof returns a tuple of (challenge, response)."""
        secret = 42
        public = pow(2, secret, 2**255 - 19)
        challenge, response = QuantumZeroKnowledge.schnorr_proof(secret, public)
        self.assertIsInstance(challenge, int)
        self.assertIsInstance(response, int)

    def test_verify_schnorr_proof_valid(self):
        """A valid Schnorr proof should verify successfully."""
        secret = 42
        modulus = 2**255 - 19
        public = pow(2, secret, modulus)
        challenge, response = QuantumZeroKnowledge.schnorr_proof(secret, public)
        is_valid = QuantumZeroKnowledge.verify_schnorr_proof(
            public, challenge, response
        )
        self.assertTrue(is_valid)

    def test_verify_schnorr_wrong_secret(self):
        """A proof for a different secret should fail verification."""
        secret = 42
        wrong_secret = 99
        modulus = 2**255 - 19
        public = pow(2, secret, modulus)
        wrong_public = pow(2, wrong_secret, modulus)
        challenge, response = QuantumZeroKnowledge.schnorr_proof(secret, public)
        is_valid = QuantumZeroKnowledge.verify_schnorr_proof(
            wrong_public, challenge, response
        )
        self.assertFalse(is_valid)

    def test_hash_based_commitment_returns_tuple(self):
        """hash_based_commitment returns (commitment, decommitment_path)."""
        commitment, path = QuantumZeroKnowledge.hash_based_commitment("test_value")
        self.assertIsInstance(commitment, str)
        self.assertIsInstance(path, list)
        self.assertGreater(len(path), 0)

    def test_verify_hash_commitment_valid(self):
        """A valid hash commitment should verify correctly."""
        value = "my_secret_value"
        commitment, path = QuantumZeroKnowledge.hash_based_commitment(value)
        is_valid = QuantumZeroKnowledge.verify_hash_commitment(commitment, value, path)
        self.assertTrue(is_valid)

    def test_verify_hash_commitment_wrong_value(self):
        """Wrong value should fail hash commitment verification."""
        commitment, path = QuantumZeroKnowledge.hash_based_commitment("real_value")
        is_valid = QuantumZeroKnowledge.verify_hash_commitment(
            commitment, "wrong_value", path
        )
        self.assertFalse(is_valid)

    def test_verify_hash_commitment_empty_path(self):
        """Empty decommitment path should return False."""
        is_valid = QuantumZeroKnowledge.verify_hash_commitment("comm", "value", [])
        self.assertFalse(is_valid)


if __name__ == "__main__":
    unittest.main()
