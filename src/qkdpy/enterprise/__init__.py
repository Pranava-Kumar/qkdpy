"""Enterprise features for QKDpy.

This module provides enterprise-grade features including:
- Hardware Security Module (HSM) integration
- Audit logging for compliance
- Compliance reporting
- Key escrow capabilities
"""

from .audit import AuditEvent, AuditEventType, AuditLogger
from .compliance import (
    ComplianceChecker,
    ComplianceReport,
    ComplianceStandard,
)
from .hsm_interface import (
    HSMInterface,
    HSMKeyHandle,
    HSMProvider,
    SoftwareHSM,
)

__all__ = [
    # HSM
    "HSMInterface",
    "HSMKeyHandle",
    "SoftwareHSM",
    "HSMProvider",
    # Audit
    "AuditLogger",
    "AuditEvent",
    "AuditEventType",
    # Compliance
    "ComplianceChecker",
    "ComplianceReport",
    "ComplianceStandard",
]
