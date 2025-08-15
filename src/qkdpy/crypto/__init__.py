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
OneTimePad.decrypt = OneTimePadDecrypt.decrypt
OneTimePad.decrypt_file = OneTimePadDecrypt.decrypt_file

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
