"""Integration plugins for QKDpy."""

import logging

logger = logging.getLogger(__name__)


def _try_import(module_name: str, class_name: str) -> bool:
    """Import an integration module, marking it unavailable on a missing dep.

    Only ``ImportError`` (missing optional dependency) is treated as a soft
    "feature unavailable" signal. Any other exception indicates a genuine bug
    in the integration module and is re-raised so it surfaces in CI/tests
    rather than being silently swallowed as "unavailable".
    """
    try:
        module = __import__(f"qkdpy.integrations.{module_name}", fromlist=[class_name])
        globals()[class_name] = getattr(module, class_name)
        return True
    except ImportError:
        return False
    except Exception:  # noqa: BLE001 - re-raise real bugs, don't mask them
        logger.exception("Failed to import integration %s", module_name)
        raise


QISKIT_AVAILABLE = _try_import("qiskit_integration", "QiskitIntegration")
CIRQ_AVAILABLE = _try_import("cirq_integration", "CirqIntegration")
PENNYLANE_AVAILABLE = _try_import("pennylane_integration", "PennyLaneIntegration")
QPIAI_AVAILABLE = _try_import("qpiai_integration", "QpiAIIntegration")

__all__ = []

if QISKIT_AVAILABLE:
    __all__.append("QiskitIntegration")

if CIRQ_AVAILABLE:
    __all__.append("CirqIntegration")

if PENNYLANE_AVAILABLE:
    __all__.append("PennyLaneIntegration")

if QPIAI_AVAILABLE:
    __all__.append("QpiAIIntegration")
