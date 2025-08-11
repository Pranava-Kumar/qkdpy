"""Example of using the BB84 protocol."""

import matplotlib.pyplot as plt
import numpy as np

from qkdpy import BB84, KeyRateAnalyzer, ProtocolVisualizer, QuantumChannel


def bb84_example():
    """Example of using the BB84 protocol to generate a secure key."""
    print("BB84 Protocol Example")
    print("====================")

    # Create a quantum channel with some noise and loss
    channel = QuantumChannel(loss=0.1, noise_model="depolarizing", noise_level=0.05)

    # Create a BB84 protocol instance
    bb84 = BB84(channel, key_length=100)

    # Execute the protocol
    results = bb84.execute()

    # Print the results
    print(f"Raw key length: {len(results['raw_key'])}")
    print(f"Sifted key length: {len(results['sifted_key'])}")
    print(f"Final key length: {len(results['final_key'])}")
    print(f"QBER: {results['qber']:.4f}")
    print(f"Is secure: {results['is_secure']}")
    print(f"Final key: {results['final_key']}")

    # Print channel statistics
    stats = results["channel_stats"]
    print("\nChannel Statistics:")
    print(f"Transmitted qubits: {stats['transmitted']}")
    print(f"Lost qubits: {stats['lost']} ({stats['loss_rate']:.2%})")
    print(f"Errors: {stats['errors']} ({stats['error_rate']:.2%})")

    # Visualize the protocol
    ProtocolVisualizer.plot_bb84_protocol(
        bb84.alice_bits, bb84.alice_bases, bb84.bob_bases, bb84.bob_results
    )
    plt.show()

    # Analyze key rate vs QBER
    qber_values = np.linspace(0, 0.2, 20)
    key_rates = []

    for qber in qber_values:
        # Create a channel with the specified QBER
        channel = QuantumChannel(
            loss=0.1, noise_model="depolarizing", noise_level=qber / 2
        )

        # Create a BB84 protocol instance
        bb84_test = BB84(channel, key_length=100)

        # Execute the protocol
        results = bb84_test.execute()

        # Calculate the key rate
        key_rate = (
            len(results["final_key"]) / len(results["raw_key"])
            if results["raw_key"]
            else 0
        )
        key_rates.append(key_rate)

    # Plot key rate vs QBER
    KeyRateAnalyzer.plot_key_rate_vs_qber(qber_values, key_rates, "BB84")
    plt.show()

    return results


if __name__ == "__main__":
    bb84_example()
