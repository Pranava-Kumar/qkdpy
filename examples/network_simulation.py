"""
Quantum Network Simulation Example

This script demonstrates how to simulate quantum networks with QKDpy.
"""

# Import QKDpy modules
from qkdpy import BB84, E91, QuantumChannel
from qkdpy.network import MultiPartyQKDNetwork, QuantumNetwork


def simulate_linear_network() -> None:
    """
    Simulate a linear quantum network topology.
    """
    print("Simulating linear quantum network...")

    # Create a quantum network
    network = QuantumNetwork("Linear Network")

    # Create quantum channels with different characteristics
    channels = [
        QuantumChannel(loss=0.05, noise_model="depolarizing", noise_level=0.02),
        QuantumChannel(loss=0.10, noise_model="depolarizing", noise_level=0.03),
        QuantumChannel(loss=0.08, noise_model="depolarizing", noise_level=0.025),
        QuantumChannel(loss=0.12, noise_model="depolarizing", noise_level=0.035),
    ]

    # Create nodes with different protocols
    protocols = [
        BB84(channels[0], key_length=100),
        BB84(channels[1], key_length=100),
        BB84(channels[2], key_length=100),
        BB84(channels[3], key_length=100),
        E91(channels[0], key_length=100),  # Different protocol for last node
    ]

    # Add nodes to the network
    node_names = ["Alice", "Node1", "Node2", "Node3", "Bob"]
    for name, protocol in zip(node_names, protocols, strict=False):
        network.add_node(name, protocol)

    # Add connections to create a linear network: Alice-Node1-Node2-Node3-Bob
    for i in range(len(node_names) - 1):
        network.add_connection(node_names[i], node_names[i + 1], channels[i])

    # Display network statistics
    stats = network.get_network_statistics()
    print(f"  Network: {stats['network_name']}")
    print(f"  Number of nodes: {stats['num_nodes']}")
    print(f"  Number of connections: {stats['num_connections']}")
    print(f"  Average degree: {stats['average_degree']:.2f}")
    print(f"  Network diameter: {stats['network_diameter']:.2f}")

    # Establish keys between end nodes (Alice and Bob)
    print("  Establishing end-to-end key...")
    key = network.establish_key_between_nodes("Alice", "Bob", key_length=64)

    if key:
        print(f"  ✓ Successfully established key: {key[:20]}...")
    else:
        print("  ✗ Failed to establish key")

    # Simulate network performance
    print("  Simulating network performance...")
    performance = network.simulate_network_performance(num_trials=50)
    print(f"  Success rate: {performance['success_rate']:.2%}")
    print(f"  Average key length: {performance['average_key_length']:.1f}")
    print(f"  Average QBER: {performance['average_qber']:.4f}")


def simulate_star_network() -> None:
    """
    Simulate a star quantum network topology.
    """
    print("\nSimulating star quantum network...")

    # Create a quantum network
    network = QuantumNetwork("Star Network")

    # Create quantum channels
    central_channel = QuantumChannel(
        loss=0.05, noise_model="depolarizing", noise_level=0.02
    )
    outer_channels = [
        QuantumChannel(loss=0.08, noise_model="depolarizing", noise_level=0.025),
        QuantumChannel(loss=0.10, noise_model="depolarizing", noise_level=0.03),
        QuantumChannel(loss=0.07, noise_model="depolarizing", noise_level=0.02),
        QuantumChannel(loss=0.09, noise_model="depolarizing", noise_level=0.028),
    ]

    # Create protocols for central node and outer nodes
    central_protocol = BB84(central_channel, key_length=100)
    outer_protocols = [BB84(channel, key_length=100) for channel in outer_channels]

    # Add central node and outer nodes
    network.add_node("Hub", central_protocol)
    outer_nodes = ["Node1", "Node2", "Node3", "Node4"]
    for name, protocol in zip(outer_nodes, outer_protocols, strict=False):
        network.add_node(name, protocol)

    # Add connections from hub to all outer nodes
    for i, node_name in enumerate(outer_nodes):
        network.add_connection("Hub", node_name, outer_channels[i])

    # Display network statistics
    stats = network.get_network_statistics()
    print(f"  Network: {stats['network_name']}")
    print(f"  Number of nodes: {stats['num_nodes']}")
    print(f"  Number of connections: {stats['num_connections']}")
    print(f"  Average degree: {stats['average_degree']:.2f}")

    # Establish keys between hub and outer nodes
    print("  Establishing keys from hub to outer nodes...")
    for node_name in outer_nodes:
        key = network.establish_key_between_nodes("Hub", node_name, key_length=64)
        if key:
            print(f"  ✓ Key with {node_name}: Established")
        else:
            print(f"  ✗ Key with {node_name}: Failed")

    # Simulate network performance
    print("  Simulating network performance...")
    performance = network.simulate_network_performance(num_trials=100)
    print(f"  Success rate: {performance['success_rate']:.2%}")
    print(f"  Average key length: {performance['average_key_length']:.1f}")
    print(f"  Average QBER: {performance['average_qber']:.4f}")


def simulate_multiparty_qkd() -> None:
    """
    Simulate multi-party QKD in a network.
    """
    print("\nSimulating multi-party QKD...")

    # Create a multi-party QKD network
    participants = ["Alice", "Bob", "Charlie", "David"]
    mp_network = MultiPartyQKDNetwork(participants)

    # Add quantum channels between all pairs
    channels = {}
    for i, node1 in enumerate(participants):
        for j, node2 in enumerate(participants):
            if i < j:
                channels[(node1, node2)] = QuantumChannel(
                    loss=0.05 + 0.02 * abs(i - j),  # Distance-dependent loss
                    noise_model="depolarizing",
                    noise_level=0.02 + 0.01 * abs(i - j),
                )
                mp_network.add_channel(node1, node2, channels[(node1, node2)])

    # Establish conference key
    print("  Establishing conference key...")
    conference_key = MultiPartyQKDNetwork.conference_key_agreement(
        mp_network, participants, key_length=128
    )

    if conference_key:
        print("  ✓ Conference key established successfully")
        print(f"    Number of participants: {len(conference_key)}")
        # Show first participant's key share
        first_participant = list(conference_key.keys())[0]
        print(
            f"    {first_participant}'s key share (first 20 bits): {conference_key[first_participant][:20]}"
        )
    else:
        print("  ✗ Failed to establish conference key")

    # Simulate security
    print("  Simulating security analysis...")
    security_results = mp_network.simulate_security_analysis(num_trials=50)
    print(f"    Security success rate: {security_results['success_rate']:.2%}")
    print(f"    Average correlation: {security_results['average_correlation']:.4f}")
    print(f"    Average QBER: {security_results['average_qber']:.4f}")


def visualize_network_topologies() -> None:
    """
    Create visualizations of different network topologies.
    """
    print("\nCreating network topology visualizations...")

    # This would typically use network visualization libraries
    # For this example, we'll just print descriptions

    topologies = {
        "Linear": "Nodes connected in a line (Alice-Node1-Node2-...-Bob)",
        "Star": "Central hub connected to all outer nodes",
        "Ring": "Nodes connected in a ring topology",
        "Mesh": "Every node connected to every other node",
        "Tree": "Hierarchical structure with branching",
    }

    print("Network Topologies:")
    for name, description in topologies.items():
        print(f"  {name:8}: {description}")


def main() -> None:
    """
    Main function to run network simulations.
    """
    print("Quantum Network Simulation Examples")
    print("=" * 40)

    # Run simulations
    simulate_linear_network()
    simulate_star_network()
    simulate_multiparty_qkd()
    visualize_network_topologies()

    print("\nNetwork simulation examples completed!")


if __name__ == "__main__":
    main()
