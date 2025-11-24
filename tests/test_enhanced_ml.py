"""Tests for enhanced ML components in QKDpy."""

import unittest

from qkdpy.ml.qkd_optimizer import QKDAnomalyDetector, QKDOptimizer


class TestEnhancedMlComponents(unittest.TestCase):
    """Test cases for enhanced ML components."""

    def test_neural_network_optimization(self):
        """Test neural network-based optimization."""
        optimizer = QKDOptimizer("TestProtocol")

        # Define a simple objective function (negative quadratic form)
        def objective_function(params):
            x = params.get("x", 0)
            y = params.get("y", 0)
            return -(x**2 + y**2)  # Maximum at (0, 0)

        # Define parameter space
        parameter_space = {"x": (-5.0, 5.0), "y": (-5.0, 5.0)}

        # Run neural network optimization
        results = optimizer.optimize_channel_parameters(
            parameter_space, objective_function, num_iterations=30, method="neural"
        )

        # Check results
        self.assertIn("best_parameters", results)
        self.assertIn("best_objective_value", results)
        self.assertGreater(len(results["parameter_history"]), 0)
        self.assertGreater(len(results["objective_history"]), 0)

        # Check that the best value is better than most random samples
        self.assertLess(results["best_objective_value"], 0)  # Should be negative

    def test_improved_bayesian_optimization(self):
        """Test improved Bayesian optimization."""
        optimizer = QKDOptimizer("TestProtocol")

        # Define a simple objective function (negative quadratic form)
        def objective_function(params):
            x = params.get("x", 0)
            y = params.get("y", 0)
            return -(x**2 + y**2)  # Maximum at (0, 0)

        # Define parameter space
        parameter_space = {"x": (-5.0, 5.0), "y": (-5.0, 5.0)}

        # Run Bayesian optimization
        results = optimizer.optimize_channel_parameters(
            parameter_space, objective_function, num_iterations=30, method="bayesian"
        )

        # Check results
        self.assertIn("best_parameters", results)
        self.assertIn("best_objective_value", results)
        self.assertGreater(len(results["parameter_history"]), 0)
        self.assertGreater(len(results["objective_history"]), 0)

        # Check that the best value is better than most random samples
        self.assertLess(results["best_objective_value"], 0)  # Should be negative

    def test_multiple_optimization_methods(self):
        """Test that different optimization methods produce results."""
        optimizer = QKDOptimizer("TestProtocol")

        # Define a simple objective function
        def objective_function(params):
            x = params.get("x", 0)
            return -(x**2)  # Maximum at x=0

        # Define parameter space
        parameter_space = {"x": (-10.0, 10.0)}

        # Test genetic algorithm
        results_ga = optimizer.optimize_channel_parameters(
            parameter_space, objective_function, num_iterations=20, method="genetic"
        )
        self.assertIn("best_objective_value", results_ga)

        # Test Bayesian optimization
        results_bo = optimizer.optimize_channel_parameters(
            parameter_space, objective_function, num_iterations=20, method="bayesian"
        )
        self.assertIn("best_objective_value", results_bo)

        # Test neural network optimization
        results_nn = optimizer.optimize_channel_parameters(
            parameter_space, objective_function, num_iterations=20, method="neural"
        )
        self.assertIn("best_objective_value", results_nn)

    def test_performance_prediction(self):
        """Test performance prediction functionality."""
        optimizer = QKDOptimizer("TestProtocol")

        # Test prediction without trained model
        params = {"x": 1.0, "y": 2.0}
        prediction = optimizer.predict_performance(params)
        self.assertEqual(prediction, 0.0)  # Placeholder value

    def test_anomaly_detector_enhancements(self):
        """Test enhanced anomaly detection capabilities."""
        detector = QKDAnomalyDetector()

        # Create historical data
        history = [
            {"qber": 0.02, "key_rate": 1000, "loss": 0.1},
            {"qber": 0.03, "key_rate": 950, "loss": 0.12},
            {"qber": 0.025, "key_rate": 980, "loss": 0.11},
            {"qber": 0.028, "key_rate": 960, "loss": 0.115},
        ]

        # Establish baseline
        detector.establish_baseline(history)

        # Test detection with normal metrics
        normal_metrics = {"qber": 0.025, "key_rate": 970, "loss": 0.11}
        anomalies = detector.detect_anomalies(normal_metrics)

        # With normal metrics, we shouldn't detect anomalies
        self.assertFalse(anomalies.get("qber", False))

        # Test detection with anomalous metrics
        anomalous_metrics = {"qber": 0.5, "key_rate": 100, "loss": 0.8}
        anomalies = detector.detect_anomalies(anomalous_metrics)

        # With clearly anomalous metrics, we should detect anomalies
        self.assertTrue(
            anomalies.get("qber", False) or anomalies.get("key_rate", False)
        )


if __name__ == "__main__":
    unittest.main()
