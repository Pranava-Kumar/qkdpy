"""Efficient neural network models for resource-constrained QKD deployment.

This module provides lightweight, resource-aware neural network architectures
that can run efficiently on devices with limited memory and compute resources.
"""

from typing import Any

import numpy as np

from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class EfficientQKDPredictor:
    """Resource-efficient predictor for QKD parameter optimization.

    Uses adaptive architecture that scales based on available resources,
    with support for model quantization and pruning.
    """

    def __init__(
        self,
        input_dim: int,
        *,
        max_memory_mb: int = 256,
        enable_quantization: bool = True,
        enable_pruning: bool = True,
        pruning_threshold: float = 0.01,
        seed: int | None = None,
    ) -> None:
        """Initialize efficient predictor.

        Args:
            input_dim: Number of input features
            max_memory_mb: Maximum memory budget in MB
            enable_quantization: Whether to use INT8 quantization for inference
            enable_pruning: Whether to prune small weights
            pruning_threshold: Threshold for weight pruning
            seed: Optional seed for reproducible weight initialization and training shuffles.  When ``None`` a cryptographically secure seed is derived from :mod:`secrets` so consecutive instances produce different results (avoids accidental correlation).
        """
        self.input_dim = input_dim
        self.max_memory_mb = max_memory_mb
        self.enable_quantization = enable_quantization
        self.enable_pruning = enable_pruning
        self.pruning_threshold = pruning_threshold

        # Per-instance RNG seeded from CSPRNG (or explicit seed) so that
        # weight initialisation and training shuffles are reproducible when
        # a seed is supplied, and independent across instances otherwise.
        import secrets

        if seed is None:
            seed = secrets.randbits(32)
        self._seed = seed
        self._rng = np.random.default_rng(seed)

        # Determine architecture based on memory budget
        self.hidden_layers = self._calculate_architecture()

        # Initialize weights
        self.weights: list[np.ndarray] = []
        self.biases: list[np.ndarray] = []
        self._initialize_weights()

        # Training state
        self.is_trained = False
        self._training_history: list[float] = []

        # Normalization parameters
        self._input_mean: np.ndarray | None = None
        self._input_std: np.ndarray | None = None
        self._output_mean: float = 0.0
        self._output_std: float = 1.0

        logger.info(
            "Initialized EfficientQKDPredictor",
            input_dim=input_dim,
            hidden_layers=self.hidden_layers,
            memory_budget_mb=max_memory_mb,
        )

    def _calculate_architecture(self) -> list[int]:
        """Calculate optimal architecture based on memory budget.

        Returns:
            List of hidden layer sizes
        """
        # Estimate bytes per parameter (float32 = 4 bytes, quantized int8 = 1 byte)
        bytes_per_param = 1 if self.enable_quantization else 4

        # Target: use at most 50% of memory budget for weights
        max_params = (self.max_memory_mb * 1024 * 1024 * 0.5) / bytes_per_param

        # Start with minimal architecture and grow
        hidden_sizes = [16]  # Minimum single hidden layer

        # Calculate current parameter count
        def count_params(layers: list[int]) -> int:
            total = 0
            prev_size = self.input_dim
            for size in layers:
                total += prev_size * size + size  # weights + biases
                prev_size = size
            total += prev_size + 1  # Output layer
            return total

        # Try to add more capacity if budget allows
        for candidate in [[32], [32, 16], [64, 32], [64, 32, 16], [128, 64, 32]]:
            if count_params(candidate) <= max_params:
                hidden_sizes = candidate

        return hidden_sizes

    def _initialize_weights(self) -> None:
        """Initialize network weights using Xavier initialization."""
        self.weights = []
        self.biases = []

        prev_size = self.input_dim
        for hidden_size in self.hidden_layers:
            # Xavier initialization
            scale = np.sqrt(2.0 / (prev_size + hidden_size))
            self.weights.append(
                self._rng.standard_normal((prev_size, hidden_size)).astype(np.float32)
                * scale
            )
            self.biases.append(np.zeros(hidden_size, dtype=np.float32))
            prev_size = hidden_size

        # Output layer (single value)
        scale = np.sqrt(2.0 / (prev_size + 1))
        self.weights.append(
            self._rng.standard_normal((prev_size, 1)).astype(np.float32) * scale
        )
        self.biases.append(np.zeros(1, dtype=np.float32))

    def _relu(self, x: np.ndarray) -> np.ndarray:
        """ReLU activation function."""
        result: np.ndarray = np.maximum(0, x)
        return result

    def _relu_derivative(self, x: np.ndarray) -> np.ndarray:
        """Derivative of ReLU activation function."""
        return (x > 0).astype(np.float32)

    def _forward(
        self, X: np.ndarray
    ) -> tuple[np.ndarray, list[np.ndarray], list[np.ndarray]]:
        """Forward pass through the network.

        Args:
            X: Input data

        Returns:
            Tuple of (output, post-activation list per layer including input, pre-activation list per hidden layer).
            pre_activations[i] corresponds to the input of layer i+1 (i.e. the value fed into ReLU
            to produce activations[i+1]) and is needed by _backward to compute ReLU derivatives.
            The pre-activation list excludes the input itself, so its length equals
            len(activations) - 1.
        """
        activations: list[np.ndarray] = [X]
        pre_activations: list[np.ndarray] = []
        current = X

        for W, b in zip(self.weights[:-1], self.biases[:-1], strict=True):
            z = current @ W + b
            pre_activations.append(z)
            current = self._relu(z)
            activations.append(current)

        # Output layer (linear; no activation, no pre-activation stored)
        output = current @ self.weights[-1] + self.biases[-1]
        return output, activations, pre_activations

    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        *,
        epochs: int = 100,
        learning_rate: float = 0.01,
        batch_size: int | None = None,
        early_stopping_patience: int = 10,
        validation_split: float = 0.1,
    ) -> dict[str, Any]:
        """Train the model with early stopping.

        Args:
            X: Input features (n_samples, n_features)
            y: Target values (n_samples,)
            epochs: Maximum number of epochs
            learning_rate: Learning rate
            batch_size: Batch size (None for full batch)
            early_stopping_patience: Epochs to wait before early stopping
            validation_split: Fraction of data for validation

        Returns:
            Training history and statistics
        """
        # Normalize inputs
        self._input_mean = np.mean(X, axis=0)
        self._input_std = np.std(X, axis=0)
        self._input_std[self._input_std == 0] = 1.0
        X_norm = (X - self._input_mean) / self._input_std

        # Normalize outputs
        self._output_mean = float(np.mean(y))
        self._output_std = float(np.std(y))
        if self._output_std == 0:
            self._output_std = 1.0
        y_norm = (y - self._output_mean) / self._output_std

        # Split data
        n_samples = len(X)
        n_val = int(n_samples * validation_split)
        indices = self._rng.permutation(n_samples)

        X_train = X_norm[indices[n_val:]]
        y_train = y_norm[indices[n_val:]]
        X_val = X_norm[indices[:n_val]] if n_val > 0 else X_train
        y_val = y_norm[indices[:n_val]] if n_val > 0 else y_train

        if batch_size is None:
            batch_size = len(X_train)

        best_val_loss = float("inf")
        patience_counter = 0
        best_weights = [w.copy() for w in self.weights]
        best_biases = [b.copy() for b in self.biases]

        self._training_history = []

        for epoch in range(epochs):
            # Shuffle training data
            perm = self._rng.permutation(len(X_train))
            X_train = X_train[perm]
            y_train = y_train[perm]

            # Mini-batch training
            epoch_loss = 0.0
            n_batches = 0

            for i in range(0, len(X_train), batch_size):
                X_batch = X_train[i : i + batch_size]
                y_batch = y_train[i : i + batch_size]

                # Forward pass
                output, activations, pre_activations = self._forward(X_batch)

                # Compute loss
                loss = np.mean((output.flatten() - y_batch) ** 2)
                epoch_loss += float(loss)
                n_batches += 1

                # Backward pass
                self._backward(
                    X_batch,
                    y_batch,
                    output,
                    activations,
                    pre_activations,
                    learning_rate,
                )

            epoch_loss /= n_batches
            self._training_history.append(epoch_loss)

            # Validation
            val_output, _, _ = self._forward(X_val)
            val_loss = float(np.mean((val_output.flatten() - y_val) ** 2))

            # Early stopping check
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                best_weights = [w.copy() for w in self.weights]
                best_biases = [b.copy() for b in self.biases]
            else:
                patience_counter += 1
                if patience_counter >= early_stopping_patience:
                    logger.info(
                        "Early stopping triggered",
                        epoch=epoch,
                        best_val_loss=best_val_loss,
                    )
                    break

        # Restore best weights
        self.weights = best_weights
        self.biases = best_biases

        # Apply pruning if enabled
        if self.enable_pruning:
            self._prune_weights()

        self.is_trained = True

        return {
            "epochs_trained": len(self._training_history),
            "final_train_loss": self._training_history[-1],
            "best_val_loss": best_val_loss,
            "training_history": self._training_history,
        }

    def _backward(
        self,
        X: np.ndarray,
        y: np.ndarray,
        output: np.ndarray,
        activations: list[np.ndarray],
        pre_activations: list[np.ndarray],
        learning_rate: float,
    ) -> None:
        """Backward pass for gradient computation and weight update.

        Uses pre-activations cached during the forward pass (rather than recomputing them from
        the post-ReLU activations) so the ReLU derivative matches the activations used to
        compute the layer's inputs exactly.
        """
        batch_size = len(X)

        # Output layer gradient (linear output, MSE loss; derivative of MSE w.r.t. output is
        # 2*(pred - y)/batch; we treat the factor-of-2 as absorbed in learning_rate scaling).
        delta = (output.flatten() - y) / batch_size
        delta = delta.reshape(-1, 1)

        # Update output layer
        dW = activations[-1].T @ delta
        db = np.sum(delta, axis=0)
        self.weights[-1] -= learning_rate * dW
        self.biases[-1] -= learning_rate * db

        # Backpropagate through hidden layers using cached pre-activations.
        # pre_activations[i] is the input to the ReLU that produced activations[i+1],
        # for layer i (the i-th hidden layer, 0-indexed).
        n_hidden = len(self.weights) - 1
        for i in range(n_hidden - 1, -1, -1):
            # Gradient flowing back from the next layer times the local ReLU derivative
            # evaluated at the *cached* pre-activation. pre_activations[i] has shape
            # (batch, hidden_i); the ReLU derivative must broadcast across batch.
            relu_d = self._relu_derivative(pre_activations[i])
            delta = delta @ self.weights[i + 1].T * relu_d
            dW = activations[i].T @ delta
            db = np.sum(delta, axis=0)

            self.weights[i] -= learning_rate * dW
            self.biases[i] -= learning_rate * db

    def _prune_weights(self) -> None:
        """Prune weights below threshold to zero."""
        total_pruned = 0
        total_weights = 0

        for W in self.weights:
            mask = np.abs(W) < self.pruning_threshold
            total_pruned += int(np.sum(mask))
            total_weights += W.size
            W[mask] = 0.0

        pruning_ratio = total_pruned / total_weights if total_weights > 0 else 0
        logger.info(
            "Weight pruning complete",
            pruning_ratio=f"{pruning_ratio:.2%}",
            weights_pruned=int(total_pruned),
        )

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions.

        Args:
            X: Input features

        Returns:
            Predicted values
        """
        if not self.is_trained:
            logger.warning("Model not trained, predictions may be unreliable")

        # Normalize input
        if self._input_mean is not None and self._input_std is not None:
            X_norm = (X - self._input_mean) / self._input_std
        else:
            X_norm = X

        # Forward pass
        output, _, _ = self._forward(X_norm)

        # Denormalize output (keep float32 to match internal precision)
        predictions = output.flatten() * self._output_std + self._output_mean

        return predictions.astype(np.float32, copy=False)

    def get_model_size_bytes(self) -> int:
        """Get model size in bytes."""
        total = 0
        for W in self.weights:
            total += W.nbytes
        for b in self.biases:
            total += b.nbytes
        return total

    def get_sparsity(self) -> float:
        """Get fraction of zero weights (sparsity)."""
        total_zeros = 0
        total_weights = 0
        for W in self.weights:
            total_zeros += np.sum(W == 0)
            total_weights += W.size
        return total_zeros / total_weights if total_weights > 0 else 0
