"""Machine learning tools for QKD optimization and analysis."""

from collections.abc import Callable
from typing import Any

import numpy as np
from scipy.special import erf


class QKDOptimizer:
    """Machine learning-based optimizer for QKD protocols."""

    def __init__(self, protocol_name: str):
        """Initialize the QKD optimizer.

        Args:
            protocol_name: Name of the QKD protocol to optimize
        """
        self.protocol_name = protocol_name
        self.optimization_history: list[dict[str, Any]] = []
        self.best_parameters: dict[str, float] = {}
        self.best_performance = 0.0
        self.model = None  # For neural network-based optimization

    def optimize_channel_parameters(
        self,
        parameter_space: dict[str, tuple[float, float]],
        objective_function: Callable[[dict[str, float]], float],
        num_iterations: int = 100,
        method: str = "bayesian",
    ) -> dict[str, Any]:
        """Optimize quantum channel parameters using machine learning.

        Args:
            parameter_space: Dictionary mapping parameter names to (min, max) tuples
            objective_function: Function to maximize (e.g., key rate, security)
            num_iterations: Number of optimization iterations
            method: Optimization method ('bayesian', 'genetic', 'neural', 'gradient')

        Returns:
            Dictionary with optimization results
        """
        if method == "bayesian":
            return self._bayesian_optimization(
                parameter_space, objective_function, num_iterations
            )
        elif method == "genetic":
            return self._genetic_algorithm_optimization(
                parameter_space, objective_function, num_iterations
            )
        elif method == "neural":
            return self._neural_network_optimization(
                parameter_space, objective_function, num_iterations
            )
        else:
            raise ValueError(f"Unsupported optimization method: {method}")

    def _bayesian_optimization(
        self,
        parameter_space: dict[str, tuple[float, float]],
        objective_function: Callable[[dict[str, float]], float],
        num_iterations: int,
    ) -> dict[str, Any]:
        """Improved Bayesian optimization for QKD parameters using Gaussian process.

        Args:
            parameter_space: Dictionary mapping parameter names to (min, max) tuples
            objective_function: Function to maximize
            num_iterations: Number of optimization iterations

        Returns:
            Dictionary with optimization results
        """
        # Initialize with random samples
        best_params = {}
        best_value: Any = float("-inf")

        # Track parameter values and objective values
        param_history = []
        objective_history = []

        # Initial random sampling
        initial_samples = min(10, num_iterations // 2)
        for _ in range(initial_samples):
            # Generate random parameters within bounds
            params = {}
            for param_name, (min_val, max_val) in parameter_space.items():
                params[param_name] = np.random.uniform(min_val, max_val)

            # Evaluate objective function
            try:
                value = objective_function(params)
            except Exception:
                value = float("-inf")  # Penalize failed evaluations

            # Update best parameters
            if value > best_value:
                best_value = value
                best_params = params.copy()

            # Store history
            param_history.append(params)
            objective_history.append(value)

        # Improved Bayesian optimization iterations
        for _ in range(num_iterations - initial_samples):
            # Fit a simple Gaussian process model to the data
            # In a full implementation, we would use a proper GP library
            # For this implementation, we'll use a simplified approach

            # If we have enough data, use expected improvement
            if len(param_history) >= 5:
                # Select next point using expected improvement
                next_params = self._expected_improvement_search(
                    parameter_space, param_history, objective_history
                )
            else:
                # Use random search with bias toward better regions
                next_params = {}
                for param_name, (min_val, max_val) in parameter_space.items():
                    # Add some bias toward better performing regions
                    if len(objective_history) > 0:
                        # Find parameters that led to good results
                        good_indices = [
                            i
                            for i, val in enumerate(objective_history)
                            if val > np.mean(objective_history)
                        ]
                        if good_indices:
                            # Sample near good parameter values
                            good_values = [
                                param_history[i][param_name] for i in good_indices
                            ]
                            mean_val = np.mean(good_values)
                            std_val = np.std(good_values)
                            # Sample from a distribution centered on good values
                            next_params[param_name] = float(
                                np.clip(
                                    np.random.normal(mean_val, std_val * 0.2),
                                    min_val,
                                    max_val,
                                )
                            )
                        else:
                            next_params[param_name] = np.random.uniform(
                                min_val, max_val
                            )
                    else:
                        next_params[param_name] = np.random.uniform(min_val, max_val)

            # Evaluate objective function
            try:
                value = objective_function(next_params)
            except Exception:
                value = float("-inf")  # Penalize failed evaluations

            # Update best parameters
            if value > best_value:
                best_value = value
                best_params = next_params.copy()

            # Store history
            param_history.append(next_params)
            objective_history.append(value)

        # Store optimization results
        result = {
            "best_parameters": best_params,
            "best_objective_value": best_value,
            "parameter_history": param_history,
            "objective_history": objective_history,
            "protocol": self.protocol_name,
        }

        # Update optimizer state
        self.best_parameters = best_params
        self.best_performance = best_value
        self.optimization_history.append(result)

        return result

    def _expected_improvement_search(
        self,
        parameter_space: dict[str, tuple[float, float]],
        param_history: list,
        objective_history: list,
    ) -> dict[str, float]:
        """Select next point using expected improvement heuristic.

        Args:
            parameter_space: Dictionary mapping parameter names to (min, max) tuples
            param_history: History of parameter evaluations
            objective_history: History of objective values

        Returns:
            Next parameter set to evaluate
        """
        # Find best observed value
        best_value = max(objective_history)

        # Try several candidate points
        candidates = []
        ei_values = []

        for _ in range(20):
            # Generate random candidate
            candidate = {}
            for param_name, (min_val, max_val) in parameter_space.items():
                candidate[param_name] = np.random.uniform(min_val, max_val)
            candidates.append(candidate)

            # Estimate expected improvement
            # This is a simplified approximation
            predicted_value = self._simple_gp_predict(
                candidate, param_history, objective_history
            )
            uncertainty = self._simple_gp_uncertainty(candidate, param_history)

            # Calculate expected improvement
            if uncertainty > 0:
                improvement = predicted_value - best_value
                z = improvement / uncertainty
                ei = improvement * self._standard_normal_cdf(
                    z
                ) + uncertainty * self._standard_normal_pdf(z)
            else:
                ei = (
                    0 if predicted_value <= best_value else predicted_value - best_value
                )

            ei_values.append(ei)

        # Select candidate with highest expected improvement
        best_idx = np.argmax(ei_values)
        return candidates[best_idx]

    def _simple_gp_predict(
        self, candidate: dict[str, float], param_history: list, objective_history: list
    ) -> float:
        """Simple Gaussian process prediction.

        Args:
            candidate: Parameter set to predict
            param_history: History of parameter evaluations
            objective_history: History of objective values

        Returns:
            Predicted objective value
        """
        if not param_history:
            return 0.0

        # Convert to vectors
        param_names = list(candidate.keys())
        candidate_vector = np.array([candidate[name] for name in param_names])
        history_vectors = np.array(
            [[params[name] for name in param_names] for params in param_history]
        )

        # Calculate distances to historical points
        distances = np.linalg.norm(history_vectors - candidate_vector, axis=1)

        # Use inverse distance weighting
        # Add small epsilon to avoid division by zero
        weights = 1.0 / (distances + 1e-6)
        weights = weights / np.sum(weights)  # Normalize

        # Weighted average of historical values
        prediction = np.sum(weights * np.array(objective_history))
        return prediction

    def _simple_gp_uncertainty(
        self, candidate: dict[str, float], param_history: list
    ) -> float:
        """Simple Gaussian process uncertainty estimate.

        Args:
            candidate: Parameter set to evaluate
            param_history: History of parameter evaluations

        Returns:
            Uncertainty estimate
        """
        if not param_history:
            return 1.0

        # Convert to vectors
        param_names = list(candidate.keys())
        candidate_vector = np.array([candidate[name] for name in param_names])
        history_vectors = np.array(
            [[params[name] for name in param_names] for params in param_history]
        )

        # Calculate distances to historical points
        distances = np.linalg.norm(history_vectors - candidate_vector, axis=1)

        # Uncertainty is higher when far from historical points
        # Use minimum distance as a measure of uncertainty
        min_distance = np.min(distances)
        # Normalize and invert so that smaller distances mean lower uncertainty
        uncertainty = 1.0 / (1.0 + np.exp(-min_distance))
        return uncertainty

    def _standard_normal_cdf(self, x: float) -> float:
        """Standard normal cumulative distribution function."""
        return 0.5 * (1 + erf(x / np.sqrt(2)))

    def _standard_normal_pdf(self, x: float) -> float:
        """Standard normal probability density function."""
        return np.exp(-0.5 * x * x) / np.sqrt(2 * np.pi)

    def _genetic_algorithm_optimization(
        self,
        parameter_space: dict[str, tuple[float, float]],
        objective_function: Callable[[dict[str, float]], float],
        num_iterations: int,
    ) -> dict[str, Any]:
        """Genetic algorithm optimization for QKD parameters.

        Args:
            parameter_space: Dictionary mapping parameter names to (min, max) tuples
            objective_function: Function to maximize
            num_iterations: Number of optimization iterations

        Returns:
            Dictionary with optimization results
        """
        # Genetic algorithm parameters
        population_size = 20
        mutation_rate = 0.1
        crossover_rate = 0.8
        elitism_count = 2

        # Initialize population
        population = []
        for _ in range(population_size):
            individual = {}
            for param_name, (min_val, max_val) in parameter_space.items():
                individual[param_name] = np.random.uniform(min_val, max_val)
            population.append(individual)

        # Evaluate initial population
        fitness_scores = []
        for individual in population:
            try:
                fitness = objective_function(individual)
            except Exception:
                fitness = float("-inf")
            fitness_scores.append(fitness)

        # Track best solution
        best_idx = np.argmax(fitness_scores)
        best_params = population[best_idx].copy()
        best_fitness = fitness_scores[best_idx]

        # Evolution loop
        for _ in range(num_iterations):
            # Create new population
            new_population = []

            # Elitism: keep best individuals
            sorted_indices = np.argsort(fitness_scores)[::-1]
            for i in range(elitism_count):
                new_population.append(population[sorted_indices[i]].copy())

            # Generate offspring
            while len(new_population) < population_size:
                # Selection (tournament selection)
                parent1 = self._tournament_selection(population, fitness_scores, 3)
                parent2 = self._tournament_selection(population, fitness_scores, 3)

                # Crossover
                if np.random.random() < crossover_rate:
                    child1, child2 = self._uniform_crossover(parent1, parent2)
                else:
                    child1, child2 = parent1.copy(), parent2.copy()

                # Mutation
                self._mutate(child1, parameter_space, mutation_rate)
                self._mutate(child2, parameter_space, mutation_rate)

                # Add to new population
                new_population.append(child1)
                if len(new_population) < population_size:
                    new_population.append(child2)

            # Evaluate new population
            population = new_population
            fitness_scores = []
            for individual in population:
                try:
                    fitness = objective_function(individual)
                except Exception:
                    fitness = float("-inf")
                fitness_scores.append(fitness)

            # Update best solution
            best_idx = np.argmax(fitness_scores)
            if fitness_scores[best_idx] > best_fitness:
                best_fitness = fitness_scores[best_idx]
                best_params = population[best_idx].copy()

        # Store optimization results
        result = {
            "best_parameters": best_params,
            "best_objective_value": best_fitness,
            "final_population": population,
            "final_fitness_scores": fitness_scores,
            "protocol": self.protocol_name,
        }

        # Update optimizer state
        self.best_parameters = best_params
        self.best_performance = best_fitness
        self.optimization_history.append(result)

        return result

    def _tournament_selection(
        self,
        population: list[dict[str, float]],
        fitness_scores: list[float],
        tournament_size: int,
    ) -> dict[str, float]:
        """Tournament selection for genetic algorithm."""
        # Select random individuals for tournament
        indices = np.random.choice(len(population), tournament_size, replace=False)

        # Find the best individual in the tournament
        best_idx = indices[0]
        for idx in indices[1:]:
            if fitness_scores[idx] > fitness_scores[best_idx]:
                best_idx = idx

        return dict(population[best_idx].copy())

    def _uniform_crossover(
        self, parent1: dict[str, float], parent2: dict[str, float]
    ) -> tuple[dict[str, float], dict[str, float]]:
        """Uniform crossover for genetic algorithm."""
        child1 = {}
        child2 = {}

        for param_name in parent1:
            if np.random.random() < 0.5:
                child1[param_name] = parent1[param_name]
                child2[param_name] = parent2[param_name]
            else:
                child1[param_name] = parent2[param_name]
                child2[param_name] = parent1[param_name]

        return child1, child2

    def _mutate(
        self,
        individual: dict[str, float],
        parameter_space: dict[str, tuple[float, float]],
        mutation_rate: float,
    ) -> None:
        """Mutation operator for genetic algorithm."""
        for param_name, (min_val, max_val) in parameter_space.items():
            if np.random.random() < mutation_rate:
                # Gaussian mutation
                current_val = individual[param_name]
                mutation_strength = (max_val - min_val) * 0.1
                new_val = np.random.normal(current_val, mutation_strength)
                individual[param_name] = np.clip(new_val, min_val, max_val)

    def get_optimization_history(self) -> list[dict[str, Any]]:
        """Get the history of all optimizations.

        Returns:
            List of optimization results
        """
        return self.optimization_history.copy()

    def _neural_network_optimization(
        self,
        parameter_space: dict[str, tuple[float, float]],
        objective_function: Callable[[dict[str, float]], float],
        num_iterations: int,
    ) -> dict[str, Any]:
        """Neural network-based optimization for QKD parameters.

        Args:
            parameter_space: Dictionary mapping parameter names to (min, max) tuples
            objective_function: Function to maximize
            num_iterations: Number of optimization iterations

        Returns:
            Dictionary with optimization results
        """
        # Initialize training data
        X_train = []  # Parameter sets
        y_train = []  # Objective values

        # Initial random sampling to build training dataset
        initial_samples = min(20, num_iterations // 2)
        for _ in range(initial_samples):
            # Generate random parameters within bounds
            params = {}
            for param_name, (min_val, max_val) in parameter_space.items():
                params[param_name] = np.random.uniform(min_val, max_val)

            # Evaluate objective function
            try:
                value = objective_function(params)
            except Exception:
                value = float("-inf")  # Penalize failed evaluations

            # Add to training data
            param_vector = [params[name] for name in parameter_space.keys()]
            X_train.append(param_vector)
            y_train.append(value)

        # Find best initial solution
        best_idx = np.argmax(y_train)
        best_params = {}
        param_names = list(parameter_space.keys())
        for i, name in enumerate(param_names):
            best_params[name] = X_train[best_idx][i]
        best_value = y_train[best_idx]

        # Track history
        param_history = []
        objective_history = []
        for i in range(len(X_train)):
            params = {}
            for j, name in enumerate(param_names):
                params[name] = X_train[i][j]
            param_history.append(params)
            objective_history.append(y_train[i])

        # Perform optimization iterations
        for _iteration in range(num_iterations - initial_samples):
            # Train a simple neural network model
            model = self._train_simple_nn(X_train, y_train)

            # Use the model to guide search
            # Try several candidate solutions and select the most promising
            candidates = []
            predictions = []

            for _ in range(10):
                # Generate candidate parameters
                candidate = {}
                candidate_vector = []
                for param_name, (min_val, max_val) in parameter_space.items():
                    val = np.random.uniform(min_val, max_val)
                    candidate[param_name] = val
                    candidate_vector.append(val)

                # Predict performance using the model
                candidate_array = np.array(candidate_vector).reshape(1, -1)
                predicted_value = model(candidate_array)[0]

                candidates.append(candidate)
                predictions.append(predicted_value)

            # Select the most promising candidate
            best_candidate_idx = np.argmax(predictions)
            selected_candidate = candidates[best_candidate_idx]

            # Evaluate the selected candidate with the actual objective function
            try:
                actual_value = objective_function(selected_candidate)
            except Exception:
                actual_value = float("-inf")

            # Update training data
            candidate_vector = [
                selected_candidate[name] for name in parameter_space.keys()
            ]
            X_train.append(candidate_vector)
            y_train.append(actual_value)

            # Update best solution if needed
            if actual_value > best_value:
                best_value = actual_value
                best_params = selected_candidate.copy()

            # Update history
            param_history.append(selected_candidate)
            objective_history.append(actual_value)

        # Store optimization results
        result = {
            "best_parameters": best_params,
            "best_objective_value": best_value,
            "parameter_history": param_history,
            "objective_history": objective_history,
            "protocol": self.protocol_name,
        }

        # Update optimizer state
        self.best_parameters = best_params
        self.best_performance = best_value
        self.optimization_history.append(result)

        return result

    def _train_simple_nn(self, X_train: list, y_train: list) -> Callable:
        """Train a simple neural network model.

        Args:
            X_train: Training input data
            y_train: Training target data

        Returns:
            A function that can make predictions
        """
        # Convert to numpy arrays
        X = np.array(X_train)
        y = np.array(y_train)

        # Normalize inputs
        X_mean = np.mean(X, axis=0)
        X_std = np.std(X, axis=0)
        X_std[X_std == 0] = 1  # Avoid division by zero
        X_norm = (X - X_mean) / X_std

        # Normalize outputs
        y_mean = np.mean(y)
        y_std = np.std(y)
        y_std = y_std if y_std > 0 else 1  # Avoid division by zero
        y_norm = (y - y_mean) / y_std

        # Simple neural network with one hidden layer
        input_dim = X.shape[1]
        hidden_dim = 10
        output_dim = 1

        # Initialize weights randomly
        W1 = np.random.randn(input_dim, hidden_dim) * 0.1
        b1 = np.zeros(hidden_dim)
        W2 = np.random.randn(hidden_dim, output_dim) * 0.1
        b2 = np.zeros(output_dim)

        # Training parameters
        learning_rate = 0.01
        epochs = 100

        # Training loop
        for _ in range(epochs):
            # Forward pass
            z1 = X_norm @ W1 + b1
            a1 = np.tanh(z1)  # Activation function
            z2 = a1 @ W2 + b2
            predictions = z2.flatten()

            # Compute loss (mean squared error)
            _loss = np.mean((predictions - y_norm) ** 2)

            # Backward pass - Corrected gradient computation
            m = len(y_norm)  # Number of samples

            # Gradients for output layer
            dZ2 = (predictions - y_norm) / m  # Shape: (m,)
            dW2 = a1.T @ dZ2.reshape(-1, 1)  # Shape: (hidden_dim, 1)
            db2 = np.sum(dZ2)  # Shape: scalar

            # Gradients for hidden layer
            dA1 = dZ2.reshape(-1, 1) @ W2.T  # Shape: (m, hidden_dim)
            dZ1 = dA1 * (1 - np.tanh(z1) ** 2)  # Shape: (m, hidden_dim)
            dW1 = X_norm.T @ dZ1  # Shape: (input_dim, hidden_dim)
            db1 = np.sum(dZ1, axis=0)  # Shape: (hidden_dim,)

            # Update weights
            W2 -= learning_rate * dW2
            b2 -= learning_rate * db2
            W1 -= learning_rate * dW1
            b1 -= learning_rate * db1

        # Return prediction function
        def predict(X_test):
            X_test_norm = (X_test - X_mean) / X_std
            z1 = X_test_norm @ W1 + b1
            a1 = np.tanh(z1)
            z2 = a1 @ W2 + b2
            predictions = z2.flatten() * y_std + y_mean  # Denormalize
            return predictions

        return predict

    def predict_performance(self, parameters: dict[str, float]) -> float:
        """Predict protocol performance for given parameters using trained model.

        Args:
            parameters: Protocol parameters

        Returns:
            Predicted performance metric
        """
        # If we have a trained model, use it for prediction
        if self.model is not None:
            # Convert parameters to vector
            param_names = list(parameters.keys())
            param_vector = [parameters[name] for name in param_names]
            X = np.array(param_vector).reshape(1, -1)
            return self.model(X)[0]

        # If no model is trained, return a simple heuristic
        # This is a placeholder - in a real implementation, we would:
        # 1. Train a model on historical protocol performance data
        # 2. Use the model to predict performance for new parameters
        # 3. Return the prediction
        return 0.0  # Placeholder


class QKDAnomalyDetector:
    """Anomaly detection for QKD systems using machine learning."""

    def __init__(self) -> None:
        """Initialize the anomaly detector."""
        self.baseline_statistics: dict[str, dict[str, float]] = {}
        self.anomaly_threshold: float = 0.05  # 5% threshold
        self.detection_history: list[dict[str, Any]] = []

    def establish_baseline(self, metrics_history: list[dict[str, float]]) -> None:
        """Establish baseline statistics from historical data.

        Args:
            metrics_history: List of historical metric dictionaries
        """
        if not metrics_history:
            return

        # Calculate statistics for each metric
        all_metrics: set[str] = set()
        for metrics in metrics_history:
            all_metrics.update(metrics.keys())

        self.baseline_statistics = {}
        for metric in all_metrics:
            values = [
                metrics[metric] for metrics in metrics_history if metric in metrics
            ]
            if values:
                self.baseline_statistics[metric] = {
                    "mean": float(np.mean(values)),
                    "std": float(np.std(values)),
                    "min": float(np.min(values)),
                    "max": float(np.max(values)),
                }

    def detect_anomalies(self, current_metrics: dict[str, float]) -> dict[str, bool]:
        """Detect anomalies in current metrics.

        Args:
            current_metrics: Current metric values

        Returns:
            Dictionary mapping metric names to anomaly flags
        """
        anomalies = {}

        for metric, value in current_metrics.items():
            if metric in self.baseline_statistics:
                stats = self.baseline_statistics[metric]
                # Simple statistical anomaly detection
                # Check if value is outside mean ± 3*std
                if stats["std"] > 0:
                    z_score = abs(value - stats["mean"]) / stats["std"]
                    anomalies[metric] = z_score > 3
                else:
                    # If std is 0, check if value differs from mean
                    anomalies[metric] = value != stats["mean"]
            else:
                # No baseline for this metric
                anomalies[metric] = False

        # Store detection result
        self.detection_history.append(
            {
                "timestamp": len(self.detection_history),
                "metrics": current_metrics,
                "anomalies": anomalies,
            }
        )

        return anomalies

    def update_anomaly_threshold(self, new_threshold: float) -> None:
        """Update the anomaly detection threshold.

        Args:
            new_threshold: New threshold value (0.0 to 1.0)
        """
        self.anomaly_threshold = max(0.0, min(1.0, new_threshold))

    def get_detection_report(self) -> dict[str, Any]:
        """Generate a report of anomaly detection results.

        Returns:
            Dictionary with detection statistics
        """
        if not self.detection_history:
            return {"error": "No detection history"}

        # Count anomalies by metric
        anomaly_counts: dict[str, int] = {}
        total_detections = len(self.detection_history)

        for detection in self.detection_history:
            for metric, is_anomaly in detection["anomalies"].items():
                if is_anomaly:
                    anomaly_counts[metric] = anomaly_counts.get(metric, 0) + 1

        # Calculate anomaly rates
        anomaly_rates = {}
        for metric, count in anomaly_counts.items():
            anomaly_rates[metric] = float(count / total_detections)

        return {
            "total_detections": float(total_detections),
            "anomaly_counts": {
                metric: float(count) for metric, count in anomaly_counts.items()
            },
            "anomaly_rates": anomaly_rates,
            "baseline_metrics": list(self.baseline_statistics.keys()),
        }
