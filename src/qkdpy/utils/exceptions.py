"""Exception-related utilities.

This module hosts exception helpers that don't belong in the
``exceptions`` module (which only contains exception class definitions).
"""

from ..exceptions import QKDException


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
