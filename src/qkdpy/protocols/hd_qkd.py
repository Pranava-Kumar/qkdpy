"""High-Dimensional Quantum Key Distribution (HD-QKD) protocol implementation."""

import numpy as np

from ..core import QuantumChannel, Qudit
from .base import BaseProtocol


class HDQKD(BaseProtocol):
    """Implementation of High-Dimensional Quantum Key Distribution protocol.

    HD-QKD uses qudits (d-dimensional quantum systems) instead of qubits,
    allowing for more information per photon and enhanced security.
    """

    def __init__(
        self,
        channel: QuantumChannel,
        key_length: int = 100,
        dimension: int = 4,
        security_threshold: float = 0.15,
    ):
        """Initialize the HD-QKD protocol.

        Args:
            channel: Quantum channel for qudit transmission
            key_length: Desired length of the final key
            dimension: Dimension of the qudit system (d)
            security_threshold: Maximum QBER value considered secure
        """
        super().__init__(channel, key_length)

        # HD-QKD-specific parameters
        self.dimension = dimension
        self.security_threshold = security_threshold

        # Number of qudits to send (more than needed to account for sifting)
        self.num_qudits = key_length * 3

        # Alice's random symbols and bases
        self.alice_symbols: list[int] = []
        self.alice_bases: list[int | None] = []

        # Bob's measurement results and bases
        self.bob_results: list[int | None] = []
        self.bob_bases: list[int | None] = []

        # MUBs (Mutually Unbiased Bases) for the dimension
        self.mubs = self._generate_mubs(dimension)

    def _generate_mubs(self, d: int) -> list[np.ndarray]:
        """Generate Mutually Unbiased Bases for a d-dimensional system.

        Args:
            d: Dimension of the system

        Returns:
            List of d+1 MUBs, each as a dxd matrix
        """
        if d == 2:
            # For qubits, we have 3 MUBs (X, Y, Z)
            return [
                np.array([[1, 0], [0, 1]]),  # Computational basis
                np.array([[1, 1], [1, -1]]) / np.sqrt(2),  # Hadamard basis
                np.array([[1, -1j], [1, 1j]]) / np.sqrt(2),  # Circular basis
            ]
        elif self._is_prime_power(d):
            # For prime power dimensions, construct MUBs using the standard construction
            return self._construct_mubs_prime_power(d)
        else:
            # For non-prime-power dimensions, use approximate construction or return identity
            # Note: Complete MUBs are only known for prime power dimensions
            mubs = [np.eye(d, dtype=complex)]  # Start with computational basis
            # Add a few more bases using Fourier transform and other methods
            # This is an approximation for non-prime-power dimensions
            for k in range(1, min(d + 1, 4)):  # Limit to 4 bases for non-prime powers
                # Create a generalized Fourier matrix
                fourier_matrix = np.zeros((d, d), dtype=complex)
                for i in range(d):
                    for j in range(d):
                        fourier_matrix[i, j] = np.exp(
                            1j * 2 * np.pi * i * j / d
                        ) / np.sqrt(d)

                # Apply some transformation to generate different basis
                shift_matrix = np.roll(np.eye(d), k, axis=1)
                mubs.append(fourier_matrix @ shift_matrix)

            return mubs

    def _is_prime_power(self, n: int) -> bool:
        """Check if a number is a prime power.

        Args:
            n: Number to check

        Returns:
            True if n is a prime power, False otherwise
        """
        if n <= 1:
            return False

        # Find the smallest prime factor
        for p in range(2, int(np.sqrt(n)) + 1):
            if n % p == 0:
                # Check if p^k = n for some k
                temp = n
                while temp % p == 0:
                    temp //= p
                if temp == 1:
                    return True
                else:
                    return False
        # If no factor found, n is prime (a prime power with exponent 1)
        return True

    def _construct_mubs_prime_power(self, d: int) -> list[np.ndarray]:
        """Construct MUBs for prime power dimension d.

        Args:
            d: Prime power dimension

        Returns:
            List of d+1 MUBs
        """
        # For simplicity, implement construction for prime dimensions
        # For prime powers, we would need finite field arithmetic which is more complex

        if self._is_prime(d):
            return self._construct_mubs_prime(d)
        else:
            # For prime powers, we'll use an approximation
            mubs = [np.eye(d, dtype=complex)]
            for k in range(1, d):
                # Create a generalized Fourier matrix with shift
                fourier_matrix = np.zeros((d, d), dtype=complex)
                for i in range(d):
                    for j in range(d):
                        fourier_matrix[i, j] = np.exp(
                            1j * 2 * np.pi * i * j / d
                        ) / np.sqrt(d)

                # Apply shift transformation
                shift_matrix = np.roll(np.eye(d), k, axis=1)
                mubs.append(fourier_matrix @ shift_matrix)

            return mubs

    def _is_prime(self, n: int) -> bool:
        """Check if a number is prime.

        Args:
            n: Number to check

        Returns:
            True if n is prime, False otherwise
        """
        if n <= 1:
            return False
        if n <= 3:
            return True
        if n % 2 == 0 or n % 3 == 0:
            return False

        i = 5
        while i * i <= n:
            if n % i == 0 or n % (i + 2) == 0:
                return False
            i += 6
        return True

    def _construct_mubs_prime(self, p: int) -> list[np.ndarray]:
        """Construct MUBs for prime dimension p using the standard construction.

        Args:
            p: Prime dimension

        Returns:
            List of p+1 MUBs
        """
        mubs = []

        # Computational basis (standard basis)
        computational_basis = np.eye(p, dtype=complex)
        mubs.append(computational_basis)

        # Remaining p bases
        for a in range(p):  # a = 0, 1, ..., p-1
            basis_matrix = np.zeros((p, p), dtype=complex)
            for m in range(p):
                for n in range(p):
                    # Element |m+a*n> in the a-th basis, where arithmetic is mod p
                    idx = (m + a * n) % p
                    basis_matrix[m, n] = np.exp(2j * np.pi * idx / p) / np.sqrt(p)
            mubs.append(basis_matrix)

        return mubs

    def prepare_states(self) -> list[Qudit]:
        """Prepare quantum states for transmission in HD-QKD.

        In HD-QKD, Alice randomly chooses symbols from {0, 1, ..., d-1} and bases.

        Returns:
            List of qudits encoded with HD information
        """
        qudits = []
        self.alice_symbols = []
        self.alice_bases = []

        for _ in range(self.num_qudits):
            # Alice randomly chooses a symbol (0 to d-1)
            symbol = np.random.randint(0, self.dimension)
            self.alice_symbols.append(symbol)

            # Alice randomly chooses a basis (0 to d)
            basis_idx = np.random.randint(0, len(self.mubs))
            self.alice_bases.append(basis_idx)

            # Prepare the qudit in the appropriate basis state
            # We first prepare in the computational basis then transform to the chosen basis
            computational_state = Qudit.computational_basis(symbol, self.dimension)

            # Transform to the chosen basis by applying the inverse of the basis transformation
            # Since MUBs are defined as transformation matrices, we apply the conjugate transpose
            basis_transformation = self.mubs[basis_idx].conj().T
            computational_state.apply_unitary(basis_transformation)

            qudits.append(computational_state)

        return qudits

    def measure_states(self, qudits: list[Qudit | None]) -> list[int]:
        """Measure received quantum states.

        In HD-QKD, Bob randomly chooses bases from the MUBs to measure in.

        Args:
            qudits: List of received qudits (may contain None for lost qudits)

        Returns:
            List of measurement results
        """
        self.bob_results = []
        self.bob_bases = []

        for qudit in qudits:
            if qudit is None:
                # Qudit was lost in the channel
                self.bob_results.append(None)
                self.bob_bases.append(None)
                continue

            # Bob randomly chooses a basis from the MUBs
            basis_idx = np.random.randint(0, len(self.mubs))
            self.bob_bases.append(basis_idx)

            # Measure in the chosen basis
            # The measurement basis is the conjugate transpose of the MUB matrix
            measurement_basis = self.mubs[basis_idx].conj().T
            result = qudit.measure(measurement_basis)

            # Collapse the state to the measurement result in the measurement basis
            qudit.collapse_state(result, measurement_basis)
            self.bob_results.append(result)

        # Filter out None values to return only int results
        return [result for result in self.bob_results if result is not None]

    def sift_keys(self) -> tuple[list[int], list[int]]:
        """Sift the raw keys to keep only measurements in matching bases.

        Returns:
            Tuple of (alice_sifted_key, bob_sifted_key)
        """
        alice_sifted = []
        bob_sifted = []

        for i in range(self.num_qudits):
            # Skip if Bob didn't receive the qudit
            if self.bob_bases[i] is None or self.bob_results[i] is None:
                continue

            # Check if Alice and Bob used the same basis
            if (
                self.alice_bases[i] is not None
                and self.bob_bases[i] is not None
                and self.alice_bases[i] == self.bob_bases[i]
            ):
                alice_sifted.append(int(self.alice_symbols[i]))
                # We already checked that self.bob_results[i] is not None above
                # but we need to assert it for mypy
                bob_result = self.bob_results[i]
                if bob_result is not None:
                    bob_sifted.append(int(bob_result))

        return alice_sifted, bob_sifted

    def estimate_qber(self) -> float:
        """Estimate the Quantum Bit Error Rate (QBER) for HD-QKD.

        Returns:
            Estimated QBER value
        """
        alice_sifted, bob_sifted = self.sift_keys()

        # If we don't have enough bits for estimation, return a high QBER
        if len(alice_sifted) < 10:
            return 1.0

        # Count errors in the sifted key
        errors = 0
        for i in range(len(alice_sifted)):
            if alice_sifted[i] != bob_sifted[i]:
                errors += 1

        # Calculate QBER
        qber = errors / len(alice_sifted) if len(alice_sifted) > 0 else 1.0
        return qber

    def _get_security_threshold(self) -> float:
        """Get the security threshold for the HD-QKD protocol.

        Returns:
            Maximum QBER value considered secure
        """
        return self.security_threshold

    def get_dimension_efficiency(self) -> float:
        """Calculate the efficiency gain from using higher dimensions.

        Returns:
            Efficiency factor compared to qubit-based protocols
        """
        # In HD-QKD, we can encode log2(d) bits per photon instead of 1
        return float(np.log2(self.dimension))

    def get_basis_distribution(self) -> dict:
        """Analyze the distribution of measurement bases.

        Returns:
            Dictionary with basis distribution statistics
        """
        alice_basis_counts: dict[str, int] = {}
        bob_basis_counts: dict[str, int] = {}

        # Count Alice's basis choices
        for basis in self.alice_bases:
            if basis is not None and basis != "":
                alice_basis_counts[basis] = alice_basis_counts.get(basis, 0) + 1

        # Count Bob's basis choices
        for basis in self.bob_bases:
            if basis is not None and basis != "":
                bob_basis_counts[basis] = bob_basis_counts.get(basis, 0) + 1

        return {
            "alice_bases": alice_basis_counts,
            "bob_bases": bob_basis_counts,
            "total_qudits": self.num_qudits,
            "dimension": self.dimension,
        }
