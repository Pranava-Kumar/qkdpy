"""ML optimizer bridge for the qpiai-qkd companion.

Wraps qkdpy's :class:`ml.qkd_optimizer.QKDOptimizer` and
:class:`ml.qkd_optimizer.QKDAnomalyDetector` so a researcher can tune QKD
channel parameters and flag anomalous link behaviour from a protocol run.

The optimizer supports several strategies (``bayesian``, ``genetic``,
``neural``, ``gradient``). We report which one actually ran — no strategy is
claimed to be superior without being the one executed.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypedDict, cast

from qkdpy.ml.qkd_optimizer import QKDAnomalyDetector, QKDOptimizer

__all__ = [
    "OptimizerResult",
    "ParameterHistoryEntry",
    "AnomalyReport",
    "optimize_protocol",
    "detect_anomaly",
    "list_strategies",
]


class ParameterHistoryEntry(TypedDict):
    """A single parameter set evaluated during optimisation."""

    # Each key is a parameter name; values are the float value at that iteration.
    # The exact keys depend on the parameter_space passed to the optimizer.
    ...


class OptimizerResult(TypedDict, total=False):
    """Typed description of the dict returned by :func:`optimize_protocol`.

    Keys tagged *method-specific* only appear for certain strategies:

    * ``parameter_history`` / ``objective_history`` — Bayesian, Neural
    * ``final_population`` / ``final_fitness_scores`` — Genetic

    The ``method`` key is always injected by the companion wrapper.
    """

    best_parameters: dict[str, float]
    """The parameter set that maximised the objective."""
    best_objective_value: float
    """Highest objective value found."""
    protocol: str
    """Protocol name passed to the optimizer."""
    method: str
    """Strategy that was executed (e.g. ``"bayesian"``)."""
    # -- Bayesian / Neural only --
    parameter_history: list[ParameterHistoryEntry]
    """Every parameter set evaluated, in order."""
    objective_history: list[float]
    """Objective value at each evaluation, aligned with parameter_history."""
    # -- Genetic only --
    final_population: list[dict[str, float]]
    """Final generation's parameter sets."""
    final_fitness_scores: list[float]
    """Fitness of each member in the final population."""


class AnomalyReport(TypedDict):
    """Maps each metric name to whether it is anomalous."""

    # Each key is a metric name (e.g. "qber"); the bool is True if anomalous.
    ...


def list_strategies() -> list[str]:
    """Return the optimization strategies the underlying optimizer supports."""
    return ["bayesian", "genetic", "neural", "gradient"]


def optimize_protocol(
    protocol_name: str,
    parameter_space: dict[str, tuple[float, float]],
    objective_function: Callable[[dict[str, float]], float],
    num_iterations: int = 100,
    method: str = "bayesian",
) -> OptimizerResult:
    """Tune channel parameters for a QKD protocol via ML.

    Args:
        protocol_name: Protocol to optimize (e.g. "BB84", "E91").
        parameter_space: ``{param: (min, max)}`` bounds.
        objective_function: Callable to maximize (e.g. secret-key rate).
        num_iterations: Optimization iterations.
        method: Strategy — one of :func:`list_strategies`.

    Returns:
        Optimization result dict (includes ``method`` so the executed strategy
        is explicit).
    """
    if method not in list_strategies():
        raise ValueError(
            f"Unknown optimization method '{method}'. Choose from {list_strategies()}."
        )
    optimizer = QKDOptimizer(protocol_name)
    result = optimizer.optimize_channel_parameters(
        parameter_space=parameter_space,
        objective_function=objective_function,
        num_iterations=num_iterations,
        method=method,
    )
    result["method"] = method  # make the executed strategy explicit
    return cast(OptimizerResult, result)


def detect_anomaly(metrics: dict[str, float]) -> AnomalyReport:
    """Flag anomalous QKD link metrics against a baseline.

    Args:
        metrics: Current per-feature metrics (e.g. ``{"qber": 0.08}``).

    Returns:
        Dict mapping metric names to anomaly flags (Z-score > 3 from baseline).
    """
    detector = QKDAnomalyDetector()
    return cast(AnomalyReport, detector.detect_anomalies(metrics))
