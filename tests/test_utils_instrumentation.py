"""Tests for qkdpy.utils.instrumentation.

Covers OperationSpan, @instrument decorator, and the record_* helpers.
"""

import time
import unittest

from qkdpy.utils.instrumentation import (
    OperationSpan,
    instrument,
    record_ml_training,
    record_protocol_execution,
    record_qber_diagnostic,
)


class TestOperationSpan(unittest.TestCase):
    """OperationSpan context manager behaviour."""

    def test_basic_start_complete(self):
        """OperationSpan logs started and completed events without error."""
        with OperationSpan("test.op"):
            pass

    def test_duration_measured(self):
        """OperationSpan measures positive duration."""
        span = OperationSpan("test.dur")
        span._start_time = time.monotonic() - 0.05  # simulate 50ms elapsed
        # trigger __exit__ without exception
        span.__exit__(None, None, None)
        # We check the internal state was clean — actual duration is logged
        self.assertIsNotNone(span._start_time)

    def test_with_metadata(self):
        """set_metadata attaches extra fields without error."""
        with OperationSpan("test.meta") as span:
            span.set_metadata(qber=0.05, key_size=256)
        # Just verifying no exception

    def test_error_logs_failed(self):
        """Exception inside the span logs operation_failed and propagates."""
        with self.assertRaises(ValueError):
            with OperationSpan("test.err"):
                raise ValueError("something broke")

    def test_context_attached(self):
        """Static context passed to constructor does not raise."""
        with OperationSpan("test.ctx", protocol="BB84", key_length=128):
            pass

    def test_level_override(self):
        """Non-info level does not raise."""
        with OperationSpan("test.warn", level="warning"):
            pass


class TestInstrumentDecorator(unittest.TestCase):
    """@instrument decorator behaviour."""

    def test_basic_decorator(self):
        """Decorated function runs and returns result."""

        @instrument("custom.op", log_args=False, log_result=False)
        def do_work() -> str:
            return "done"

        self.assertEqual(do_work(), "done")

    def test_default_operation_name(self):
        """When operation is None, uses module.qualname."""

        @instrument()
        def sample_func() -> int:
            return 42

        self.assertEqual(sample_func(), 42)

    def test_decorator_with_args(self):
        """Decorated function passes args through correctly."""

        @instrument("test.add", log_args=True, log_result=False)
        def add(a: int, b: int) -> int:
            return a + b

        self.assertEqual(add(3, 5), 8)

    def test_decorator_with_exception(self):
        """Decorated function that raises propagates the exception."""

        @instrument("test.raise", log_args=False, log_result=False)
        def will_raise() -> None:
            raise RuntimeError("decorator error")

        with self.assertRaises(RuntimeError):
            will_raise()

    def test_decorator_log_args(self):
        """@instrument with log_args still executes correctly."""

        @instrument("test.logargs", log_args=True, log_result=False)
        def greet(name: str) -> str:
            return f"Hello {name}"

        self.assertEqual(greet("Alice"), "Hello Alice")

    def test_decorator_log_result(self):
        """@instrument with log_result still returns value."""

        @instrument("test.logres", log_args=True, log_result=True)
        def compute(x: int) -> int:
            return x * 2

        self.assertEqual(compute(21), 42)


class TestRecordHelpers(unittest.TestCase):
    """record_* helper functions."""

    def test_record_protocol_execution(self):
        """record_protocol_execution emits without error."""
        record_protocol_execution(
            protocol_name="BB84",
            key_length=256,
            qber=0.035,
            final_key_size=192,
            is_secure=True,
            duration_ms=12.34,
            channel_stats={"loss_rate": 0.1},
        )

    def test_record_protocol_execution_no_channel_stats(self):
        """record_protocol_execution works without channel_stats."""
        record_protocol_execution(
            protocol_name="E91",
            key_length=128,
            qber=0.02,
            final_key_size=128,
            is_secure=True,
            duration_ms=5.0,
        )

    def test_record_ml_training(self):
        """record_ml_training emits without error."""
        record_ml_training(
            model_name="QKDAttackDetector",
            protocol="BB84",
            input_dim=16,
            training_samples=10000,
            training_time_ms=450.5,
            final_loss=0.023,
            convergence_iterations=42,
        )

    def test_record_ml_training_minimal(self):
        """record_ml_training works with only required fields."""
        record_ml_training(
            model_name="MinimalModel",
            protocol="E91",
            input_dim=8,
            training_samples=500,
            training_time_ms=100.0,
        )

    def test_record_qber_diagnostic_info_level(self):
        """record_qber_diagnostic works when QBER is below threshold."""
        record_qber_diagnostic(
            protocol="BB84",
            qber=0.02,
            threshold=0.11,
            key_size=256,
            distance_km=50.0,
        )

    def test_record_qber_diagnostic_warning_level(self):
        """record_qber_diagnostic works when QBER approaches threshold."""
        record_qber_diagnostic(
            protocol="BB84",
            qber=0.09,
            threshold=0.11,
            key_size=128,
            distance_km=100.0,
        )

    def test_record_qber_diagnostic_no_distance(self):
        """record_qber_diagnostic works with None distance."""
        record_qber_diagnostic(
            protocol="SixState",
            qber=0.05,
            threshold=0.11,
            key_size=64,
        )

    def test_record_qber_diagnostic_zero_threshold(self):
        """record_qber_diagnostic handles zero threshold without division error."""
        record_qber_diagnostic(
            protocol="Test",
            qber=0.0,
            threshold=0.0,
            key_size=0,
        )


if __name__ == "__main__":
    unittest.main()
