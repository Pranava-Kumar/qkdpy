from qkdpy.ml.qkd_optimizer import QKDOptimizer


def objective_function(params):
    """Simple objective function: -(x-2)^2 - (y-3)^2 + 10. Max at (2, 3)."""
    x = params["x"]
    y = params["y"]
    return -((x - 2) ** 2) - ((y - 3) ** 2) + 10


def test_bayesian_optimization():
    """Test Bayesian optimization."""
    optimizer = QKDOptimizer("TestProtocol")

    param_space = {"x": (0.0, 5.0), "y": (0.0, 5.0)}

    result = optimizer.optimize_channel_parameters(
        param_space, objective_function, num_iterations=20, method="bayesian"
    )

    best_params = result["best_parameters"]
    best_val = result["best_objective_value"]

    # Should be close to max value 10
    assert best_val > 8.0
    # Parameters should be close to (2, 3)
    assert 1.0 < best_params["x"] < 3.0
    assert 2.0 < best_params["y"] < 4.0


def test_neural_optimization():
    """Test Neural Network optimization."""
    optimizer = QKDOptimizer("TestProtocol")

    param_space = {"x": (0.0, 5.0), "y": (0.0, 5.0)}

    result = optimizer.optimize_channel_parameters(
        param_space, objective_function, num_iterations=20, method="neural"
    )

    best_val = result["best_objective_value"]
    assert (
        best_val > 5.0
    )  # Neural might need more iters, but should find decent solution
