"""Base class for QKD protocols."""

from abc import ABC, abstractmethod
from collections.abc import Sequence

from ..core import (
    QuantumChannel,
    Qubit,
    Qudit,
)
from ..core.secure_random import secure_bits  # noqa: F401 — kept for subclass access


class BaseProtocol(ABC):
    """Abstract base class for QKD protocols.

    This class defines the interface that all QKD protocol implementations should follow.
    """

    def __init__(self, channel: QuantumChannel, key_length: int = 100):
        """Initialize the protocol.

        Args:
            channel: Quantum channel for qubit transmission
            key_length: Desired length of the final key

        """
        if not isinstance(channel, QuantumChannel):
            raise TypeError(
                f"channel must be an instance of QuantumChannel, got {type(channel)}"
            )
        self.channel = channel
        self.key_length = key_length

        # Protocol statistics
        self.raw_key: list[int] = []
        self.sifted_key: list[int] = []
        self.final_key: list[int] = []
        self.qber: float = 0.0

        # Basis information
        self.alice_bases: list[int | str | None] = []
        self.bob_bases: list[int | str | None] = []

        # Error correction and privacy amplification parameters
        self.error_correction_method: str = "cascade"
        self.privacy_amplification_method: str = "universal_hashing"

        # Protocol status
        self.is_complete: bool = False
        self.is_secure: bool = False

    @abstractmethod
    def prepare_states(self) -> list[Qubit | Qudit]:
        """Prepare quantum states for transmission.

        Returns:
            List of quantum states (qubits or qudits) to be sent through the channel

        """
        pass

    @abstractmethod
    def measure_states(self, states: Sequence[Qubit | Qudit | None]) -> list[int]:
        """Measure received quantum states.

        Args:
            states: List of received quantum states (may contain None for lost states)

        Returns:
            List of measurement results

        """
        pass

    @abstractmethod
    def sift_keys(self) -> tuple[list[int], list[int]]:
        """Sift the raw keys to keep only measurements in matching bases.

        Returns:
            Tuple of (alice_sifted_key, bob_sifted_key)

        """
        pass

    @abstractmethod
    def estimate_qber(self) -> float:
        """Estimate the Quantum Bit Error Rate (QBER).

        Returns:
            Estimated QBER value

        """
        pass

    def error_correction(
        self, alice_key: list[int], bob_key: list[int]
    ) -> tuple[list[int], list[int]]:
        """Perform error correction on the sifted keys.

        Args:
            alice_key: Alice's sifted key
            bob_key: Bob's sifted key

        Returns:
            Tuple of corrected (alice_key, bob_key)

        """
        if self.error_correction_method == "cascade":
            return self._cascade_error_correction(alice_key, bob_key)
        else:
            raise ValueError(
                f"Unknown error correction method: {self.error_correction_method}"
            )

    def privacy_amplification(self, key: list[int], leak: int) -> list[int]:
        """Perform privacy amplification to reduce Eve's information.

        Args:
            key: Key to be amplified
            leak: Estimated amount of information leaked to Eve

        Returns:
            Shortened, more secure key

        """
        if self.privacy_amplification_method == "universal_hashing":
            return self._universal_hashing_privacy_amplification(key, leak)
        else:
            raise ValueError(
                f"Unknown privacy amplification method: {self.privacy_amplification_method}"
            )

    def execute(
        self,
    ) -> dict[str, list[int] | float | bool | dict[str, int | float | bool]]:
        """Execute the full QKD protocol.

        Returns:
            Dictionary containing protocol results and statistics

        """
        # Lazy imports to avoid circular dependency (protocols → utils.instrumentation → utils.__init__ → ..protocols.base)
        from ..utils.instrumentation import (  # noqa: PLC0415
            OperationSpan,
            record_protocol_execution,
            record_qber_diagnostic,
        )

        with OperationSpan(f"protocol.execute.{self.__class__.__name__}"):
            # Reset statistics
            self.reset()

            # Step 1: Alice prepares quantum states
            qubits = self.prepare_states()

            # Step 2: Transmit qubits through the quantum channel
            received_qubits = self.channel.transmit_batch(qubits)

            # Step 3: Bob measures the received states
            measurement_results = self.measure_states(received_qubits)

            # Step 4: Sift keys based on matching bases
            alice_sifted, bob_sifted = self.sift_keys()

            # Step 5: Estimate QBER
            qber = self.estimate_qber()
            record_qber_diagnostic(
                protocol=self.__class__.__name__,
                qber=qber,
                threshold=self._get_security_threshold(),
                key_size=len(alice_sifted),
                distance_km=getattr(self.channel, "distance_km", None)
                or getattr(self.channel, "distance", None),
            )

            # Step 6: Error correction
            alice_corrected, bob_corrected = self.error_correction(
                alice_sifted, bob_sifted
            )

            # Convert to Python integers to avoid numpy.int32 issues
            alice_corrected = [int(bit) for bit in alice_corrected]
            bob_corrected = [int(bit) for bit in bob_corrected]

            # Step 7: Privacy amplification
            # Estimate information leak based on QBER
            leak = int(len(alice_corrected) * self._estimate_eve_information(qber))
            final_key = self.privacy_amplification(alice_corrected, leak)

            # Truncate to requested key length if necessary
            if len(final_key) > self.key_length:
                final_key = final_key[: self.key_length]

            # Update protocol status
            self.raw_key = measurement_results
            self.sifted_key = alice_sifted
            self.final_key = final_key
            self.qber = qber
            self.is_complete = True
            self.is_secure = qber < self._get_security_threshold()

            # Build result dict
            result: dict[
                str, list[int] | float | bool | dict[str, int | float | bool]
            ] = {
                "raw_key": self.raw_key,
                "sifted_key": self.sifted_key,
                "final_key": self.final_key,
                "qber": self.qber,
                "is_secure": self.is_secure,
                "channel_stats": self.channel.get_statistics(),
            }

            record_protocol_execution(
                protocol_name=self.__class__.__name__,
                key_length=self.key_length,
                qber=self.qber,
                final_key_size=len(self.final_key),
                is_secure=self.is_secure,
                duration_ms=0.0,
                channel_stats=self.channel.get_statistics(),
            )
            return result

    def reset(self) -> None:
        """Reset the protocol state."""
        self.raw_key = []
        self.sifted_key = []
        self.final_key = []
        self.qber = 0.0
        self.alice_bases = []
        self.bob_bases = []
        self.is_complete = False
        self.is_secure = False
        self.channel.reset_statistics()

    def _cascade_error_correction(
        self, alice_key: list[int], bob_key: list[int]
    ) -> tuple[list[int], list[int]]:
        """Cascade error correction protocol.

        Delegates to :meth:`ErrorCorrection.cascade` for a proper multi-pass
        implementation with random permutations (rather than a simplified
        single-pass version).

        Args:
            alice_key: Alice's sifted key
            bob_key: Bob's sifted key

        Returns:
            Tuple of corrected (alice_key, bob_key)

        """
        # Lazy import to avoid circular dependency at module level
        from ..key_management.error_correction import (  # noqa: PLC0415
            ErrorCorrection,
        )

        return ErrorCorrection.cascade(alice_key, bob_key)

    def _universal_hashing_privacy_amplification(
        self, key: list[int], leak: int
    ) -> list[int]:
        """Universal hashing for privacy amplification.

        Delegates to :meth:`PrivacyAmplification.universal_hashing` for the
        actual hash computation.

        Args:
            key: Key to be amplified
            leak: Estimated amount of information leaked to Eve

        Returns:
            Shortened, more secure key

        """
        # Lazy import to avoid circular dependency at module level
        from ..key_management.privacy_amplification import (  # noqa: PLC0415
            PrivacyAmplification,
        )

        # Calculate the length of the final key using the leftover hash lemma:
        # r = n - s - leak, where n is the original key length and s is a
        # security parameter.
        n = len(key)
        s = 10  # Security parameter
        r = max(1, n - s - leak)  # Ensure at least 1 bit remains

        # Clamp to the actual key length (universal_hashing requires output < input)
        if r >= n:
            r = max(1, n - 1)

        return PrivacyAmplification.universal_hashing(key, r)

    def _estimate_eve_information(self, qber: float) -> float:
        """Estimate the upper bound on information Eve holds, given the QBER.

        Args:
            qber: Quantum Bit Error Rate

        Returns:
            Estimated fraction of information leaked to Eve.

        The naive ``min(1.0, 2 * qber)`` heuristic overestimates Eve's
        knowledge (it can exceed the actual error fraction for small QBER and
        is not grounded in the protocol's information theory). For BB84 against
        the most general collective attack, the Devetak-Winter bound gives
        Eve's accessible information as the binary entropy of the QBER,
        ``h2(qber) = -qber log2(qber) - (1-qber) log2(1-qber)``. This is a
        provable *upper* bound and is always conservative (h2(q) <= q for
        q in (0, 1)), so it never under-amplifies privacy.
        """
        if qber <= 0.0 or qber >= 1.0:
            return 0.0 if qber <= 0.0 else 1.0
        from math import log2

        return float(-qber * log2(qber) - (1.0 - qber) * log2(1.0 - qber))

    @abstractmethod
    def _get_security_threshold(self) -> float:
        """Get the security threshold for the protocol.

        Returns:
            Maximum QBER value considered secure

        """
        pass
