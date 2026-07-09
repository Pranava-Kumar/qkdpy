"""Knowledge distillation for transferring from large to small models.

This module provides a teacher-student paradigm to train smaller, efficient
models that approximate the behavior of larger, more accurate models.
"""

from collections.abc import Callable
from typing import Any

import numpy as np

from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class KnowledgeDistillation:
    """Knowledge distillation for transferring from large to small models.

    Uses a teacher-student paradigm to train smaller, efficient models
    that approximate the behavior of larger, more accurate models.
    """

    def __init__(
        self,
        teacher_predict: Callable[[np.ndarray], np.ndarray],
        temperature: float = 2.0,
        alpha: float = 0.5,
    ) -> None:
        """Initialize knowledge distillation.

        Args:
            teacher_predict: Teacher model's predict function
            temperature: Softening temperature for soft targets
            alpha: Weight for distillation loss vs hard label loss
        """
        self.teacher_predict = teacher_predict
        self.temperature = temperature
        self.alpha = alpha

    def generate_soft_targets(self, X: np.ndarray) -> np.ndarray:
        """Generate soft targets from teacher model.

        Args:
            X: Input data

        Returns:
            Soft targets from teacher
        """
        return self.teacher_predict(X)

    def distill(
        self,
        student,
        X_train: np.ndarray,
        y_train: np.ndarray,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Train student model using knowledge distillation.

        Args:
            student: Student model to train (an EfficientQKDPredictor)
            X_train: Training input data
            y_train: Hard labels (ground truth)
            **kwargs: Additional training arguments

        Returns:
            Training results
        """
        soft_targets = self.generate_soft_targets(X_train)
        combined_targets = self.alpha * soft_targets + (1 - self.alpha) * y_train
        return student.fit(X_train, combined_targets, **kwargs)
