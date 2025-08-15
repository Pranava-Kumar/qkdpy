"""Machine learning tools for QKD optimization and analysis."""

from typing import Any

import numpy as np


class QKDOptimizer:
    """Machine learning-based optimizer for QKD protocols."""

    def __init__(self, protocol_name: str):
        """Initialize the QKD optimizer.

        Args:
            protocol_name: Name of the QKD protocol to optimize
        """
        self.protocol_name = protocol_name
        self.optimization_history = []
        self.best_parameters = {}
        self.best_performance = 0.0

    def optimize_channel_parameters(
        self,
        parameter_space: dict[str, tuple[float, float]],
        objective_function,
        num_iterations: int = 100,
        method: str = "bayesian",
    ) -> dict[str, Any]:
        """Optimize quantum channel parameters using machine learning.

        Args:
            parameter_space: Dictionary mapping parameter names to (min, max) tuples
            objective_function: Function to maximize (e.g., key rate, security)
            num_iterations: Number of optimization iterations
            method: Optimization method ('bayesian', 'genetic', 'gradient')

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
        else:
            raise ValueError(f"Unsupported optimization method: {method}")

    def _bayesian_optimization(
        self,
        parameter_space: dict[str, tuple[float, float]],
        objective_function,
        num_iterations: int,
    ) -> dict[str, Any]:
        """Bayesian optimization for QKD parameters.

        Args:
            parameter_space: Dictionary mapping parameter names to (min, max) tuples
            objective_function: Function to maximize
            num_iterations: Number of optimization iterations

        Returns:
            Dictionary with optimization results
        """
        # Simplified Bayesian optimization implementation
        # In a real implementation, this would use Gaussian processes

        # Initialize with random samples
        best_params = {}
        best_value = float("-inf")

        # Track parameter values and objective values
        param_history = []
        objective_history = []

        # Initial random sampling
        for _ in range(min(10, num_iterations)):
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

        # Simulated Bayesian optimization iterations
        for _ in range(num_iterations - min(10, num_iterations)):
            # In a real implementation, we would:
            # 1. Fit a Gaussian process model to the data
            # 2. Calculate acquisition function (e.g., expected improvement)
            # 3. Select next point to evaluate

            # For this simplified version, we'll use a random search with bias toward better regions
            params = {}
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
                        params[param_name] = np.clip(
                            np.random.normal(mean_val, std_val * 0.2), min_val, max_val
                        )
                    else:
                        params[param_name] = np.random.uniform(min_val, max_val)
                else:
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

    def _genetic_algorithm_optimization(
        self,
        parameter_space: dict[str, tuple[float, float]],
        objective_function,
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

        return population[best_idx].copy()

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
    ):
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

    def predict_performance(self, parameters: dict[str, float]) -> float:
        """Predict protocol performance for given parameters.

        In a real implementation, this would use a trained ML model.
        For now, we'll return a placeholder value.

        Args:
            parameters: Protocol parameters

        Returns:
            Predicted performance metric
        """
        # This is a placeholder - in a real implementation, we would:
        # 1. Train a model on historical protocol performance data
        # 2. Use the model to predict performance for new parameters
        # 3. Return the prediction
        return 0.0  # Placeholder


class QKDAnomalyDetector:
    """Anomaly detection for QKD systems using machine learning."""

    def __init__(self):
        """Initialize the anomaly detector."""
        self.baseline_statistics = {}
        self.anomaly_threshold = 0.05  # 5% threshold
        self.detection_history = []

    def establish_baseline(self, metrics_history: list[dict[str, float]]):
        """Establish baseline statistics from historical data.

        Args:
            metrics_history: List of historical metric dictionaries
        """
        if not metrics_history:
            return

        # Calculate statistics for each metric
        all_metrics = set()
        for metrics in metrics_history:
            all_metrics.update(metrics.keys())

        self.baseline_statistics = {}
        for metric in all_metrics:
            values = [
                metrics[metric] for metrics in metrics_history if metric in metrics
            ]
            if values:
                self.baseline_statistics[metric] = {
                    "mean": np.mean(values),
                    "std": np.std(values),
                    "min": np.min(values),
                    "max": np.max(values),
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

    def update_anomaly_threshold(self, new_threshold: float):
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
        anomaly_counts = {}
        total_detections = len(self.detection_history)

        for detection in self.detection_history:
            for metric, is_anomaly in detection["anomalies"].items():
                if is_anomaly:
                    anomaly_counts[metric] = anomaly_counts.get(metric, 0) + 1

        # Calculate anomaly rates
        anomaly_rates = {}
        for metric, count in anomaly_counts.items():
            anomaly_rates[metric] = count / total_detections

        return {
            "total_detections": total_detections,
            "anomaly_counts": anomaly_counts,
            "anomaly_rates": anomaly_rates,
            "baseline_metrics": list(self.baseline_statistics.keys()),
        }
