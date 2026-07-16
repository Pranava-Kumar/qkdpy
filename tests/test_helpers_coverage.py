"""Coverage tests for utils/helpers.py (was 35%)."""

import pytest

from qkdpy.utils.helpers import (
    apply_permutation,
    binary_entropy,
    bits_to_bytes,
    bits_to_int,
    bytes_to_bits,
    calculate_qber,
    generate_random_permutation,
    hamming_distance,
    int_to_bits,
    mutual_information,
    random_bit_string,
)


class TestRandomBitString:
    def test_length(self):
        """random_bit_string should return a list of the requested length."""
        result = random_bit_string(100)
        assert len(result) == 100

    def test_bits_are_zero_or_one(self):
        """Every element should be 0 or 1."""
        result = random_bit_string(50)
        assert all(b in (0, 1) for b in result)

    def test_zero_length(self):
        """Edge case: length 0."""
        result = random_bit_string(0)
        assert result == []

    def test_reproducibility_not_guaranteed(self):
        """Two calls produce (with extremely high probability) different results."""
        r1 = random_bit_string(200)
        r2 = random_bit_string(200)
        # At least one bit should differ (astronomically improbable to match)
        assert r1 != r2


class TestBitsToBytes:
    def test_exact_byte(self):
        """bits_to_bytes([0, 0, 0, 0, 0, 0, 0, 0]) → b'\\x00'."""
        assert bits_to_bytes([0, 0, 0, 0, 0, 0, 0, 0]) == b"\x00"
        assert bits_to_bytes([1, 1, 1, 1, 1, 1, 1, 1]) == b"\xff"
        assert bits_to_bytes([0, 0, 0, 0, 0, 0, 0, 1]) == b"\x01"

    def test_multi_byte(self):
        """0x01 0x02 → [0,0,0,0,0,0,0,1, 0,0,0,0,0,0,1,0]."""
        bits = (
            [0, 0, 0, 0, 0, 0, 0, 1]
            + [0, 0, 0, 0, 0, 0, 1, 0]
        )
        assert bits_to_bytes(bits) == b"\x01\x02"

    def test_partial_byte_dropped(self):
        """Only complete bytes are returned."""
        bits = [1, 0, 1, 0, 1, 0, 1, 0, 1]  # 9 bits → only 1 byte
        assert bits_to_bytes(bits) == b"\xaa"

    def test_empty(self):
        """Edge case: empty list."""
        assert bits_to_bytes([]) == b""


class TestBytesToBits:
    def test_single_byte(self):
        result = bytes_to_bits(b"\x00")
        assert result == [0, 0, 0, 0, 0, 0, 0, 0]

        result = bytes_to_bits(b"\xff")
        assert result == [1, 1, 1, 1, 1, 1, 1, 1]

        result = bytes_to_bits(b"\xaa")
        assert result == [1, 0, 1, 0, 1, 0, 1, 0]

    def test_multi_byte(self):
        result = bytes_to_bits(b"\x01\x02")
        assert result == (
            [0, 0, 0, 0, 0, 0, 0, 1] + [0, 0, 0, 0, 0, 0, 1, 0]
        )

    def test_empty(self):
        assert bytes_to_bits(b"") == []

    def test_roundtrip(self):
        """bits → bytes → bits gives the original (padded to 8)."""
        original = [1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 1, 0, 0, 0, 0, 1]
        mid = bits_to_bytes(original)
        restored = bytes_to_bits(mid)
        assert restored == original

    def test_roundtrip_short(self):
        """Less-than-8-bit input produces empty bytes (bits are dropped)."""
        original = [1, 0, 1]
        mid = bits_to_bytes(original)
        assert mid == b""  # 3 bits < 8, no complete byte
        restored = bytes_to_bits(mid)
        assert restored == []


class TestBitsToInt:
    def test_basic(self):
        assert bits_to_int([0, 0, 0, 0]) == 0
        assert bits_to_int([1]) == 1
        assert bits_to_int([1, 0]) == 2
        assert bits_to_int([1, 1]) == 3
        assert bits_to_int([1, 0, 1]) == 5

    def test_empty(self):
        assert bits_to_int([]) == 0


class TestIntToBits:
    def test_basic(self):
        assert int_to_bits(0) == [0]
        assert int_to_bits(1) == [1]
        assert int_to_bits(2) == [1, 0]
        assert int_to_bits(5) == [1, 0, 1]
        assert int_to_bits(255) == [1, 1, 1, 1, 1, 1, 1, 1]

    def test_with_length(self):
        assert int_to_bits(0, length=5) == [0, 0, 0, 0, 0]
        assert int_to_bits(5, length=8) == [0, 0, 0, 0, 0, 1, 0, 1]
        assert int_to_bits(5, length=3) == [1, 0, 1]
        assert int_to_bits(5, length=2) == [1, 0, 1]  # longer than length

    def test_roundtrip(self):
        for n in [0, 1, 2, 3, 7, 8, 42, 127, 128, 1023]:
            bits = int_to_bits(n)
            assert bits_to_int(bits) == n


class TestHammingDistance:
    def test_identical(self):
        assert hamming_distance([0, 1, 0, 1], [0, 1, 0, 1]) == 0

    def test_all_different(self):
        assert hamming_distance([0, 0, 0], [1, 1, 1]) == 3

    def test_partial(self):
        assert hamming_distance([1, 0, 1, 0], [1, 1, 0, 0]) == 2

    def test_length_mismatch(self):
        with pytest.raises(ValueError, match="same length"):
            hamming_distance([0, 1], [0, 1, 0])

    def test_empty(self):
        assert hamming_distance([], []) == 0


class TestBinaryEntropy:
    def test_boundary(self):
        """binary_entropy(0) = 0, binary_entropy(1) = 0."""
        assert binary_entropy(0) == 0.0
        assert binary_entropy(1) == 0.0

    def test_maximum(self):
        """binary_entropy(0.5) = 1.0."""
        h = binary_entropy(0.5)
        assert h == pytest.approx(1.0, abs=1e-12)

    def test_symmetric(self):
        """H(p) = H(1-p)."""
        h1 = binary_entropy(0.3)
        h2 = binary_entropy(0.7)
        assert h1 == pytest.approx(h2, abs=1e-12)

    def test_known_values(self):
        assert binary_entropy(0.11) == pytest.approx(0.5, abs=1e-1)


class TestCalculateQBER:
    def test_zero_error(self):
        assert calculate_qber([0, 1, 0], [0, 1, 0]) == 0.0

    def test_50_percent(self):
        assert calculate_qber([0, 0, 0, 0], [0, 1, 0, 1]) == 0.5

    def test_100_percent(self):
        assert calculate_qber([0, 1], [1, 0]) == 1.0

    def test_length_mismatch(self):
        with pytest.raises(ValueError, match="same length"):
            calculate_qber([0], [0, 1])

    def test_empty(self):
        """Empty bit strings should return 0.0."""
        assert calculate_qber([], []) == 0.0


class TestMutualInformation:
    def test_identical(self):
        """Two identical lists should have maximal MI."""
        x = [0, 1, 0, 1, 0, 1]
        y = [0, 1, 0, 1, 0, 1]
        mi = mutual_information(x, y)
        # H(X) = H(Y) = 1 (balanced), H(X,Y) = 1 (same) → MI = 1
        assert mi == pytest.approx(1.0, abs=1e-10)

    def test_independent(self):
        """Independent variables should have ~0 MI."""
        x = [0, 0, 0, 0, 1, 1, 1, 1]
        y = [0, 1, 0, 1, 0, 1, 0, 1]
        mi = mutual_information(x, y)
        # Should be very small
        assert mi < 0.1

    def test_length_mismatch(self):
        with pytest.raises(ValueError, match="same length"):
            mutual_information([0], [0, 1])

    def test_single_value(self):
        """Single unique value in both -> 0 MI."""
        mi = mutual_information([0, 0, 0], [0, 0, 0])
        assert mi == pytest.approx(0.0, abs=1e-10)

    def test_multi_values(self):
        """Values > 1 should still work."""
        mi = mutual_information([0, 1, 2, 3], [0, 1, 2, 3])
        assert mi == pytest.approx(2.0, abs=1e-10)


class TestGenerateRandomPermutation:
    def test_length(self):
        p = generate_random_permutation(10)
        assert len(p) == 10

    def test_is_permutation(self):
        """Result should be a valid permutation of 0..n-1."""
        n = 20
        p = generate_random_permutation(n)
        assert sorted(p) == list(range(n))

    def test_n_equals_1(self):
        assert generate_random_permutation(1) == [0]

    def test_n_equals_0(self):
        assert generate_random_permutation(0) == []


class TestApplyPermutation:
    def test_basic(self):
        bits = [1, 0, 1, 0]
        perm = [0, 2, 1, 3]
        assert apply_permutation(bits, perm) == [1, 1, 0, 0]

    def test_identity(self):
        bits = [1, 0, 0, 1]
        perm = [0, 1, 2, 3]
        assert apply_permutation(bits, perm) == bits

    def test_reverse(self):
        bits = [1, 0, 1, 0]
        perm = [3, 2, 1, 0]
        assert apply_permutation(bits, perm) == [0, 1, 0, 1]

    def test_length_mismatch(self):
        with pytest.raises(ValueError, match="Permutation length must match"):
            apply_permutation([1, 0], [0, 1, 2])

    def test_invalid_permutation(self):
        """Permutation must contain all integers from 0 to n-1."""
        with pytest.raises(ValueError, match="must contain all integers"):
            apply_permutation([1, 0], [0, 0])
