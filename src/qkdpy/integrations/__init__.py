"""Integration plugins for QKDpy."""

# Import integrations individually with error handling
try:
    from .qiskit_integration import QiskitIntegration  # noqa: F401

    QISKIT_AVAILABLE = True
except (ImportError, NameError):
    QISKIT_AVAILABLE = False

try:
    from .cirq_integration import CirqIntegration  # noqa: F401

    CIRQ_AVAILABLE = True
except (ImportError, NameError):
    CIRQ_AVAILABLE = False

try:
    from .pennylane_integration import PennyLaneIntegration  # noqa: F401

    PENNYLANE_AVAILABLE = True
except (ImportError, NameError):
    PENNYLANE_AVAILABLE = False

__all__ = []

if QISKIT_AVAILABLE:
    __all__.append("QiskitIntegration")

if CIRQ_AVAILABLE:
    __all__.append("CirqIntegration")

if PENNYLANE_AVAILABLE:
    __all__.append("PennyLaneIntegration")
