"""Enterprise features for QKDpy.

This module provides enterprise-grade features including:
- Hardware Security Module (HSM) integration
- Audit logging for compliance
- Compliance reporting
- Key escrow capabilities
- Product tier licensing (FREE / ENTERPRISE / PREMIUM)
- Quantum-safe migration toolkit (PREMIUM tier)
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

# Licensing — always import (defaults to FREE tier)
from .licensing import (
    Feature,
    LicenseError,
    ProductTier,
    feature_available,
    get_active_tier,
    require_feature,
    set_active_tier,
)

# Quantum-safe migration toolkit (PREMIUM tier)
from .quantum_safe import (
    CryptoAlgorithmType,
    CryptoAsset,
    CryptoInventoryReport,
    MigrationPhase,
    MigrationRoadmap,
    MigrationStep,
    QuantumResistance,
    QuantumSafeAssessment,
    classic_enterprise_profile,
    generate_roadmap,
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
    # Licensing
    "ProductTier",
    "Feature",
    "LicenseError",
    "get_active_tier",
    "set_active_tier",
    "feature_available",
    "require_feature",
    # Quantum-safe
    "CryptoAlgorithmType",
    "CryptoAsset",
    "CryptoInventoryReport",
    "QuantumResistance",
    "MigrationPhase",
    "MigrationStep",
    "MigrationRoadmap",
    "QuantumSafeAssessment",
    "classic_enterprise_profile",
    "generate_roadmap",
]
