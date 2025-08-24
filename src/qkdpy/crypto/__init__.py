"""Cryptographic utilities for quantum keys."""

from .authentication import QuantumAuth
from .decryption import OneTimePadDecrypt
from .encryption import OneTimePad
from .enhanced_security import (
    QuantumAuthentication,
    QuantumKeyValidation,
    QuantumSideChannelProtection,
)
from .key_exchange import QuantumKeyExchange
from .quantum_auth import QuantumAuthenticator
from .quantum_rng import QuantumRandomNumberGenerator

# For backward compatibility
# We use type: ignore to avoid mypy errors
if not hasattr(OneTimePad, "decrypt"):
    OneTimePad.decrypt = staticmethod(OneTimePadDecrypt.decrypt)  # type: ignore
if not hasattr(OneTimePad, "decrypt_file"):
    OneTimePad.decrypt_file = staticmethod(OneTimePadDecrypt.decrypt_file)  # type: ignore

__all__ = [
    "OneTimePad",
    "QuantumAuth",
    "QuantumAuthenticator",
    "QuantumKeyExchange",
    "QuantumRandomNumberGenerator",
    "QuantumAuthentication",
    "QuantumKeyValidation",
    "QuantumSideChannelProtection",
]
