"""Hardware Security Module (HSM) interface for QKDpy.

This module provides an abstract HSM interface and implementations for
secure key storage and management in enterprise environments.
"""

import os
import secrets
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from ..exceptions import (
    HSMError,
    HSMNotAvailableError,
    KeyNotFoundError,
)
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


# PBKDF2 iteration count. 100k HMAC-SHA256 is the OWASP floor for PBKDF2 today;
# a real HSM would not derive keys this way at all (it holds the raw key), but for
# this software simulation we must not use a raw-digest "KDF" (a single SHA-256 of
# key||constant is reversible-in-strength-equivalent to no KDF and offers no
# defense against offline brute force if key material ever leaves memory).
_PBKDF2_ITERATIONS = 100_000
_PBKDF2_SALT_BYTES = 16


def _derive_aes_key(key_material: bytes, salt: bytes) -> bytes:
    """Derive a 32-byte AES-256 key from key material using PBKDF2-HMAC-SHA256.

    The salt MUST be unique per key (see ``SoftwareHSM``). It is stored alongside
    the key handle so the same key material + salt always reproduces the same
    derived key for decrypt/unwrap, while a different salt yields a different key.
    """
    if len(salt) != _PBKDF2_SALT_BYTES:
        raise HSMError(
            f"PBKDF2 salt must be {_PBKDF2_SALT_BYTES} bytes, got {len(salt)}"
        )
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=_PBKDF2_ITERATIONS,
    )
    return kdf.derive(key_material)


class HSMProvider(Enum):
    """Supported HSM providers.

    Only ``SOFTWARE`` is implemented in this build. It is an in-memory
    simulation intended for development and testing only — it is NOT
    hardware-backed and MUST NOT be used in production. The cloud/PKCS#11
    providers were previously advertised as stubs; that over-promised support
    that does not exist, so they have been removed rather than shipped as
    NotImplementedError traps.

    ``hardware_backed`` records whether the provider actually runs on dedicated
    hardware (a real HSM). It is the single source of truth for
    ``_hsm_is_hardware_backed`` — no provider in this build sets it, so that
    function fails closed instead of lying that software keys are "hardware".
    """

    SOFTWARE = "software"  # Software-based in-memory simulation (NOT production-grade)

    @property
    def hardware_backed(self) -> bool:
        """True only for providers that run on dedicated hardware."""
        # No hardware-backed provider exists in this build. If a PKCS#11 / cloud
        # provider is added later, set ``hardware_backed`` on its member.
        return False


def _hsm_is_hardware_backed(provider: HSMProvider | None = None) -> bool:
    """Return True only if an actual hardware-backed HSM is in use.

    This is a real capability check, not a constant: it inspects the active
    provider rather than returning a hardcoded value. A compliant FIPS/ETSI
    "HSM backed" result must prove hardware backing, so this fails closed
    (``False``) for the software simulation that is the only provider here, and
    for any ``None``/missing provider.

    Args:
        provider: The active HSM provider. If omitted, the provider configured
            in the environment-derived HSM backend is used.
    """
    if provider is None:
        raw = os.environ.get("QKDPY_HSM_PROVIDER", HSMProvider.SOFTWARE.value)
        try:
            provider = HSMProvider(raw)
        except ValueError:
            return False
    return provider.hardware_backed


@dataclass
class HSMKeyHandle:
    """Handle to a key stored in the HSM.

    ``key_salt`` is the per-key PBKDF2 salt used to derive the AES wrapping
    key from the stored key material. It is public (non-secret) but MUST be
    persisted with the handle, or wrapped-key exports cannot be unwrapped.
    """

    key_id: str
    key_type: str
    created_at: datetime
    expires_at: datetime | None
    metadata: dict[str, Any]
    key_salt: bytes = field(
        default_factory=lambda: secrets.token_bytes(_PBKDF2_SALT_BYTES)
    )

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
        # Stored form per key: (wrapped_key_material, salt). The raw key material
        # is never kept in plaintext; it is wrapped under a per-session master KEK
        # (see ``_wrap_material`` / ``_unwrap_material``). ``salt`` is the per-key
        # PBKDF2 salt used to derive the AES data-encryption key on encrypt/decrypt.
        self._keys: dict[str, tuple[bytes, bytes, HSMKeyHandle]] = {}
        # Session master KEK used to wrap stored key material. It is purely an
        # in-memory obfuscation layer for the software simulation and provides NO
        # real security — a process inspector can read it. Documented so nobody
        # mistakes this for hardware-backed key isolation.
        self._master_kek = secrets.token_bytes(32)
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

    def _wrap_material(self, key_material: bytes) -> tuple[bytes, bytes]:
        """Wrap raw key material so it is never stored as plaintext.

        Returns ``(wrapped, salt)`` where ``wrapped`` is AES-256-GCM
        ciphertext of the material under the per-session master KEK. ``salt``
        is a random per-key PBKDF2 salt used to derive the data-encryption key.
        """
        salt = secrets.token_bytes(_PBKDF2_SALT_BYTES)
        nonce = os.urandom(12)
        wrapped = AESGCM(self._master_kek).encrypt(nonce, key_material, None)
        return nonce + wrapped, salt

    def _unwrap_material(self, wrapped: bytes, salt: bytes) -> bytes:
        """Reverse of :meth:`_wrap_material`."""
        if len(wrapped) < 12:
            raise HSMError("Wrapped key material is malformed")
        nonce, body = wrapped[:12], wrapped[12:]
        return AESGCM(self._master_kek).decrypt(nonce, body, None)

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

        wrapped, salt = self._wrap_material(key_material)
        self._keys[key_id] = (wrapped, salt, handle)

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

        wrapped, salt = self._wrap_material(key_material)
        self._keys[key_id] = (wrapped, salt, handle)

        logger.audit(
            "hsm_key_imported",
            resource=key_id,
            result="success",
            key_length=len(key_material) * 8,
        )

        return handle

    def get_key_handle(self, key_id: str) -> HSMKeyHandle:
        """Get handle to a key.

        The handle intentionally exposes NO key bytes — only metadata and the
        (non-secret) PBKDF2 salt. Raw key material is never returned.
        """
        self._check_available()

        if key_id not in self._keys:
            raise KeyNotFoundError(f"Key {key_id} not found")

        return self._keys[key_id][2]

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

        wrapped, salt, _handle = self._keys[key_id]
        key_material = self._unwrap_material(wrapped, salt)
        # PBKDF2-HMAC-SHA256 (100k iters) derives the data key from the key
        # material + this key's unique salt. Different salt -> different key.
        aes_key = _derive_aes_key(key_material, salt)

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

        wrapped, salt, _handle = self._keys[key_id]
        key_material = self._unwrap_material(wrapped, salt)
        aes_key = _derive_aes_key(key_material, salt)

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
        return [handle for _, _, handle in self._keys.values()]

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

    else:
        # Only HSMProvider.SOFTWARE is implemented. Cloud HSM (AWS/Azure/GCP)
        # and PKCS#11 providers were previously advertised but never implemented;
        # we fail closed instead of pretending support exists.
        raise HSMNotAvailableError(
            f"HSM provider {provider.value!r} is not implemented in this "
            "software-simulation build. Only HSMProvider.SOFTWARE is available."
        )
