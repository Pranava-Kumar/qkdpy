"""
Enterprise QKD Features Demo
===========================

This example demonstrates the new enterprise-grade features of QKDpy:
1. Advanced ML Optimization (Bayesian)
2. Secure Key Rotation
3. Entanglement Swapping
4. E91 Protocol Simulation
"""

import numpy as np

from qkdpy import QuantumChannel, QuantumNetwork
from qkdpy.crypto.key_exchange import QuantumKeyExchange
from qkdpy.integrations.qiskit_integration import QISKIT_AVAILABLE, QiskitIntegration
from qkdpy.ml.qkd_optimizer import QKDOptimizer


def demo_ml_optimization():
    print("\n--- 1. Machine Learning Optimization (Bayesian) ---")
    optimizer = QKDOptimizer("BB84")

    # Define a dummy objective function (e.g., maximizing key rate based on parameters)
    def objective(params):
        # Simulate key rate dependence on loss and noise
        # Optimal is low loss, low noise
        loss = params["loss"]
        noise = params["noise"]
        return 100 * np.exp(-loss) * (1 - noise * 5)

    param_space = {"loss": (0.0, 1.0), "noise": (0.0, 0.1)}

    print("Optimizing channel parameters...")
    result = optimizer.optimize_channel_parameters(
        param_space, objective, num_iterations=15, method="bayesian"
    )

    print(f"Best Parameters: {result['best_parameters']}")
    print(f"Best Objective Value: {result['best_objective_value']:.4f}")


def demo_key_rotation():
    print("\n--- 2. Secure Key Rotation ---")
    channel = QuantumChannel(loss=0.1, noise_level=0.01)
    exchange = QuantumKeyExchange(channel)

    print("Initiating session...")
    session_id = exchange.initiate_key_exchange("Alice", "Bob", key_length=128)

    if exchange.execute_key_exchange(session_id):
        key1 = exchange.get_shared_key(session_id)
        print(f"Initial Key (first 10 bits): {key1[:10]}...")

        print("Rotating key...")
        if exchange.rotate_key(session_id, new_key_length=128):
            key2 = exchange.get_shared_key(session_id)
            print(f"New Key (first 10 bits):     {key2[:10]}...")
            print(f"Keys are different: {key1 != key2}")
        else:
            print("Key rotation failed.")
    else:
        print("Initial exchange failed.")


def demo_entanglement_swapping():
    print("\n--- 3. Entanglement Swapping ---")
    network = QuantumNetwork("EntanglementNet")
    network.add_node("Alice", position=(0, 0))
    network.add_node("Relay", position=(10, 0))
    network.add_node("Bob", position=(20, 0))

    network.add_connection("Alice", "Relay", distance=10)
    network.add_connection("Relay", "Bob", distance=10)

    print("Performing entanglement swapping between Alice and Bob via Relay...")
    success = network.perform_entanglement_swapping("Alice", "Bob")
    print(f"Swapping successful: {success}")


def demo_e91_integration():
    print("\n--- 4. E91 Protocol with Qiskit ---")
    if not QISKIT_AVAILABLE:
        print("Qiskit not installed, skipping E91 demo.")
        return

    integration = QiskitIntegration()
    print("Simulating E91 protocol circuit...")
    alice_bits, bob_bits, _, _ = integration.simulate_e91_with_qiskit(num_pairs=5)

    print(f"Alice's bits: {alice_bits}")
    print(f"Bob's bits:   {bob_bits}")

    # In E91, perfect correlation in matching bases (simplified here)
    # Real E91 checks CHSH violation
    print("Simulation complete.")


if __name__ == "__main__":
    demo_ml_optimization()
    demo_key_rotation()
    demo_entanglement_swapping()
    demo_e91_integration()
