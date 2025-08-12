"""Visualization tools for QKDpy."""

import matplotlib.pyplot as plt
import numpy as np

from ..core import Qubit


class BlochSphere:
    """Visualization of qubit states on the Bloch sphere."""

    @staticmethod
    def plot_qubit(
        qubit: Qubit,
        ax: plt.Axes | None = None,
        title: str = "Qubit State on Bloch Sphere",
    ) -> plt.Axes:
        """Plot a qubit state on the Bloch sphere.

        Args:
            qubit: Qubit to plot
            ax: Matplotlib axes to plot on (optional)
            title: Title for the plot

        Returns:
            Matplotlib axes object

        """
        # Get the Bloch vector coordinates
        x, y, z = qubit.bloch_vector()

        # Create a new figure if no axes are provided
        if ax is None:
            fig = plt.figure(figsize=(8, 8))
            ax = fig.add_subplot(111, projection="3d")

        # Draw the Bloch sphere
        u = np.linspace(0, 2 * np.pi, 100)
        v = np.linspace(0, np.pi, 100)
        x_sphere = np.outer(np.cos(u), np.sin(v))
        y_sphere = np.outer(np.sin(u), np.sin(v))
        z_sphere = np.outer(np.ones(np.size(u)), np.cos(v))

        ax.plot_surface(x_sphere, y_sphere, z_sphere, color="lightgray", alpha=0.2)

        # Draw the coordinate axes
        ax.quiver(0, 0, 0, 1.2, 0, 0, color="r", arrow_length_ratio=0.1)
        ax.quiver(0, 0, 0, 0, 1.2, 0, color="g", arrow_length_ratio=0.1)
        ax.quiver(0, 0, 0, 0, 0, 1.2, color="b", arrow_length_ratio=0.1)

        # Label the axes
        ax.text(1.3, 0, 0, "X", color="r")
        ax.text(0, 1.3, 0, "Y", color="g")
        ax.text(0, 0, 1.3, "Z", color="b")

        # Draw the state vector
        ax.quiver(0, 0, 0, x, y, z, color="m", arrow_length_ratio=0.1)

        # Set the limits and labels
        ax.set_xlim([-1.2, 1.2])
        ax.set_ylim([-1.2, 1.2])
        ax.set_zlim([-1.2, 1.2])
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_zlabel("Z")
        ax.set_title(title)

        return ax

    @staticmethod
    def plot_multiple_qubits(
        qubits: list[Qubit],
        labels: list[str] = None,
        title: str = "Multiple Qubit States on Bloch Sphere",
    ) -> plt.Figure:
        """Plot multiple qubit states on the Bloch sphere.

        Args:
            qubits: List of qubits to plot
            labels: Labels for each qubit (optional)
            title: Title for the plot

        Returns:
            Matplotlib figure object

        """
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection="3d")

        # Draw the Bloch sphere
        u = np.linspace(0, 2 * np.pi, 100)
        v = np.linspace(0, np.pi, 100)
        x_sphere = np.outer(np.cos(u), np.sin(v))
        y_sphere = np.outer(np.sin(u), np.sin(v))
        z_sphere = np.outer(np.ones(np.size(u)), np.cos(v))

        ax.plot_surface(x_sphere, y_sphere, z_sphere, color="lightgray", alpha=0.2)

        # Draw the coordinate axes
        ax.quiver(0, 0, 0, 1.2, 0, 0, color="r", arrow_length_ratio=0.1)
        ax.quiver(0, 0, 0, 0, 1.2, 0, color="g", arrow_length_ratio=0.1)
        ax.quiver(0, 0, 0, 0, 0, 1.2, color="b", arrow_length_ratio=0.1)

        # Label the axes
        ax.text(1.3, 0, 0, "X", color="r")
        ax.text(0, 1.3, 0, "Y", color="g")
        ax.text(0, 0, 1.3, "Z", color="b")

        # Colors for each qubit
        colors = plt.cm.tab10(np.linspace(0, 1, len(qubits)))

        # Draw each qubit state
        for i, qubit in enumerate(qubits):
            x, y, z = qubit.bloch_vector()
            ax.quiver(0, 0, 0, x, y, z, color=colors[i], arrow_length_ratio=0.1)

            # Add a label if provided
            if labels and i < len(labels):
                ax.text(x * 1.1, y * 1.1, z * 1.1, labels[i], color=colors[i])

        # Set the limits and labels
        ax.set_xlim([-1.2, 1.2])
        ax.set_ylim([-1.2, 1.2])
        ax.set_zlim([-1.2, 1.2])
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_zlabel("Z")
        ax.set_title(title)

        return fig


class ProtocolVisualizer:
    """Visualization tools for QKD protocols."""

    @staticmethod
    def _filter_protocol_data(*args):
        """Filters out None values from protocol data lists."""
        if not args:
            return ()

        valid_indices = [i for i, res in enumerate(args[0]) if res is not None]

        filtered_data = []
        for arg in args:
            if arg is not None:
                filtered_data.append([arg[i] for i in valid_indices])
            else:
                filtered_data.append(None)

        return tuple(filtered_data)

    @staticmethod
    def plot_bb84_protocol(
        alice_bits: list[int],
        alice_bases: list[str],
        bob_bases: list[str],
        bob_results: list[int],
        title: str = "BB84 Protocol Visualization",
    ) -> plt.Figure:
        """Visualize the BB84 protocol.

        Args:
            alice_bits: Alice's random bits
            alice_bases: Alice's random bases
            bob_bases: Bob's random bases
            bob_results: Bob's measurement results
            title: Title for the plot

        Returns:
            Matplotlib figure object

        """
        fig, ax = plt.subplots(figsize=(12, 6))

        # Filter out lost qubits
        alice_bits, alice_bases, bob_bases, bob_results = (
            ProtocolVisualizer._filter_protocol_data(
                alice_bits, alice_bases, bob_bases, bob_results
            )
        )
        length = len(alice_bits)

        # Create arrays for plotting
        x = np.arange(length)

        # Plot Alice's bits
        ax.scatter(x, alice_bits, color="blue", label="Alice's Bits", marker="o")

        # Plot Alice's bases
        alice_basis_values = [
            0 if basis == "computational" else 1 for basis in alice_bases
        ]
        ax.scatter(
            x,
            [b + 0.1 for b in alice_basis_values],
            color="cyan",
            label="Alice's Bases (0=Z, 1=X)",
            marker="s",
        )

        # Plot Bob's bases
        bob_basis_values = [0 if basis == "computational" else 1 for basis in bob_bases]
        ax.scatter(
            x,
            [b - 0.1 for b in bob_basis_values],
            color="green",
            label="Bob's Bases (0=Z, 1=X)",
            marker="s",
        )

        # Plot Bob's results
        ax.scatter(
            x,
            [r - 0.2 for r in bob_results],
            color="red",
            label="Bob's Results",
            marker="x",
        )

        # Highlight matching bases
        for i in range(length):
            if alice_bases[i] == bob_bases[i]:
                ax.axvline(x=i, color="yellow", alpha=0.3)

        # Set the labels and title
        ax.set_xlabel("Qubit Index")
        ax.set_ylabel("Value")
        ax.set_title(title)
        ax.set_yticks([-0.2, 0, 0.1, 0.9, 1.0, 1.1])
        ax.set_yticklabels(
            ["Bob: 0", "Alice: 0", "Alice: Z", "Bob: X", "Alice: 1", "Alice: X"]
        )
        ax.legend()

        return fig

    @staticmethod
    def plot_e91_protocol(
        alice_choices: list[int],
        alice_results: list[int],
        bob_choices: list[int],
        bob_results: list[int],
        title: str = "E91 Protocol Visualization",
    ) -> plt.Figure:
        """Visualize the E91 protocol.

        Args:
            alice_choices: Alice's measurement choices
            alice_results: Alice's measurement results
            bob_choices: Bob's measurement choices
            bob_results: Bob's measurement results
            title: Title for the plot

        Returns:
            Matplotlib figure object

        """
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

        # Filter out lost qubits
        alice_choices, alice_results, bob_choices, bob_results = (
            ProtocolVisualizer._filter_protocol_data(
                alice_choices, alice_results, bob_choices, bob_results
            )
        )
        length = len(alice_choices)

        # Create arrays for plotting
        x = np.arange(length)

        # Plot Alice's choices and results
        ax1.scatter(x, alice_choices, color="blue", label="Alice's Choices", marker="o")
        ax1.scatter(
            x,
            [r + 0.1 for r in alice_results],
            color="cyan",
            label="Alice's Results",
            marker="x",
        )

        # Set the labels and title for Alice
        ax1.set_xlabel("Entangled Pair Index")
        ax1.set_ylabel("Value")
        ax1.set_title(f"{title} - Alice")
        ax1.set_yticks([0, 1, 1.1])
        ax1.set_yticklabels(["Choice 0", "Choice 2", "Result"])
        ax1.legend()

        # Plot Bob's choices and results
        ax2.scatter(
            x,
            [c + 1 for c in bob_choices],
            color="green",
            label="Bob's Choices",
            marker="o",
        )
        ax2.scatter(
            x,
            [r + 0.9 for r in bob_results],
            color="red",
            label="Bob's Results",
            marker="x",
        )

        # Set the labels and title for Bob
        ax2.set_xlabel("Entangled Pair Index")
        ax2.set_ylabel("Value")
        ax2.set_title(f"{title} - Bob")
        ax2.set_yticks([1, 2, 3, 0.9, 1.9])
        ax2.set_yticklabels(
            ["Choice 0", "Choice 1", "Choice 2", "Result 0", "Result 1"]
        )
        ax2.legend()

        plt.tight_layout()
        return fig

    @staticmethod
    def plot_sarg04_protocol(
        alice_bits: list[int],
        alice_bases: list[str],
        bob_bases: list[str],
        bob_results: list[int],
        bob_guesses: list[int],
        title: str = "SARG04 Protocol Visualization",
    ) -> plt.Figure:
        """Visualize the SARG04 protocol.

        Args:
            alice_bits: Alice's random bits
            alice_bases: Alice's random bases
            bob_bases: Bob's random bases
            bob_results: Bob's measurement results
            bob_guesses: Bob's guesses about Alice's states
            title: Title for the plot

        Returns:
            Matplotlib figure object

        """
        fig, ax = plt.subplots(figsize=(12, 6))

        # Filter out lost qubits
        alice_bits, alice_bases, bob_bases, bob_results, bob_guesses = (
            ProtocolVisualizer._filter_protocol_data(
                alice_bits, alice_bases, bob_bases, bob_results, bob_guesses
            )
        )
        length = len(alice_bits)

        # Create arrays for plotting
        x = np.arange(length)

        # Plot Alice's bits
        ax.scatter(x, alice_bits, color="blue", label="Alice's Bits", marker="o")

        # Plot Alice's bases
        alice_basis_values = [
            0 if basis == "computational" else 1 for basis in alice_bases
        ]
        ax.scatter(
            x,
            [b + 0.1 for b in alice_basis_values],
            color="cyan",
            label="Alice's Bases (0=Z, 1=X)",
            marker="s",
        )

        # Plot Bob's bases
        bob_basis_values = [0 if basis == "computational" else 1 for basis in bob_bases]
        ax.scatter(
            x,
            [b - 0.1 for b in bob_basis_values],
            color="green",
            label="Bob's Bases (0=Z, 1=X)",
            marker="s",
        )

        # Plot Bob's results
        ax.scatter(
            x,
            [r - 0.2 for r in bob_results],
            color="red",
            label="Bob's Results",
            marker="x",
        )

        # Plot Bob's guesses
        ax.scatter(
            x,
            [g - 0.3 for g in bob_guesses],
            color="purple",
            label="Bob's Guesses",
            marker="^",
        )

        # Highlight sifted key bits
        for i in range(length):
            alice_basis_index = 0 if alice_bases[i] == "computational" else 1
            bob_guess_basis = 1 - (0 if bob_bases[i] == "computational" else 1)

            if alice_basis_index == bob_guess_basis:
                ax.axvline(x=i, color="yellow", alpha=0.3)

        # Set the labels and title
        ax.set_xlabel("Qubit Index")
        ax.set_ylabel("Value")
        ax.set_title(title)
        ax.set_yticks([-0.3, -0.2, 0, 0.1, 0.9, 1.0, 1.1])
        ax.set_yticklabels(
            [
                "Guess: 1",
                "Bob: 0",
                "Alice: 0",
                "Alice: Z",
                "Bob: X",
                "Alice: 1",
                "Alice: X",
            ]
        )
        ax.legend()

        return fig


class KeyRateAnalyzer:
    """Tools for analyzing key rates in QKD protocols."""

    @staticmethod
    def plot_key_rate_vs_qber(
        qber_values: list[float],
        key_rates: list[float],
        protocol_name: str = "QKD Protocol",
    ) -> plt.Figure:
        """Plot key rate as a function of QBER.

        Args:
            qber_values: List of QBER values
            key_rates: List of corresponding key rates
            protocol_name: Name of the protocol

        Returns:
            Matplotlib figure object

        """
        fig, ax = plt.subplots(figsize=(10, 6))

        # Plot the key rate vs QBER
        ax.plot(
            qber_values,
            key_rates,
            "o-",
            color="blue",
            label=f"{protocol_name} Key Rate",
        )

        # Add a vertical line at the security threshold (11% for BB84)
        ax.axvline(
            x=0.11, color="red", linestyle="--", label="Security Threshold (11%)"
        )

        # Set the labels and title
        ax.set_xlabel("Quantum Bit Error Rate (QBER)")
        ax.set_ylabel("Key Rate")
        ax.set_title(f"Key Rate vs QBER for {protocol_name}")
        ax.legend()
        ax.grid(True)

        return fig

    @staticmethod
    def plot_key_rate_vs_distance(
        distances: list[float],
        key_rates: list[float],
        protocol_name: str = "QKD Protocol",
    ) -> plt.Figure:
        """Plot key rate as a function of distance.

        Args:
            distances: List of distances (in km)
            key_rates: List of corresponding key rates
            protocol_name: Name of the protocol

        Returns:
            Matplotlib figure object

        """
        fig, ax = plt.subplots(figsize=(10, 6))

        # Plot the key rate vs distance
        ax.plot(
            distances, key_rates, "o-", color="green", label=f"{protocol_name} Key Rate"
        )

        # Set the labels and title
        ax.set_xlabel("Distance (km)")
        ax.set_ylabel("Key Rate")
        ax.set_title(f"Key Rate vs Distance for {protocol_name}")
        ax.legend()
        ax.grid(True)

        # Use a logarithmic scale for the y-axis if key rates vary widely
        if max(key_rates) / min(key_rates) > 100:
            ax.set_yscale("log")

        return fig

    @staticmethod
    def compare_protocols(
        protocol_data: dict[str, tuple[list[float], list[float]]],
        x_label: str = "QBER",
        y_label: str = "Key Rate",
    ) -> plt.Figure:
        """Compare key rates between different protocols.

        Args:
            protocol_data: Dictionary mapping protocol names to (x_values, y_values) tuples
            x_label: Label for the x-axis
            y_label: Label for the y-axis

        Returns:
            Matplotlib figure object

        """
        fig, ax = plt.subplots(figsize=(12, 8))

        # Colors for each protocol
        colors = plt.cm.tab10(np.linspace(0, 1, len(protocol_data)))

        # Plot each protocol
        for i, (protocol_name, (x_values, y_values)) in enumerate(
            protocol_data.items()
        ):
            ax.plot(x_values, y_values, "o-", color=colors[i], label=protocol_name)

        # Add a vertical line at the security threshold (11% for BB84)
        if x_label == "QBER":
            ax.axvline(
                x=0.11, color="red", linestyle="--", label="Security Threshold (11%)"
            )

        # Set the labels and title
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.set_title("Comparison of QKD Protocols")
        ax.legend()
        ax.grid(True)

        # Use a logarithmic scale for the y-axis if key rates vary widely
        all_y_values = [
            y for _, (_, y_values) in protocol_data.items() for y in y_values
        ]
        if max(all_y_values) / min(all_y_values) > 100:
            ax.set_yscale("log")

        return fig
