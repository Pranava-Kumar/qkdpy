"""Product tier and feature licensing for QKDpy.

Defines a three-tier product model (FREE / ENTERPRISE / PREMIUM) with
fine-grained feature gating.  Every enterprise and premium feature can
be checked at runtime so callers get a clear ``LicenseError`` instead
of silently degraded behaviour.
"""

from __future__ import annotations

from collections.abc import Callable
from enum import StrEnum
from functools import wraps
from typing import Any, TypeVar

from ..exceptions import QKDException

F = TypeVar("F", bound=Callable[..., Any])


class ProductTier(StrEnum):
    """QKDpy product tiers."""

    FREE = "free"
    ENTERPRISE = "enterprise"
    PREMIUM = "premium"


class Feature(StrEnum):
    """Individual features that can be gated behind a tier."""

    COMPLIANCE_REPORTING = "compliance_reporting"
    COMPLIANCE_HTML_EXPORT = "compliance_html_export"
    HSM_INTEGRATION = "hsm_integration"
    ML_ATTACK_DETECTION = "ml_attack_detection"
    AUDIT_EXPORT = "audit_export"
    KEY_ESCROW = "key_escrow"
    QUANTUM_SAFE_MIGRATION = "quantum_safe_migration"
    CRYPTO_INVENTORY = "crypto_inventory"
    PRIORITY_SUPPORT = "priority_support"
    ADVANCED_VISUALIZATION = "advanced_visualization"


# Tier → feature availability map.
TIER_FEATURES: dict[ProductTier, set[Feature]] = {
    ProductTier.FREE: {
        # FREE tier gets core protocols, basic simulation, basic viz
        Feature.ADVANCED_VISUALIZATION,
    },
    ProductTier.ENTERPRISE: {
        Feature.COMPLIANCE_REPORTING,
        Feature.COMPLIANCE_HTML_EXPORT,
        Feature.HSM_INTEGRATION,
        Feature.ML_ATTACK_DETECTION,
        Feature.AUDIT_EXPORT,
        Feature.KEY_ESCROW,
        Feature.ADVANCED_VISUALIZATION,
    },
    ProductTier.PREMIUM: {
        Feature.COMPLIANCE_REPORTING,
        Feature.COMPLIANCE_HTML_EXPORT,
        Feature.HSM_INTEGRATION,
        Feature.ML_ATTACK_DETECTION,
        Feature.AUDIT_EXPORT,
        Feature.KEY_ESCROW,
        Feature.QUANTUM_SAFE_MIGRATION,
        Feature.CRYPTO_INVENTORY,
        Feature.PRIORITY_SUPPORT,
        Feature.ADVANCED_VISUALIZATION,
    },
}

# Global active tier — defaults to FREE.
_active_tier: ProductTier = ProductTier.FREE


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


class LicenseError(QKDException):
    """Raised when a feature is not available in the current tier."""

    error_code = "QKD_LICENSE_ERROR"


def get_active_tier() -> ProductTier:
    """Return the currently active product tier."""
    return _active_tier


def set_active_tier(tier: ProductTier) -> None:
    """Set the active product tier at runtime.

    Calling this with a non-FREE tier is the equivalent of activating an
    enterprise or premium license key.

    WARNING: This build performs NO cryptographic verification of any license
    key. The tier is an in-memory runtime variable controlled entirely by the
    caller (or the ``QKDPY_PRODUCT_TIER`` env var). Any operator can set a
    non-FREE tier without a valid key. Treat this as a local demo gate only —
    it provides feature availability, not license enforcement or anti-piracy.
    """
    global _active_tier
    _active_tier = tier


def feature_available(feature: Feature, *, tier: ProductTier | None = None) -> bool:
    """Check whether *feature* is available in the given or current tier."""
    return feature in TIER_FEATURES[tier or _active_tier]


def require_feature(feature: Feature) -> Callable[[F], F]:
    """Decorator — raises ``LicenseError`` if the feature is not licensed.

    Usage::

        @require_feature(Feature.COMPLIANCE_HTML_EXPORT)
        def export_html(self) -> str:
            ...
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not feature_available(feature):
                raise LicenseError(
                    f"'{feature.value}' requires the "
                    f"{_min_tier_for_feature(feature).value.title()} tier or higher. "
                    f"Current tier: {_active_tier.value}"
                )
            return func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _min_tier_for_feature(feature: Feature) -> ProductTier:
    """Return the lowest tier that includes *feature*."""
    for tier in (ProductTier.PREMIUM, ProductTier.ENTERPRISE, ProductTier.FREE):
        if feature in TIER_FEATURES[tier]:
            return tier
    return ProductTier.PREMIUM  # fallback — should not happen for known features


__all__ = [
    "Feature",
    "LicenseError",
    "ProductTier",
    "feature_available",
    "get_active_tier",
    "require_feature",
    "set_active_tier",
]
