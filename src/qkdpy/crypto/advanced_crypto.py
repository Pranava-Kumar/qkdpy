"""Advanced quantum cryptography utilities."""

import hashlib
import secrets
import time

import numpy as np

from ..utils import bits_to_bytes, bytes_to_bits


class QuantumHash:
    """Quantum-resistant hash functions and utilities."""

    @staticmethod
    def sha3_256_hash(data: bytes) -> bytes:
        """Compute SHA3-256 hash of data.

        Args:
            data: Input data to hash

        Returns:
            SHA3-256 hash of the data
        """
        try:
            import hashlib

            return hashlib.sha3_256(data).digest()
        except (ImportError, AttributeError):
            # Fallback to SHA256 if SHA3 is not available
            return hashlib.sha256(data).digest()

    @staticmethod
    def shake_256_hash(data: bytes, length: int) -> bytes:
        """Compute SHAKE-256 extendable output function.

        Args:
            data: Input data to hash
            length: Desired output length in bytes

        Returns:
            SHAKE-256 hash of the data with specified length
        """
        try:
            import hashlib

            return hashlib.shake_256(data).digest(length)
        except (ImportError, AttributeError):
            # Fallback to SHA256 with truncation if SHAKE is not available
            hash_result = hashlib.sha256(data).digest()
            return hash_result[:length] if len(hash_result) >= length else hash_result

    @staticmethod
    def quantum_hash(bits: list[int]) -> list[int]:
        """Compute a quantum-resistant hash of a bit string.

        Args:
            bits: Input bit string

        Returns:
            Hashed bit string
        """
        # Convert bits to bytes
        data_bytes = bits_to_bytes(bits)

        # Compute SHA3-256 hash
        hash_bytes = QuantumHash.sha3_256_hash(data_bytes)

        # Convert back to bits
        hash_bits = bytes_to_bits(hash_bytes)

        return hash_bits

    @staticmethod
    def merkle_tree_hash(leaves: list[list[int]]) -> list[int]:
        """Compute the root hash of a Merkle tree.

        Args:
            leaves: List of leaf values (bit strings)

        Returns:
            Root hash of the Merkle tree
        """
        if not leaves:
            return []

        if len(leaves) == 1:
            return QuantumHash.quantum_hash(leaves[0])

        # Build the Merkle tree
        current_level = leaves[:]

        while len(current_level) > 1:
            next_level = []

            # Pair up adjacent nodes and hash them together
            for i in range(0, len(current_level), 2):
                if i + 1 < len(current_level):
                    # Hash the concatenation of two nodes
                    combined = current_level[i] + current_level[i + 1]
                    hashed = QuantumHash.quantum_hash(combined)
                    next_level.append(hashed)
                else:
                    # Odd number of nodes, just pass through the last one
                    next_level.append(current_level[i])

            current_level = next_level

        return current_level[0]

    @staticmethod
    def hash_chain(seed: list[int], length: int) -> list[list[int]]:
        """Generate a hash chain of specified length.

        Args:
            seed: Initial seed value
            length: Number of hashes to generate

        Returns:
            List of hash values in the chain
        """
        if length <= 0:
            return []

        chain = [seed]

        for _ in range(length - 1):
            # Hash the previous value to get the next one
            next_value = QuantumHash.quantum_hash(chain[-1])
            chain.append(next_value)

        return chain


class QuantumCommitment:
    """Quantum cryptographic commitment schemes."""

    def __init__(self):
        """Initialize the quantum commitment scheme."""
        self.commitments: dict[str, dict] = {}

    def commit(self, value: str, salt: str | None = None) -> tuple[str, str]:
        """Create a commitment to a value.

        Args:
            value: Value to commit to
            salt: Salt for the commitment (optional)

        Returns:
            Tuple of (commitment_id, opening_key)
        """
        # Generate a random salt if not provided
        if salt is None:
            salt = secrets.token_hex(16)

        # Generate a random opening key
        opening_key = secrets.token_hex(32)

        # Create the commitment by hashing value + salt + opening_key
        commitment_data = f"{value}:{salt}:{opening_key}".encode()
        commitment = hashlib.sha256(commitment_data).hexdigest()

        # Generate a unique commitment ID
        commitment_id = (
            f"commit_{int(time.time() * 1000000)}_{np.random.randint(10000)}"
        )

        # Store the commitment
        self.commitments[commitment_id] = {
            "value": value,
            "salt": salt,
            "opening_key": opening_key,
            "commitment": commitment,
            "timestamp": time.time(),
        }

        return (commitment_id, opening_key)

    def open_commitment(self, commitment_id: str, opening_key: str) -> dict | None:
        """Open a commitment to reveal the value.

        Args:
            commitment_id: ID of the commitment to open
            opening_key: Key to open the commitment

        Returns:
            Dictionary with commitment details if valid, None otherwise
        """
        if commitment_id not in self.commitments:
            return None

        commitment_info = self.commitments[commitment_id]

        # Verify the opening key
        if commitment_info["opening_key"] != opening_key:
            return None

        # Verify the commitment is still valid (24 hours)
        if time.time() - commitment_info["timestamp"] > 86400:
            return None

        # Reconstruct and verify the commitment
        commitment_data = f"{commitment_info['value']}:{commitment_info['salt']}:{opening_key}".encode()
        reconstructed_commitment = hashlib.sha256(commitment_data).hexdigest()

        if reconstructed_commitment != commitment_info["commitment"]:
            return None

        return {
            "value": commitment_info["value"],
            "salt": commitment_info["salt"],
            "commitment": commitment_info["commitment"],
        }

    def verify_commitment(
        self, commitment_id: str, value: str, salt: str, opening_key: str
    ) -> bool:
        """Verify that a commitment matches a value.

        Args:
            commitment_id: ID of the commitment
            value: Value to verify
            salt: Salt used in the commitment
            opening_key: Opening key for the commitment

        Returns:
            True if commitment matches the value, False otherwise
        """
        if commitment_id not in self.commitments:
            return False

        commitment_info = self.commitments[commitment_id]

        # Check if the provided details match the stored commitment
        if (
            commitment_info["value"] != value
            or commitment_info["salt"] != salt
            or commitment_info["opening_key"] != opening_key
        ):
            return False

        # Reconstruct and verify the commitment
        commitment_data = f"{value}:{salt}:{opening_key}".encode()
        reconstructed_commitment = hashlib.sha256(commitment_data).hexdigest()

        return reconstructed_commitment == commitment_info["commitment"]

    def get_commitment_info(self, commitment_id: str) -> dict | None:
        """Get information about a commitment.

        Args:
            commitment_id: ID of the commitment

        Returns:
            Dictionary with commitment information, None if not found
        """
        if commitment_id not in self.commitments:
            return None

        # Return a copy without sensitive information
        commitment_info = self.commitments[commitment_id].copy()
        del commitment_info["opening_key"]  # Don't reveal the opening key
        del commitment_info["value"]  # Don't reveal the committed value

        return commitment_info


class QuantumZeroKnowledge:
    """Quantum zero-knowledge proof utilities."""

    @staticmethod
    def schnorr_proof(
        secret: int, public: int, generator: int = 2, modulus: int = 2**255 - 19
    ) -> tuple[int, int]:
        """Generate a Schnorr zero-knowledge proof.

        Args:
            secret: Secret value
            public: Public value (g^secret mod p)
            generator: Generator for the cyclic group
            modulus: Modulus for the cyclic group

        Returns:
            Tuple of (challenge, response) for the proof
        """
        # Generate a random nonce
        nonce = secrets.randbelow(modulus)

        # Compute the commitment (g^nonce mod p)
        commitment = pow(generator, nonce, modulus)

        # Generate a challenge (in a real implementation, this would be a hash)
        challenge = (commitment + public) % modulus

        # Compute the response (nonce + challenge * secret mod (p-1))
        response = (nonce + challenge * secret) % (modulus - 1)

        return (challenge, response)

    @staticmethod
    def verify_schnorr_proof(
        public: int,
        challenge: int,
        response: int,
        generator: int = 2,
        modulus: int = 2**255 - 19,
    ) -> bool:
        """Verify a Schnorr zero-knowledge proof.

        Args:
            public: Public value (g^secret mod p)
            challenge: Challenge from the proof
            response: Response from the proof
            generator: Generator for the cyclic group
            modulus: Modulus for the cyclic group

        Returns:
            True if proof is valid, False otherwise
        """
        # Compute g^response mod p
        left_side = pow(generator, response, modulus)

        # Compute commitment * public^challenge mod p
        commitment = pow(generator, response - challenge * (modulus - 1), modulus)
        right_side = (commitment * pow(public, challenge, modulus)) % modulus

        return left_side == right_side

    @staticmethod
    def hash_based_commitment(value: str) -> tuple[str, list[str]]:
        """Create a hash-based commitment for zero-knowledge proofs.

        Args:
            value: Value to commit to

        Returns:
            Tuple of (commitment, decommitment_path) for use in ZKPs
        """
        # Generate a random salt
        salt = secrets.token_hex(16)

        # Create the commitment
        commitment_data = f"{value}:{salt}".encode()
        commitment = hashlib.sha256(commitment_data).hexdigest()

        # For this simplified implementation, we'll just return the salt as the decommitment
        # In a real implementation, this would be a Merkle tree path or similar structure
        decommitment_path = [salt]

        return (commitment, decommitment_path)

    @staticmethod
    def verify_hash_commitment(
        commitment: str, value: str, decommitment_path: list[str]
    ) -> bool:
        """Verify a hash-based commitment.

        Args:
            commitment: Commitment to verify
            value: Value that was committed
            decommitment_path: Path to verify the commitment

        Returns:
            True if commitment is valid, False otherwise
        """
        if not decommitment_path:
            return False

        # Reconstruct the commitment
        salt = decommitment_path[0]
        commitment_data = f"{value}:{salt}".encode()
        reconstructed_commitment = hashlib.sha256(commitment_data).hexdigest()

        return reconstructed_commitment == commitment
