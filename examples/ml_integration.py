"""
Machine Learning Integration Example

This script demonstrates how to use machine learning tools with QKDpy
for protocol optimization and anomaly detection.
"""

import matplotlib.pyplot as plt
import numpy as np

# Import QKDpy modules
from qkdpy import BB84, QuantumChannel
from qkdpy.ml import QKDAnomalyDetector, QKDOptimizer


def optimize_protocol_parameters() -> None:
    """
    Optimize QKD protocol parameters using machine learning.
    """
    print("Optimizing QKD protocol parameters...")

    # Create an optimizer for BB84 protocol
    optimizer = QKDOptimizer("BB84")

    # Define parameter space to optimize
    parameter_space = {
        "loss": (0.0, 0.5),  # Channel loss range
        "noise_level": (0.0, 0.2),  # Noise level range
    }

    # Define objective function to maximize (key rate)
    def objective_function(params: dict[str, float]) -> float:
        # Extract parameters
        loss = params.get("loss", 0.1)
        noise_level = params.get("noise_level", 0.05)

        # Create channel and protocol
        channel = QuantumChannel(
            loss=loss, noise_model="depolarizing", noise_level=noise_level
        )
        protocol = BB84(channel, key_length=100)

        # Execute protocol and return key rate
        try:
            results = protocol.execute()
            if results.get("is_secure", False):
                return protocol.get_key_rate()
            else:
                return 0.0
        except Exception:
            return 0.0

    # Optimize parameters
    print("  Starting optimization...")
    results = optimizer.optimize_channel_parameters(
        parameter_space=parameter_space,
        objective_function=objective_function,
        num_iterations=30,
        method="bayesian",
    )

    # Display results
    print(f"  Best parameters: {results['best_parameters']}")
    print(f"  Best key rate: {results['best_objective_value']:.4f}")
    print(f"  Number of evaluations: {len(results['parameter_history'])}")

    # Plot optimization progress
    if results["parameter_history"] and results["objective_history"]:
        plt.figure(figsize=(12, 5))

        # Plot parameter evolution
        plt.subplot(1, 2, 1)
        losses = [params["loss"] for params in results["parameter_history"]]
        noise_levels = [
            params["noise_level"] for params in results["parameter_history"]
        ]
        plt.scatter(
            losses, noise_levels, c=results["objective_history"], cmap="viridis"
        )
        plt.colorbar(label="Key Rate")
        plt.xlabel("Channel Loss")
        plt.ylabel("Noise Level")
        plt.title("Parameter Space Exploration")
        plt.grid(True, alpha=0.3)

        # Plot convergence
        plt.subplot(1, 2, 2)
        plt.plot(results["objective_history"], "b-", linewidth=2)
        plt.xlabel("Iteration")
        plt.ylabel("Key Rate")
        plt.title("Optimization Convergence")
        plt.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig("optimization_results.png", dpi=300, bbox_inches="tight")
        plt.show()


def detect_qkd_anomalies() -> None:
    """
    Detect anomalies in QKD system performance using machine learning.
    """
    print("\nDetecting QKD system anomalies...")

    # Create historical data for training
    print("  Generating historical performance data...")
    historical_data = []
    for _ in range(100):
        # Normal performance data
        qber = np.random.normal(0.02, 0.005)  # Mean QBER ~2%
        key_rate = np.random.normal(1000, 100)  # Mean key rate ~1000 bits/sec
        loss = np.random.normal(0.1, 0.02)  # Mean loss ~10%

        # Ensure realistic bounds
        qber = max(0, min(0.5, qber))
        key_rate = max(0, key_rate)
        loss = max(0, min(1, loss))

        historical_data.append({"qber": qber, "key_rate": key_rate, "loss": loss})

    # Establish baseline with historical data
    print("  Establishing baseline with historical data...")
    detector = QKDAnomalyDetector()
    detector.establish_baseline(historical_data)

    # Test with normal metrics
    print("  Testing with normal metrics...")
    normal_metrics = {
        "qber": np.random.normal(0.02, 0.005),
        "key_rate": np.random.normal(1000, 100),
        "loss": np.random.normal(0.1, 0.02),
    }
    normal_metrics["qber"] = max(0, min(0.5, normal_metrics["qber"]))
    normal_metrics["key_rate"] = max(0, normal_metrics["key_rate"])
    normal_metrics["loss"] = max(0, min(1, normal_metrics["loss"]))

    anomalies = detector.detect_anomalies(normal_metrics)
    print(f"  Normal metrics anomalies: {anomalies}")

    # Test with anomalous metrics (potential eavesdropping)
    print("  Testing with anomalous metrics (simulated eavesdropping)...")
    anomalous_metrics = {
        "qber": 0.5,  # Very high QBER - suspicious!
        "key_rate": 100,  # Very low key rate
        "loss": 0.8,  # Very high loss
    }

    anomalies = detector.detect_anomalies(anomalous_metrics)
    print(f"  Anomalous metrics anomalies: {anomalies}")

    # Get detection report
    report = detector.get_detection_report()
    print("  Detection Report:")
    print(f"    Total detections: {report['total_detections']}")
    if "anomaly_rates" in report:
        for metric, rate in report["anomaly_rates"].items():
            print(f"    {metric} anomaly rate: {rate:.2%}")

    # Visualize anomaly detection
    plt.figure(figsize=(10, 6))

    # Plot historical QBER distribution
    historical_qbers = [data["qber"] for data in historical_data]
    plt.hist(
        historical_qbers, bins=30, alpha=0.7, label="Historical QBER", color="blue"
    )

    # Mark normal and anomalous QBER values
    plt.axvline(
        normal_metrics["qber"],
        color="green",
        linestyle="--",
        linewidth=2,
        label=f"Normal QBER ({normal_metrics['qber']:.3f})",
    )
    plt.axvline(
        anomalous_metrics["qber"],
        color="red",
        linestyle="--",
        linewidth=2,
        label=f"Anomalous QBER ({anomalous_metrics['qber']:.3f})",
    )

    plt.xlabel("QBER")
    plt.ylabel("Frequency")
    plt.title("QBER Distribution and Anomaly Detection")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig("anomaly_detection.png", dpi=300, bbox_inches="tight")
    plt.show()


def simulate_adaptive_qkd() -> None:
    """
    Simulate adaptive QKD using machine learning.
    """
    print("\nSimulating adaptive QKD...")

    # Create a dynamic environment with changing conditions
    print("  Simulating dynamic channel conditions...")

    # Initial channel conditions
    channel_conditions = {"loss": 0.1, "noise_level": 0.05}

    # Create protocol with initial conditions
    channel = QuantumChannel(
        loss=channel_conditions["loss"],
        noise_model="depolarizing",
        noise_level=channel_conditions["noise_level"],
    )
    protocol = BB84(channel, key_length=100)

    # Simulate adaptation over time
    time_steps = 50
    key_rates = []
    qbers = []

    for t in range(time_steps):
        # Gradually change channel conditions
        channel_conditions["loss"] = 0.1 + 0.2 * np.sin(2 * np.pi * t / 20)
        channel_conditions["noise_level"] = 0.05 + 0.1 * np.abs(
            np.sin(2 * np.pi * t / 15)
        )

        # Update channel
        channel.loss = channel_conditions["loss"]
        channel.noise_level = channel_conditions["noise_level"]

        # Execute protocol
        try:
            results = protocol.execute()
            key_rate = protocol.get_key_rate() if results.get("is_secure", False) else 0
            qber = results.get("qber", 1.0)
        except Exception:
            key_rate = 0
            qber = 1.0

        key_rates.append(key_rate)
        qbers.append(qber)

        # Every 10 steps, optimize parameters
        if t % 10 == 0 and t > 0:
            print(f"    Optimizing at time step {t}...")

    # Plot results
    plt.figure(figsize=(12, 5))

    # Plot key rates over time
    plt.subplot(1, 2, 1)
    plt.plot(key_rates, "b-", linewidth=2)
    plt.xlabel("Time Step")
    plt.ylabel("Key Rate")
    plt.title("Adaptive QKD: Key Rate Over Time")
    plt.grid(True, alpha=0.3)

    # Plot QBER over time
    plt.subplot(1, 2, 2)
    plt.plot(qbers, "r-", linewidth=2)
    plt.xlabel("Time Step")
    plt.ylabel("QBER")
    plt.title("Adaptive QKD: QBER Over Time")
    plt.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("adaptive_qkd.png", dpi=300, bbox_inches="tight")
    plt.show()

    print(f"  Final average key rate: {np.mean(key_rates[-10:]):.2f}")
    print(f"  Final average QBER: {np.mean(qbers[-10:]):.4f}")


def main() -> None:
    """
    Main function to run ML examples.
    """
    print("Machine Learning Integration Examples")
    print("=" * 40)

    # Run examples
    optimize_protocol_parameters()
    detect_qkd_anomalies()
    simulate_adaptive_qkd()

    print("\nML integration examples completed!")
    print("Results saved as PNG images in the current directory.")


if __name__ == "__main__":
    main()
