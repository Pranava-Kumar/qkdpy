"""Input validation utilities for QKDpy.

This module provides decorators and utilities for validating function
inputs, ensuring type safety, and catching invalid parameters early.
"""

import functools
import inspect
from collections.abc import Callable, Sequence
from typing import (
    Any,
    ParamSpec,
    TypeVar,
)

import numpy as np

from ..exceptions import (
    ParameterError,
    RangeError,
    TypeValidationError,
)

P = ParamSpec("P")
R = TypeVar("R")


def _extract_param_value(
    param_name: str,
    func: Callable[..., Any],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> tuple[Any | None, bool]:
    """Extract a parameter value and a found flag from args or kwargs.

    Returns ``(value, found)``.  ``found`` is False when ``param_name`` was
    neither in kwargs nor in the positional args, which distinguishes "the
    parameter was not supplied" from "the parameter was supplied as None".
    """
    if param_name in kwargs:
        return kwargs[param_name], True

    sig = inspect.signature(func)
    params = list(sig.parameters.keys())
    try:
        idx = params.index(param_name)
        if idx < len(args):
            return args[idx], True
    except ValueError:
        pass
    return None, False


def validate_range(
    param_name: str,
    min_value: float | None = None,
    max_value: float | None = None,
    *,
    min_inclusive: bool = True,
    max_inclusive: bool = True,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator to validate numeric parameter is within range.

    Args:
        param_name: Name of parameter to validate
        min_value: Minimum allowed value (None for no minimum)
        max_value: Maximum allowed value (None for no maximum)
        min_inclusive: Whether minimum is inclusive
        max_inclusive: Whether maximum is inclusive

    Returns:
        Decorator function
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            value, found = _extract_param_value(param_name, func, args, kwargs)
            if found and value is not None:
                _validate_numeric_range(
                    param_name,
                    value,
                    min_value,
                    max_value,
                    min_inclusive,
                    max_inclusive,
                )
            return func(*args, **kwargs)

        return wrapper

    return decorator


def validate_type(
    param_name: str,
    expected_types: type | tuple[type, ...],
    *,
    allow_none: bool = False,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator to validate parameter type.

    Args:
        param_name: Name of parameter to validate
        expected_types: Expected type or tuple of types
        allow_none: Whether None is allowed

    Returns:
        Decorator function
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            value, found = _extract_param_value(param_name, func, args, kwargs)

            if found:
                if value is None and allow_none:
                    pass
                elif not isinstance(value, expected_types):
                    raise TypeValidationError(
                        f"Parameter '{param_name}' must be {expected_types}, "
                        f"got {type(value).__name__}",
                        parameter=param_name,
                        value=value,
                        expected=str(expected_types),
                    )

            return func(*args, **kwargs)

        return wrapper

    return decorator


def validate_positive(
    param_name: str,
    *,
    allow_zero: bool = False,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator to validate parameter is positive.

    Args:
        param_name: Name of parameter to validate
        allow_zero: Whether zero is allowed

    Returns:
        Decorator function
    """
    return validate_range(
        param_name,
        min_value=0.0,
        min_inclusive=allow_zero,
    )


def validate_probability(
    param_name: str,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator to validate parameter is a valid probability [0, 1].

    Args:
        param_name: Name of parameter to validate

    Returns:
        Decorator function
    """
    return validate_range(param_name, min_value=0.0, max_value=1.0)


def validate_not_empty(
    param_name: str,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator to validate sequence parameter is not empty.

    Args:
        param_name: Name of parameter to validate

    Returns:
        Decorator function
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            value, _ = _extract_param_value(param_name, func, args, kwargs)

            if value is not None and len(value) == 0:
                raise ParameterError(
                    f"Parameter '{param_name}' cannot be empty",
                    parameter=param_name,
                    value=value,
                    expected="non-empty sequence",
                )

            return func(*args, **kwargs)

        return wrapper

    return decorator


# === Utility Functions ===


def _validate_numeric_range(
    param_name: str,
    value: float | int,
    min_value: float | None,
    max_value: float | None,
    min_inclusive: bool,
    max_inclusive: bool,
) -> None:
    """Validate numeric value is within range."""
    if min_value is not None:
        if min_inclusive:
            if value < min_value:
                raise RangeError(
                    f"Parameter '{param_name}' must be >= {min_value}, got {value}",
                    parameter=param_name,
                    value=value,
                    expected=f">= {min_value}",
                )
        else:
            if value <= min_value:
                raise RangeError(
                    f"Parameter '{param_name}' must be > {min_value}, got {value}",
                    parameter=param_name,
                    value=value,
                    expected=f"> {min_value}",
                )

    if max_value is not None:
        if max_inclusive:
            if value > max_value:
                raise RangeError(
                    f"Parameter '{param_name}' must be <= {max_value}, got {value}",
                    parameter=param_name,
                    value=value,
                    expected=f"<= {max_value}",
                )
        else:
            if value >= max_value:
                raise RangeError(
                    f"Parameter '{param_name}' must be < {max_value}, got {value}",
                    parameter=param_name,
                    value=value,
                    expected=f"< {max_value}",
                )


def validate_key_length(key: Sequence[int], min_length: int = 1) -> None:
    """Validate key has sufficient length.

    Args:
        key: Binary key to validate
        min_length: Minimum required length

    Raises:
        ParameterError: If key is too short
    """
    if len(key) < min_length:
        raise ParameterError(
            f"Key must have at least {min_length} bits, got {len(key)}",
            parameter="key",
            value=f"[{len(key)} bits]",
            expected=f"length >= {min_length}",
        )


def validate_binary_key(key: Sequence[int]) -> None:
    """Validate key contains only binary values (0 or 1).

    Args:
        key: Key to validate

    Raises:
        ParameterError: If key contains non-binary values
    """
    for i, bit in enumerate(key):
        if bit not in (0, 1):
            raise ParameterError(
                f"Key must contain only 0 and 1, found {bit} at position {i}",
                parameter="key",
                value=f"bit={bit} at index={i}",
                expected="0 or 1",
            )


def validate_qber(qber: float) -> None:
    """Validate QBER value is in valid range [0, 0.5].

    Args:
        qber: QBER value to validate

    Raises:
        RangeError: If QBER is out of valid range
    """
    if qber < 0 or qber > 0.5:
        raise RangeError(
            f"QBER must be in range [0, 0.5], got {qber}",
            parameter="qber",
            value=qber,
            expected="0 <= qber <= 0.5",
        )


def validate_unitary(matrix: np.ndarray, atol: float = 1e-10) -> None:
    """Validate matrix is unitary.

    Args:
        matrix: Matrix to validate
        atol: Absolute tolerance for comparison

    Raises:
        ParameterError: If matrix is not unitary
    """
    if matrix.ndim != 2:
        raise ParameterError(
            "Matrix must be 2-dimensional",
            parameter="matrix",
            expected="2D array",
        )

    if matrix.shape[0] != matrix.shape[1]:
        raise ParameterError(
            "Matrix must be square",
            parameter="matrix",
            value=f"shape={matrix.shape}",
            expected="square matrix",
        )

    identity = np.eye(matrix.shape[0])
    product = matrix @ matrix.conj().T

    if not np.allclose(product, identity, atol=atol):
        raise ParameterError(
            "Matrix must be unitary (U @ U† = I)",
            parameter="matrix",
            expected="unitary matrix",
        )


def validate_normalized_state(state: np.ndarray, atol: float = 1e-10) -> None:
    """Validate quantum state is normalized.

    Args:
        state: State vector to validate
        atol: Absolute tolerance for comparison

    Raises:
        ParameterError: If state is not normalized
    """
    norm = np.linalg.norm(state)
    if not np.isclose(norm, 1.0, atol=atol):
        raise ParameterError(
            f"State must be normalized (|α|² + |β|² = 1), got norm={norm}",
            parameter="state",
            value=f"norm={norm}",
            expected="normalized state (norm=1)",
        )


def validate_density_matrix(rho: np.ndarray, atol: float = 1e-10) -> None:
    """Validate density matrix properties.

    Args:
        rho: Density matrix to validate
        atol: Absolute tolerance for comparison

    Raises:
        ParameterError: If matrix is not a valid density matrix
    """
    if rho.ndim != 2:
        raise ParameterError(
            "Density matrix must be 2-dimensional",
            parameter="rho",
            expected="2D array",
        )

    if rho.shape[0] != rho.shape[1]:
        raise ParameterError(
            "Density matrix must be square",
            parameter="rho",
            value=f"shape={rho.shape}",
            expected="square matrix",
        )

    # Check Hermiticity
    if not np.allclose(rho, rho.conj().T, atol=atol):
        raise ParameterError(
            "Density matrix must be Hermitian (ρ = ρ†)",
            parameter="rho",
            expected="Hermitian matrix",
        )

    # Check trace = 1
    trace = np.trace(rho)
    if not np.isclose(trace, 1.0, atol=atol):
        raise ParameterError(
            f"Density matrix must have trace 1, got {trace}",
            parameter="rho",
            value=f"trace={trace}",
            expected="trace=1",
        )

    # Check positive semi-definiteness
    eigenvalues = np.linalg.eigvalsh(rho)
    if np.any(eigenvalues < -atol):
        raise ParameterError(
            "Density matrix must be positive semi-definite",
            parameter="rho",
            value=f"min_eigenvalue={eigenvalues.min()}",
            expected="all eigenvalues >= 0",
        )
