"""Tests for qkdpy.utils.validation decorators."""

import unittest

from qkdpy.utils.validation import (
    ParameterError,
    RangeError,
    TypeValidationError,
    validate_not_empty,
    validate_positive,
    validate_probability,
    validate_range,
    validate_type,
)

# ── Helper functions decorated for testing ──────────────────────────────────


@validate_range("x", min_value=0, max_value=10)
def _needs_range(x: int) -> int:
    return x


@validate_type("data", expected_types=(str, bytes))
def _needs_str_bytes(data) -> ...:
    return data


@validate_positive("count")
def _needs_positive(count: float) -> float:
    return count


@validate_probability("prob")
def _needs_probability(prob: float) -> float:
    return prob


@validate_not_empty("items")
def _needs_nonempty(items: list[str]) -> list[str]:
    return items


# ── Tests ────────────────────────────────────────────────────────────────────


class TestValidationDecorators(unittest.TestCase):
    """Test cases for validation decorators in utils.validation."""

    # -- validate_range --------------------------------------------

    def test_range_valid(self):
        self.assertEqual(_needs_range(5), 5)

    def test_range_too_low(self):
        with self.assertRaises(RangeError):
            _needs_range(-1)

    def test_range_too_high(self):
        with self.assertRaises(RangeError):
            _needs_range(11)

    def test_range_boundary(self):
        self.assertEqual(_needs_range(0), 0)
        self.assertEqual(_needs_range(10), 10)

    # -- validate_type ----------------------------------------------

    def test_type_valid(self):
        self.assertEqual(_needs_str_bytes("hello"), "hello")

    def test_type_invalid(self):
        with self.assertRaises(TypeValidationError):
            _needs_str_bytes(42)

    # -- validate_positive ------------------------------------------

    def test_positive_valid(self):
        self.assertEqual(_needs_positive(3.14), 3.14)

    def test_positive_invalid(self):
        with self.assertRaises(RangeError):
            _needs_positive(-1)

    def test_positive_zero(self):
        with self.assertRaises(RangeError):
            _needs_positive(0)

    # -- validate_probability ---------------------------------------

    def test_probability_valid(self):
        self.assertEqual(_needs_probability(0.5), 0.5)
        self.assertEqual(_needs_probability(0.0), 0.0)
        self.assertEqual(_needs_probability(1.0), 1.0)

    def test_probability_out_of_range(self):
        with self.assertRaises(RangeError):
            _needs_probability(1.5)

    def test_probability_negative(self):
        with self.assertRaises(RangeError):
            _needs_probability(-0.1)

    # -- validate_not_empty -----------------------------------------

    def test_not_empty_valid(self):
        self.assertEqual(_needs_nonempty(["a", "b"]), ["a", "b"])

    def test_not_empty_invalid(self):
        with self.assertRaises(ParameterError):
            _needs_nonempty([])

    def test_not_empty_none_is_ok(self):
        """Decorators can handle None (not parameter error)."""
        from qkdpy.utils.validation import validate_not_empty

        @validate_not_empty("val")
        def _accepts_none(val=None):
            return val

        self.assertIsNone(_accepts_none(None))


if __name__ == "__main__":
    unittest.main()
