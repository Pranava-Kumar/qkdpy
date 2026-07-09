"""Tests for qkdpy.ml.efficient_models (EfficientQKDPredictor)."""

import unittest

import numpy as np

from qkdpy.ml import EfficientQKDPredictor


class TestEfficientQKDPredictor(unittest.TestCase):
    """Test cases for EfficientQKDPredictor."""

    def setUp(self):
        np.random.seed(42)
        self.X = np.random.randn(40, 3).astype(np.float32)
        self.y = (self.X[:, 0] + 0.3 * self.X[:, 1] - 0.2 * self.X[:, 2]).astype(
            np.float32
        )

    def test_fit_returns_history(self):
        p = EfficientQKDPredictor(input_dim=3, max_memory_mb=64, enable_pruning=False)
        result = p.fit(self.X, self.y, epochs=10, learning_rate=0.05, batch_size=8)
        self.assertIn("epochs_trained", result)
        self.assertIn("final_train_loss", result)
        self.assertTrue(p.is_trained)

    def test_loss_decreases(self):
        p = EfficientQKDPredictor(input_dim=3, max_memory_mb=64, enable_pruning=False)
        result = p.fit(self.X, self.y, epochs=20, learning_rate=0.1, batch_size=8)
        self.assertLess(result["final_train_loss"], result["training_history"][0])

    def test_predict_shape(self):
        p = EfficientQKDPredictor(input_dim=3, max_memory_mb=64, enable_pruning=False)
        p.fit(self.X, self.y, epochs=5, learning_rate=0.05, batch_size=8)
        preds = p.predict(self.X)
        self.assertEqual(preds.shape, (40,))

    def test_predict_returns_float32(self):
        p = EfficientQKDPredictor(input_dim=3, max_memory_mb=64, enable_pruning=False)
        p.fit(self.X, self.y, epochs=5, learning_rate=0.05, batch_size=8)
        self.assertEqual(p.predict(self.X).dtype, np.float32)

    def test_fit_accepts_validation_split(self):
        p = EfficientQKDPredictor(input_dim=3, max_memory_mb=64, enable_pruning=False)
        result = p.fit(
            self.X,
            self.y,
            epochs=10,
            learning_rate=0.05,
            batch_size=8,
            validation_split=0.3,
        )
        self.assertIn("best_val_loss", result)
        self.assertIsNotNone(result["best_val_loss"])

    def test_fit_early_stopping(self):
        p = EfficientQKDPredictor(input_dim=3, max_memory_mb=64, enable_pruning=False)
        result = p.fit(
            self.X,
            self.y,
            epochs=100,
            learning_rate=0.05,
            batch_size=8,
            validation_split=0.3,
            early_stopping_patience=3,
        )
        # Should have stopped early (not hit 100)
        self.assertLess(result["epochs_trained"], 100)

    def test_backward_does_not_crash(self):
        """Backprop with pre-activation caching does not raise."""
        p = EfficientQKDPredictor(input_dim=3, max_memory_mb=64, enable_pruning=False)
        p.fit(self.X, self.y, epochs=5, learning_rate=0.05, batch_size=8)
        # Re-fitting should also work (tests gradient state reset)
        p.fit(self.X, self.y, epochs=3, learning_rate=0.05, batch_size=8)

    def test_weight_initialization_default_architecture(self):
        p = EfficientQKDPredictor(input_dim=3)
        self.assertGreater(len(p.weights), 0)
        self.assertEqual(len(p.weights), len(p.biases))


class TestKnowledgeDistillation(unittest.TestCase):
    """KnowledgeDistillation integration."""

    def setUp(self):
        np.random.seed(42)
        self.X = np.random.randn(20, 2).astype(np.float32)
        self.y = (self.X[:, 0] + 0.5 * self.X[:, 1]).astype(np.float32)

    def test_generate_soft_targets_invokes_teacher(self):
        from qkdpy.ml import KnowledgeDistillation

        called = []

        def teacher(x):
            called.append(x)
            return np.zeros(len(x))

        kd = KnowledgeDistillation(teacher_predict=teacher)
        kd.generate_soft_targets(self.X)
        self.assertEqual(len(called), 1)

    def test_distill_trains_student(self):
        from qkdpy.ml import EfficientQKDPredictor, KnowledgeDistillation

        teacher = EfficientQKDPredictor(
            input_dim=2, max_memory_mb=64, enable_pruning=False
        )
        teacher.fit(self.X, self.y, epochs=5, learning_rate=0.05, batch_size=8)
        kd = KnowledgeDistillation(teacher_predict=teacher.predict)
        student = EfficientQKDPredictor(
            input_dim=2, max_memory_mb=64, enable_pruning=False
        )
        result = kd.distill(student, self.X, self.y, epochs=5, batch_size=8)
        self.assertIn("epochs_trained", result)


class TestAdaptiveModelSelector(unittest.TestCase):
    """AdaptiveModelSelector smoke tests."""

    def test_create_optimal_predictor(self):
        from qkdpy.ml import AdaptiveModelSelector

        predictor = AdaptiveModelSelector.create_optimal_predictor(input_dim=4)
        self.assertIsInstance(predictor, EfficientQKDPredictor)

    def test_get_available_memory_positive(self):
        from qkdpy.ml import AdaptiveModelSelector

        mem = AdaptiveModelSelector.get_available_memory_mb()
        self.assertGreater(mem, 0)


if __name__ == "__main__":
    unittest.main()
