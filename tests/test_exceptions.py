"""Tests for qkdpy.exceptions hierarchy and helpers."""

import unittest

from qkdpy.exceptions import (
    InvalidConfigError,
    QKDException,
    wrap_exception,
)


class TestExceptions(unittest.TestCase):
    """Test cases for the exception hierarchy."""

    def test_qkd_exception_defaults(self):
        """QKDException has sensible defaults."""
        exc = QKDException("test error")
        self.assertEqual(str(exc), "test error")
        self.assertEqual(exc.recoverable, True)
        self.assertEqual(exc.context, {})

    def test_chained_cause(self):
        """Chained exception preserves __cause__."""
        inner = ValueError("inner")
        outer = QKDException("wrapped", cause=inner)
        self.assertIs(outer.__cause__, inner)

    def test_to_dict_includes_all_keys(self):
        """to_dict returns the expected structure."""
        exc = QKDException(
            "boom",
            context={"user": "alice", "protocol": "bb84"},
        )
        d = exc.to_dict()
        self.assertEqual(d["error_type"], "QKDException")
        self.assertEqual(d["message"], "boom")
        self.assertIn("user", d["context"])
        self.assertIn("protocol", d["context"])

    def test_to_dict_redacts_sensitive_keys(self):
        """to_dict redacts values under known sensitive keys."""
        exc = QKDException(
            "key leak check",
            context={"raw_key": "should-not-appear", "qber": 0.05},
        )
        d = exc.to_dict()
        self.assertEqual(d["context"]["raw_key"], "[REDACTED]")
        self.assertEqual(d["context"]["qber"], 0.05)  # not redacted

    def test_parameter_error_recoverable(self):
        """A ParameterError is marked as recoverable."""
        from qkdpy.exceptions import ParameterError

        exc = ParameterError("bad param", parameter="x")
        self.assertTrue(exc.recoverable)
        self.assertEqual(exc.context["parameter"], "x")

    def test_wrap_exception(self):
        """wrap_exception preserves the original message and chain."""
        inner = ValueError("original message")
        wrapped = wrap_exception(inner, InvalidConfigError, "config failure")
        self.assertIsInstance(wrapped, InvalidConfigError)
        self.assertIn("config failure", str(wrapped))
        self.assertIs(wrapped.__cause__, inner)

    def test_wrap_exception_default_message(self):
        """wrap_exception falls back to the original message if none given."""
        inner = RuntimeError("runtime problem")
        wrapped = wrap_exception(inner)
        self.assertIn("runtime problem", str(wrapped))


if __name__ == "__main__":
    unittest.main()
