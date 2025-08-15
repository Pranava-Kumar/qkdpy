"""Example of using the B92 protocol."""

import matplotlib.pyplot as plt
import numpy as np

from qkdpy import B92, KeyRateAnalyzer, QuantumChannel


def b92_example():
    """Example of using the B92 protocol to generate a secure key."""
    print("B92 Protocol Example")
    print("===================")

    # Create a quantum channel with some noise and loss
    channel = QuantumChannel(loss=0.1, noise_model="depolarizing", noise_level=0.05)

    # Create a B92 protocol instance
    b92 = B92(channel, key_length=100)

    # Execute the protocol
    results = b92.execute()

    # Print the results
    print(f"Raw key length: {len(results['raw_key'])}")
    print(f"Sifted key length: {len(results['sifted_key'])}")
    print(f"Final key length: {len(results['final_key'])}")
    print(f"QBER: {results['qber']:.4f}")
    print(f"Is secure: {results['is_secure']}")
    print(f"Final key: {[int(bit) for bit in results['final_key']]}")

    # Print channel statistics
    stats = results["channel_stats"]
    print("\nChannel Statistics:")
    print(f"Transmitted qubits: {stats['transmitted']}")
    print(f"Lost qubits: {stats['lost']} ({stats['loss_rate']:.2%})")
    print(f"Errors: {stats['errors']} ({stats['error_rate']:.2%})")

    # Analyze key rate vs QBER
    qber_values = np.linspace(0, 0.3, 20)
    key_rates = []

    for qber in qber_values:
        # Create a channel with the specified QBER
        channel = QuantumChannel(
            loss=0.1, noise_model="depolarizing", noise_level=qber / 2
        )

        # Create a B92 protocol instance
        b92_test = B92(channel, key_length=100)

        # Execute the protocol
        results = b92_test.execute()

        # Calculate the key rate
        key_rate = (
            len(results["final_key"]) / len(results["raw_key"])
            if results["raw_key"]
            else 0
        )
        key_rates.append(key_rate)

    # Plot key rate vs QBER
    KeyRateAnalyzer.plot_key_rate_vs_qber(qber_values, key_rates, "B92")
    plt.show()

    return results


if __name__ == "__main__":
    b92_example()
