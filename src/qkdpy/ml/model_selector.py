"""Automatic model selection based on device capabilities.

This module provides a selector that picks a sensible model configuration
based on the host memory detected at runtime.
"""

from ..utils.logging_config import get_logger
from .efficient_models import EfficientQKDPredictor

logger = get_logger(__name__)


class AdaptiveModelSelector:
    """Automatically select appropriate model based on device capabilities."""

    @staticmethod
    def get_available_memory_mb() -> int:
        """Estimate available memory in MB.

        Returns:
            Estimated available memory
        """
        try:
            import psutil

            return int(psutil.virtual_memory().available / (1024 * 1024))
        except ImportError:
            # Conservative fallback when psutil is unavailable.
            return 256

    @staticmethod
    def create_optimal_predictor(
        input_dim: int,
        *,
        use_quantization: bool | None = None,
    ) -> EfficientQKDPredictor:
        """Create predictor with optimal settings for current device.

        Args:
            input_dim: Number of input features
            use_quantization: Override quantization setting

        Returns:
            Optimally configured predictor
        """
        available_mb = AdaptiveModelSelector.get_available_memory_mb()
        max_memory = min(available_mb // 4, 512)

        if use_quantization is None:
            use_quantization = available_mb < 1024

        logger.info(
            "Creating adaptive predictor",
            available_memory_mb=available_mb,
            allocated_memory_mb=max_memory,
            quantization=use_quantization,
        )

        return EfficientQKDPredictor(
            input_dim,
            max_memory_mb=max_memory,
            enable_quantization=use_quantization,
        )
