"""Hardware Security Module (HSM) interface for QKDpy.

This module provides an abstract HSM interface and implementations for
secure key storage and management in enterprise environments.
"""

import hashlib
import os
import secrets
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from ..exceptions import HSMError, HSMNotAvailableError, KeyNotFoundError
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


# AES-256-GCM requires a 32-byte key. HSM-stored key material can have any length;
# we deterministically derive a 32-byte AES key via SHA-256. A real HSM provider
# would store keys of the correct size already and we would not be re-deriving.
def _derive_aes_key(key_material: bytes) -> bytes:
    """Derive a 32-byte AES-256 key from arbitrary-length HSM key material."""
    return hashlib.sha256(key_material + b"qkdpy.hsm.aesgcm").digest()


class HSMProvider(Enum):
    """Supported HSM providers."""

    SOFTWARE = "software"  # Software-based HSM for testing
    PKCS11 = "pkcs11"  # PKCS#11 compatible HSMs
    AWS_CLOUDHSM = "aws_cloudhsm"
    AZURE_HSM = "azure_hsm"
    GOOGLE_CLOUD_HSM = "google_cloud_hsm"


@dataclass
class HSMKeyHandle:
    """Handle to a key stored in the HSM."""

    key_id: str
    key_type: str
    created_at: datetime
    expires_at: datetime | None
    metadata: dict[str, Any]

    def is_expired(self) -> bool:
        """Check if the key has expired."""
        if self.expires_at is None:
            return False
        return datetime.now(UTC) > self.expires_at


class HSMInterface(ABC):
    """Abstract interface for Hardware Security Module operations.

    This interface defines the operations that an HSM must support
    for QKD key management. Implementations can target different
    HSM providers (PKCS#11, cloud HSMs, etc.).
    """

    @abstractmethod
    def initialize(self, config: dict[str, Any]) -> None:
        """Initialize connection to the HSM.

        Args:
            config: HSM-specific configuration

        Raises:
            HSMError: If initialization fails
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the HSM is available and connected.

        Returns:
            True if HSM is available
        """
        pass

    @abstractmethod
    def generate_key(
        self,
        key_id: str,
        key_length: int = 256,
        *,
        metadata: dict[str, Any] | None = None,
        expires_in_seconds: int | None = None,
    ) -> HSMKeyHandle:
        """Generate a new key in the HSM.

        Args:
            key_id: Unique identifier for the key
            key_length: Key length in bits
            metadata: Optional metadata to store with the key
            expires_in_seconds: Key expiration time

        Returns:
            Handle to the generated key

        Raises:
            HSMError: If key generation fails
        """
        pass

    @abstractmethod
    def import_key(
        self,
        key_id: str,
        key_material: bytes,
        *,
        metadata: dict[str, Any] | None = None,
        expires_in_seconds: int | None = None,
    ) -> HSMKeyHandle:
        """Import an existing key into the HSM.

        Args:
            key_id: Unique identifier for the key
            key_material: Raw key bytes
            metadata: Optional metadata to store with the key
            expires_in_seconds: Key expiration time

        Returns:
            Handle to the imported key

        Raises:
            HSMError: If import fails
        """
        pass

    @abstractmethod
    def get_key_handle(self, key_id: str) -> HSMKeyHandle:
        """Get a handle to an existing key.

        Args:
            key_id: Key identifier

        Returns:
            Handle to the key

        Raises:
            KeyNotFoundError: If key doesn't exist
        """
        pass

    @abstractmethod
    def delete_key(self, key_id: str) -> bool:
        """Delete a key from the HSM.

        Args:
            key_id: Key identifier

        Returns:
            True if key was deleted

        Raises:
            KeyNotFoundError: If key doesn't exist
        """
        pass

    @abstractmethod
    def encrypt(
        self,
        key_id: str,
        plaintext: bytes,
        *,
        aad: bytes | None = None,
    ) -> bytes:
        """Encrypt data using a key in the HSM.

        Args:
            key_id: Key to use for encryption
            plaintext: Data to encrypt
            aad: Additional authenticated data

        Returns:
            Encrypted data (including IV/nonce)

        Raises:
            KeyNotFoundError: If key doesn't exist
            HSMError: If encryption fails
        """
        pass

    @abstractmethod
    def decrypt(
        self,
        key_id: str,
        ciphertext: bytes,
        *,
        aad: bytes | None = None,
    ) -> bytes:
        """Decrypt data using a key in the HSM.

        Args:
            key_id: Key to use for decryption
            ciphertext: Data to decrypt
            aad: Additional authenticated data

        Returns:
            Decrypted data

        Raises:
            KeyNotFoundError: If key doesn't exist
            HSMError: If decryption fails
        """
        pass

    @abstractmethod
    def wrap_key(
        self,
        wrapping_key_id: str,
        key_to_wrap: bytes,
    ) -> bytes:
        """Wrap (encrypt) a key for secure export.

        Args:
            wrapping_key_id: Key to use for wrapping
            key_to_wrap: Key material to wrap

        Returns:
            Wrapped key
        """
        pass

    @abstractmethod
    def unwrap_key(
        self,
        wrapping_key_id: str,
        wrapped_key: bytes,
        new_key_id: str,
    ) -> HSMKeyHandle:
        """Unwrap (decrypt) a wrapped key and import it.

        Args:
            wrapping_key_id: Key to use for unwrapping
            wrapped_key: Wrapped key material
            new_key_id: ID for the imported key

        Returns:
            Handle to the unwrapped key
        """
        pass

    @abstractmethod
    def list_keys(self) -> list[HSMKeyHandle]:
        """List all keys in the HSM.

        Returns:
            List of key handles
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Close connection to the HSM."""
        pass


class SoftwareHSM(HSMInterface):
    """Software-based HSM implementation for development and testing.

    WARNING: This is NOT secure for production use. It stores keys
    in memory and uses software-based cryptography. Use a real HSM
    for production deployments.
    """

    def __init__(self) -> None:
        """Initialize software HSM."""
        self._initialized = False
        self._keys: dict[str, tuple[bytes, HSMKeyHandle]] = {}
        logger.warning(
            "SoftwareHSM initialized - NOT FOR PRODUCTION USE",
            provider=HSMProvider.SOFTWARE.value,
        )

    def initialize(self, config: dict[str, Any]) -> None:
        """Initialize the software HSM."""
        self._initialized = True
        logger.info("SoftwareHSM initialized", config_keys=list(config.keys()))

    def is_available(self) -> bool:
        """Check if HSM is available."""
        return self._initialized

    def _check_available(self) -> None:
        """Raise if HSM not available."""
        if not self._initialized:
            raise HSMNotAvailableError("HSM not initialized")

    def generate_key(
        self,
        key_id: str,
        key_length: int = 256,
        *,
        metadata: dict[str, Any] | None = None,
        expires_in_seconds: int | None = None,
    ) -> HSMKeyHandle:
        """Generate a key using secrets module."""
        self._check_available()

        if key_id in self._keys:
            raise HSMError(f"Key {key_id} already exists")

        # Generate random key material
        key_bytes = key_length // 8
        key_material = secrets.token_bytes(key_bytes)

        now = datetime.now(UTC)
        expires_at = None
        if expires_in_seconds:
            from datetime import timedelta

            expires_at = now + timedelta(seconds=expires_in_seconds)

        handle = HSMKeyHandle(
            key_id=key_id,
            key_type="AES",
            created_at=now,
            expires_at=expires_at,
            metadata=metadata or {},
        )

        self._keys[key_id] = (key_material, handle)

        logger.audit(
            "hsm_key_generated",
            resource=key_id,
            result="success",
            key_length=key_length,
        )

        return handle

    def import_key(
        self,
        key_id: str,
        key_material: bytes,
        *,
        metadata: dict[str, Any] | None = None,
        expires_in_seconds: int | None = None,
    ) -> HSMKeyHandle:
        """Import a key into the software HSM."""
        self._check_available()

        if key_id in self._keys:
            raise HSMError(f"Key {key_id} already exists")

        now = datetime.now(UTC)
        expires_at = None
        if expires_in_seconds:
            from datetime import timedelta

            expires_at = now + timedelta(seconds=expires_in_seconds)

        handle = HSMKeyHandle(
            key_id=key_id,
            key_type="AES",
            created_at=now,
            expires_at=expires_at,
            metadata=metadata or {},
        )

        self._keys[key_id] = (key_material, handle)

        logger.audit(
            "hsm_key_imported",
            resource=key_id,
            result="success",
            key_length=len(key_material) * 8,
        )

        return handle

    def get_key_handle(self, key_id: str) -> HSMKeyHandle:
        """Get handle to a key."""
        self._check_available()

        if key_id not in self._keys:
            raise KeyNotFoundError(f"Key {key_id} not found")

        return self._keys[key_id][1]

    def delete_key(self, key_id: str) -> bool:
        """Delete a key."""
        self._check_available()

        if key_id not in self._keys:
            raise KeyNotFoundError(f"Key {key_id} not found")

        del self._keys[key_id]

        logger.audit(
            "hsm_key_deleted",
            resource=key_id,
            result="success",
        )

        return True

    def encrypt(
        self,
        key_id: str,
        plaintext: bytes,
        *,
        aad: bytes | None = None,
    ) -> bytes:
        """Encrypt using AES-256-GCM.

        Wire format: ``nonce (12 bytes) || ciphertext || tag (16 bytes)``.
        AES-GCM appends its authentication tag automatically, so this matches
        the previous IV+ciphertext+tag layout byte-for-byte at the call site.
        """
        self._check_available()

        if key_id not in self._keys:
            raise KeyNotFoundError(f"Key {key_id} not found")

        key_material = self._keys[key_id][0]
        aes_key = _derive_aes_key(key_material)

        # 96-bit nonce is the AES-GCM-recommended size.
        nonce = os.urandom(12)

        try:
            ciphertext = AESGCM(aes_key).encrypt(nonce, plaintext, aad)
        except (ValueError, TypeError):
            # cryptography raises ValueError on key-size mismatch and TypeError on
            # bad input types. Re-raise as HSMError so callers get a domain error.
            raise HSMError("Encryption failed") from None
        return nonce + ciphertext

    def decrypt(
        self,
        key_id: str,
        ciphertext: bytes,
        *,
        aad: bytes | None = None,
    ) -> bytes:
        """Decrypt using AES-256-GCM.

        AES-GCM authenticates the ciphertext and (optionally) ``aad``; tampering
        of any byte raises ``cryptography.exceptions.InvalidTag`` which we
        surface as ``HSMError``.
        """
        self._check_available()

        if key_id not in self._keys:
            raise KeyNotFoundError(f"Key {key_id} not found")

        if len(ciphertext) < 12 + 16:
            raise HSMError("Ciphertext too short")

        key_material = self._keys[key_id][0]
        aes_key = _derive_aes_key(key_material)

        nonce = ciphertext[:12]
        body = ciphertext[12:]
        try:
            return AESGCM(aes_key).decrypt(nonce, body, aad)
        except Exception as e:
            # cryptography.exceptions.InvalidTag (or any tag failure) lands here.
            raise HSMError("Authentication tag verification failed") from e

    def wrap_key(
        self,
        wrapping_key_id: str,
        key_to_wrap: bytes,
    ) -> bytes:
        """Wrap a key using encryption."""
        return self.encrypt(wrapping_key_id, key_to_wrap)

    def unwrap_key(
        self,
        wrapping_key_id: str,
        wrapped_key: bytes,
        new_key_id: str,
    ) -> HSMKeyHandle:
        """Unwrap and import a key."""
        key_material = self.decrypt(wrapping_key_id, wrapped_key)
        return self.import_key(new_key_id, key_material)

    def list_keys(self) -> list[HSMKeyHandle]:
        """List all keys."""
        self._check_available()
        return [handle for _, handle in self._keys.values()]

    def close(self) -> None:
        """Close and clear all keys."""
        self._keys.clear()
        self._initialized = False
        logger.info("SoftwareHSM closed")


def get_hsm(
    provider: HSMProvider = HSMProvider.SOFTWARE,
    config: dict[str, Any] | None = None,
) -> HSMInterface:
    """Factory function to get an HSM instance.

    Args:
        provider: HSM provider to use
        config: Provider-specific configuration

    Returns:
        HSM instance

    Raises:
        HSMNotAvailableError: If provider not available
    """
    if provider == HSMProvider.SOFTWARE:
        hsm = SoftwareHSM()
        hsm.initialize(config or {})
        return hsm

    elif provider == HSMProvider.PKCS11:
        # Check if PKCS#11 library is available
        try:
            import pkcs11  # type: ignore[import-not-found]  # noqa: F401

            raise NotImplementedError("PKCS#11 HSM not yet implemented")
        except ImportError:
            raise HSMNotAvailableError(
                "PKCS#11 support requires the 'python-pkcs11' package. "
                "Install with: pip install qkdpy[enterprise]"
            ) from None

    else:
        raise HSMNotAvailableError(f"HSM provider {provider} not available")
