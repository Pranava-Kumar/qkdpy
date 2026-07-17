"""Extended tests for qkdpy.utils.logging_config.

Covers untested paths: STRUCTLOG_AVAILABLE=False, ImportError handling.
"""

import logging
import unittest
from unittest.mock import MagicMock, patch

from qkdpy.utils.logging_config import (
    QKDLogger,
    _configure_structlog,
    _default_logger_lazy,
    _get_version,
    configure_default_logger,
    get_logger,
    log_error,
    log_security,
    log_warning,
)


class TestStructlogNotAvailable(unittest.TestCase):
    """Tests for when structlog is not available (STRUCTLOG_AVAILABLE=False)."""

    def test_get_logger_returns_qkd_logger_when_structlog_missing(self):
        """get_logger returns a working QKDLogger instance without structlog."""
        with patch("qkdpy.utils.logging_config.STRUCTLOG_AVAILABLE", False):
            logger = get_logger("test.no_structlog")
            self.assertIsInstance(logger, QKDLogger)
            logger.info("fallback works")

    def test_qkd_logger_stdlib_fallback_init(self):
        """QKDLogger.__init__ creates stdlib logger with handler when structlog missing."""
        with patch("qkdpy.utils.logging_config.STRUCTLOG_AVAILABLE", False):
            with patch("qkdpy.utils.logging_config.logging.getLogger") as mock_get_logger:
                mock_stdlib = MagicMock(spec=logging.Logger)
                mock_stdlib.handlers = []
                mock_get_logger.return_value = mock_stdlib

                logger = QKDLogger("test.stdlib")

                mock_get_logger.assert_called_once_with("test.stdlib")
                mock_stdlib.addHandler.assert_called_once()
                handler = mock_stdlib.addHandler.call_args[0][0]
                self.assertIsInstance(handler, logging.StreamHandler)
                self.assertIsNotNone(handler.formatter)
                mock_stdlib.setLevel.assert_called_once_with(logging.INFO)
                self.assertIsNone(logger._logger)

    def test_stdlib_fallback_log_methods_no_raise(self):
        """info/debug/warning/error work with stdlib fallback (no exceptions)."""
        with patch("qkdpy.utils.logging_config.STRUCTLOG_AVAILABLE", False):
            logger = get_logger("test.methods")
            logger.info("info message")
            logger.debug("debug message")
            logger.warning("warning message")
            logger.error("error message")

    def test_stdlib_fallback_log_with_kwargs(self):
        """_log with merged-context kwargs works in stdlib fallback."""
        with patch("qkdpy.utils.logging_config.STRUCTLOG_AVAILABLE", False):
            logger = get_logger("test.kwargs")
            logger.info("data event", key="value", count=42)
            logger.warning("warning event", error_code=500)
            logger.info("plain event")

    def test_stdlib_fallback_security_and_critical(self):
        """security() and critical() work with stdlib fallback."""
        with patch("qkdpy.utils.logging_config.STRUCTLOG_AVAILABLE", False):
            logger = get_logger("test.security")
            logger.security("unauthorized access")
            logger.critical("system failure")
            logger.security("intrusion detected", source_ip="10.0.0.1")

    def test_configure_structlog_early_return(self):
        """_configure_structlog returns early when STRUCTLOG_AVAILABLE is False."""
        with patch("qkdpy.utils.logging_config.STRUCTLOG_AVAILABLE", False):
            _configure_structlog()

    def test_configure_default_logger_no_structlog(self):
        """configure_default_logger produces a working logger without structlog."""
        with patch("qkdpy.utils.logging_config.STRUCTLOG_AVAILABLE", False):
            logger = configure_default_logger()
            self.assertIsInstance(logger, QKDLogger)


class TestImportErrorPaths(unittest.TestCase):
    """Tests for ImportError handling in the module."""

    def test_get_version_returns_unknown_on_import_error(self):
        """_get_version returns unknown when qkdpy.__version__ is inaccessible."""
        import qkdpy
        _get_version.cache_clear()
        saved = qkdpy.__version__
        try:
            del qkdpy.__version__
            result = _get_version()
            self.assertEqual(result, "unknown")
        finally:
            qkdpy.__version__ = saved
            _get_version.cache_clear()

    def test_colorama_import_error_does_not_crash(self):
        """Missing colorama does not crash when structlog is available."""
        with patch("qkdpy.utils.logging_config.STRUCTLOG_AVAILABLE", True):
            with patch("importlib.import_module", side_effect=ImportError("no colorama")):
                logger = get_logger("test.colorama")
                logger.info("still working without colorama")


class TestGetLoggerWithoutName(unittest.TestCase):
    """Tests for get_logger() with None name and inspect resolution."""

    def test_get_logger_no_name_uses_caller_module(self):
        """get_logger() reads caller __name__ via inspect."""
        with patch("inspect.currentframe") as mock_cf:
            fake_frame = MagicMock()
            fake_frame.f_back = MagicMock()
            fake_frame.f_back.f_globals = {"__name__": "test.caller.module"}
            mock_cf.return_value = fake_frame

            logger = get_logger()
            self.assertEqual(logger.name, "test.caller.module")

    def test_get_logger_no_name_fallback_when_no_frame(self):
        """get_logger() falls back to qkdpy when inspect.currentframe() is None."""
        with patch("inspect.currentframe", return_value=None):
            logger = get_logger()
            self.assertEqual(logger.name, "qkdpy")

    def test_get_logger_no_name_fallback_when_no_f_back(self):
        """get_logger() falls back to qkdpy when frame has no f_back."""
        with patch("inspect.currentframe") as mock_cf:
            fake_frame = MagicMock()
            fake_frame.f_back = None
            mock_cf.return_value = fake_frame

            logger = get_logger()
            self.assertEqual(logger.name, "qkdpy")

    def test_get_logger_no_name_fallback_missing_name_in_globals(self):
        """get_logger() falls back to qkdpy when caller globals lack __name__."""
        with patch("inspect.currentframe") as mock_cf:
            fake_frame = MagicMock()
            fake_frame.f_back = MagicMock()
            fake_frame.f_back.f_globals = {}
            mock_cf.return_value = fake_frame

            logger = get_logger()
            self.assertEqual(logger.name, "qkdpy")


class TestDefaultLoggerLazy(unittest.TestCase):
    """Tests for _default_logger_lazy singleton behavior."""

    def test_creates_logger_on_first_call(self):
        """_default_logger_lazy() creates a QKDLogger on first invocation."""
        with patch("qkdpy.utils.logging_config._default_logger", None):
            logger = _default_logger_lazy()
            self.assertIsInstance(logger, QKDLogger)
            self.assertEqual(logger.name, "qkdpy")

    def test_returns_same_instance_on_subsequent_calls(self):
        """_default_logger_lazy() returns cached instance on later calls."""
        with patch("qkdpy.utils.logging_config._default_logger", None):
            first = _default_logger_lazy()
            second = _default_logger_lazy()
            self.assertIs(first, second)


class TestConvenienceFunctions(unittest.TestCase):
    """Tests for module-level convenience functions: log_warning, log_error, log_security."""

    def test_log_warning_delegates_to_default_logger(self):
        """log_warning delegates to _default_logger_lazy().warning()."""
        with patch("qkdpy.utils.logging_config._default_logger_lazy") as mock_lazy:
            mock_logger = MagicMock()
            mock_lazy.return_value = mock_logger

            log_warning("test warning", extra="data")

            mock_logger.warning.assert_called_once_with("test warning", extra="data")

    def test_log_error_delegates_to_default_logger(self):
        """log_error delegates to _default_logger_lazy().error()."""
        with patch("qkdpy.utils.logging_config._default_logger_lazy") as mock_lazy:
            mock_logger = MagicMock()
            mock_lazy.return_value = mock_logger

            log_error("test error", errno=500)

            mock_logger.error.assert_called_once_with("test error", errno=500)

    def test_log_security_delegates_to_default_logger(self):
        """log_security delegates to _default_logger_lazy().security()."""
        with patch("qkdpy.utils.logging_config._default_logger_lazy") as mock_lazy:
            mock_logger = MagicMock()
            mock_lazy.return_value = mock_logger

            log_security("security event", ip="10.0.0.1")

            mock_logger.security.assert_called_once_with("security event", ip="10.0.0.1")


if __name__ == "__main__":
    unittest.main()
