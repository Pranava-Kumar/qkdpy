"""Audit logging for QKDpy enterprise deployments.

This module provides tamper-evident audit logging for compliance
with security standards and regulations.
"""

import hashlib
import hmac
import json
import os
import secrets
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from ..utils.logging_config import get_logger

logger = get_logger(__name__)

# Keyed secret for the audit hash chain. A plain SHA-256 chain only detects
# *accidental* corruption: anyone with write access to the log can recompute
# every ``previous_hash`` and produce a valid chain. Using a keyed HMAC means
# a tamperer cannot forge chain links without this in-process secret, turning
# the chain from corruption-evident into tamper-resistant.
_CHAIN_SECRET = secrets.token_bytes(32)


class AuditEventType(Enum):
    """Types of auditable events."""

    # Key events
    KEY_GENERATED = "key_generated"
    KEY_IMPORTED = "key_imported"
    KEY_EXPORTED = "key_exported"
    KEY_DELETED = "key_deleted"
    KEY_ROTATED = "key_rotated"
    KEY_ACCESSED = "key_accessed"
    KEY_EXPIRED = "key_expired"
    KEY_DISTRIBUTED = "key_distributed"

    # Protocol events
    PROTOCOL_STARTED = "protocol_started"
    PROTOCOL_COMPLETED = "protocol_completed"
    PROTOCOL_EXECUTED = "protocol_executed"
    PROTOCOL_FAILED = "protocol_failed"
    PROTOCOL_ABORTED = "protocol_aborted"

    # Security events
    SECURITY_VIOLATION = "security_violation"
    ATTACK_DETECTED = "attack_detected"
    QBER_THRESHOLD_EXCEEDED = "qber_threshold_exceeded"
    AUTHENTICATION_FAILED = "authentication_failed"

    # System events
    SYSTEM_STARTED = "system_started"
    SYSTEM_STOPPED = "system_stopped"
    CONFIG_CHANGED = "config_changed"
    HSM_CONNECTED = "hsm_connected"
    HSM_DISCONNECTED = "hsm_disconnected"

    # Access events
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"


@dataclass
class AuditEvent:
    """Represents an audit log event."""

    event_id: str
    event_type: AuditEventType
    timestamp: datetime
    actor: str | None
    resource: str | None
    action: str
    result: str
    details: dict[str, Any]
    previous_hash: str | None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data["event_type"] = self.event_type.value
        data["timestamp"] = self.timestamp.isoformat()
        return data

    def compute_hash(self) -> str:
        """Compute the keyed-HMAC of the event for tamper-resistant chaining."""
        data = json.dumps(self.to_dict(), sort_keys=True).encode()
        return hmac.new(_CHAIN_SECRET, data, hashlib.sha256).hexdigest()


class AuditLogger:
    """Tamper-evident audit logger for QKD operations.

    Creates a chain of audit events where each event includes
    a hash of the previous event, enabling detection of tampering.
    """

    def __init__(
        self,
        *,
        storage_path: str | None = None,
        enable_chain_verification: bool = True,
    ) -> None:
        """Initialize audit logger.

        Args:
            storage_path: Path to store audit logs (None for memory only)
            enable_chain_verification: Whether to verify chain integrity
        """
        self.storage_path = storage_path
        self.enable_chain_verification = enable_chain_verification

        self._events: list[AuditEvent] = []
        self._last_hash: str | None = None

        logger.info(
            "AuditLogger initialized",
            storage_path=storage_path,
            chain_verification=enable_chain_verification,
        )

    def log_event(
        self,
        event_type: AuditEventType,
        action: str,
        *,
        actor: str | None = None,
        resource: str | None = None,
        result: str = "success",
        details: dict[str, Any] | None = None,
    ) -> AuditEvent:
        """Log an audit event.

        Args:
            event_type: Type of event
            action: Description of the action
            actor: Entity performing the action
            resource: Resource being acted upon
            result: Result of the action
            details: Additional event details

        Returns:
            The created audit event
        """
        event = AuditEvent(
            event_id=secrets.token_hex(16),
            event_type=event_type,
            timestamp=datetime.now(UTC),
            actor=actor,
            resource=resource,
            action=action,
            result=result,
            details=details or {},
            previous_hash=self._last_hash,
        )

        # Update chain
        self._last_hash = event.compute_hash()
        self._events.append(event)

        # Persist if storage configured
        if self.storage_path:
            self._persist_event(event)

        # Log to structured logger as well
        logger.info(
            f"AUDIT: {event_type.value}",
            event_id=event.event_id,
            actor=actor,
            resource=resource,
            result=result,
        )

        return event

    def _persist_event(self, event: AuditEvent) -> None:
        """Persist event to storage (append + fsync).

        Each event is appended as a single JSON line.  The file descriptor is
        flushed and fsynced after every write to guard against data loss on
        crash (the most recent line may still be lost if the OS cannot flush
        the disk cache, but no prior content will be corrupt).
        """
        assert self.storage_path is not None
        line = json.dumps(event.to_dict()) + "\n"
        try:
            with open(self.storage_path, "a") as f:
                f.write(line)
                f.flush()
                os.fsync(f.fileno())
        except Exception as e:
            logger.error("Failed to persist audit event", error=str(e))

    def log_key_event(
        self,
        event_type: AuditEventType,
        key_id: str,
        *,
        actor: str | None = None,
        result: str = "success",
        **details: Any,
    ) -> AuditEvent:
        """Log a key-related event.

        Args:
            event_type: Type of key event
            key_id: Key identifier
            actor: Entity performing the action
            result: Result of the action
            **details: Additional details

        Returns:
            The created audit event
        """
        return self.log_event(
            event_type,
            f"Key operation: {event_type.value}",
            actor=actor,
            resource=f"key:{key_id}",
            result=result,
            details=details,
        )

    def log_protocol_event(
        self,
        event_type: AuditEventType,
        protocol_name: str,
        session_id: str | None = None,
        *,
        actor: str | None = None,
        result: str = "success",
        **details: Any,
    ) -> AuditEvent:
        """Log a protocol-related event.

        Args:
            event_type: Type of protocol event
            protocol_name: Name of the protocol
            session_id: Session identifier
            actor: Entity performing the action
            result: Result of the action
            **details: Additional details

        Returns:
            The created audit event
        """
        resource = f"protocol:{protocol_name}"
        if session_id:
            resource += f":{session_id}"

        return self.log_event(
            event_type,
            f"Protocol operation: {event_type.value}",
            actor=actor,
            resource=resource,
            result=result,
            details=details,
        )

    def log_security_event(
        self,
        event_type: AuditEventType,
        description: str,
        *,
        actor: str | None = None,
        resource: str | None = None,
        severity: str = "high",
        **details: Any,
    ) -> AuditEvent:
        """Log a security-related event.

        Args:
            event_type: Type of security event
            description: Description of the event
            actor: Entity involved
            resource: Resource involved
            severity: Severity level
            **details: Additional details

        Returns:
            The created audit event
        """
        details["severity"] = severity

        return self.log_event(
            event_type,
            description,
            actor=actor,
            resource=resource,
            result="security_alert",
            details=details,
        )

    def verify_chain_integrity(self) -> tuple[bool, list[str]]:
        """Verify the keyed-HMAC integrity of the audit chain.

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        if not self.enable_chain_verification:
            return True, []

        errors: list[str] = []

        for i, event in enumerate(self._events):
            if i == 0:
                if event.previous_hash is not None:
                    errors.append("First event has non-null previous_hash")
            else:
                expected_hash = self._events[i - 1].compute_hash()
                if not hmac.compare_digest(event.previous_hash or "", expected_hash):
                    errors.append(
                        f"Chain broken at event {i} ({event.event_id}): "
                        f"expected {expected_hash}, got {event.previous_hash}"
                    )

        is_valid = len(errors) == 0

        if not is_valid:
            logger.security(
                "Audit chain integrity violation detected",
                error_count=len(errors),
            )

        return is_valid, errors

    def get_events(
        self,
        *,
        event_type: AuditEventType | None = None,
        actor: str | None = None,
        resource: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int | None = None,
    ) -> list[AuditEvent]:
        """Query audit events.

        Args:
            event_type: Filter by event type
            actor: Filter by actor
            resource: Filter by resource
            since: Events after this time
            until: Events before this time
            limit: Maximum number of events to return

        Returns:
            Matching audit events
        """
        results = self._events

        if event_type:
            results = [e for e in results if e.event_type == event_type]

        if actor:
            results = [e for e in results if e.actor == actor]

        if resource:
            results = [e for e in results if e.resource and resource in e.resource]

        if since:
            results = [e for e in results if e.timestamp >= since]

        if until:
            results = [e for e in results if e.timestamp <= until]

        if limit:
            results = results[-limit:]

        return results

    def export_events(
        self,
        format: str = "json",
    ) -> str:
        """Export audit events to a string.

        Args:
            format: Export format ("json", "cef", or "leef")

        Returns:
            Exported audit log
        """
        if format == "json":
            return json.dumps(
                [e.to_dict() for e in self._events],
                indent=2,
            )

        elif format == "cef":
            # Common Event Format (for SIEM integration)
            lines = []
            for event in self._events:
                severity = event.details.get("severity", "5")
                line = (
                    f"CEF:0|QKDpy|QKD|1.0|{event.event_type.value}|"
                    f"{event.action}|{severity}|"
                    f"eventId={event.event_id} "
                    f"timestamp={event.timestamp.isoformat()} "
                    f"actor={event.actor or 'unknown'} "
                    f"resource={event.resource or 'unknown'} "
                    f"result={event.result}"
                )
                lines.append(line)
            return "\n".join(lines)

        elif format == "leef":
            # Log Event Extended Format (IBM QRadar)
            lines = []
            for event in self._events:
                line = (
                    f"LEEF:1.0|QKDpy|QKD|1.0|{event.event_type.value}|"
                    f"devTime={event.timestamp.isoformat()}\t"
                    f"usrName={event.actor or 'unknown'}\t"
                    f"resource={event.resource or 'unknown'}\t"
                    f"result={event.result}"
                )
                lines.append(line)
            return "\n".join(lines)

        else:
            raise ValueError(f"Unsupported export format: {format}")

    def get_statistics(self) -> dict[str, Any]:
        """Get audit statistics.

        Returns:
            Dictionary with audit statistics
        """
        stats: dict[str, int] = {}
        for event in self._events:
            key = event.event_type.value
            stats[key] = stats.get(key, 0) + 1

        return {
            "total_events": len(self._events),
            "events_by_type": stats,
            "chain_valid": self.verify_chain_integrity()[0],
        }
