"""
Protocol Comparison Example

This script compares the performance of different QKD protocols
under various channel conditions.
"""

import matplotlib.pyplot as plt
import numpy as np

# Import QKDpy modules
from qkdpy import BB84, E91, SARG04, QuantumChannel
from qkdpy.protocols.cv_qkd import CVQKD
from qkdpy.protocols.hd_qkd import HDQKD


def compare_protocols_vs_loss() -> None:
    """
    Compare different QKD protocols as a function of channel loss.
    """
    print("Comparing QKD protocols vs. channel loss...")

    # Define loss values to test
    loss_values = np.linspace(0.0, 0.5, 21)

    # Store results for each protocol
    results: dict[str, dict[str, list[float]]] = {
        "BB84": {"key_rate": [], "qber": []},
        "E91": {"key_rate": [], "qber": []},
        "SARG04": {"key_rate": [], "qber": []},
        "CV-QKD": {"key_rate": [], "qber": []},
        "HD-QKD": {"key_rate": [], "qber": []},
    }

    # Test each protocol at different loss levels
    for i, loss in enumerate(loss_values):
        print(f"  Testing at loss = {loss:.2f} ({i + 1}/{len(loss_values)})")

        # Create a quantum channel
        channel = QuantumChannel(
            loss=loss, noise_model="depolarizing", noise_level=0.05
        )

        # Test each protocol
        protocols = [
            ("BB84", BB84(channel, key_length=100)),
            ("E91", E91(channel, key_length=100)),
            ("SARG04", SARG04(channel, key_length=100)),
            ("CV-QKD", CVQKD(channel, key_length=100)),
            ("HD-QKD", HDQKD(channel, key_length=100, dimension=4)),
        ]

        for name, protocol in protocols:
            try:
                # Execute the protocol
                result = protocol.execute()

                # Store results
                if result["is_secure"]:
                    key_rate = protocol.get_key_rate()
                    qber = result["qber"]
                else:
                    key_rate = 0.0
                    qber = 1.0  # High QBER for insecure connections

                results[name]["key_rate"].append(key_rate)
                results[name]["qber"].append(qber)

            except Exception as e:
                print(f"    Error with {name}: {e}")
                results[name]["key_rate"].append(0.0)
                results[name]["qber"].append(1.0)

    # Plot the results
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    # Plot key rate vs loss
    for name, data in results.items():
        ax1.plot(loss_values, data["key_rate"], marker="o", linewidth=2, label=name)

    ax1.set_xlabel("Channel Loss")
    ax1.set_ylabel("Key Rate (bits/channel use)")
    ax1.set_title("Key Rate vs. Channel Loss")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Plot QBER vs loss
    for name, data in results.items():
        ax2.plot(loss_values, data["qber"], marker="s", linewidth=2, label=name)

    ax2.set_xlabel("Channel Loss")
    ax2.set_ylabel("Quantum Bit Error Rate (QBER)")
    ax2.set_title("QBER vs. Channel Loss")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("protocol_comparison.png", dpi=300, bbox_inches="tight")
    plt.show()


def compare_protocols_vs_noise() -> None:
    """
    Compare different QKD protocols as a function of channel noise.
    """
    print("Comparing QKD protocols vs. channel noise...")

    # Define noise levels to test
    noise_levels = np.linspace(0.0, 0.3, 21)

    # Store results for each protocol
    results: dict[str, dict[str, list[float]]] = {
        "BB84": {"key_rate": [], "qber": []},
        "E91": {"key_rate": [], "qber": []},
        "SARG04": {"key_rate": [], "qber": []},
        "CV-QKD": {"key_rate": [], "qber": []},
        "HD-QKD": {"key_rate": [], "qber": []},
    }

    # Test each protocol at different noise levels
    for i, noise in enumerate(noise_levels):
        print(f"  Testing at noise = {noise:.2f} ({i + 1}/{len(noise_levels)})")

        # Create a quantum channel
        channel = QuantumChannel(
            loss=0.1,  # Fixed loss
            noise_model="depolarizing",
            noise_level=noise,
        )

        # Test each protocol
        protocols = [
            ("BB84", BB84(channel, key_length=100)),
            ("E91", E91(channel, key_length=100)),
            ("SARG04", SARG04(channel, key_length=100)),
            ("CV-QKD", CVQKD(channel, key_length=100)),
            ("HD-QKD", HDQKD(channel, key_length=100, dimension=4)),
        ]

        for name, protocol in protocols:
            try:
                # Execute the protocol
                result = protocol.execute()

                # Store results
                if result["is_secure"]:
                    key_rate = protocol.get_key_rate()
                    qber = result["qber"]
                else:
                    key_rate = 0.0
                    qber = 1.0  # High QBER for insecure connections

                results[name]["key_rate"].append(key_rate)
                results[name]["qber"].append(qber)

            except Exception as e:
                print(f"    Error with {name}: {e}")
                results[name]["key_rate"].append(0.0)
                results[name]["qber"].append(1.0)

    # Plot the results
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    # Plot key rate vs noise
    for name, data in results.items():
        ax1.plot(noise_levels, data["key_rate"], marker="o", linewidth=2, label=name)

    ax1.set_xlabel("Channel Noise Level")
    ax1.set_ylabel("Key Rate (bits/channel use)")
    ax1.set_title("Key Rate vs. Channel Noise")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Plot QBER vs noise
    for name, data in results.items():
        ax2.plot(noise_levels, data["qber"], marker="s", linewidth=2, label=name)

    ax2.set_xlabel("Channel Noise Level")
    ax2.set_ylabel("Quantum Bit Error Rate (QBER)")
    ax2.set_title("QBER vs. Channel Noise")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("protocol_comparison_noise.png", dpi=300, bbox_inches="tight")
    plt.show()


def main() -> None:
    """
    Main function to run protocol comparisons.
    """
    print("QKD Protocol Comparison Examples")
    print("=" * 40)

    # Run comparisons
    compare_protocols_vs_loss()
    compare_protocols_vs_noise()

    print(
        "\nComparison plots saved as 'protocol_comparison.png' and 'protocol_comparison_noise.png'"
    )


if __name__ == "__main__":
    main()
