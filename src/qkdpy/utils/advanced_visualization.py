"""Advanced visualization and analysis tools for QKD."""

import matplotlib.pyplot as plt
import numpy as np

from ..core import Qubit
from ..protocols import BaseProtocol


class AdvancedProtocolVisualizer:
    """Advanced visualization tools for QKD protocols."""

    @staticmethod
    def plot_quantum_state_evolution(
        states: list[Qubit], title: str = "Quantum State Evolution"
    ) -> plt.Figure:
        """Plot the evolution of quantum states on the Bloch sphere.

        Args:
            states: List of Qubit objects representing state evolution
            title: Title for the plot

        Returns:
            Matplotlib figure object
        """
        fig = plt.figure(figsize=(12, 10))
        ax = fig.add_subplot(111, projection="3d")

        # Draw the Bloch sphere
        u = np.linspace(0, 2 * np.pi, 100)
        v = np.linspace(0, np.pi, 100)
        x_sphere = np.outer(np.cos(u), np.sin(v))
        y_sphere = np.outer(np.sin(u), np.sin(v))
        z_sphere = np.outer(np.ones(np.size(u)), np.cos(v))

        ax.plot_surface(x_sphere, y_sphere, z_sphere, color="lightgray", alpha=0.2)

        # Draw the coordinate axes
        ax.quiver(0, 0, 0, 1.5, 0, 0, color="r", arrow_length_ratio=0.05)
        ax.quiver(0, 0, 0, 0, 1.5, 0, color="g", arrow_length_ratio=0.05)
        ax.quiver(0, 0, 0, 0, 0, 1.5, color="b", arrow_length_ratio=0.05)

        # Label the axes
        ax.text(1.6, 0, 0, "X", color="r", fontsize=12)
        ax.text(0, 1.6, 0, "Y", color="g", fontsize=12)
        ax.text(0, 0, 1.6, "Z", color="b", fontsize=12)

        # Plot the state evolution
        x_coords, y_coords, z_coords = [], [], []
        for state in states:
            x, y, z = state.bloch_vector()
            x_coords.append(x)
            y_coords.append(y)
            z_coords.append(z)

        # Plot the trajectory
        ax.plot(x_coords, y_coords, z_coords, "o-", color="purple", markersize=6)

        # Highlight the start and end points
        ax.scatter(
            [x_coords[0]],
            [y_coords[0]],
            [z_coords[0]],
            color="green",
            s=100,
            label="Start",
            zorder=5,
        )
        ax.scatter(
            [x_coords[-1]],
            [y_coords[-1]],
            [z_coords[-1]],
            color="red",
            s=100,
            label="End",
            zorder=5,
        )

        # Set the limits and labels
        ax.set_xlim([-1.5, 1.5])
        ax.set_ylim([-1.5, 1.5])
        ax.set_zlim([-1.5, 1.5])
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_zlabel("Z")
        ax.set_title(title)
        ax.legend()

        return fig

    @staticmethod
    def plot_protocol_comparison(
        protocols_data: dict,
        metric: str = "key_rate",
        title: str = "QKD Protocol Comparison",
    ) -> plt.Figure:
        """Plot a comparison of different QKD protocols.

        Args:
            protocols_data: Dictionary mapping protocol names to performance data
            metric: Metric to compare ('key_rate', 'qber', 'efficiency')
            title: Title for the plot

        Returns:
            Matplotlib figure object
        """
        fig, ax = plt.subplots(figsize=(12, 8))

        # Extract protocol names and values
        protocols = list(protocols_data.keys())
        values = [data.get(metric, 0) for data in protocols_data.values()]

        # Create bar chart
        bars = ax.bar(
            protocols, values, color=plt.cm.tab10(np.linspace(0, 1, len(protocols)))
        )

        # Add value labels on bars
        for bar, value in zip(bars, values, strict=False):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"{value:.3f}",
                ha="center",
                va="bottom",
            )

        # Set labels and title
        ax.set_xlabel("QKD Protocols")
        ax.set_ylabel(metric.replace("_", " ").title())
        ax.set_title(title)
        ax.grid(axis="y", alpha=0.3)

        return fig

    @staticmethod
    def plot_security_bounds(
        qber_values: list[float], title: str = "Security Bounds Analysis"
    ) -> plt.Figure:
        """Plot security bounds for QKD protocols.

        Args:
            qber_values: List of QBER values
            title: Title for the plot

        Returns:
            Matplotlib figure object
        """
        fig, ax = plt.subplots(figsize=(12, 8))

        # Calculate security bounds for different protocols
        # BB84 security bound (simple linear model)
        bb84_bound = [max(0, 1 - 2 * qber) for qber in qber_values]

        # SARG04 security bound (different slope)
        sarg04_bound = [max(0, 1 - 3 * qber) for qber in qber_values]

        # E91 security bound (based on Bell violation)
        e91_bound = [max(0, 0.5 * (1 - qber / 0.25)) for qber in qber_values]

        # Plot the bounds
        ax.plot(qber_values, bb84_bound, "o-", label="BB84 Security Bound", linewidth=2)
        ax.plot(
            qber_values, sarg04_bound, "s-", label="SARG04 Security Bound", linewidth=2
        )
        ax.plot(qber_values, e91_bound, "^-", label="E91 Security Bound", linewidth=2)

        # Add threshold lines
        ax.axhline(
            y=0, color="r", linestyle="--", alpha=0.7, label="Security Threshold"
        )
        ax.axvline(x=0.11, color="g", linestyle=":", alpha=0.7, label="BB84 QBER Limit")

        # Set labels and title
        ax.set_xlabel("Quantum Bit Error Rate (QBER)")
        ax.set_ylabel("Security Parameter")
        ax.set_title(title)
        ax.legend()
        ax.grid(True, alpha=0.3)

        return fig

    @staticmethod
    def plot_entanglement_verification(
        bell_test_results: dict, title: str = "Entanglement Verification"
    ) -> plt.Figure:
        """Plot entanglement verification results.

        Args:
            bell_test_results: Dictionary with Bell test results
            title: Title for the plot

        Returns:
            Matplotlib figure object
        """
        fig, ax = plt.subplots(figsize=(10, 8))

        # Extract correlation values
        correlations = bell_test_results.get("correlations", {})
        settings = list(correlations.keys())
        values = list(correlations.values())

        # Create bar chart
        bars = ax.bar(settings, values, color="purple", alpha=0.7)

        # Add value labels
        for bar, value in zip(bars, values, strict=False):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"{value:.3f}",
                ha="center",
                va="bottom",
            )

        # Add Bell bound lines
        ax.axhline(y=2.0, color="r", linestyle="--", label="Classical Bound (S = 2)")
        ax.axhline(
            y=2 * np.sqrt(2), color="g", linestyle="-.", label="Quantum Bound (S = 2√2)"
        )

        # Highlight the S value
        s_value = bell_test_results.get("s_value", 0)
        ax.axhline(
            y=s_value,
            color="b",
            linestyle="-",
            linewidth=2,
            label=f"Measured S = {s_value:.3f}",
        )

        # Set labels and title
        ax.set_xlabel("Measurement Settings")
        ax.set_ylabel("Correlation Value")
        ax.set_title(title)
        ax.legend()
        ax.grid(True, alpha=0.3)

        return fig


class AdvancedKeyRateAnalyzer:
    """Advanced tools for analyzing key rates in QKD protocols."""

    @staticmethod
    def plot_key_rate_vs_parameters(
        protocol: BaseProtocol,
        parameter_name: str,
        parameter_values: list,
        title: str = "Key Rate vs Parameter",
    ) -> plt.Figure:
        """Plot key rate as a function of a protocol parameter.

        Args:
            protocol: QKD protocol instance
            parameter_name: Name of the parameter to vary
            parameter_values: Values to test
            title: Title for the plot

        Returns:
            Matplotlib figure object
        """
        fig, ax = plt.subplots(figsize=(12, 8))

        key_rates = []
        secure_rates = []

        # Test different parameter values
        for value in parameter_values:
            # This is a simplified approach - in practice, you would need to
            # modify the protocol parameters and re-run the protocol
            # For this example, we'll simulate the results

            # Simulate key rate based on parameter value
            if parameter_name == "channel_loss":
                # Higher loss leads to lower key rate
                key_rate = max(0, 1.0 - value * 5)
            elif parameter_name == "noise_level":
                # Higher noise leads to lower key rate
                key_rate = max(0, 1.0 - value * 10)
            else:
                # Default behavior
                key_rate = 0.5

            key_rates.append(key_rate)

            # Determine if the rate is secure (simplified)
            is_secure = key_rate > 0.1
            secure_rates.append(is_secure)

        # Plot key rates
        (line,) = ax.plot(parameter_values, key_rates, "o-", linewidth=2, markersize=8)

        # Highlight secure points
        secure_points = [i for i, secure in enumerate(secure_rates) if secure]
        insecure_points = [i for i, secure in enumerate(secure_rates) if not secure]

        if secure_points:
            ax.scatter(
                [parameter_values[i] for i in secure_points],
                [key_rates[i] for i in secure_points],
                color="green",
                s=100,
                label="Secure",
                zorder=5,
            )

        if insecure_points:
            ax.scatter(
                [parameter_values[i] for i in insecure_points],
                [key_rates[i] for i in insecure_points],
                color="red",
                s=100,
                label="Insecure",
                zorder=5,
            )

        # Add threshold line
        ax.axhline(
            y=0.1, color="r", linestyle="--", alpha=0.7, label="Security Threshold"
        )

        # Set labels and title
        ax.set_xlabel(parameter_name.replace("_", " ").title())
        ax.set_ylabel("Key Rate")
        ax.set_title(title)
        ax.legend()
        ax.grid(True, alpha=0.3)

        return fig

    @staticmethod
    def plot_multi_dimensional_analysis(
        protocols_data: dict, title: str = "Multi-Dimensional QKD Analysis"
    ) -> plt.Figure:
        """Plot a multi-dimensional analysis of QKD protocols.

        Args:
            protocols_data: Dictionary mapping protocol names to multi-dimensional data
            title: Title for the plot

        Returns:
            Matplotlib figure object
        """
        fig = plt.figure(figsize=(14, 10))
        ax = fig.add_subplot(111, projection="3d")

        # Extract data for 3D plot
        protocols = list(protocols_data.keys())
        key_rates = [data.get("key_rate", 0) for data in protocols_data.values()]
        qber_values = [data.get("qber", 0) for data in protocols_data.values()]
        distances = [data.get("distance", 0) for data in protocols_data.values()]

        # Create 3D scatter plot
        _ = ax.scatter(
            key_rates,
            qber_values,
            distances,
            c=range(len(protocols)),
            cmap="tab10",
            s=100,
            alpha=0.7,
        )

        # Add protocol labels
        for i, protocol in enumerate(protocols):
            ax.text(key_rates[i], qber_values[i], distances[i], protocol, fontsize=9)

        # Set labels and title
        ax.set_xlabel("Key Rate")
        ax.set_ylabel("QBER")
        ax.set_zlabel("Distance (km)")
        ax.set_title(title)

        return fig
