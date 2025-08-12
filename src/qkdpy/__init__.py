"""QKDpy: A Python Package for Quantum Key Distribution.

QKDpy is a comprehensive library for Quantum Key Distribution (QKD) simulations,
implementing various QKD protocols, quantum simulators, and cryptographic tools.
"""

__version__ = "0.1.4"
__author__ = "Pranava-Kumar"
__email__ = "pranavakumar.it@gmail.com"

# Import core components
from .core import Measurement, QuantumChannel, QuantumGate, Qubit

# Import crypto utilities
from .crypto import OneTimePad, QuantumAuth

# Import key management
from .key_management import ErrorCorrection, KeyDistillation, PrivacyAmplification

# Import protocols
from .protocols import BB84, E91, SARG04

# Import utilities
from .utils import BlochSphere, KeyRateAnalyzer, ProtocolVisualizer

__all__ = [
    # Core components
    "Qubit",
    "QuantumGate",
    "QuantumChannel",
    "Measurement",
    # Protocols
    "BB84",
    "E91",
    "SARG04",
    # Key management
    "ErrorCorrection",
    "PrivacyAmplification",
    "KeyDistillation",
    # Crypto utilities
    "OneTimePad",
    "QuantumAuth",
    # Utilities
    "BlochSphere",
    "ProtocolVisualizer",
    "KeyRateAnalyzer",
]
