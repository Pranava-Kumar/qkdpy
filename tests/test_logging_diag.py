"""Diagnostic tests for qkdpy.utils.logging_config.

These tests verify the logging configuration module without assuming
the ability to capture structlog output directly.
"""

import unittest

from qkdpy.utils.logging_config import (
    QKDLogger,
    configure_default_logger,
    get_logger,
    log_debug,
    log_info,
    redact_sensitive_data,
)


class TestLoggingDiagnostics(unittest.TestCase):
    """Test logging_config without deep structlog capture."""

    def test_get_logger_returns_qkd_logger(self):
        """get_logger returns a QKDLogger instance."""
        logger = get_logger("test.module")
        self.assertIsInstance(logger, QKDLogger)

    def test_get_logger_independent_instances(self):
        """Multiple get_logger calls return distinct instances."""
        a = get_logger("alpha")
        b = get_logger("beta")
        self.assertIsNot(a, b)
        self.assertEqual(a.name, "alpha")
        self.assertEqual(b.name, "beta")

    def test_qkd_logger_bind_unbind(self):
        """bind / unbind do not raise."""
        logger = get_logger("test.bind")
        bound = logger.bind(extra="value")
        self.assertIs(bound, logger)  # returns self for chaining
        logger.unbind("extra")

    def test_convenience_funcs_auto_init(self):
        """log_info etc auto-initialize without explicit configure_default_logger."""
        # This must not raise.
        log_info("auto init test", extra=1)
        log_debug("debug test (may be filtered)")

    def test_configure_default_logger(self):
        """configure_default_logger returns a working logger."""
        logger = configure_default_logger()
        self.assertIsInstance(logger, QKDLogger)
        logger.info("post-configure test")

    # ── redact_sensitive_data (pure function) ──────────────────────

    def test_redact_drops_raw_key(self):
        result = redact_sensitive_data(None, "", {"raw_key": b"secret"})
        self.assertTrue(str(result["raw_key"]).startswith("[REDACTED"))

    def test_redact_preserves_key_rate(self):
        """key_rate is NOT redacted (no substring false positive)."""
        result = redact_sensitive_data(None, "", {"key_rate": 1.0e6})
        self.assertEqual(result["key_rate"], 1.0e6)

    def test_redact_preserves_qber(self):
        """qber is NOT redacted."""
        result = redact_sensitive_data(None, "", {"qber": 0.02})
        self.assertEqual(result["qber"], 0.02)

    def test_redact_private_key(self):
        result = redact_sensitive_data(None, "", {"private_key": "abc"})
        self.assertTrue(str(result["private_key"]).startswith("[REDACTED"))

    def test_redact_multiple_keys(self):
        event = {"raw_key": b"k1", "key_rate": 1e6, "qber": 0.03, "user": "alice"}
        result = redact_sensitive_data(None, "", event)
        self.assertTrue(str(result["raw_key"]).startswith("[REDACTED"))
        self.assertEqual(result["key_rate"], 1e6)
        self.assertEqual(result["qber"], 0.03)
        self.assertEqual(result["user"], "alice")


if __name__ == "__main__":
    unittest.main()
