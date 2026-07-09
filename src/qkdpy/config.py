"""Centralized configuration management for QKDpy.

This module provides a configuration system with environment-based
configuration, secure defaults, and runtime parameter validation.
"""

import os
from dataclasses import dataclass, field
from enum import Enum

from .exceptions import InvalidConfigError


class LogLevel(Enum):
    """Log level enumeration."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class SecurityMode(Enum):
    """Security mode enumeration."""

    DEVELOPMENT = "development"  # Relaxed security for testing
    TESTING = "testing"  # Standard security with verbose logging
    PRODUCTION = "production"  # Maximum security, minimal logging


@dataclass
class LoggingConfig:
    """Logging configuration."""

    level: LogLevel = LogLevel.INFO
    json_output: bool = False
    include_caller: bool = True
    redact_secrets: bool = True
    audit_enabled: bool = True
    log_file: str | None = None


@dataclass
class SecurityConfig:
    """Security configuration."""

    mode: SecurityMode = SecurityMode.PRODUCTION
    min_key_length: int = 128
    max_qber_threshold: float = 0.11
    require_authentication: bool = True
    enable_key_rotation: bool = True
    key_rotation_interval_seconds: int = 3600
    enable_audit_logging: bool = True


@dataclass
class ProtocolConfig:
    """Protocol execution configuration."""

    default_protocol: str = "BB84"
    default_key_length: int = 256
    security_threshold: float = 0.11
    num_decoy_states: int = 2
    enable_finite_key_analysis: bool = True


@dataclass
class ChannelConfig:
    """Quantum channel configuration."""

    default_loss_coefficient: float = 0.2  # dB/km
    default_noise_model: str = "depolarizing"
    default_noise_level: float = 0.01
    enable_polarization_drift: bool = True
    enable_phase_fluctuations: bool = True
    temperature_kelvin: float = 293.0  # Room temperature


@dataclass
class MLConfig:
    """Machine learning configuration."""

    enable_ml_optimization: bool = True
    default_optimization_method: str = "bayesian"
    max_iterations: int = 100
    enable_model_caching: bool = True
    model_cache_dir: str | None = None
    # Resource-aware settings
    enable_quantization: bool = False
    max_memory_mb: int = 512
    enable_early_stopping: bool = True


@dataclass
class EnterpriseConfig:
    """Enterprise features configuration."""

    enable_hsm: bool = False
    hsm_library_path: str | None = None
    enable_compliance_reporting: bool = False
    compliance_standard: str = "ETSI-GS-QKD-014"
    enable_key_escrow: bool = False
    product_tier: str = "free"  # "free" | "enterprise" | "premium"
    license_key: str | None = None


@dataclass
class QKDConfig:
    """Main QKDpy configuration container."""

    logging: LoggingConfig = field(default_factory=LoggingConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    protocol: ProtocolConfig = field(default_factory=ProtocolConfig)
    channel: ChannelConfig = field(default_factory=ChannelConfig)
    ml: MLConfig = field(default_factory=MLConfig)
    enterprise: EnterpriseConfig = field(default_factory=EnterpriseConfig)

    # General settings
    debug_mode: bool = False
    strict_validation: bool = True


# Global configuration instance
_config: QKDConfig | None = None


def get_config() -> QKDConfig:
    """Get the current configuration.

    Returns:
        Current QKDpy configuration
    """
    global _config
    if _config is None:
        _config = load_config_from_env()
    return _config


def set_config(config: QKDConfig) -> None:
    """Set the global configuration.

    If the config includes an enterprise product tier, the licensing
    module is synchronised automatically.

    Args:
        config: Configuration to set
    """
    global _config
    _config = config
    # Sync product tier to licensing module
    tier_str = config.enterprise.product_tier.lower()
    try:
        from .enterprise.licensing import ProductTier, set_active_tier  # noqa: PLC0415

        set_active_tier(ProductTier(tier_str))
    except (ImportError, ValueError):
        pass  # licensing module unavailable or unknown tier — use default


def reset_config() -> None:
    """Reset configuration to defaults."""
    global _config
    _config = None


def load_config_from_env() -> QKDConfig:
    """Load configuration from environment variables.

    Environment variables are prefixed with QKDPY_ and use underscores
    for nested settings. For example:
    - QKDPY_DEBUG_MODE=true
    - QKDPY_LOGGING_LEVEL=DEBUG
    - QKDPY_SECURITY_MODE=production

    Returns:
        Configuration loaded from environment
    """
    config = QKDConfig()

    # General settings
    if _get_env_bool("QKDPY_DEBUG_MODE"):
        config.debug_mode = True
        config.logging.level = LogLevel.DEBUG
        config.security.mode = SecurityMode.DEVELOPMENT

    # Logging settings
    if level := os.getenv("QKDPY_LOGGING_LEVEL"):
        try:
            config.logging.level = LogLevel(level.upper())
        except ValueError:
            pass

    config.logging.json_output = _get_env_bool("QKDPY_LOGGING_JSON")

    # Security settings
    if mode := os.getenv("QKDPY_SECURITY_MODE"):
        try:
            config.security.mode = SecurityMode(mode.lower())
        except ValueError:
            pass

    if min_key := os.getenv("QKDPY_MIN_KEY_LENGTH"):
        config.security.min_key_length = int(min_key)

    # ML settings
    if not _get_env_bool("QKDPY_ML_ENABLED", default=True):
        config.ml.enable_ml_optimization = False

    config.ml.enable_quantization = _get_env_bool("QKDPY_ML_QUANTIZATION")

    if max_mem := os.getenv("QKDPY_ML_MAX_MEMORY_MB"):
        config.ml.max_memory_mb = int(max_mem)

    # Enterprise settings
    config.enterprise.enable_hsm = _get_env_bool("QKDPY_HSM_ENABLED")
    config.enterprise.hsm_library_path = os.getenv("QKDPY_HSM_LIBRARY_PATH")
    config.enterprise.compliance_standard = os.getenv(
        "QKDPY_COMPLIANCE_STANDARD", config.enterprise.compliance_standard
    )
    config.enterprise.product_tier = os.getenv(
        "QKDPY_PRODUCT_TIER", config.enterprise.product_tier
    )
    config.enterprise.license_key = os.getenv("QKDPY_LICENSE_KEY")

    return config


def _get_env_bool(key: str, default: bool = False) -> bool:
    """Get boolean value from environment variable."""
    value = os.getenv(key, "").lower()
    if value in ("true", "1", "yes", "on"):
        return True
    if value in ("false", "0", "no", "off"):
        return False
    return default


def validate_config(config: QKDConfig) -> list[str]:
    """Validate configuration and return list of warnings.

    Args:
        config: Configuration to validate

    Returns:
        List of warning messages

    Raises:
        InvalidConfigError: If configuration is invalid
    """
    warnings: list[str] = []

    # Security validations
    if config.security.min_key_length < 64:
        raise InvalidConfigError(
            "Minimum key length must be at least 64 bits",
            context={"min_key_length": config.security.min_key_length},
        )

    if config.security.max_qber_threshold > 0.25:
        warnings.append(
            f"QBER threshold {config.security.max_qber_threshold} is very high, "
            "consider lowering for better security"
        )

    # Production mode checks
    if config.security.mode == SecurityMode.PRODUCTION:
        if config.debug_mode:
            raise InvalidConfigError(
                "Debug mode cannot be enabled in production security mode"
            )

        if not config.security.require_authentication:
            warnings.append(
                "Authentication is disabled in production mode - this is not recommended"
            )

        if not config.logging.redact_secrets:
            raise InvalidConfigError(
                "Secret redaction must be enabled in production mode"
            )

    # HSM validation
    if config.enterprise.enable_hsm and not config.enterprise.hsm_library_path:
        raise InvalidConfigError(
            "HSM library path must be specified when HSM is enabled",
            context={"enable_hsm": True, "hsm_library_path": None},
        )

    return warnings


# Convenience functions for common configuration access


def is_debug_mode() -> bool:
    """Check if debug mode is enabled."""
    return get_config().debug_mode


def is_production_mode() -> bool:
    """Check if running in production security mode."""
    return get_config().security.mode == SecurityMode.PRODUCTION


def get_security_threshold() -> float:
    """Get the current QBER security threshold."""
    return get_config().protocol.security_threshold


def get_min_key_length() -> int:
    """Get minimum required key length."""
    return get_config().security.min_key_length


def is_hsm_enabled() -> bool:
    """Check if HSM integration is enabled."""
    return get_config().enterprise.enable_hsm


def is_ml_enabled() -> bool:
    """Check if ML optimization is enabled."""
    return get_config().ml.enable_ml_optimization
