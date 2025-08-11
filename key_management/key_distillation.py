"""Key distillation methods for QKD protocols."""

from .error_correction import ErrorCorrection
from .privacy_amplification import PrivacyAmplification


class KeyDistillation:
    """Provides key distillation methods for QKD protocols.

    This class combines error correction and privacy amplification to distill
    a secure key from the raw quantum transmission.
    """

    def __init__(
        self,
        error_correction_method: str = "cascade",
        privacy_amplification_method: str = "universal_hashing",
    ):
        """Initialize the key distillation process.

        Args:
            error_correction_method: Method for error correction
            privacy_amplification_method: Method for privacy amplification

        """
        self.error_correction_method = error_correction_method
        self.privacy_amplification_method = privacy_amplification_method

        # Distillation statistics
        self.initial_key_length = 0
        self.corrected_key_length = 0
        self.final_key_length = 0
        self.error_rate = 0.0
        self.eve_information = 0.0

    def distill(
        self,
        alice_key: list[int],
        bob_key: list[int],
        qber: float = 0.0,
        final_key_length: int = None,
    ) -> dict[str, list[int] | float]:
        """Perform key distillation.

        Args:
            alice_key: Alice's raw key
            bob_key: Bob's raw key
            qber: Estimated Quantum Bit Error Rate
            final_key_length: Desired length of the final key (optional)

        Returns:
            Dictionary containing distillation results and statistics

        """
        # Reset statistics
        self.initial_key_length = len(alice_key)
        self.error_rate = ErrorCorrection.error_rate(alice_key, bob_key)

        # Step 1: Error correction
        if self.error_correction_method == "cascade":
            alice_corrected, bob_corrected = ErrorCorrection.cascade(alice_key, bob_key)
        elif self.error_correction_method == "winnow":
            alice_corrected, bob_corrected = ErrorCorrection.winnow(alice_key, bob_key)
        elif self.error_correction_method == "ldpc":
            alice_corrected, bob_corrected = ErrorCorrection.ldpc(alice_key, bob_key)
        else:
            raise ValueError(
                f"Unknown error correction method: {self.error_correction_method}"
            )

        self.corrected_key_length = len(alice_corrected)

        # Verify that error correction was successful
        if ErrorCorrection.error_rate(alice_corrected, bob_corrected) > 0:
            raise RuntimeError("Error correction failed to reconcile the keys")

        # Step 2: Estimate Eve's information
        self.eve_information = self._estimate_eve_information(qber)

        # Step 3: Privacy amplification
        if final_key_length is None:
            # Calculate a safe final key length based on Eve's information
            # We'll use the formula: r = n - s - t
            # where n is the corrected key length, s is a security parameter,
            # and t is an estimate of Eve's information
            s = 10  # Security parameter
            t = int(self.corrected_key_length * self.eve_information)
            final_key_length = max(1, self.corrected_key_length - s - t)

        if self.privacy_amplification_method == "universal_hashing":
            final_key = PrivacyAmplification.universal_hashing(
                alice_corrected, final_key_length
            )
        elif self.privacy_amplification_method == "toeplitz_hashing":
            final_key = PrivacyAmplification.toeplitz_hashing(
                alice_corrected, final_key_length
            )
        elif self.privacy_amplification_method == "cryptographic_hash":
            final_key = PrivacyAmplification.cryptographic_hash(
                alice_corrected, final_key_length
            )
        elif self.privacy_amplification_method == "bennett_brassard":
            final_key = PrivacyAmplification.bennett_brassard_hashing(
                alice_corrected, final_key_length, self.error_rate
            )
        else:
            raise ValueError(
                f"Unknown privacy amplification method: {self.privacy_amplification_method}"
            )

        self.final_key_length = len(final_key)

        # Return distillation results
        return {
            "alice_key": alice_corrected,
            "bob_key": bob_corrected,
            "final_key": final_key,
            "initial_length": self.initial_key_length,
            "corrected_length": self.corrected_key_length,
            "final_length": self.final_key_length,
            "error_rate": self.error_rate,
            "eve_information": self.eve_information,
            "key_rate": (
                self.final_key_length / self.initial_key_length
                if self.initial_key_length > 0
                else 0
            ),
        }

    def _estimate_eve_information(self, qber: float) -> float:
        """Estimate the fraction of information Eve has about the key.

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

    def get_statistics(self) -> dict[str, int | float]:
        """Get distillation statistics.

        Returns:
            Dictionary containing distillation statistics

        """
        return {
            "initial_length": self.initial_key_length,
            "corrected_length": self.corrected_key_length,
            "final_length": self.final_key_length,
            "error_rate": self.error_rate,
            "eve_information": self.eve_information,
            "key_rate": (
                self.final_key_length / self.initial_key_length
                if self.initial_key_length > 0
                else 0
            ),
        }

    def reset_statistics(self) -> None:
        """Reset all statistics counters."""
        self.initial_key_length = 0
        self.corrected_key_length = 0
        self.final_key_length = 0
        self.error_rate = 0.0
        self.eve_information = 0.0
