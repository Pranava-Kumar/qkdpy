"""Instrumentation and telemetry for QKDpy operations.

Provides decorators and context managers for observing protocol execution,
ML training, and other key operations with structured events and timing.
"""

import time
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from .logging_config import get_logger

F = TypeVar("F", bound=Callable[..., Any])

logger = get_logger(__name__)


class OperationSpan:
    """Context manager for timing and logging an operation.

    Usage::

        with OperationSpan("protocol.execute", protocol="BB84", key_length=256) as span:
            result = protocol.execute()
            span.set_metadata(qber=result["qber"], key_size=len(result["final_key"]))

    Emits structured ``operation_started`` and ``operation_completed`` /
    ``operation_failed`` events with duration in milliseconds.
    """

    def __init__(
        self,
        operation: str,
        *,
        level: str = "info",
        logger_override: Any = None,
        **context: Any,
    ) -> None:
        """Start an operation span.

        Args:
            operation: Stable operation name (e.g. ``protocol.execute``)
            level: Log level for completion events
            logger_override: Logger instance to use (defaults to module logger)
            **context: Static context attached to all events in this span
        """
        self.operation = operation
        self.level = level
        self._log = logger_override or logger
        self._context = context
        self._metadata: dict[str, Any] = {}
        self._start_time: float | None = None

    def set_metadata(self, **metadata: Any) -> None:
        """Attach additional metadata to the completion event."""
        self._metadata.update(metadata)

    def __enter__(self) -> "OperationSpan":
        self._start_time = time.monotonic()
        self._log.info(
            "operation_started",
            operation=self.operation,
            **self._context,
        )
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        duration_ms = (
            (time.monotonic() - self._start_time) * 1000 if self._start_time else 0.0
        )

        if exc_type is not None:
            self._log.error(
                "operation_failed",
                operation=self.operation,
                duration_ms=round(duration_ms, 2),
                error_type=exc_type.__name__,
                error=str(exc_val) if exc_val else None,
                **self._context,
                **self._metadata,
            )
        else:
            log_method = getattr(self._log, self.level.lower(), self._log.info)
            log_method(
                "operation_completed",
                operation=self.operation,
                duration_ms=round(duration_ms, 2),
                **self._context,
                **self._metadata,
            )


def instrument(
    operation: str | None = None,
    *,
    level: str = "info",
    log_args: bool = True,
    log_result: bool = False,
) -> Callable[[F], F]:
    """Decorator that instruments a function with an ``OperationSpan``.

    Usage::

        @instrument("qkd.bb84.execute")
        def execute(self, ...):
            ...

    When *operation* is ``None``, the fully-qualified function name
    ``module.function`` is used as the span name.

    Args:
        operation: Stable operation name (defaults to ``module.function``)
        level: Log level for the completion event
        log_args: If ``True``, attach call arguments to the started event
        log_result: If ``True``, attach the return value to the completed event
    """

    def decorator(func: F) -> F:
        op_name = operation or f"{func.__module__}.{func.__qualname__}"

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            context: dict[str, Any] = {}
            if log_args:
                # Skip 'self' and 'cls' for bound methods
                bound_args = {}
                if args and hasattr(func, "__qualname__"):
                    pass  # handled below
                if args:
                    bound_args["_arg_count"] = len(args)
                if kwargs:
                    # Log kwarg keys only, not values (avoid secrets)
                    context["kwargs"] = list(kwargs.keys())
                context["arg_count"] = len(args)

            with OperationSpan(op_name, level=level, **context) as span:
                result = func(*args, **kwargs)
                if log_result and result is not None:
                    span.set_metadata(has_result=True)
                return result

        return wrapper  # type: ignore

    return decorator


def record_protocol_execution(
    protocol_name: str,
    key_length: int,
    qber: float,
    final_key_size: int,
    is_secure: bool,
    duration_ms: float,
    channel_stats: dict[str, Any] | None = None,
) -> None:
    """Emit a structured event for a completed protocol execution.

    This is a convenience helper for the emit-on-completion pattern,
    separate from the per-step ``OperationSpan`` instrumentation.

    Args:
        protocol_name: Name of the protocol (e.g. ``BB84``)
        key_length: Requested key length in bits
        qber: Measured quantum bit error rate
        final_key_size: Size of the final distilled key
        is_secure: Whether the protocol met the security threshold
        duration_ms: Total execution time in milliseconds
        channel_stats: Optional channel statistics dict
    """
    logger.info(
        "protocol_executed",
        protocol=protocol_name,
        key_length=key_length,
        qber=round(qber, 6),
        final_key_size=final_key_size,
        is_secure=is_secure,
        duration_ms=round(duration_ms, 2),
        channel_stats=channel_stats,
    )


def record_ml_training(
    model_name: str,
    protocol: str,
    input_dim: int,
    training_samples: int,
    training_time_ms: float,
    final_loss: float | None = None,
    convergence_iterations: int | None = None,
) -> None:
    """Emit a structured event for ML model training.

    Args:
        model_name: Name of the ML model
        protocol: QKD protocol the model targets
        input_dim: Input feature dimensionality
        training_samples: Number of training samples used
        training_time_ms: Training duration in milliseconds
        final_loss: Final training loss value
        convergence_iterations: Iterations to convergence
    """
    logger.info(
        "ml_training_completed",
        model=model_name,
        protocol=protocol,
        input_dim=input_dim,
        training_samples=training_samples,
        training_time_ms=round(training_time_ms, 2),
        final_loss=final_loss,
        convergence_iterations=convergence_iterations,
    )


def record_qber_diagnostic(
    protocol: str,
    qber: float,
    threshold: float,
    key_size: int,
    distance_km: float | None = None,
) -> None:
    """Emit a structured QBER diagnostic event.

    Args:
        protocol: Protocol name
        qber: Measured QBER
        threshold: Security threshold
        key_size: Sifted key size
        distance_km: Simulated channel distance in km
    """
    level = "warning" if qber > threshold * 0.8 else "info"
    log_fn = getattr(logger, level, logger.info)
    log_fn(
        "qber_diagnostic",
        protocol=protocol,
        qber=round(qber, 6),
        threshold=threshold,
        margin_pct=round((1 - qber / threshold) * 100, 1) if threshold > 0 else 0.0,
        key_size=key_size,
        distance_km=distance_km,
    )
