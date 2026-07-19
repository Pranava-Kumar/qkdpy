"""Product tier and feature licensing for QKDpy.

Defines a three-tier product model (FREE / ENTERPRISE / PREMIUM) with
fine-grained feature gating.  Every enterprise and premium feature can
be checked at runtime so callers get a clear ``LicenseError`` instead
of silently degraded behaviour.
"""

from __future__ import annotations

import hashlib
import hmac
import os
from collections.abc import Callable
from enum import StrEnum
from functools import wraps
from typing import Any, TypeVar

from ..exceptions import QKDException

F = TypeVar("F", bound=Callable[..., Any])

# Optional license-key enforcement. By default the tier system is a local demo
# gate (no anti-piracy). Set ``QKDPY_LICENSE_ENFORCEMENT=1`` to require a valid
# HMAC-signed license key before a non-FREE tier can be activated — this makes
# the audit finding (tier set without verification) addressable in deployments
# that need it.
LicenseKeyMissing = object()


def _enforcement_enabled() -> bool:
    return os.environ.get("QKDPY_LICENSE_ENFORCEMENT", "0") == "1"


def _verify_license_key(tier: ProductTier, license_key: Any) -> bool:
    """Verify a license key for the requested tier.

    The key must be a string holding ``<tier>:<hmac>`` where ``<hmac>`` is an
    HMAC-SHA256 of the tier name under the deployment secret
    (``QKDPY_LICENSE_SECRET``). Without a configured secret the deployment is
    treated as unlicensed (keys cannot be forged without the secret).
    """
    if not isinstance(license_key, str) or ":" not in license_key:
        return False
    declared_tier, received_hmac = license_key.split(":", 1)
    if declared_tier != tier.value:
        return False
    secret = os.environ.get("QKDPY_LICENSE_SECRET", "")
    if not secret:
        return False
    expected = hmac.new(
        secret.encode(), tier.value.encode(), hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, received_hmac)


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


def set_active_tier(tier: ProductTier, *, license_key: str | None = None) -> None:
    """Set the active product tier at runtime.

    Calling this with a non-FREE tier is the equivalent of activating an
    enterprise or premium license, so it MUST be accompanied by a license key.
    The call refuses to silently pass: a non-FREE tier without a license key
    raises ``LicenseError``.

    In demo mode (default, ``QKDPY_LICENSE_ENFORCEMENT`` unset or ``0``) a
    non-empty ``license_key`` is accepted as an unverified demo license — this
    still forces the caller to acknowledge the license rather than flipping a
    tier with nothing. When ``QKDPY_LICENSE_ENFORCEMENT=1`` is set, the key must
    be a valid HMAC-signed ``"<tier>:<hmac>"`` under ``QKDPY_LICENSE_SECRET``;
    any other value is rejected.

    Args:
        tier: The tier to activate.
        license_key: License key for the requested tier. Required for non-FREE
            tiers. Ignored for FREE.

    Raises:
        LicenseError: If a non-FREE tier is requested without a valid license.
    """
    global _active_tier

    if tier == ProductTier.FREE:
        _active_tier = tier
        return

    # Non-FREE tier: a license key is mandatory — never silently pass.
    if not isinstance(license_key, str) or not license_key.strip():
        raise LicenseError(
            f"Activating tier '{tier.value}' requires a license key. "
            f"Provide a valid license_key; this tier switch is refused without one."
        )

    if _enforcement_enabled() and not _verify_license_key(tier, license_key):
        raise LicenseError(
            f"Activating tier '{tier.value}' requires a valid license key. "
            f"Set QKDPY_LICENSE_ENFORCEMENT=0 for demo mode or supply a signed key."
        )

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
