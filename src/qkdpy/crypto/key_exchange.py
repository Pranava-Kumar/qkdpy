"""Quantum key exchange protocols and utilities."""

import json
import time

import numpy as np

from ..core import QuantumChannel
from ..protocols import BB84, E91
from .quantum_auth import QuantumAuthenticator


class QuantumKeyExchange:
    """Manages quantum key exchange between parties."""

    def __init__(self, channel: QuantumChannel):
        """Initialize the quantum key exchange system.

        Args:
            channel: Quantum channel for key exchange
        """
        self.channel = channel
        self.exchange_sessions: dict[str, dict] = {}
        self.authenticator = QuantumAuthenticator(channel)
        self.successful_exchanges = 0
        self.failed_exchanges = 0

    def initiate_key_exchange(
        self,
        party_a: str,
        party_b: str,
        key_length: int = 128,
        protocol: str = "BB84",
        timeout: float = 30.0,
    ) -> str | None:
        """Initiate a quantum key exchange between two parties.

        Args:
            party_a: Identifier for the first party
            party_b: Identifier for the second party
            key_length: Desired length of the exchanged key
            protocol: QKD protocol to use ('BB84', 'E91', etc.)
            timeout: Maximum time to wait for exchange completion

        Returns:
            Session identifier if successful, None otherwise
        """
        # Generate a unique session identifier
        session_id = f"exchange_{int(time.time() * 1000000)}_{np.random.randint(10000)}"

        # Register both parties for authentication
        if not self.authenticator.register_party(party_a, key_length):
            return None

        if not self.authenticator.register_party(party_b, key_length):
            # Clean up party A registration
            self.authenticator.remove_party(party_a)
            return None

        # Create exchange session
        self.exchange_sessions[session_id] = {
            "party_a": party_a,
            "party_b": party_b,
            "protocol": protocol,
            "key_length": key_length,
            "status": "initiated",
            "start_time": time.time(),
            "timeout": timeout,
            "shared_key": None,
            "qber": None,
        }

        return session_id

    def execute_key_exchange(self, session_id: str) -> bool:
        """Execute the quantum key exchange for a session.

        Args:
            session_id: Session identifier

        Returns:
            True if exchange successful, False otherwise
        """
        if session_id not in self.exchange_sessions:
            return False

        session = self.exchange_sessions[session_id]

        # Check if session has timed out
        if time.time() - session["start_time"] > session["timeout"]:
            session["status"] = "timeout"
            self.failed_exchanges += 1
            return False

        try:
            # Execute the QKD protocol
            if session["protocol"] == "BB84":
                qkd = BB84(self.channel, key_length=session["key_length"])
            elif session["protocol"] == "E91":
                qkd = E91(self.channel, key_length=session["key_length"])
            else:
                raise ValueError(f"Unsupported protocol: {session['protocol']}")

            # Run the protocol
            results = qkd.execute()

            # Check if the exchange was successful
            if not results["is_secure"] or len(results["final_key"]) == 0:
                session["status"] = "failed"
                self.failed_exchanges += 1
                return False

            # Store the shared key
            session["shared_key"] = results["final_key"]
            session["qber"] = results["qber"]
            session["status"] = "completed"
            session["end_time"] = time.time()

            self.successful_exchanges += 1
            return True

        except Exception as e:
            print(f"Error during key exchange: {e}")
            session["status"] = "error"
            session["error"] = str(e)
            self.failed_exchanges += 1
            return False

    def get_shared_key(self, session_id: str) -> list[int] | None:
        """Get the shared key from a completed exchange.

        Args:
            session_id: Session identifier

        Returns:
            Shared key if exchange was successful, None otherwise
        """
        if session_id not in self.exchange_sessions:
            return None

        session = self.exchange_sessions[session_id]
        if session["status"] == "completed":
            return session["shared_key"]
        return None

    def verify_key_exchange(
        self, session_id: str, party: str, challenge: str | None = None
    ) -> str | None:
        """Verify a party's participation in a key exchange.

        Args:
            session_id: Session identifier
            party: Party identifier
            challenge: Challenge string for authentication (optional)

        Returns:
            Authentication token if verification successful, None otherwise
        """
        if session_id not in self.exchange_sessions:
            return None

        session = self.exchange_sessions[session_id]

        # Check if party is part of this exchange
        if party not in [session["party_a"], session["party_b"]]:
            return None

        # Check if exchange was successful
        if session["status"] != "completed":
            return None

        # Authenticate the party
        return self.authenticator.authenticate_party(party, challenge)

    def get_session_info(self, session_id: str) -> dict | None:
        """Get information about a key exchange session.

        Args:
            session_id: Session identifier

        Returns:
            Dictionary with session information, None if not found
        """
        if session_id not in self.exchange_sessions:
            return None

        # Return a copy of the session information
        session_info = self.exchange_sessions[session_id].copy()

        # Remove sensitive information
        if "shared_key" in session_info:
            del session_info["shared_key"]

        return session_info

    def get_exchange_statistics(self) -> dict:
        """Get statistics about key exchanges.

        Returns:
            Dictionary with exchange statistics
        """
        total_exchanges = self.successful_exchanges + self.failed_exchanges
        success_rate = (
            self.successful_exchanges / total_exchanges if total_exchanges > 0 else 0.0
        )

        return {
            "successful_exchanges": self.successful_exchanges,
            "failed_exchanges": self.failed_exchanges,
            "total_exchanges": total_exchanges,
            "success_rate": success_rate,
            "active_sessions": len(self.exchange_sessions),
        }

    def cleanup_expired_sessions(self, max_age: float = 3600.0) -> int:
        """Remove expired sessions.

        Args:
            max_age: Maximum age of sessions in seconds

        Returns:
            Number of sessions cleaned up
        """
        current_time = time.time()
        expired_sessions = []

        for session_id, session_info in self.exchange_sessions.items():
            # Check if session has expired based on age
            session_age = current_time - session_info.get("start_time", current_time)
            if session_age > max_age:
                expired_sessions.append(session_id)

        # Remove expired sessions
        for session_id in expired_sessions:
            del self.exchange_sessions[session_id]

        return len(expired_sessions)

    def export_session_log(self, filename: str) -> bool:
        """Export session log to a file.

        Args:
            filename: Name of the file to export to

        Returns:
            True if successful, False otherwise
        """
        try:
            # Prepare session data for export (without sensitive information)
            export_data = {}
            for session_id, session_info in self.exchange_sessions.items():
                # Copy session info
                safe_info = session_info.copy()

                # Remove sensitive information
                if "shared_key" in safe_info:
                    del safe_info["shared_key"]

                export_data[session_id] = safe_info

            # Write to file
            with open(filename, "w") as f:
                json.dump(export_data, f, indent=2, default=str)

            return True
        except Exception as e:
            print(f"Error exporting session log: {e}")
            return False
