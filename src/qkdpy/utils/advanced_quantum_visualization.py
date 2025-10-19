"""Advanced visualization tools for quantum states and protocol execution."""

from typing import Any

import matplotlib.pyplot as plt
import numpy as np

# Optional imports
try:
    import seaborn as sns

    SEABORN_AVAILABLE = True
except ImportError:
    SEABORN_AVAILABLE = False
    sns = None

from ..core import QuantumChannel, Qubit
from ..protocols.base import BaseProtocol


class QuantumStateVisualizer:
    """Advanced visualization tools for quantum states."""

    @staticmethod
    def plot_density_matrix(
        qubit: Qubit,
        title: str = "Density Matrix Visualization",
        figsize: tuple[int, int] = (8, 6),
    ) -> plt.Figure:
        """Plot the density matrix of a qubit.

        Args:
            qubit: Qubit to visualize
            title: Title for the plot
            figsize: Figure size (width, height)

        Returns:
            Matplotlib figure object
        """
        # Calculate the density matrix
        rho = qubit.density_matrix()

        # Create figure
        fig, ax = plt.subplots(1, 1, figsize=figsize)

        # Plot real part of density matrix
        im = ax.imshow(rho.real, cmap="RdBu_r", vmin=-1, vmax=1)
        ax.set_xticks([0, 1])
        ax.set_yticks([0, 1])
        ax.set_xticklabels(["|0⟩", "|1⟩"])
        ax.set_yticklabels(["|0⟩", "|1⟩"])
        ax.set_title(f"{title} - Real Part")

        # Add colorbar
        plt.colorbar(im, ax=ax)

        # Add value annotations
        for i in range(2):
            for j in range(2):
                ax.text(
                    j,
                    i,
                    f"{rho[i, j].real:.2f}",
                    ha="center",
                    va="center",
                    color="white" if abs(rho[i, j].real) < 0.5 else "black",
                )

        plt.tight_layout()
        return fig

    @staticmethod
    def plot_bloch_vector_evolution(
        qubit_states: list[Qubit],
        time_points: list[float] | None = None,
        title: str = "Bloch Vector Evolution",
        figsize: tuple[int, int] = (10, 8),
    ) -> plt.Figure:
        """Plot the evolution of a qubit's Bloch vector over time.

        Args:
            qubit_states: List of qubit states at different times
            time_points: Time points corresponding to each state
            title: Title for the plot
            figsize: Figure size (width, height)

        Returns:
            Matplotlib figure object
        """
        if time_points is None:
            time_points = list(range(len(qubit_states)))

        # Extract Bloch vectors
        bloch_vectors = [qubit.bloch_vector() for qubit in qubit_states]
        x_coords = [vec[0] for vec in bloch_vectors]
        y_coords = [vec[1] for vec in bloch_vectors]
        z_coords = [vec[2] for vec in bloch_vectors]

        # Create figure
        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(111, projection="3d")

        # Draw the Bloch sphere
        u = np.linspace(0, 2 * np.pi, 100)
        v = np.linspace(0, np.pi, 100)
        x_sphere = np.outer(np.cos(u), np.sin(v))
        y_sphere = np.outer(np.sin(u), np.sin(v))
        z_sphere = np.outer(np.ones(np.size(u)), np.cos(v))
        ax.plot_surface(x_sphere, y_sphere, z_sphere, color="lightgray", alpha=0.2)

        # Plot the evolution path
        ax.plot(x_coords, y_coords, z_coords, "b-", linewidth=2, alpha=0.7)
        ax.scatter(x_coords, y_coords, z_coords, c=time_points, cmap="viridis", s=50)

        # Draw coordinate axes
        ax.quiver(0, 0, 0, 1.2, 0, 0, color="r", arrow_length_ratio=0.1)
        ax.quiver(0, 0, 0, 0, 1.2, 0, color="g", arrow_length_ratio=0.1)
        ax.quiver(0, 0, 0, 0, 0, 1.2, color="b", arrow_length_ratio=0.1)

        # Set labels and title
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_zlabel("Z")
        ax.set_title(title)

        return fig

    @staticmethod
    def plot_quantum_state_histogram(
        qubit_states: list[Qubit],
        measurement_axis: str = "Z",
        title: str = "Quantum State Measurement Probabilities",
        figsize: tuple[int, int] = (10, 6),
    ) -> plt.Figure:
        """Plot histogram of measurement probabilities for multiple qubit states.

        Args:
            qubit_states: List of qubit states
            measurement_axis: Axis to measure ('X', 'Y', or 'Z')
            title: Title for the plot
            figsize: Figure size (width, height)

        Returns:
            Matplotlib figure object
        """
        # Calculate measurement probabilities
        probabilities = []
        for qubit in qubit_states:
            # Create a copy of the qubit to avoid modifying the original
            qubit_copy = Qubit(qubit.state[0], qubit.state[1])
            probs = qubit_copy.probabilities

            if measurement_axis == "X":
                # Rotate to X basis
                hadamard = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
                qubit_copy.apply_gate(hadamard)
                probs = qubit_copy.probabilities
            elif measurement_axis == "Y":
                # Rotate to Y basis
                y_basis = np.array([[1, -1j], [1, 1j]], dtype=complex) / np.sqrt(2)
                qubit_copy.apply_gate(y_basis)
                probs = qubit_copy.probabilities

            probabilities.append(probs)

        prob_0 = [p[0] for p in probabilities]
        prob_1 = [p[1] for p in probabilities]

        # Create figure
        fig, ax = plt.subplots(1, 1, figsize=figsize)

        # Create bar chart
        x_pos = np.arange(len(qubit_states))
        width = 0.35

        ax.bar(x_pos - width / 2, prob_0, width, label="P(|0\u27e9)", alpha=0.8)
        ax.bar(x_pos + width / 2, prob_1, width, label="P(|1\u27e9)", alpha=0.8)

        # Set labels and title
        ax.set_xlabel("Qubit Index")
        ax.set_ylabel("Probability")
        ax.set_title(title)
        ax.set_xticks(x_pos)
        ax.set_xticklabels([f"|\u03c8{i}\u27e9" for i in range(len(qubit_states))])
        ax.legend()
        ax.grid(True, alpha=0.3)

        return fig

    @staticmethod
    def plot_quantum_channel_characteristics(
        channel: QuantumChannel,
        title: str = "Quantum Channel Characteristics",
        figsize: tuple[int, int] = (12, 8),
    ) -> plt.Figure:
        """Plot characteristics of a quantum channel.

        Args:
            channel: Quantum channel to visualize
            title: Title for the plot
            figsize: Figure size (width, height)

        Returns:
            Matplotlib figure object
        """
        # Create figure with subplots
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=figsize)

        # Plot loss characteristic
        ax1.bar(["Loss"], [channel.loss], color="red", alpha=0.7)
        ax1.set_ylabel("Loss Probability")
        ax1.set_title("Channel Loss")
        ax1.set_ylim(0, 1)

        # Plot noise level
        ax2.bar(["Noise Level"], [channel.noise_level], color="orange", alpha=0.7)
        ax2.set_ylabel("Noise Level")
        ax2.set_title("Channel Noise")
        ax2.set_ylim(0, 1)

        # Plot noise model
        ax3.text(
            0.5,
            0.5,
            channel.noise_model.replace("_", " ").title(),
            horizontalalignment="center",
            verticalalignment="center",
            fontsize=14,
            bbox={"boxstyle": "round,pad=0.3", "facecolor": "lightblue"},
        )
        ax3.set_title("Noise Model")
        ax3.axis("off")

        # Plot combined channel quality
        quality = 1 - (channel.loss + channel.noise_level) / 2
        ax4.bar(["Channel Quality"], [quality], color="green", alpha=0.7)
        ax4.set_ylabel("Quality Score")
        ax4.set_title("Overall Channel Quality")
        ax4.set_ylim(0, 1)

        plt.suptitle(title)
        plt.tight_layout()
        return fig


class ProtocolExecutionVisualizer:
    """Visualization tools for protocol execution and performance."""

    @staticmethod
    def plot_protocol_execution_timeline(
        protocol: BaseProtocol,
        title: str = "Protocol Execution Timeline",
        figsize: tuple[int, int] = (12, 8),
    ) -> plt.Figure:
        """Plot timeline of protocol execution steps.

        Args:
            protocol: Protocol to visualize
            title: Title for the plot
            figsize: Figure size (width, height)

        Returns:
            Matplotlib figure object
        """
        # Create figure
        fig, ax = plt.subplots(1, 1, figsize=figsize)

        # Define execution steps (this is a simplified example)
        steps = [
            "Initialization",
            "State Preparation",
            "Transmission",
            "Measurement",
            "Key Sifting",
            "Error Correction",
            "Privacy Amplification",
            "Final Key",
        ]

        # Simulate timing (in arbitrary units)
        timings = [0.5, 1.2, 2.0, 1.5, 0.8, 1.0, 0.7, 0.3]
        cumulative_timings = np.cumsum([0] + timings)

        # Plot timeline
        for i, (step, start, duration) in enumerate(
            zip(steps, cumulative_timings[:-1], timings, strict=False)
        ):
            ax.barh(i, duration, left=start, height=0.5, alpha=0.7)
            ax.text(start + duration / 2, i, step, ha="center", va="center", fontsize=9)

        # Set labels and title
        ax.set_xlabel("Time (arbitrary units)")
        ax.set_ylabel("Execution Steps")
        ax.set_title(title)
        ax.set_yticks(range(len(steps)))
        ax.set_yticklabels([])
        ax.grid(True, axis="x", alpha=0.3)

        return fig

    @staticmethod
    def plot_key_generation_performance(
        key_lengths: list[int],
        execution_times: list[float],
        qber_values: list[float],
        title: str = "Key Generation Performance",
        figsize: tuple[int, int] = (12, 8),
    ) -> plt.Figure:
        """Plot key generation performance metrics.

        Args:
            key_lengths: List of key lengths
            execution_times: List of execution times
            qber_values: List of QBER values
            title: Title for the plot
            figsize: Figure size (width, height)

        Returns:
            Matplotlib figure object
        """
        # Create figure with subplots
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=figsize)

        # Plot key length vs execution time
        ax1.scatter(key_lengths, execution_times, alpha=0.7, color="blue")
        ax1.set_xlabel("Key Length")
        ax1.set_ylabel("Execution Time (seconds)")
        ax1.set_title("Key Length vs Execution Time")
        ax1.grid(True, alpha=0.3)

        # Plot key length vs QBER
        ax2.scatter(key_lengths, qber_values, alpha=0.7, color="red")
        ax2.set_xlabel("Key Length")
        ax2.set_ylabel("QBER")
        ax2.set_title("Key Length vs QBER")
        ax2.grid(True, alpha=0.3)

        # Plot execution time vs QBER
        ax3.scatter(execution_times, qber_values, alpha=0.7, color="green")
        ax3.set_xlabel("Execution Time (seconds)")
        ax3.set_ylabel("QBER")
        ax3.set_title("Execution Time vs QBER")
        ax3.grid(True, alpha=0.3)

        plt.suptitle(title)
        plt.tight_layout()
        return fig

    @staticmethod
    def plot_security_analysis(
        qber_values: list[float],
        secure_threshold: float,
        title: str = "Security Analysis",
        figsize: tuple[int, int] = (10, 6),
    ) -> plt.Figure:
        """Plot security analysis based on QBER values.

        Args:
            qber_values: List of QBER values
            secure_threshold: Security threshold
            title: Title for the plot
            figsize: Figure size (width, height)

        Returns:
            Matplotlib figure object
        """
        # Create figure
        fig, ax = plt.subplots(1, 1, figsize=figsize)

        # Plot QBER values
        ax.plot(qber_values, "b-", linewidth=2, marker="o", markersize=4, label="QBER")
        ax.axhline(
            y=secure_threshold,
            color="r",
            linestyle="--",
            linewidth=2,
            label=f"Security Threshold ({secure_threshold})",
        )

        # Shade secure/insecure regions
        ax.fill_between(
            range(len(qber_values)),
            0,
            secure_threshold,
            alpha=0.3,
            color="green",
            label="Secure Region",
        )
        ax.fill_between(
            range(len(qber_values)),
            secure_threshold,
            1,
            alpha=0.3,
            color="red",
            label="Insecure Region",
        )

        # Calculate security status
        secure_count = sum(1 for qber in qber_values if qber <= secure_threshold)
        _insecure_count = len(qber_values) - secure_count
        security_rate = secure_count / len(qber_values) if qber_values else 0

        # Add text box with statistics
        stats_text = f"Secure: {secure_count}/{len(qber_values)} ({security_rate:.1%})"
        ax.text(
            0.02,
            0.98,
            stats_text,
            transform=ax.transAxes,
            fontsize=10,
            verticalalignment="top",
            bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.8},
        )

        # Set labels and title
        ax.set_xlabel("Trial Index")
        ax.set_ylabel("QBER")
        ax.set_title(title)
        ax.set_ylim(0, 1)
        ax.legend()
        ax.grid(True, alpha=0.3)

        return fig

    @staticmethod
    def plot_protocol_comparison(
        protocol_results: dict[str, dict[str, Any]],
        metrics: list[str] | None = None,
        title: str = "Protocol Comparison",
        figsize: tuple[int, int] = (12, 8),
    ) -> plt.Figure:
        """Compare different protocols based on performance metrics.

        Args:
            protocol_results: Dictionary with protocol results
            metrics: List of metrics to compare
            title: Title for the plot
            figsize: Figure size (width, height)

        Returns:
            Matplotlib figure object
        """
        # Set default metrics if not provided
        metrics = metrics or ["key_rate", "qber", "execution_time"]

        # Extract data
        protocols = list(protocol_results.keys())
        data = {metric: [] for metric in metrics}

        for protocol in protocols:
            results = protocol_results[protocol]
            for metric in metrics:
                if metric in results:
                    data[metric].append(results[metric])
                else:
                    data[metric].append(0)

        # Create figure
        fig, ax = plt.subplots(1, 1, figsize=figsize)

        # Create grouped bar chart
        x_pos = np.arange(len(protocols))
        width = 0.8 / len(metrics)

        for i, metric in enumerate(metrics):
            values = data[metric]
            # Normalize values for better visualization
            if max(values) > 0:
                normalized_values = [v / max(values) for v in values]
            else:
                normalized_values = values
            ax.bar(
                x_pos + i * width,
                normalized_values,
                width,
                label=metric.replace("_", " ").title(),
                alpha=0.8,
            )

        # Set labels and title
        ax.set_xlabel("Protocols")
        ax.set_ylabel("Normalized Performance")
        ax.set_title(title)
        ax.set_xticks(x_pos + width * (len(metrics) - 1) / 2)
        ax.set_xticklabels(protocols)
        ax.legend()
        ax.grid(True, alpha=0.3)

        return fig


class InteractiveQuantumVisualizer:
    """Interactive visualization tools for quantum states and protocols."""

    @staticmethod
    def create_interactive_bloch_sphere(
        qubit: Qubit, title: str = "Interactive Bloch Sphere"
    ) -> plt.Figure:
        """Create an interactive Bloch sphere visualization.

        Args:
            qubit: Qubit to visualize
            title: Title for the plot

        Returns:
            Matplotlib figure object
        """
        # This is a static version - in a real implementation,
        # this would use interactive plotting libraries like Plotly or ipywidgets

        # Get Bloch vector
        x, y, z = qubit.bloch_vector()

        # Create figure
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection="3d")

        # Draw the Bloch sphere
        u = np.linspace(0, 2 * np.pi, 100)
        v = np.linspace(0, np.pi, 100)
        x_sphere = np.outer(np.cos(u), np.sin(v))
        y_sphere = np.outer(np.sin(u), np.sin(v))
        z_sphere = np.outer(np.ones(np.size(u)), np.cos(v))
        ax.plot_surface(x_sphere, y_sphere, z_sphere, color="lightgray", alpha=0.2)

        # Draw the state vector
        ax.quiver(0, 0, 0, x, y, z, color="m", arrow_length_ratio=0.1, linewidth=3)

        # Draw coordinate axes
        ax.quiver(0, 0, 0, 1.2, 0, 0, color="r", arrow_length_ratio=0.1)
        ax.quiver(0, 0, 0, 0, 1.2, 0, color="g", arrow_length_ratio=0.1)
        ax.quiver(0, 0, 0, 0, 0, 1.2, color="b", arrow_length_ratio=0.1)

        # Set labels and title
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_zlabel("Z")
        ax.set_title(title)
        ax.set_xlim([-1.2, 1.2])
        ax.set_ylim([-1.2, 1.2])
        ax.set_zlim([-1.2, 1.2])

        return fig

    @staticmethod
    def animate_qubit_evolution(
        qubit_states: list[Qubit],
        interval: int = 200,
        title: str = "Animated Qubit Evolution",
    ) -> plt.Figure:
        """Create an animation of qubit state evolution.

        Args:
            qubit_states: List of qubit states at different times
            interval: Animation interval in milliseconds
            title: Title for the plot

        Returns:
            Matplotlib figure object
        """
        # For this static implementation, we'll create a series of plots
        # showing the evolution at different time points

        num_states = len(qubit_states)
        if num_states == 0:
            raise ValueError("No qubit states provided")

        # Create figure
        fig = plt.figure(figsize=(15, 5))

        # Select 3 representative states to show
        indices = [0, num_states // 2, num_states - 1]
        titles = ["Initial State", "Intermediate State", "Final State"]

        for i, (idx, subtitle) in enumerate(zip(indices, titles, strict=False)):
            ax = fig.add_subplot(1, 3, i + 1, projection="3d")
            qubit = qubit_states[idx]

            # Get Bloch vector
            x, y, z = qubit.bloch_vector()

            # Draw the Bloch sphere
            u = np.linspace(0, 2 * np.pi, 100)
            v = np.linspace(0, np.pi, 100)
            x_sphere = np.outer(np.cos(u), np.sin(v))
            y_sphere = np.outer(np.sin(u), np.sin(v))
            z_sphere = np.outer(np.ones(np.size(u)), np.cos(v))
            ax.plot_surface(x_sphere, y_sphere, z_sphere, color="lightgray", alpha=0.2)

            # Draw the state vector
            ax.quiver(0, 0, 0, x, y, z, color="m", arrow_length_ratio=0.1, linewidth=3)

            # Draw coordinate axes
            ax.quiver(0, 0, 0, 1.2, 0, 0, color="r", arrow_length_ratio=0.1)
            ax.quiver(0, 0, 0, 0, 1.2, 0, color="g", arrow_length_ratio=0.1)
            ax.quiver(0, 0, 0, 0, 0, 1.2, color="b", arrow_length_ratio=0.1)

            # Set labels and title
            ax.set_xlabel("X")
            ax.set_ylabel("Y")
            ax.set_zlabel("Z")
            ax.set_title(f"{title}\n{subtitle}")
            ax.set_xlim([-1.2, 1.2])
            ax.set_ylim([-1.2, 1.2])
            ax.set_zlim([-1.2, 1.2])

        plt.tight_layout()
        return fig
