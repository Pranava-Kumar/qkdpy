"""QKDpy Exception Hierarchy.

This module provides a structured exception hierarchy for enterprise-grade
error handling in QKD applications. All exceptions inherit from a base
QKDException class and provide detailed context for debugging and auditing.
"""

from typing import Any

_REDACT_KEYS: frozenset[str] = frozenset(
    {
        "raw_key",
        "key_material",
        "secret_key",
        "shared_secret",
        "password",
        "token",
        "api_key",
        "private_key",
        "session_key",
    }
)


def _redact_context(context: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of ``context`` with sensitive keys redacted.

    Uses the same denylist as the structured logger to avoid leaking
    secrets into logs or external error reporting.
    """
    redacted: dict[str, Any] = {}
    for key, value in context.items():
        if key in _REDACT_KEYS:
            redacted[key] = "[REDACTED]"
        else:
            redacted[key] = value
    return redacted


class QKDException(Exception):
    """Base exception for all QKDpy errors.

    Provides structured error information including error codes,
    context data, and recovery suggestions for enterprise deployments.
    """

    error_code: str = "QKD_GENERIC_ERROR"

    def __init__(
        self,
        message: str,
        *,
        error_code: str | None = None,
        context: dict[str, Any] | None = None,
        cause: Exception | None = None,
        recoverable: bool = True,
    ) -> None:
        """Initialize QKD exception.

        Args:
            message: Human-readable error message
            error_code: Machine-readable error code for logging
            context: Additional context data for debugging
            cause: Original exception that caused this error
            recoverable: Whether the operation can be retried
        """
        super().__init__(message)
        self.error_code = error_code or self.__class__.error_code
        self.context = context or {}
        self.cause = cause
        self.recoverable = recoverable

        # Chain the original exception if provided
        if cause is not None:
            self.__cause__ = cause

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for logging/serialization.

        Context values keyed by names in the sensitive-data denylist
        (e.g., ``raw_key``, ``secret_key``) are redacted to ``[REDACTED]``
        before return so error reports do not leak secrets.
        """
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": str(self),
            "context": _redact_context(self.context),
            "recoverable": self.recoverable,
            "cause": str(self.cause) if self.cause else None,
        }


# === Protocol Errors ===


class ProtocolError(QKDException):
    """Base class for protocol-related errors."""

    error_code = "QKD_PROTOCOL_ERROR"


class ProtocolSecurityError(ProtocolError):
    """Security violation detected in protocol execution.

    Raised when QBER exceeds threshold, eavesdropping is detected,
    or other security conditions are violated.
    """

    error_code = "QKD_SECURITY_VIOLATION"

    def __init__(
        self,
        message: str,
        *,
        qber: float | None = None,
        threshold: float | None = None,
        attack_type: str | None = None,
        **kwargs: Any,
    ) -> None:
        context = kwargs.pop("context", {})
        if qber is not None:
            context["qber"] = qber
        if threshold is not None:
            context["threshold"] = threshold
        if attack_type is not None:
            context["attack_type"] = attack_type
        super().__init__(message, context=context, recoverable=False, **kwargs)


class ProtocolStateError(ProtocolError):
    """Protocol is in an invalid state for the requested operation."""

    error_code = "QKD_PROTOCOL_STATE_ERROR"


class InsufficientKeyError(ProtocolError):
    """Insufficient key material generated."""

    error_code = "QKD_INSUFFICIENT_KEY"


# === Channel Errors ===


class ChannelError(QKDException):
    """Base class for quantum channel errors."""

    error_code = "QKD_CHANNEL_ERROR"


class ChannelLossError(ChannelError):
    """Excessive loss detected in quantum channel."""

    error_code = "QKD_CHANNEL_LOSS"

    def __init__(
        self,
        message: str,
        *,
        loss_rate: float | None = None,
        expected_rate: float | None = None,
        **kwargs: Any,
    ) -> None:
        context = kwargs.pop("context", {})
        if loss_rate is not None:
            context["loss_rate"] = loss_rate
        if expected_rate is not None:
            context["expected_rate"] = expected_rate
        super().__init__(message, context=context, **kwargs)


class ChannelNoiseError(ChannelError):
    """Excessive noise detected in quantum channel."""

    error_code = "QKD_CHANNEL_NOISE"


class ChannelCalibrationError(ChannelError):
    """Channel calibration failed or is required."""

    error_code = "QKD_CHANNEL_CALIBRATION"


# === Key Management Errors ===


class KeyManagementError(QKDException):
    """Base class for key management errors."""

    error_code = "QKD_KEY_MANAGEMENT_ERROR"


class KeyNotFoundError(KeyManagementError):
    """Requested key not found in storage."""

    error_code = "QKD_KEY_NOT_FOUND"


class KeyExpiredError(KeyManagementError):
    """Key has expired and cannot be used."""

    error_code = "QKD_KEY_EXPIRED"


class KeyExhaustedError(KeyManagementError):
    """Key usage limit has been reached."""

    error_code = "QKD_KEY_EXHAUSTED"


class KeyStorageError(KeyManagementError):
    """Error accessing key storage."""

    error_code = "QKD_KEY_STORAGE_ERROR"


# === Cryptographic Errors ===


class CryptoError(QKDException):
    """Base class for cryptographic operation errors."""

    error_code = "QKD_CRYPTO_ERROR"


class EncryptionError(CryptoError):
    """Encryption operation failed."""

    error_code = "QKD_ENCRYPTION_ERROR"


class DecryptionError(CryptoError):
    """Decryption operation failed."""

    error_code = "QKD_DECRYPTION_ERROR"


class AuthenticationError(CryptoError):
    """Authentication failed."""

    error_code = "QKD_AUTHENTICATION_ERROR"


class IntegrityError(CryptoError):
    """Data integrity check failed."""

    error_code = "QKD_INTEGRITY_ERROR"


# === Validation Errors ===


class ValidationError(QKDException):
    """Base class for input validation errors."""

    error_code = "QKD_VALIDATION_ERROR"


class ParameterError(ValidationError):
    """Invalid parameter value."""

    error_code = "QKD_PARAMETER_ERROR"

    def __init__(
        self,
        message: str,
        *,
        parameter: str | None = None,
        value: Any = None,
        expected: str | None = None,
        **kwargs: Any,
    ) -> None:
        context = kwargs.pop("context", {})
        if parameter is not None:
            context["parameter"] = parameter
        if value is not None:
            context["value"] = repr(value)
        if expected is not None:
            context["expected"] = expected
        super().__init__(message, context=context, **kwargs)


class RangeError(ParameterError):
    """Parameter value out of valid range."""

    error_code = "QKD_RANGE_ERROR"


class TypeValidationError(ParameterError):
    """Parameter has wrong type."""

    error_code = "QKD_TYPE_ERROR"


# === Configuration Errors ===


class ConfigurationError(QKDException):
    """Base class for configuration errors."""

    error_code = "QKD_CONFIG_ERROR"


class MissingConfigError(ConfigurationError):
    """Required configuration is missing."""

    error_code = "QKD_MISSING_CONFIG"


class InvalidConfigError(ConfigurationError):
    """Configuration value is invalid."""

    error_code = "QKD_INVALID_CONFIG"


# === Network Errors ===


class NetworkError(QKDException):
    """Base class for quantum network errors."""

    error_code = "QKD_NETWORK_ERROR"


class NodeNotFoundError(NetworkError):
    """Node not found in network."""

    error_code = "QKD_NODE_NOT_FOUND"


class ConnectionError(NetworkError):
    """Failed to establish connection between nodes."""

    error_code = "QKD_CONNECTION_ERROR"


class PathNotFoundError(NetworkError):
    """No path found between source and destination."""

    error_code = "QKD_PATH_NOT_FOUND"


# === Hardware/HSM Errors ===


class HardwareError(QKDException):
    """Base class for hardware-related errors."""

    error_code = "QKD_HARDWARE_ERROR"


class HSMError(HardwareError):
    """Hardware Security Module error."""

    error_code = "QKD_HSM_ERROR"


class HSMNotAvailableError(HSMError):
    """HSM is not available or not configured."""

    error_code = "QKD_HSM_NOT_AVAILABLE"


class DetectorError(HardwareError):
    """Quantum detector error."""

    error_code = "QKD_DETECTOR_ERROR"


# === ML Errors ===


class MLError(QKDException):
    """Base class for machine learning errors."""

    error_code = "QKD_ML_ERROR"


class ModelNotTrainedError(MLError):
    """Model has not been trained."""

    error_code = "QKD_MODEL_NOT_TRAINED"


class InsufficientDataError(MLError):
    """Insufficient data for training or prediction."""

    error_code = "QKD_INSUFFICIENT_DATA"


class OptimizationError(MLError):
    """Optimization failed to converge."""

    error_code = "QKD_OPTIMIZATION_ERROR"


# === Exception utilities ===


def wrap_exception(
    original: Exception,
    qkd_exception_class: type[QKDException] = QKDException,
    message: str | None = None,
) -> QKDException:
    """Wrap a standard exception in a QKD exception.

    The wrapped exception carries the original via Python's ``__cause__``,
    so tracebacks preserve the full chain.

    Args:
        original: Original exception to wrap
        qkd_exception_class: QKD exception class to use
        message: Optional custom message (defaults to original message)

    Returns:
        Wrapped QKD exception with original as cause
    """
    return qkd_exception_class(
        message or str(original),
        cause=original,
    )


__all__ = [
    # Exception classes
    "QKDException",
    "ProtocolError",
    "ProtocolSecurityError",
    "ProtocolStateError",
    "InsufficientKeyError",
    "ChannelError",
    "ChannelLossError",
    "ChannelNoiseError",
    "ChannelCalibrationError",
    "KeyManagementError",
    "KeyNotFoundError",
    "KeyExpiredError",
    "KeyExhaustedError",
    "KeyStorageError",
    "CryptoError",
    "EncryptionError",
    "DecryptionError",
    "AuthenticationError",
    "IntegrityError",
    "ValidationError",
    "ParameterError",
    "RangeError",
    "TypeValidationError",
    "ConfigurationError",
    "MissingConfigError",
    "InvalidConfigError",
    "NetworkError",
    "NodeNotFoundError",
    "ConnectionError",
    "PathNotFoundError",
    "HardwareError",
    "HSMError",
    "HSMNotAvailableError",
    "DetectorError",
    "MLError",
    "ModelNotTrainedError",
    "InsufficientDataError",
    "OptimizationError",
    # Utilities
    "wrap_exception",
]
