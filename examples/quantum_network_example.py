"""Example demonstrating quantum network simulation."""

from qkdpy import QuantumChannel, QuantumNetwork


def quantum_network_example():
    """Example of using the quantum network simulation."""
    print("Quantum Network Simulation Example")
    print("==================================")

    # Create a quantum network
    network = QuantumNetwork("Research Network")

    # Create quantum channels with different characteristics
    channel_ab = QuantumChannel(loss=0.05, noise_model="depolarizing", noise_level=0.02)
    channel_ac = QuantumChannel(loss=0.10, noise_model="depolarizing", noise_level=0.05)
    channel_bc = QuantumChannel(loss=0.08, noise_model="depolarizing", noise_level=0.03)
    channel_bd = QuantumChannel(loss=0.12, noise_model="depolarizing", noise_level=0.06)
    channel_cd = QuantumChannel(loss=0.07, noise_model="depolarizing", noise_level=0.04)

    # Create nodes with BB84 protocols
    network.add_node("Alice")
    network.add_node("Bob")
    network.add_node("Charlie")
    network.add_node("David")

    # Add connections between nodes
    network.add_connection("Alice", "Bob", channel_ab)
    network.add_connection("Alice", "Charlie", channel_ac)
    network.add_connection("Bob", "Charlie", channel_bc)
    network.add_connection("Bob", "David", channel_bd)
    network.add_connection("Charlie", "David", channel_cd)

    # Print network information
    stats = network.get_network_statistics()
    print(f"Network: {stats['network_name']}")
    print(f"Number of nodes: {stats['num_nodes']}")
    print(f"Number of connections: {stats['num_connections']}")
    print(f"Average degree: {stats['average_degree']:.2f}")
    print(f"Network diameter: {stats['network_diameter']}")
    print(f"Nodes: {stats['node_list']}")

    # Find paths between nodes
    print("\nPath Finding:")
    path_ab = network.get_shortest_path("Alice", "Bob")
    print(f"Shortest path from Alice to Bob: {path_ab}")

    path_ad = network.get_shortest_path("Alice", "David")
    print(f"Shortest path from Alice to David: {path_ad}")

    # Try to establish keys between nodes
    print("\nKey Establishment:")
    key_ab = network.establish_key_between_nodes("Alice", "Bob", 64)
    if key_ab:
        print(f"Key established between Alice and Bob: {len(key_ab)} bits")
        print(f"First 10 bits: {key_ab[:10]}")
    else:
        print("Failed to establish key between Alice and Bob")

    key_ad = network.establish_key_between_nodes("Alice", "David", 64)
    if key_ad:
        print(f"Key established between Alice and David: {len(key_ad)} bits")
        print(f"First 10 bits: {key_ad[:10]}")
    else:
        print(
            "Failed to establish key between Alice and David (expected for multi-hop)"
        )

    # Simulate network performance
    print("\nNetwork Performance Simulation:")
    performance = network.simulate_network_performance(num_trials=50)
    if "error" not in performance:
        print(f"Number of trials: {performance['num_trials']}")
        print(f"Successful key exchanges: {performance['successful_key_exchanges']}")
        print(f"Success rate: {performance['success_rate']:.2%}")
        print(f"Average key length: {performance['average_key_length']:.1f} bits")
        print(f"Average QBER: {performance['average_qber']:.4f}")
        print(
            f"Average execution time: {performance['average_execution_time']:.4f} seconds"
        )
    else:
        print(f"Simulation error: {performance['error']}")


def multiparty_qkd_example():
    """Example of multi-party QKD using secret sharing."""
    print("\n\nMulti-Party QKD Example")
    print("=======================")

    from qkdpy.network.quantum_network import MultiPartyQKD

    # Create a secret to share
    secret = [1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1, 1]
    print(f"Original secret: {secret}")

    # Share the secret among 4 parties with threshold 3
    shares = MultiPartyQKD.quantum_secret_sharing(secret, 4, 3)
    print("\nSecret shares for 4 parties (threshold=3):")
    for i, share in enumerate(shares):
        print(f"  Party {i + 1}: {share}")

    # Reconstruct the secret with different subsets
    print("\nReconstruction tests:")

    # With all 4 shares
    reconstructed_all = MultiPartyQKD.reconstruct_secret(shares)
    print(f"  With all 4 shares: {reconstructed_all}")
    print(f"  Correct: {reconstructed_all == secret}")

    # With first 3 shares
    reconstructed_3 = MultiPartyQKD.reconstruct_secret(shares[:3])
    print(f"  With first 3 shares: {reconstructed_3}")
    print(f"  Correct: {reconstructed_3 == secret}")

    # With last 3 shares
    reconstructed_last3 = MultiPartyQKD.reconstruct_secret(shares[1:])
    print(f"  With last 3 shares: {reconstructed_last3}")
    print(f"  Correct: {reconstructed_last3 == secret}")


if __name__ == "__main__":
    # Run the quantum network example
    quantum_network_example()

    # Run the multi-party QKD example
    multiparty_qkd_example()
