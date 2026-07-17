"""Extended tests for qkdpy.utils.validation -- uncovered functions.

Adds test coverage for:

- validate_key_length
- validate_binary_key
- validate_qber
- validate_unitary
- validate_normalized_state
- validate_density_matrix
- validate_range edge cases (min_exclusive / max_exclusive)
- validate_type with allow_none=True
- _extract_param_value
"""

import unittest

import numpy as np

from qkdpy.utils.validation import (
    ParameterError,
    RangeError,
    TypeValidationError,
    _extract_param_value,
    validate_binary_key,
    validate_density_matrix,
    validate_key_length,
    validate_normalized_state,
    validate_qber,
    validate_range,
    validate_type,
    validate_unitary,
)


# -- Helper functions for testing decorators ---------------------


@validate_range("x", min_value=0, max_value=10, min_inclusive=False)
def _needs_range_min_exclusive(x: int) -> int:
    return x


@validate_range("x", min_value=0, max_value=10, max_inclusive=False)
def _needs_range_max_exclusive(x: int) -> int:
    return x


@validate_type("val", expected_types=int, allow_none=True)
def _accepts_int_or_none(val: int | None = None) -> int | None:
    return val


@validate_type("val", expected_types=str, allow_none=True)
def _accepts_str_or_none(val: str | None = None) -> str | None:
    return val


def _dummy_func(a: int, b: str, c: float = 0.0) -> None:
    pass


class TestValidateKeyLength(unittest.TestCase):
    """Tests for validate_key_length."""

    def test_sufficient_length(self):
        """Key with sufficient length should pass."""
        validate_key_length([0, 1, 0, 1], min_length=1)
        validate_key_length([0], min_length=1)
        validate_key_length([1, 1, 1, 1, 1], min_length=5)

    def test_short_key(self):
        """Key shorter than min_length should raise ParameterError."""
        with self.assertRaises(ParameterError):
            validate_key_length([], min_length=1)
        with self.assertRaises(ParameterError):
            validate_key_length([0], min_length=5)
        with self.assertRaises(ParameterError):
            validate_key_length([1, 0], min_length=3)

    def test_custom_min_length(self):
        """Custom min_length should be respected."""
        with self.assertRaises(ParameterError):
            validate_key_length([0, 1, 0], min_length=5)
        validate_key_length([0, 1, 0, 1, 0], min_length=5)


class TestValidateBinaryKey(unittest.TestCase):
    """Tests for validate_binary_key."""

    def test_all_binary(self):
        """Key with only 0s and 1s should pass."""
        validate_binary_key([])
        validate_binary_key([0])
        validate_binary_key([1])
        validate_binary_key([0, 1, 0, 1, 1, 0])

    def test_non_binary_value(self):
        """Key with non-binary value should raise ParameterError."""
        with self.assertRaises(ParameterError) as cm:
            validate_binary_key([0, 1, 2])
        self.assertIn("position 2", str(cm.exception))

    def test_non_binary_value_at_start(self):
        """Non-binary value at position 0."""
        with self.assertRaises(ParameterError) as cm:
            validate_binary_key([3, 0, 1])
        self.assertIn("position 0", str(cm.exception))

    def test_non_binary_negative(self):
        """Negative value is not binary."""
        with self.assertRaises(ParameterError):
            validate_binary_key([0, -1, 1])


class TestValidateQBER(unittest.TestCase):
    """Tests for validate_qber."""

    def test_valid_qber_zero(self):
        """QBER of 0.0 should pass."""
        validate_qber(0.0)

    def test_valid_qber_mid(self):
        """QBER of 0.25 should pass."""
        validate_qber(0.25)

    def test_valid_qber_half(self):
        """QBER of 0.5 should pass."""
        validate_qber(0.5)

    def test_negative_qber(self):
        """Negative QBER should raise RangeError."""
        with self.assertRaises(RangeError):
            validate_qber(-0.1)

    def test_qber_above_half(self):
        """QBER larger than 0.5 should raise RangeError."""
        with self.assertRaises(RangeError):
            validate_qber(0.6)


class TestValidateUnitary(unittest.TestCase):
    """Tests for validate_unitary."""

    def test_non_2d(self):
        """Non-2D array should raise ParameterError."""
        with self.assertRaises(ParameterError):
            validate_unitary(np.array([1, 0, 0, 0]))

    def test_non_square(self):
        """Non-square matrix should raise ParameterError."""
        with self.assertRaises(ParameterError):
            validate_unitary(np.array([[1, 0, 0], [0, 1, 0]]))

    def test_non_unitary(self):
        """Non-unitary matrix should raise ParameterError."""
        with self.assertRaises(ParameterError):
            validate_unitary(np.array([[1, 2], [3, 4]]))

    def test_identity(self):
        """Identity matrix is unitary."""
        validate_unitary(np.eye(2))
        validate_unitary(np.eye(4))

    def test_hadamard(self):
        """Hadamard matrix is unitary."""
        H = (1 / np.sqrt(2)) * np.array([[1, 1], [1, -1]])
        validate_unitary(H)

    def test_custom_atol(self):
        """Near-unitary matrix passes with relaxed tolerance."""
        almost_I = np.eye(2) + 1e-8 * np.array([[0, 1], [1, 0]])
        validate_unitary(almost_I, atol=1e-6)
        with self.assertRaises(ParameterError):
            validate_unitary(almost_I, atol=1e-10)


class TestValidateNormalizedState(unittest.TestCase):
    """Tests for validate_normalized_state."""

    def test_normalized_zero(self):
        """|0> state is normalized."""
        validate_normalized_state(np.array([1, 0]))

    def test_normalized_one(self):
        """|1> state is normalized."""
        validate_normalized_state(np.array([0, 1]))

    def test_normalized_plus(self):
        """|+> state is normalized."""
        validate_normalized_state(np.array([1, 1]) / np.sqrt(2))

    def test_not_normalized_double(self):
        """[2, 0] has norm 2 -- raises ParameterError."""
        with self.assertRaises(ParameterError):
            validate_normalized_state(np.array([2, 0]))

    def test_not_normalized_equal(self):
        """[1, 1] has norm sqrt(2) -- raises ParameterError."""
        with self.assertRaises(ParameterError):
            validate_normalized_state(np.array([1, 1]))

    def test_custom_atol(self):
        """Near-normalized state passes with relaxed tolerance."""
        # np.isclose uses rtol=1e-5 by default.
        # [1, 0.0045] has norm ~= 1.0000101, so |norm-1| ~= 1.01e-5.
        # atol=1e-6 gives threshold 1.1e-5 (pass), atol=1e-10 gives ~1e-5 (fail).
        near_norm = np.array([1.0, 0.0045])
        validate_normalized_state(near_norm, atol=1e-6)
        with self.assertRaises(ParameterError):
            validate_normalized_state(near_norm, atol=1e-10)


class TestValidateDensityMatrix(unittest.TestCase):
    """Tests for validate_density_matrix."""

    def test_non_2d(self):
        """Non-2D array raises ParameterError."""
        with self.assertRaises(ParameterError):
            validate_density_matrix(np.array([0.5, 0.5]))

    def test_non_square(self):
        """Non-square matrix raises ParameterError."""
        with self.assertRaises(ParameterError):
            validate_density_matrix(
                np.array([[0.5, 0, 0], [0, 0.5, 0]])
            )

    def test_non_hermitian(self):
        """Non-Hermitian matrix raises ParameterError."""
        rho = np.array([[0.5 + 0j, 1j], [0 + 0j, 0.5 + 0j]])
        with self.assertRaises(ParameterError):
            validate_density_matrix(rho)

    def test_trace_not_one(self):
        """Matrix with trace != 1 raises ParameterError."""
        rho = np.array([[1 + 0j, 0], [0, 0.5 + 0j]])
        with self.assertRaises(ParameterError):
            validate_density_matrix(rho)

    def test_not_positive_semidefinite(self):
        """Non-PSD Hermitian matrix (trace=1) raises ParameterError."""
        rho = np.array([[0.5 + 0j, 1], [1, 0.5 + 0j]])
        with self.assertRaises(ParameterError):
            validate_density_matrix(rho)

    def test_valid_mixed_state(self):
        """Valid mixed state passes."""
        rho = np.array([[0.5 + 0j, 0], [0, 0.5 + 0j]])
        validate_density_matrix(rho)

    def test_valid_pure_state(self):
        """Valid pure state passes."""
        rho = np.array([[1 + 0j, 0], [0, 0 + 0j]])
        validate_density_matrix(rho)

    def test_valid_maximally_mixed_3d(self):
        """Maximally mixed state in 3D passes."""
        rho = np.eye(3) / 3
        validate_density_matrix(rho)


class TestValidateRangeEdgeCases(unittest.TestCase):
    """Edge cases for validate_range decorator (exclusive boundaries)."""

    def test_min_exclusive_boundary(self):
        """min_exclusive=True rejects value at exactly min_value."""
        with self.assertRaises(RangeError):
            _needs_range_min_exclusive(0)
        _needs_range_min_exclusive(1e-12)

    def test_max_exclusive_boundary(self):
        """max_exclusive=True rejects value at exactly max_value."""
        with self.assertRaises(RangeError):
            _needs_range_max_exclusive(10)
        _needs_range_max_exclusive(9.999)

    def test_both_exclusive(self):
        """Both boundaries exclusive."""

        @validate_range(
            "x", min_value=0, max_value=10,
            min_inclusive=False, max_inclusive=False,
        )
        def _both_exclusive(x: float) -> float:
            return x

        with self.assertRaises(RangeError):
            _both_exclusive(0)
        with self.assertRaises(RangeError):
            _both_exclusive(10)
        self.assertEqual(_both_exclusive(5), 5)


class TestValidateTypeAllowNone(unittest.TestCase):
    """Tests for validate_type with allow_none=True."""

    def test_none_passes(self):
        """None should pass with allow_none=True."""
        self.assertIsNone(_accepts_int_or_none(None))
        self.assertIsNone(_accepts_str_or_none(None))

    def test_valid_type_still_works(self):
        """Valid type still passes with allow_none=True."""
        self.assertEqual(_accepts_int_or_none(42), 42)
        self.assertEqual(_accepts_str_or_none("hi"), "hi")

    def test_invalid_type_still_fails(self):
        """Invalid type still raises TypeValidationError with allow_none=True."""
        with self.assertRaises(TypeValidationError):
            _accepts_int_or_none("not an int")


class TestExtractParamValue(unittest.TestCase):
    """Tests for the _extract_param_value helper."""

    def test_found_in_kwargs(self):
        """Parameter found in kwargs."""
        value, found = _extract_param_value(
            "b", _dummy_func, (), {"b": "hello"}
        )
        self.assertTrue(found)
        self.assertEqual(value, "hello")

    def test_found_in_positional_args(self):
        """Parameter found in positional args."""
        value, found = _extract_param_value(
            "a", _dummy_func, (42, "hello"), {}
        )
        self.assertTrue(found)
        self.assertEqual(value, 42)

    def test_not_found(self):
        """Parameter not provided -- found is False."""
        value, found = _extract_param_value(
            "c", _dummy_func, (42, "hello"), {}
        )
        self.assertFalse(found)
        self.assertIsNone(value)

    def test_kwargs_precedence(self):
        """kwargs should take precedence over positional args."""
        value, found = _extract_param_value(
            "a", _dummy_func, (99, "hello"), {"a": 42}
        )
        self.assertTrue(found)
        self.assertEqual(value, 42)

    def test_none_in_kwargs_is_found(self):
        """None passed explicitly in kwargs yields found=True."""
        value, found = _extract_param_value(
            "b", _dummy_func, (), {"b": None}
        )
        self.assertTrue(found)
        self.assertIsNone(value)

    def test_param_name_not_in_signature(self):
        """Name not in function signature returns (None, False)."""
        value, found = _extract_param_value(
            "nonexistent", _dummy_func, (42, "hello"), {}
        )
        self.assertFalse(found)
        self.assertIsNone(value)


if __name__ == "__main__":
    unittest.main()
