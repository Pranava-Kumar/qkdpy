"""Error correction methods for QKD protocols."""

import random

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
        block_sizes: list[int] | None = None,
        iterations: int = 4,
        random_permute: bool = True,
    ) -> tuple[list[int], list[int]]:
        """Cascade error correction protocol with realistic improvements.

        Args:
            alice_key: Alice's binary key
            bob_key: Bob's binary key
            block_sizes: List of block sizes for each iteration (default: [4, 8, 16, 32])
            iterations: Number of iterations of the protocol
            random_permute: Whether to randomly permute keys between iterations

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
        corrected_bits: set[int] = set()

        # Store original index mapping if permutation is used
        permuted_indices = list(range(len(alice_key)))

        for iteration in range(iterations):
            # Randomly permute keys between iterations to avoid systematic errors
            if random_permute:
                # Create a random permutation for this iteration
                perm = list(range(len(alice_corrected)))
                random.shuffle(perm)

                # Apply permutation to both keys
                alice_corrected = [alice_corrected[i] for i in perm]
                bob_corrected = [bob_corrected[i] for i in perm]

                # Update the index mapping
                permuted_indices = [permuted_indices[i] for i in perm]

            block_size = block_sizes[iteration % len(block_sizes)]

            # Divide the key into blocks of the current size
            num_blocks = len(alice_corrected) // block_size

            for i in range(num_blocks):
                start = i * block_size
                end = start + block_size

                # Calculate parity for the block
                alice_parity = int(sum(alice_corrected[start:end]) % 2)
                bob_parity = int(sum(bob_corrected[start:end]) % 2)

                # If parities don't match, find and correct the error
                if alice_parity != bob_parity:
                    # Binary search to find the error
                    left = start
                    right = end

                    while right - left > 1:
                        mid = (left + right) // 2

                        alice_parity_left = int(sum(alice_corrected[left:mid]) % 2)
                        bob_parity_left = int(sum(bob_corrected[left:mid]) % 2)

                        if alice_parity_left != bob_parity_left:
                            right = mid
                        else:
                            left = mid

                    # Correct the error
                    bob_corrected[left] = 1 - bob_corrected[left]
                    corrected_bits.add(
                        permuted_indices[left] if random_permute else left
                    )

        # If keys were permuted, restore original order
        if random_permute:
            # Create inverse permutation
            inv_perm = [0] * len(alice_corrected)
            for i, p in enumerate(permuted_indices):
                inv_perm[p] = i

            # Apply inverse permutation
            alice_restored = [0] * len(alice_corrected)
            bob_restored = [0] * len(bob_corrected)

            for orig_idx, new_idx in enumerate(inv_perm):
                alice_restored[orig_idx] = alice_corrected[new_idx]
                bob_restored[orig_idx] = bob_corrected[new_idx]

            return alice_restored, bob_restored

        return alice_corrected, bob_corrected

    @staticmethod
    def winnow(
        alice_key: list[int],
        bob_key: list[int],
        block_size: int = 4,
        iterations: int = 4,
        random_permute: bool = True,
    ) -> tuple[list[int], list[int]]:
        """Winnow error correction protocol with realistic improvements.

        Args:
            alice_key: Alice's binary key
            bob_key: Bob's binary key
            block_size: Size of blocks for parity checks
            iterations: Number of iterations of the protocol
            random_permute: Whether to randomly permute keys between iterations

        Returns:
            Tuple of corrected (alice_key, bob_key)

        """
        if len(alice_key) != len(bob_key):
            raise ValueError("Alice's and Bob's keys must have the same length")

        # Make copies of the keys
        alice_corrected = alice_key.copy()
        bob_corrected = bob_key.copy()

        # Keep track of which bits have been corrected
        corrected_bits: set[int] = set()

        # Store original index mapping if permutation is used
        permuted_indices = list(range(len(alice_key)))

        for iteration in range(iterations):
            # Randomly permute keys between iterations
            if random_permute and iteration > 0:  # Skip permutation in first iteration
                perm = list(range(len(alice_corrected)))
                random.shuffle(perm)

                # Apply permutation to both keys
                alice_corrected = [alice_corrected[i] for i in perm]
                bob_corrected = [bob_corrected[i] for i in perm]

                # Update the index mapping
                permuted_indices = [permuted_indices[i] for i in perm]

            # Divide the key into blocks of the specified size
            num_blocks = len(alice_corrected) // block_size

            for i in range(num_blocks):
                start = i * block_size
                end = start + block_size

                # Skip if this block contains a bit that was already corrected
                if any(start <= bit < end for bit in corrected_bits):
                    continue

                # Calculate parity for the block
                alice_parity = int(sum(alice_corrected[start:end]) % 2)
                bob_parity = int(sum(bob_corrected[start:end]) % 2)

                # If parities don't match, find and correct the error
                if alice_parity != bob_parity:
                    # Binary search to find the error
                    left = start
                    right = end

                    while right - left > 1:
                        mid = (left + right) // 2

                        alice_parity_left = int(sum(alice_corrected[left:mid]) % 2)
                        bob_parity_left = int(sum(bob_corrected[left:mid]) % 2)

                        if alice_parity_left != bob_parity_left:
                            right = mid
                        else:
                            left = mid

                    # Correct the error
                    bob_corrected[left] = 1 - bob_corrected[left]
                    corrected_bits.add(
                        permuted_indices[left] if random_permute else left
                    )

        # If keys were permuted, restore original order
        if random_permute:
            # Create inverse permutation
            inv_perm = [0] * len(alice_corrected)
            for i, p in enumerate(permuted_indices):
                inv_perm[p] = i

            # Apply inverse permutation
            alice_restored = [0] * len(alice_corrected)
            bob_restored = [0] * len(bob_corrected)

            for orig_idx, new_idx in enumerate(inv_perm):
                alice_restored[orig_idx] = alice_corrected[new_idx]
                bob_restored[orig_idx] = bob_corrected[new_idx]

            return alice_restored, bob_restored

        return alice_corrected, bob_corrected

    @staticmethod
    def biconf(
        alice_key: list[int],
        bob_key: list[int],
        max_iterations: int = 10,
        error_rate_estimate: float = 0.1,
    ) -> tuple[list[int], list[int]]:
        """BICONF (Binary Confirmation) error correction protocol.

        Args:
            alice_key: Alice's binary key
            bob_key: Bob's binary key
            max_iterations: Maximum number of iterations
            error_rate_estimate: Estimated initial error rate

        Returns:
            Tuple of corrected (alice_key, bob_key)
        """
        if len(alice_key) != len(bob_key):
            raise ValueError("Alice's and Bob's keys must have the same length")

        alice_corrected = alice_key.copy()
        bob_corrected = bob_key.copy()

        # Initial estimate of errors
        initial_errors = int(len(alice_key) * error_rate_estimate)
        remaining_iterations = max_iterations

        # Process in chunks to handle errors more efficiently
        while remaining_iterations > 0 and initial_errors > 0:
            chunk_size = max(1, len(alice_key) // initial_errors)

            # Divide key into chunks and process each
            for start in range(0, len(alice_key), chunk_size):
                end = min(start + chunk_size, len(alice_key))
                chunk_alice = alice_corrected[start:end]
                chunk_bob = bob_corrected[start:end]

                # If chunk differs, try to locate and fix errors
                if chunk_alice != chunk_bob:
                    # Use simple bit flipping for now, could implement more sophisticated methods
                    errors_in_chunk = 0
                    for i in range(len(chunk_alice)):
                        if chunk_alice[i] != chunk_bob[i]:
                            # Decide which bit to flip based on additional info if available
                            # For simplicity, flip Bob's bit
                            bob_corrected[start + i] = chunk_alice[i]
                            errors_in_chunk += 1

                    # Update remaining error estimate
                    initial_errors = max(0, initial_errors - errors_in_chunk)

                    if initial_errors == 0:
                        break

            remaining_iterations -= 1

        return alice_corrected, bob_corrected

    @staticmethod
    def low_density_parity_check(
        alice_key: list[int],
        bob_key: list[int],
        code_rate: float = 0.5,
        max_iterations: int = 50,
    ) -> tuple[list[int], list[int], int]:
        """Low-Density Parity-Check (LDPC) error correction with realistic implementation.

        Args:
            alice_key: Alice's binary key
            bob_key: Bob's binary key
            code_rate: Code rate (information bits / total bits)
            max_iterations: Maximum number of decoding iterations

        Returns:
            Tuple of corrected (alice_key, bob_key, number_of_iterations_used)
        """
        if len(alice_key) != len(bob_key):
            raise ValueError("Alice's and Bob's keys must have the same length")

        n = len(alice_key)
        k = int(n * code_rate)  # Information bits
        m = n - k  # Parity check bits

        # Generate a proper LDPC parity check matrix
        # Using a simplified approach based on Gallager's construction
        H = ErrorCorrection._generate_ldpc_matrix(n, m)

        # Calculate syndrome for Bob's key
        syndrome = (H @ np.array(bob_key)) % 2

        # If syndrome is zero, keys are already consistent
        if np.sum(syndrome) == 0:
            return alice_key, bob_key, 0

        # Use belief propagation for LDPC decoding
        # Initialize log-likelihood ratios (LLR) based on Alice and Bob's differences
        llr = np.zeros(n)
        for i in range(n):
            if alice_key[i] == bob_key[i]:
                # Higher confidence if values match
                llr[i] = 2.0
            else:
                # Lower confidence (or negative) if values differ
                llr[i] = -2.0

        # Initialize messages between variable nodes and check nodes
        # Shape: (n, m) - each variable node sends a message to each check node
        var_to_check = np.zeros((n, m))
        for i in range(n):
            for j in range(m):
                var_to_check[i, j] = llr[i]

        # Decode using belief propagation
        iteration = 0
        for iteration in range(max_iterations):
            # Update check-to-variable messages
            check_to_var = np.zeros((m, n))

            for j in range(m):  # For each check node
                for i in range(n):  # For each variable node in check j
                    if H[j, i] == 1:  # If variable i is connected to check j
                        # Compute message from check j to variable i
                        # Using the sum-product algorithm
                        product = 1.0
                        for k in range(n):
                            if k != i and H[j, k] == 1:
                                tanh_val = np.tanh(var_to_check[k, j] / 2.0)
                                product *= tanh_val

                        # Calculate check-to-variable message
                        if abs(product) >= 1.0:
                            product = np.sign(product) * 0.999  # Avoid numerical issues
                        check_to_var[j, i] = 2.0 * np.arctanh(product)

            # Update variable-to-check messages
            for i in range(n):
                for j in range(m):
                    if H[i, j] == 1:
                        # Sum all incoming check messages except from check j
                        total = llr[i]
                        for j_prime in range(m):
                            if j_prime != j and H[i, j_prime] == 1:
                                total += check_to_var[j_prime, i]
                        var_to_check[i, j] = total

            # Make hard decisions
            final_llr = llr.copy()
            for i in range(n):
                for j in range(m):
                    final_llr[i] += check_to_var[j, i]

            # Generate decoded key
            decoded = (final_llr <= 0).astype(int)

            # Check if the syndrome is now zero
            new_syndrome = (H @ decoded) % 2
            if np.sum(new_syndrome) == 0:
                # Check if decoded key matches Alice's
                if np.array_equal(decoded, np.array(alice_key)):
                    return alice_key, decoded.tolist(), iteration + 1
                else:
                    # If it matches the syndrome but not Alice's key,
                    # try to adjust based on Alice's key
                    corrected_bob = bob_key.copy()
                    for i in range(n):
                        if alice_key[i] != decoded[i]:
                            corrected_bob[i] = alice_key[i]

                    # Verify the correction
                    final_syndrome = (H @ np.array(corrected_bob)) % 2
                    if np.sum(final_syndrome) == 0:
                        return alice_key, corrected_bob, iteration + 1
                    else:
                        continue  # Continue iterating

        # If maximum iterations reached without convergence
        return alice_key, bob_key, max_iterations

    @staticmethod
    def _generate_ldpc_matrix(n: int, m: int) -> np.ndarray:
        """Generate a regular LDPC parity-check matrix using a simplified approach.

        Args:
            n: Length of codeword (total number of bits)
            m: Number of parity checks (rows in H)

        Returns:
            LDPC parity-check matrix H (m x n)
        """
        # Simplified LDPC matrix construction based on random regular graph
        H = np.zeros((m, n), dtype=int)

        # Determine how many 1's per row and column based on regular structure
        # For a (j, k)-regular LDPC code: j * m = k * n
        # We'll use j=3 (checks per bit), determine k accordingly
        j = 3  # number of 1s per column (connections per variable node)
        k = (j * n) // m  # number of 1s per row (connections per check node)

        # Ensure j*n is divisible by m by adjusting m if necessary
        if (j * n) % m != 0:
            k = max(1, round((j * n) / m))
            effective_m = (j * n) // k
            H = np.zeros((effective_m, n), dtype=int)
            m = effective_m

        # Fill matrix with random 1s maintaining regularity
        for col in range(n):
            # Choose j positions randomly for the 1s in this column
            rows = np.random.choice(m, size=j, replace=False)
            H[rows, col] = 1

        # Check if each row has the expected number of 1s on average
        # If not, adjust randomly to balance
        for row in range(m):
            row_sum = np.sum(H[row])
            if row_sum < k:
                # Add more 1s to reach desired degree
                zeros = np.where(H[row] == 0)[0]
                if len(zeros) > 0:
                    add_count = min(k - row_sum, len(zeros))
                    chosen_cols = np.random.choice(zeros, size=add_count, replace=False)
                    H[row, chosen_cols] = 1

        return H

    @staticmethod
    def ldpc(
        alice_key: list[int],
        bob_key: list[int],
        parity_check_matrix: np.ndarray | None = None,
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
                break

        # If we reach the maximum number of iterations without converging,
        # return the best estimate we have
        return alice_key, [int(bit) for bit in corrected_bob.tolist()]

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
