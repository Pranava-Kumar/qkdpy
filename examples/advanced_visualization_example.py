"""Example of using advanced visualization and simulation tools."""

import numpy as np

from qkdpy.core import Qubit
from qkdpy.protocols import BB84
from qkdpy.utils import (
    AdvancedKeyRateAnalyzer,
    AdvancedProtocolVisualizer,
    QuantumNetworkAnalyzer,
    QuantumSimulator,
)


def advanced_visualization_example():
    """Demonstrates the advanced visualization and simulation tools."""
    print("Advanced Visualization and Simulation Example")
    print("=============================================")

    # 1. Advanced Protocol Visualizer
    print("\n1. Advanced Protocol Visualizer")

    # Plot quantum state evolution
    states = [
        Qubit.zero(),
        Qubit.plus(),
        Qubit.one(),
        Qubit.minus(),
        Qubit(1 / np.sqrt(2), 1j / np.sqrt(2)),  # |+i>
        Qubit(1 / np.sqrt(2), -1j / np.sqrt(2)),  # |-i>
    ]

    print("  - Creating quantum state evolution plot...")
    _ = AdvancedProtocolVisualizer.plot_quantum_state_evolution(
        states, "Quantum State Evolution on Bloch Sphere"
    )
    print("  - Quantum state evolution plot created")

    # Plot protocol comparison
    protocols_data = {
        "BB84": {"key_rate": 0.8, "qber": 0.05, "efficiency": 0.7},
        "B92": {"key_rate": 0.6, "qber": 0.08, "efficiency": 0.6},
        "E91": {"key_rate": 0.5, "qber": 0.03, "efficiency": 0.8},
        "SARG04": {"key_rate": 0.7, "qber": 0.06, "efficiency": 0.65},
    }

    print("  - Creating protocol comparison plot...")
    _ = AdvancedProtocolVisualizer.plot_protocol_comparison(
        protocols_data, "key_rate", "QKD Protocol Key Rate Comparison"
    )
    print("  - Protocol comparison plot created")

    # 2. Advanced Key Rate Analyzer
    print("\n2. Advanced Key Rate Analyzer")

    # Create a BB84 protocol for analysis
    from qkdpy.core import QuantumChannel

    channel = QuantumChannel(loss=0.1, noise_model="depolarizing", noise_level=0.05)
    protocol = BB84(channel, key_length=100)

    # Plot key rate vs parameter
    parameter_values = np.linspace(0, 0.5, 10)
    print("  - Creating key rate vs parameter plot...")
    _ = AdvancedKeyRateAnalyzer.plot_key_rate_vs_parameters(
        protocol, "channel_loss", parameter_values, "Key Rate vs Channel Loss"
    )
    print("  - Key rate vs parameter plot created")

    # 3. Quantum Simulator
    print("\n3. Quantum Simulator")
    simulator = QuantumSimulator()

    # Simulate channel performance
    print("  - Simulating channel performance...")
    channel_stats = simulator.simulate_channel_performance(
        channel, num_trials=1000, initial_state=Qubit.zero()
    )
    print(f"  - Transmission rate: {channel_stats['transmission_rate']:.4f}")
    print(f"  - Average fidelity: {channel_stats['average_fidelity']:.4f}")

    # Analyze protocol security
    print("  - Analyzing protocol security...")
    security_stats = simulator.analyze_protocol_security(
        protocol, num_simulations=50, eavesdropping_probability=0.3
    )
    print(f"  - Security rate: {security_stats['security_rate']:.4f}")
    print(f"  - Average QBER under eavesdropping: {security_stats['average_qber']:.4f}")

    # 4. Quantum Network Analyzer
    print("\n4. Quantum Network Analyzer")
    network_analyzer = QuantumNetworkAnalyzer()

    # Analyze network topology
    nodes = ["Alice", "Bob", "Charlie", "David"]
    connections = [
        ("Alice", "Bob", 10.0),
        ("Bob", "Charlie", 15.0),
        ("Charlie", "David", 12.0),
        ("Alice", "David", 20.0),
    ]

    print("  - Analyzing network topology...")
    topology_stats = network_analyzer.analyze_network_topology(nodes, connections)
    print(f"  - Number of nodes: {topology_stats['num_nodes']}")
    print(f"  - Number of connections: {topology_stats['num_connections']}")
    print(f"  - Network is connected: {topology_stats['is_connected']}")

    # Simulate network performance
    node_performance = {
        "Alice": {"key_rate": 0.8, "qber": 0.05, "distance": 10},
        "Bob": {"key_rate": 0.7, "qber": 0.06, "distance": 15},
        "Charlie": {"key_rate": 0.75, "qber": 0.04, "distance": 12},
        "David": {"key_rate": 0.65, "qber": 0.07, "distance": 20},
    }

    print("  - Simulating network performance...")
    network_stats = network_analyzer.simulate_network_performance(node_performance)
    print(f"  - Network average key rate: {network_stats['network_avg_key_rate']:.4f}")
    print(f"  - Best performing node: {network_stats['best_performing_node']}")
    print(f"  - Worst performing node: {network_stats['worst_performing_node']}")

    print(
        "\nExample completed. In a full implementation, the plots would be displayed."
    )


if __name__ == "__main__":
    advanced_visualization_example()
