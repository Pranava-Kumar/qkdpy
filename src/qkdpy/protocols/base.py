"""Base class for QKD protocols."""

from abc import ABC, abstractmethod

import numpy as np

from ..core import QuantumChannel, Qubit


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
        self.channel = channel
        self.key_length = key_length

        # Protocol statistics
        self.raw_key = []
        self.sifted_key = []
        self.final_key = []
        self.qber = 0.0

        # Basis information
        self.alice_bases = []
        self.bob_bases = []

        # Error correction and privacy amplification parameters
        self.error_correction_method = "cascade"
        self.privacy_amplification_method = "universal_hashing"

        # Protocol status
        self.is_complete = False
        self.is_secure = False

    @abstractmethod
    def prepare_states(self) -> list[Qubit]:
        """Prepare quantum states for transmission.

        Returns:
            List of qubits to be sent through the quantum channel

        """
        pass

    @abstractmethod
    def measure_states(self, qubits: list[Qubit]) -> list[int]:
        """Measure received quantum states.

        Args:
            qubits: List of received qubits

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

    def execute(self) -> dict[str, list[int] | float | bool]:
        """Execute the full QKD protocol.

        Returns:
            Dictionary containing protocol results and statistics

        """
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

        # Step 6: Error correction
        alice_corrected, bob_corrected = self.error_correction(alice_sifted, bob_sifted)

        # Step 7: Privacy amplification
        # Estimate information leak based on QBER
        leak = int(len(alice_corrected) * self._estimate_eve_information(qber))
        final_key = self.privacy_amplification(alice_corrected, leak)

        # Update protocol status
        self.raw_key = measurement_results
        self.sifted_key = alice_sifted
        self.final_key = final_key
        self.qber = qber
        self.is_complete = True
        self.is_secure = qber < self._get_security_threshold()

        # Return protocol results
        return {
            "raw_key": self.raw_key,
            "sifted_key": self.sifted_key,
            "final_key": self.final_key,
            "qber": self.qber,
            "is_secure": self.is_secure,
            "channel_stats": self.channel.get_statistics(),
        }

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

        Args:
            alice_key: Alice's sifted key
            bob_key: Bob's sifted key

        Returns:
            Tuple of corrected (alice_key, bob_key)

        """
        # This is a simplified implementation of the Cascade protocol
        # A full implementation would involve multiple passes with different block sizes

        # Make copies of the keys
        alice_corrected = alice_key.copy()
        bob_corrected = bob_key.copy()

        # Initial pass with a fixed block size
        block_size = 4
        num_blocks = len(alice_key) // block_size

        for i in range(num_blocks):
            start = i * block_size
            end = start + block_size

            # Calculate parity for the block
            alice_parity = sum(alice_corrected[start:end]) % 2
            bob_parity = sum(bob_corrected[start:end]) % 2

            # If parities don't match, find and correct the error
            if alice_parity != bob_parity:
                # Binary search to find the error
                left = start
                right = end

                while right - left > 1:
                    mid = (left + right) // 2

                    alice_parity_left = sum(alice_corrected[left:mid]) % 2
                    bob_parity_left = sum(bob_corrected[left:mid]) % 2

                    if alice_parity_left != bob_parity_left:
                        right = mid
                    else:
                        left = mid

                # Correct the error
                bob_corrected[left] = 1 - bob_corrected[left]

        return alice_corrected, bob_corrected

    def _universal_hashing_privacy_amplification(
        self, key: list[int], leak: int
    ) -> list[int]:
        """Universal hashing for privacy amplification.

        Args:
            key: Key to be amplified
            leak: Estimated amount of information leaked to Eve

        Returns:
            Shortened, more secure key

        """
        # Calculate the length of the final key
        # We'll use the leftover hash lemma: r = n - s - leak
        # where n is the original key length, s is a security parameter
        n = len(key)
        s = 10  # Security parameter

        r = max(1, n - s - leak)  # Ensure at least 1 bit remains

        # Convert the key to a binary string
        key_str = "".join(map(str, key))

        # Use a simple universal hash function (Toeplitz matrix)
        # In a real implementation, we would use a cryptographically secure hash function

        # Generate a random seed for the hash function
        np.random.seed(42)  # Fixed seed for reproducibility
        seed = np.random.randint(0, 2, size=(r, n))

        # Apply the hash function
        result = []
        for i in range(r):
            # Compute the dot product modulo 2
            bit = sum(seed[i][j] * int(key_str[j]) for j in range(n)) % 2
            result.append(bit)

        return result

    def _estimate_eve_information(self, qber: float) -> float:
        """Estimate the amount of information Eve has based on QBER.

        Args:
            qber: Quantum Bit Error Rate

        Returns:
            Estimated fraction of information leaked to Eve

        """
        # This is a simplified model
        # In a real implementation, this would depend on the specific protocol and attack model

        # For BB84, the relationship between QBER and Eve's information is well-studied
        # For simplicity, we'll use a linear model here
        return min(1.0, qber * 2)

    @abstractmethod
    def _get_security_threshold(self) -> float:
        """Get the security threshold for the protocol.

        Returns:
            Maximum QBER value considered secure

        """
        pass
