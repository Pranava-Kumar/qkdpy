"""Structured logging configuration for QKDpy.

This module provides enterprise-grade structured logging using structlog,
with support for JSON output, audit trails, and SIEM integration.

structlog is configured **exactly once** at module import time so that the
processor chain is deterministic regardless of import order.  Individual
``QKDLogger`` instances created by ``get_logger(name)`` are lightweight
wrappers around ``structlog.get_logger(name)`` — they do NOT reconfigure
structlog globally.
"""

import logging
import sys
from collections.abc import MutableMapping
from datetime import UTC, datetime
from functools import lru_cache
from typing import Any

from ..exceptions import _REDACT_KEYS

try:
    import structlog
    from structlog.types import Processor

    STRUCTLOG_AVAILABLE = True
except ImportError:
    STRUCTLOG_AVAILABLE = False
    structlog = None  # type: ignore

# structlog's ConsoleRenderer(colors=True) on Windows requires colorama to be
# initialized, otherwise import raises SystemError. Initialize it (when present)
# before structlog is configured so a Windows `import qkdpy` does not crash.
# Use importlib so mypy does not require colorama type stubs.
if STRUCTLOG_AVAILABLE:
    try:
        import importlib

        importlib.import_module("colorama").init()
    except ImportError:
        pass


# Log levels with security-specific addition
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
    "SECURITY": 35,  # Between WARNING and ERROR
}

# Register custom SECURITY level
logging.addLevelName(LOG_LEVELS["SECURITY"], "SECURITY")


def add_timestamp(
    logger: Any, method_name: str, event_dict: MutableMapping[str, Any]
) -> MutableMapping[str, Any]:
    """Add ISO-8601 timestamp to log events."""
    event_dict["timestamp"] = datetime.now(UTC).isoformat()
    return event_dict


def add_qkd_context(
    logger: Any, method_name: str, event_dict: MutableMapping[str, Any]
) -> MutableMapping[str, Any]:
    """Add QKD-specific context to log events."""
    event_dict["library"] = "qkdpy"
    event_dict["library_version"] = _get_version()
    return event_dict


def redact_sensitive_data(
    logger: Any, method_name: str, event_dict: MutableMapping[str, Any]
) -> MutableMapping[str, Any]:
    """Redact sensitive data from log events.

    Uses an **explicit denylist** of full key names — substring matching
    (e.g., ``if 'key' in key.lower()``) caused false positives on
    legitimate public fields like ``key_rate`` and ``qber``.
    """
    for key in list(event_dict.keys()):
        if key in _REDACT_KEYS:
            value = event_dict[key]
            if isinstance(value, list | bytes | str):
                event_dict[key] = f"[REDACTED: {len(value)} items]"
            else:
                event_dict[key] = "[REDACTED]"

    return event_dict


@lru_cache(maxsize=1)
def _get_version() -> str:
    """Get QKDpy version."""
    try:
        from qkdpy import __version__

        return __version__
    except ImportError:
        return "unknown"


def _configure_structlog() -> None:
    """Configure structlog globally — called *once* at module load.

    This is the single source of truth for the processor chain.  Subsequent
    ``get_logger(name)`` calls use ``structlog.get_logger(name)`` which
    inherits this configuration.
    """
    if not STRUCTLOG_AVAILABLE:
        return

    processors: list[Processor] = [
        structlog.stdlib.filter_by_level,
        add_timestamp,
        add_qkd_context,
        structlog.stdlib.add_logger_name,
        structlog.processors.CallsiteParameterAdder(
            [
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.LINENO,
                structlog.processors.CallsiteParameter.FUNC_NAME,
            ]
        ),
        redact_sensitive_data,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.dev.ConsoleRenderer(colors=True),
    ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )


# Run once at import time — before any module-level ``get_logger(__name__)`` calls.
_configure_structlog()


class QKDLogger:
    """Structured logger wrapper for QKDpy.

    Each instance is a lightweight wrapper around a stdlib+structlog logger
    obtained via ``structlog.get_logger(name)``.  The global structlog
    configuration is set at module-import time and never mutated by
    individual instances.
    """

    def __init__(self, name: str) -> None:
        """Initialize QKD logger.

        Args:
            name: Logger name (usually module name)
        """
        self.name = name
        self._context: dict[str, Any] = {}

        if STRUCTLOG_AVAILABLE:
            self._logger = structlog.get_logger(name)
        else:
            self._stdlib_logger = logging.getLogger(name)
            if not self._stdlib_logger.handlers:
                handler = logging.StreamHandler(sys.stdout)
                handler.setFormatter(
                    logging.Formatter(
                        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
                    )
                )
                self._stdlib_logger.addHandler(handler)
            self._stdlib_logger.setLevel(logging.INFO)
            self._logger = None

    def bind(self, **kwargs: Any) -> "QKDLogger":
        """Bind context data to logger."""
        self._context.update(kwargs)
        if self._logger is not None:
            self._logger = self._logger.bind(**kwargs)
        return self

    def unbind(self, *keys: str) -> "QKDLogger":
        """Remove context data from logger."""
        for key in keys:
            self._context.pop(key, None)
        if self._logger is not None:
            self._logger = self._logger.unbind(*keys)
        return self

    def _log(self, level: str, event: str, **kwargs: Any) -> None:
        """Internal logging method."""
        merged = {**self._context, **kwargs}

        if STRUCTLOG_AVAILABLE and self._logger is not None:
            # Map custom levels to nearest standard structlog method
            structlog_level = level.lower()
            if structlog_level == "security":
                structlog_level = "warning"
            getattr(self._logger, structlog_level)(event, **merged)
        else:
            if merged:
                msg = f"{event} | {merged}"
            else:
                msg = event
            log_level = LOG_LEVELS.get(level.upper(), logging.INFO)
            self._stdlib_logger.log(log_level, msg)

    def debug(self, event: str, **kwargs: Any) -> None:
        """Log debug message."""
        self._log("DEBUG", event, **kwargs)

    def info(self, event: str, **kwargs: Any) -> None:
        """Log info message."""
        self._log("INFO", event, **kwargs)

    def warning(self, event: str, **kwargs: Any) -> None:
        """Log warning message."""
        self._log("WARNING", event, **kwargs)

    def error(self, event: str, **kwargs: Any) -> None:
        """Log error message."""
        self._log("ERROR", event, **kwargs)

    def critical(self, event: str, **kwargs: Any) -> None:
        """Log critical message."""
        self._log("CRITICAL", event, **kwargs)

    def security(self, event: str, **kwargs: Any) -> None:
        """Log security-relevant event."""
        kwargs["security_event"] = True
        self._log("SECURITY", event, **kwargs)

    def audit(
        self,
        action: str,
        *,
        actor: str | None = None,
        resource: str | None = None,
        result: str = "success",
        **kwargs: Any,
    ) -> None:
        """Log audit trail event."""
        audit_data = {
            "audit": True,
            "action": action,
            "result": result,
        }
        if actor:
            audit_data["actor"] = actor
        if resource:
            audit_data["resource"] = resource

        self._log("INFO", f"AUDIT: {action}", **audit_data, **kwargs)


def get_logger(name: str | None = None) -> QKDLogger:
    """Get a QKD logger instance.

    Does NOT reconfigure structlog globally — that happened once at module import.

    Args:
        name: Logger name (defaults to calling module)

    Returns:
        Configured QKDLogger instance wrapping structlog (or stdlib as fallback)
    """
    if name is None:
        import inspect

        frame = inspect.currentframe()
        if frame and frame.f_back:
            name = frame.f_back.f_globals.get("__name__", "qkdpy")
        else:
            name = "qkdpy"

    return QKDLogger(name)


# Module-level convenience logger — lazily created on first use.
_default_logger: QKDLogger | None = None


def _default_logger_lazy() -> QKDLogger:
    """Get or create the module-level default logger."""
    global _default_logger
    if _default_logger is None:
        _default_logger = get_logger("qkdpy")
    return _default_logger


def configure_default_logger(
    level: str = "INFO",
    json_output: bool = False,
) -> QKDLogger:
    """Configure the default module-level logger.

    Args:
        level: Minimum log level (stdlib fallback only; structlog uses global config)
        json_output: Whether to output JSON format (stdlib fallback only)

    Returns:
        Configured default logger
    """
    global _default_logger
    _default_logger = get_logger("qkdpy")
    return _default_logger


def log_debug(event: str, **kwargs: Any) -> None:
    """Log debug message using default logger."""
    _default_logger_lazy().debug(event, **kwargs)


def log_info(event: str, **kwargs: Any) -> None:
    """Log info message using default logger."""
    _default_logger_lazy().info(event, **kwargs)


def log_warning(event: str, **kwargs: Any) -> None:
    """Log warning message using default logger."""
    _default_logger_lazy().warning(event, **kwargs)


def log_error(event: str, **kwargs: Any) -> None:
    """Log error message using default logger."""
    _default_logger_lazy().error(event, **kwargs)


def log_security(event: str, **kwargs: Any) -> None:
    """Log security event using default logger."""
    _default_logger_lazy().security(event, **kwargs)
