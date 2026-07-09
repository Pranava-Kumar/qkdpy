"""Tests for qkdpy.config."""

import os
import unittest

from qkdpy.config import (
    QKDConfig,
    SecurityMode,
    get_config,
    load_config_from_env,
    set_config,
    validate_config,
)


class TestQKDConfig(unittest.TestCase):
    """Test cases for QKDConfig and config module functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.env_restore = {}
        for key in os.environ:
            if key.startswith("QKDPY_"):
                self.env_restore[key] = os.environ[key]
        for key in list(self.env_restore.keys()):
            del os.environ[key]

    def tearDown(self):
        """Restore original environment."""
        for key in list(os.environ.keys()):
            if key.startswith("QKDPY_"):
                del os.environ[key]
        os.environ.update(self.env_restore)

    # ── QKDConfig construction ──────────────────────────────────────────────

    def test_default_config(self):
        """Default QKDConfig has expected fields."""
        cfg = QKDConfig()
        self.assertEqual(cfg.security.mode, SecurityMode.PRODUCTION)
        self.assertEqual(cfg.protocol.default_protocol, "BB84")
        self.assertTrue(cfg.ml.enable_ml_optimization)

    def test_custom_config(self):
        """QKDConfig accepts overrides."""
        cfg = QKDConfig(debug_mode=True)
        self.assertTrue(cfg.debug_mode)

    # ── load_config_from_env ─────────────────────────────────────────────────

    def test_load_config_from_env(self):
        """load_config_from_env reads QKDPY_ prefixed env vars."""
        os.environ["QKDPY_DEBUG_MODE"] = "true"
        cfg = load_config_from_env()
        self.assertTrue(cfg.debug_mode)

    def test_load_config_default(self):
        """No env vars produces reasonable defaults."""
        cfg = load_config_from_env()
        self.assertFalse(cfg.debug_mode)

    # ── validate_config ─────────────────────────────────────────────────────

    def test_validate_config_returns_list(self):
        """validate_config returns a list of warning strings."""
        cfg = QKDConfig()
        warnings = validate_config(cfg)
        self.assertIsInstance(warnings, list)

    # ── global config singleton ─────────────────────────────────────────────

    def test_set_and_get_config(self):
        """set_config/get_config round-trip."""
        cfg = QKDConfig(debug_mode=True)
        set_config(cfg)
        retrieved = get_config()
        self.assertIs(retrieved, cfg)


if __name__ == "__main__":
    unittest.main()
