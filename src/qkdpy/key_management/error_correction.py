"""Error correction methods for QKD protocols."""

import numpy as np


class ErrorCorrection:
    """Provides various error correction methods for QKD protocols.

    This class implements different error correction algorithms that can be used
    to reconcile Alice's and Bob's keys after the quantum transmission phase.
    """

    @staticmethod
    def cascade(
        alice_key: list[int],
        bob_key: list[int],
        block_sizes: list[int] = None,
        iterations: int = 4,
    ) -> tuple[list[int], list[int]]:
        """Cascade error correction protocol.

        Args:
            alice_key: Alice's binary key
            bob_key: Bob's binary key
            block_sizes: List of block sizes for each iteration (default: [4, 8, 16, 32])
            iterations: Number of iterations of the protocol

        Returns:
            Tuple of corrected (alice_key, bob_key)

        """
        if len(alice_key) != len(bob_key):
            raise ValueError("Alice's and Bob's keys must have the same length")

        if block_sizes is None:
            # Default block sizes for each iteration
            block_sizes = [4, 8, 16, 32]

        # Make copies of the keys
        alice_corrected = alice_key.copy()
        bob_corrected = bob_key.copy()

        # Keep track of which bits have been corrected in previous iterations
        corrected_bits = set()

        for iteration in range(iterations):
            block_size = block_sizes[iteration % len(block_sizes)]

            # Divide the key into blocks of the current size
            num_blocks = len(alice_corrected) // block_size

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
                    corrected_bits.add(left)

            # In subsequent iterations, also check blocks that contain previously corrected bits
            if iteration > 0:
                newly_corrected_bits = set()
                for bit_pos in corrected_bits.copy():
                    # Create a block around the corrected bit
                    block_start = max(0, bit_pos - block_size // 2)
                    block_end = min(len(alice_corrected), block_start + block_size)

                    # Calculate parity for the block
                    alice_parity = sum(alice_corrected[block_start:block_end]) % 2
                    bob_parity = sum(bob_corrected[block_start:block_end]) % 2

                    # If parities don't match, find and correct the error
                    if alice_parity != bob_parity:
                        # Binary search to find the error
                        left = block_start
                        right = block_end

                        while right - left > 1:
                            mid = (left + right) // 2

                            alice_parity_left = sum(alice_corrected[left:mid]) % 2
                            bob_parity_left = sum(bob_corrected[left:mid]) % 2

                            if alice_parity_left != bob_parity_left:
                                right = mid
                            else:
                                left = mid

                        # Correct the error if it's a new position
                        if left not in corrected_bits:
                            bob_corrected[left] = 1 - bob_corrected[left]
                            newly_corrected_bits.add(left)
                corrected_bits.update(newly_corrected_bits)

        return alice_corrected, bob_corrected

    @staticmethod
    def winnow(
        alice_key: list[int],
        bob_key: list[int],
        block_size: int = 4,
        iterations: int = 4,
    ) -> tuple[list[int], list[int]]:
        """Winnow error correction protocol.

        Args:
            alice_key: Alice's binary key
            bob_key: Bob's binary key
            block_size: Size of blocks for parity checks
            iterations: Number of iterations of the protocol

        Returns:
            Tuple of corrected (alice_key, bob_key)

        """
        if len(alice_key) != len(bob_key):
            raise ValueError("Alice's and Bob's keys must have the same length")

        # Make copies of the keys
        alice_corrected = alice_key.copy()
        bob_corrected = bob_key.copy()

        # Keep track of which bits have been corrected
        corrected_bits = set()

        for _iteration in range(iterations):
            # Divide the key into blocks of the specified size
            num_blocks = len(alice_corrected) // block_size

            for i in range(num_blocks):
                start = i * block_size
                end = start + block_size

                # Skip if this block contains a bit that was already corrected
                if any(start <= bit < end for bit in corrected_bits):
                    continue

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
                    corrected_bits.add(left)

        return alice_corrected, bob_corrected

    @staticmethod
    def ldpc(
        alice_key: list[int],
        bob_key: list[int],
        parity_check_matrix: np.ndarray = None,
        max_iterations: int = 100,
    ) -> tuple[list[int], list[int]]:
        """LDPC (Low-Density Parity-Check) error correction.

        Args:
            alice_key: Alice's binary key
            bob_key: Bob's binary key
            parity_check_matrix: Parity check matrix for LDPC codes
            max_iterations: Maximum number of iterations for the belief propagation algorithm

        Returns:
            Tuple of corrected (alice_key, bob_key)

        """
        if len(alice_key) != len(bob_key):
            raise ValueError("Alice's and Bob's keys must have the same length")

        n = len(alice_key)

        # If no parity check matrix is provided, create a random one
        if parity_check_matrix is None:
            # Create a regular LDPC matrix with 3 ones per column and 6 ones per row
            m = n // 2  # Number of parity checks

            # Initialize an empty matrix
            parity_check_matrix = np.zeros((m, n), dtype=int)

            # Fill the matrix with 1s to satisfy the constraints
            for j in range(n):
                # Randomly choose 3 rows to put 1s in this column
                rows = np.random.choice(m, size=3, replace=False)
                parity_check_matrix[rows, j] = 1

            # Ensure each row has approximately 6 ones
            for i in range(m):
                row_sum = np.sum(parity_check_matrix[i])
                if row_sum < 6:
                    # Randomly choose additional columns to put 1s
                    cols = np.random.choice(n, size=6 - row_sum, replace=False)
                    parity_check_matrix[i, cols] = 1

        # Convert keys to numpy arrays
        alice_array = np.array(alice_key)
        bob_array = np.array(bob_key)

        # Calculate the syndrome (parity checks)
        syndrome = np.dot(parity_check_matrix, bob_array) % 2

        # If the syndrome is all zeros, no errors are detected
        if np.all(syndrome == 0):
            return alice_key, bob_key

        # Belief propagation algorithm for LDPC decoding
        # This is a simplified implementation

        # Initialize likelihood ratios
        llr = np.zeros(n)
        for i in range(n):
            if alice_array[i] == bob_array[i]:
                llr[i] = 10.0  # High confidence that the bit is correct
            else:
                llr[i] = -10.0  # High confidence that the bit is incorrect

        # Initialize messages from variable nodes to check nodes
        v_to_c_messages = np.zeros(
            (parity_check_matrix.shape[1], parity_check_matrix.shape[0])
        )
        for i in range(n):
            for j in range(parity_check_matrix.shape[0]):
                if parity_check_matrix[j, i] == 1:
                    v_to_c_messages[i, j] = llr[i]

        # Belief propagation iterations
        for _iteration in range(max_iterations):
            # Check to variable messages
            c_to_v_messages = np.zeros(
                (parity_check_matrix.shape[0], parity_check_matrix.shape[1])
            )

            for j in range(parity_check_matrix.shape[0]):
                for i in range(parity_check_matrix.shape[1]):
                    if parity_check_matrix[j, i] == 1:
                        # Compute the product of incoming messages from other variable nodes
                        product = 1.0
                        for k in range(parity_check_matrix.shape[1]):
                            if k != i and parity_check_matrix[j, k] == 1:
                                product *= np.tanh(v_to_c_messages[k, j] / 2.0)

                        # Compute the check to variable message
                        c_to_v_messages[j, i] = 2.0 * np.arctanh(
                            product * (1 - 2 * syndrome[j])
                        )

            # Update variable to check messages
            for i in range(n):
                for j in range(parity_check_matrix.shape[0]):
                    if parity_check_matrix[j, i] == 1:
                        # Sum all incoming check messages except the one from check j
                        total = llr[i]
                        for k in range(parity_check_matrix.shape[0]):
                            if k != j and parity_check_matrix[k, i] == 1:
                                total += c_to_v_messages[k, i]

                        v_to_c_messages[i, j] = total

            # Compute the total likelihood for each variable
            total_llr = llr.copy()
            for i in range(n):
                for j in range(parity_check_matrix.shape[0]):
                    if parity_check_matrix[j, i] == 1:
                        total_llr[i] += c_to_v_messages[j, i]

            # Make a hard decision based on the total likelihood
            corrected_bob = np.zeros(n, dtype=int)
            for i in range(n):
                corrected_bob[i] = 0 if total_llr[i] > 0 else 1

            # Check if the syndrome is now all zeros
            new_syndrome = np.dot(parity_check_matrix, corrected_bob) % 2
            if np.all(new_syndrome == 0):
                return alice_key, corrected_bob.tolist()

        # If we reach the maximum number of iterations without converging,
        # return the best estimate we have
        return alice_key, corrected_bob.tolist()

    @staticmethod
    def hamming_distance(key1: list[int], key2: list[int]) -> int:
        """Calculate the Hamming distance between two keys.

        Args:
            key1: First binary key
            key2: Second binary key

        Returns:
            Number of positions where the keys differ

        """
        if len(key1) != len(key2):
            raise ValueError("Keys must have the same length")

        return sum(1 for a, b in zip(key1, key2, strict=False) if a != b)

    @staticmethod
    def error_rate(key1: list[int], key2: list[int]) -> float:
        """Calculate the error rate between two keys.

        Args:
            key1: First binary key
            key2: Second binary key

        Returns:
            Fraction of positions where the keys differ

        """
        if len(key1) != len(key2):
            raise ValueError("Keys must have the same length")

        if len(key1) == 0:
            return 0.0

        return ErrorCorrection.hamming_distance(key1, key2) / len(key1)
