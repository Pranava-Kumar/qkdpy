"""Quantum key management and distribution system."""

import json
import time

import numpy as np

from ..core import QuantumChannel
from ..protocols import BB84


class QuantumKeyManager:
    """Manages quantum key generation, storage, and distribution."""

    def __init__(self, channel: QuantumChannel):
        """Initialize the quantum key manager.

        Args:
            channel: Quantum channel for key generation
        """
        self.channel = channel
        self.key_store: dict[str, dict] = {}
        self.active_sessions: dict[str, dict] = {}
        self.key_generation_rate = 0.0
        self.total_keys_generated = 0

    def generate_key(
        self, session_id: str, key_length: int = 128, protocol: str = "BB84"
    ) -> str | None:
        """Generate a quantum key for a session.

        Args:
            session_id: Unique identifier for the session
            key_length: Desired length of the key
            protocol: QKD protocol to use

        Returns:
            Key identifier if successful, None otherwise
        """
        try:
            # Create a QKD protocol instance
            if protocol == "BB84":
                qkd = BB84(self.channel, key_length=key_length)
            else:
                raise ValueError(f"Unsupported protocol: {protocol}")

            # Execute the protocol
            results = qkd.execute()

            # Check if the key generation was successful
            if not results["is_secure"] or len(results["final_key"]) == 0:
                return None

            # Generate a unique key identifier
            key_id = f"key_{int(time.time() * 1000000)}_{np.random.randint(10000)}"

            # Store the key
            self.key_store[key_id] = {
                "session_id": session_id,
                "key": results["final_key"],
                "length": len(results["final_key"]),
                "timestamp": time.time(),
                "qber": results["qber"],
                "protocol": protocol,
            }

            # Update session information
            if session_id not in self.active_sessions:
                self.active_sessions[session_id] = {
                    "keys": [],
                    "created": time.time(),
                    "last_activity": time.time(),
                }

            self.active_sessions[session_id]["keys"].append(key_id)
            self.active_sessions[session_id]["last_activity"] = time.time()

            # Update statistics
            self.total_keys_generated += 1
            self.key_generation_rate = (
                self.total_keys_generated
                / (time.time() - self.active_sessions[session_id]["created"])
                if time.time() - self.active_sessions[session_id]["created"] > 0
                else 0
            )

            return key_id

        except Exception as e:
            print(f"Error generating key: {e}")
            return None

    def get_key(self, key_id: str) -> list[int] | None:
        """Retrieve a key by its identifier.

        Args:
            key_id: Unique identifier for the key

        Returns:
            The key if found, None otherwise
        """
        if key_id in self.key_store:
            return self.key_store[key_id]["key"]
        return None

    def delete_key(self, key_id: str) -> bool:
        """Delete a key from storage.

        Args:
            key_id: Unique identifier for the key

        Returns:
            True if successful, False otherwise
        """
        if key_id in self.key_store:
            # Remove from session tracking
            session_id = self.key_store[key_id]["session_id"]
            if session_id in self.active_sessions:
                if key_id in self.active_sessions[session_id]["keys"]:
                    self.active_sessions[session_id]["keys"].remove(key_id)

            # Remove from key store
            del self.key_store[key_id]
            return True
        return False

    def get_session_keys(self, session_id: str) -> list[str]:
        """Get all key identifiers for a session.

        Args:
            session_id: Unique identifier for the session

        Returns:
            List of key identifiers
        """
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]["keys"]
        return []

    def rotate_session_key(self, session_id: str, key_length: int = 128) -> str | None:
        """Generate a new key for a session (key rotation).

        Args:
            session_id: Unique identifier for the session
            key_length: Desired length of the new key

        Returns:
            New key identifier if successful, None otherwise
        """
        return self.generate_key(session_id, key_length)

    def get_key_statistics(self) -> dict:
        """Get statistics about key generation and storage.

        Returns:
            Dictionary with key statistics
        """
        return {
            "total_keys": len(self.key_store),
            "total_sessions": len(self.active_sessions),
            "key_generation_rate": self.key_generation_rate,
            "total_keys_generated": self.total_keys_generated,
        }

    def export_key_store(self, filename: str) -> bool:
        """Export the key store to a file.

        Args:
            filename: Name of the file to export to

        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert keys to a serializable format
            export_data = {}
            for key_id, key_info in self.key_store.items():
                export_data[key_id] = {
                    "session_id": key_info["session_id"],
                    "length": key_info["length"],
                    "timestamp": key_info["timestamp"],
                    "qber": key_info["qber"],
                    "protocol": key_info["protocol"],
                    # Note: Actual keys are not exported for security
                }

            with open(filename, "w") as f:
                json.dump(export_data, f, indent=2)

            return True
        except Exception as e:
            print(f"Error exporting key store: {e}")
            return False

    def import_key_store(self, filename: str) -> bool:
        """Import a key store from a file.

        Args:
            filename: Name of the file to import from

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(filename) as f:
                import_data = json.load(f)

            # Update the key store
            for key_id, key_info in import_data.items():
                self.key_store[key_id] = {
                    "session_id": key_info["session_id"],
                    "length": key_info["length"],
                    "timestamp": key_info["timestamp"],
                    "qber": key_info["qber"],
                    "protocol": key_info["protocol"],
                    # Note: Actual keys are not imported for security
                }

            return True
        except Exception as e:
            print(f"Error importing key store: {e}")
            return False

    def cleanup_expired_sessions(self, max_age: float = 3600.0) -> int:
        """Remove expired sessions and their keys.

        Args:
            max_age: Maximum age of sessions in seconds

        Returns:
            Number of sessions cleaned up
        """
        current_time = time.time()
        expired_sessions = []

        for session_id, session_info in self.active_sessions.items():
            if current_time - session_info["last_activity"] > max_age:
                expired_sessions.append(session_id)

        # Remove expired sessions and their keys
        for session_id in expired_sessions:
            # Delete all keys for this session
            for key_id in self.active_sessions[session_id]["keys"]:
                if key_id in self.key_store:
                    del self.key_store[key_id]

            # Remove the session
            del self.active_sessions[session_id]

        return len(expired_sessions)
