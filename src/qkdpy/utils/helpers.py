"""Helper functions for QKDpy."""

import numpy as np


def random_bit_string(length: int) -> list[int]:
    """Generate a random binary string.

    Args:
        length: Length of the binary string

    Returns:
        List of random bits

    """
    return [int(np.random.randint(0, 2)) for _ in range(length)]


def bits_to_bytes(bits: list[int]) -> bytes:
    """Convert a list of bits to bytes.

    Args:
        bits: List of bits to convert

    Returns:
        Bytes represented by the bits

    """
    # Group bits into bytes (8 bits each)
    bytes_data = bytearray()
    for i in range(0, len(bits), 8):
        if i + 8 <= len(bits):
            byte = bits[i : i + 8]
            byte_value = sum(byte[j] << (7 - j) for j in range(8))
            bytes_data.append(byte_value)

    return bytes(bytes_data)


def bytes_to_bits(data: bytes) -> list[int]:
    """Convert bytes to a list of bits.

    Args:
        data: Bytes to convert

    Returns:
        List of bits representing the bytes

    """
    bits = []
    for byte in data:
        for i in range(8):
            bits.append((byte >> (7 - i)) & 1)

    return bits


def bits_to_int(bits: list[int]) -> int:
    """Convert a list of bits to an integer.

    Args:
        bits: List of bits to convert

    Returns:
        Integer represented by the bits

    """
    return sum(bit << i for i, bit in enumerate(reversed(bits)))


def int_to_bits(n: int, length: int = None) -> list[int]:
    """Convert an integer to a list of bits.

    Args:
        n: Integer to convert
        length: Desired length of the bit list (optional)

    Returns:
        List of bits representing the integer

    """
    if n == 0:
        return [0] if length is None else [0] * length

    bits = []
    while n > 0:
        bits.append(n % 2)
        n = n // 2

    bits.reverse()

    if length is not None and len(bits) < length:
        bits = [0] * (length - len(bits)) + bits

    return bits


def hamming_distance(bits1: list[int], bits2: list[int]) -> int:
    """Calculate the Hamming distance between two bit strings.

    Args:
        bits1: First bit string
        bits2: Second bit string

    Returns:
        Number of positions where the bit strings differ

    Raises:
        ValueError: If the bit strings have different lengths

    """
    if len(bits1) != len(bits2):
        raise ValueError("Bit strings must have the same length")

    return sum(1 for b1, b2 in zip(bits1, bits2, strict=False) if b1 != b2)


def binary_entropy(p: float) -> float:
    """Calculate the binary entropy function.

    Args:
        p: Probability (between 0 and 1)

    Returns:
        Binary entropy value

    """
    if p == 0 or p == 1:
        return 0

    return -p * np.log2(p) - (1 - p) * np.log2(1 - p)


def calculate_qber(alice_bits: list[int], bob_bits: list[int]) -> float:
    """Calculate the Quantum Bit Error Rate (QBER) between two bit strings.

    Args:
        alice_bits: Alice's bit string
        bob_bits: Bob's bit string

    Returns:
        QBER value

    Raises:
        ValueError: If the bit strings have different lengths

    """
    if len(alice_bits) != len(bob_bits):
        raise ValueError("Bit strings must have the same length")

    if len(alice_bits) == 0:
        return 0.0

    errors = hamming_distance(alice_bits, bob_bits)
    return errors / len(alice_bits)


def mutual_information(x: list[int], y: list[int]) -> float:
    """Calculate the mutual information between two random variables.

    Args:
        x: First random variable (list of integers)
        y: Second random variable (list of integers)

    Returns:
        Mutual information value

    Raises:
        ValueError: If the lists have different lengths

    """
    if len(x) != len(y):
        raise ValueError("Lists must have the same length")

    # Calculate joint and marginal probabilities
    joint_prob = {}
    marginal_x = {}
    marginal_y = {}

    for i, j in zip(x, y, strict=False):
        key = (i, j)
        joint_prob[key] = joint_prob.get(key, 0) + 1
        marginal_x[i] = marginal_x.get(i, 0) + 1
        marginal_y[j] = marginal_y.get(j, 0) + 1

    # Normalize probabilities
    total = len(x)
    for key in joint_prob:
        joint_prob[key] /= total
    for key in marginal_x:
        marginal_x[key] /= total
    for key in marginal_y:
        marginal_y[key] /= total

    # Calculate entropies
    h_x = -sum(p * np.log2(p) for p in marginal_x.values())
    h_y = -sum(p * np.log2(p) for p in marginal_y.values())
    h_xy = -sum(p * np.log2(p) for p in joint_prob.values())

    # Calculate mutual information
    mi = h_x + h_y - h_xy

    return mi


def generate_random_permutation(n: int) -> list[int]:
    """Generate a random permutation of integers from 0 to n-1.

    Args:
        n: Length of the permutation

    Returns:
        Random permutation of integers

    """
    permutation = list(range(n))
    np.random.shuffle(permutation)
    return permutation


def apply_permutation(bits: list[int], permutation: list[int]) -> list[int]:
    """Apply a permutation to a list of bits.

    Args:
        bits: List of bits to permute
        permutation: Permutation to apply

    Returns:
        Permuted list of bits

    Raises:
        ValueError: If the permutation is not valid for the bit list

    """
    if len(bits) != len(permutation):
        raise ValueError("Permutation length must match bit list length")

    if set(permutation) != set(range(len(bits))):
        raise ValueError("Permutation must contain all integers from 0 to n-1")

    return [bits[i] for i in permutation]
