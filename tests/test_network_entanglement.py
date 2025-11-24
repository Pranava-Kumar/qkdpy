from qkdpy.network.quantum_network import QuantumNetwork


def test_entanglement_swapping():
    """Test entanglement swapping functionality."""
    network = QuantumNetwork("TestNet")

    # Setup: Node1 -- Relay -- Node2
    network.add_node("Alice", position=(0, 0))
    network.add_node("Relay", position=(10, 0))
    network.add_node("Bob", position=(20, 0))

    network.add_connection("Alice", "Relay", distance=10)
    network.add_connection("Relay", "Bob", distance=10)

    # Verify path exists
    path = network.get_shortest_path("Alice", "Bob")
    assert path == ["Alice", "Relay", "Bob"]

    # Perform swapping
    success = network.perform_entanglement_swapping("Alice", "Bob")

    # Should succeed with our new implementation
    assert success is True


def test_entanglement_swapping_no_path():
    """Test swapping failure when no path exists."""
    network = QuantumNetwork("TestNet")
    network.add_node("Alice")
    network.add_node("Bob")

    success = network.perform_entanglement_swapping("Alice", "Bob")
    assert success is False
