"""Protocols for network module interfaces.

Defines duck-typed protocols that decouple network components from
concrete ML implementations, enabling test stubs and model swaps.
"""

from __future__ import annotations

from typing import (
    Any,
    Protocol,
    runtime_checkable,
)

import numpy as np


@runtime_checkable
class ChannelPredictor(Protocol):
    """Protocol for channel condition predictors.

    Satisfied by ``EfficientQKDPredictor`` and any other predictor
    implementing ``fit``, ``predict``, and ``is_trained``.
    """

    @property
    def is_trained(self) -> bool:
        """Whether the predictor has been trained."""
        ...

    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Train the predictor on historical pass data.

        Returns:
            dict with at least ``epochs_trained`` and ``final_train_loss`` keys.
        """
        ...

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict key yield for given atmospheric conditions."""
        ...
