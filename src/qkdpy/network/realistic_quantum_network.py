"""Enhanced quantum network simulation with realistic hardware constraints."""

import time
from typing import Any

import numpy as np

from ..core import QuantumChannel
from ..key_management import QuantumKeyManager
from ..protocols import BaseProtocol
from ..protocols.bb84 import BB84


class RealisticQuantumNode:
    """Represents a node in a quantum network with realistic hardware constraints."""

    def __init__(self, node_id: str, protocol: BaseProtocol):
        """Initialize a realistic quantum node.

        Args:
            node_id: Unique identifier for the node
            protocol: QKD protocol for the node
        """
        self.node_id = node_id
        self.protocol = protocol
        self.neighbors: dict[str, QuantumChannel] = {}
        self.keys: dict[str, list[int]] = {}  # Shared keys with other nodes
        self.key_manager = QuantumKeyManager(QuantumChannel())  # For key management

        # Hardware constraints
        self.memory_capacity = 1000  # Number of qubits that can be stored
        self.memory_used = 0  # Currently used memory
        self.processing_rate = 1000  # Qubits per second processing rate
        self.detection_efficiency = 0.7  # Photon detection efficiency
        self.dark_count_rate = 1e-6  # Dark count rate per second
        self.jitter = 50e-12  # Timing jitter in seconds
        self.temperature = 293.15  # Temperature in Kelvin (20°C)
        self.hardware_status = "operational"  # operational, degraded, failed
        self.last_calibration = time.time()  # Last calibration time

        # Performance metrics
        self.key_generation_rate = 0.0  # Keys per second
        self.error_rate = 0.0  # Current error rate
        self.uptime = 0.0  # Uptime percentage

        # Hardware degradation model
        self.degradation_rate = 1e-9  # Degradation per operation
        self.health = 1.0  # Hardware health (1.0 = perfect, 0.0 = failed)

    def add_neighbor(self, neighbor_id: str, channel: QuantumChannel) -> None:
        """Add a neighbor to this node.

        Args:
            neighbor_id: Identifier of the neighbor node
            channel: Quantum channel to the neighbor
        """
        self.neighbors[neighbor_id] = channel

    def remove_neighbor(self, neighbor_id: str) -> None:
        """Remove a neighbor from this node.

        Args:
            neighbor_id: Identifier of the neighbor node to remove
        """
        if neighbor_id in self.neighbors:
            del self.neighbors[neighbor_id]

    def get_neighbors(self) -> list[str]:
        """Get the list of neighbor node identifiers.

        Returns:
            List of neighbor node identifiers
        """
        return list(self.neighbors.keys())

    def store_key(self, partner_id: str, key: list[int]) -> bool:
        """Store a shared key with a partner node.

        Args:
            partner_id: Identifier of the partner node
            key: Shared key to store

        Returns:
            True if key was stored successfully, False otherwise
        """
        # Check if we have enough memory
        if self.memory_used + len(key) > self.memory_capacity:
            return False

        self.keys[partner_id] = key.copy()
        self.memory_used += len(key)
        return True

    def get_key(self, partner_id: str) -> list[int] | None:
        """Retrieve a shared key with a partner node.

        Args:
            partner_id: Identifier of the partner node

        Returns:
            Shared key if it exists, None otherwise
        """
        return self.keys.get(partner_id)

    def remove_key(self, partner_id: str) -> bool:
        """Remove a shared key with a partner node.

        Args:
            partner_id: Identifier of the partner node

        Returns:
            True if key was removed, False if key didn't exist
        """
        if partner_id in self.keys:
            key_length = len(self.keys[partner_id])
            del self.keys[partner_id]
            self.memory_used = max(0, self.memory_used - key_length)
            return True
        return False

    def update_hardware_status(self) -> None:
        """Update the hardware status based on health and environmental conditions."""
        # Update hardware health based on degradation
        self.health = max(0.0, self.health - self.degradation_rate)

        # Check if hardware has failed
        if self.health < 0.1:
            self.hardware_status = "failed"
        elif self.health < 0.5:
            self.hardware_status = "degraded"
        else:
            self.hardware_status = "operational"

        # Update error rate based on health
        self.error_rate = 1.0 - self.health

    def calibrate(self) -> bool:
        """Calibrate the node hardware.

        Returns:
            True if calibration was successful, False otherwise
        """
        if self.hardware_status == "failed":
            return False

        # Reset health to a better state
        self.health = min(1.0, self.health + 0.1)
        self.last_calibration = time.time()

        # Update status
        self.update_hardware_status()
        return True

    def get_performance_metrics(self) -> dict[str, Any]:
        """Get performance metrics for this node.

        Returns:
            Dictionary with performance metrics
        """
        return {
            "node_id": self.node_id,
            "memory_usage": self.memory_used / self.memory_capacity,
            "health": self.health,
            "hardware_status": self.hardware_status,
            "key_generation_rate": self.key_generation_rate,
            "error_rate": self.error_rate,
            "uptime": self.uptime,
            "temperature": self.temperature,
            "detection_efficiency": self.detection_efficiency,
            "dark_count_rate": self.dark_count_rate,
            "processing_rate": self.processing_rate,
            "jitter": self.jitter,
            "last_calibration": self.last_calibration,
        }


class RealisticQuantumNetwork:
    """Represents a quantum network with realistic hardware constraints."""

    def __init__(self, name: str = "Realistic Quantum Network"):
        """Initialize a realistic quantum network.

        Args:
            name: Name of the quantum network
        """
        self.name = name
        self.nodes: dict[str, RealisticQuantumNode] = {}
        self.connections: dict[tuple[str, str], QuantumChannel] = {}
        self.network_topology: dict[str, list[str]] = {}
        self.routing_table: dict[str, dict[str, list[str]]] = {}

        # Network-wide constraints
        self.max_latency = 0.1  # Maximum latency in seconds
        self.min_fidelity = 0.8  # Minimum acceptable fidelity
        self.network_status = "operational"  # operational, degraded, failed
        self.total_qubits_processed = 0
        self.total_keys_generated = 0
        self.network_uptime = 0.0

        # Environmental factors
        self.ambient_temperature = 293.15  # Ambient temperature in Kelvin
        self.electromagnetic_interference = 0.0  # Interference level
        self.vibration_level = 0.0  # Vibration level

        # Performance tracking
        self.network_throughput = 0.0  # Keys per second
        self.average_latency = 0.0  # Average latency in seconds
        self.network_reliability = 1.0  # Network reliability

    def add_node(self, node_id: str, protocol: BaseProtocol | None = None) -> bool:
        """Add a node to the quantum network.

        Args:
            node_id: Unique identifier for the node
            protocol: QKD protocol for the node (default: BB84)

        Returns:
            True if node was added successfully, False otherwise
        """
        if node_id in self.nodes:
            return False

        if protocol is None:
            # Create a default BB84 protocol with a noiseless channel
            channel = QuantumChannel()
            protocol = BB84(channel)

        self.nodes[node_id] = RealisticQuantumNode(node_id, protocol)
        return True

    def add_connection(
        self, node1_id: str, node2_id: str, channel: QuantumChannel | None = None
    ) -> bool:
        """Add a quantum connection between two nodes.

        Args:
            node1_id: Identifier of the first node
            node2_id: Identifier of the second node
            channel: Quantum channel for the connection (default: noiseless)

        Returns:
            True if connection was added successfully, False otherwise
        """
        if node1_id not in self.nodes or node2_id not in self.nodes:
            return False

        if channel is None:
            channel = QuantumChannel()

        # Add bidirectional connection
        self.connections[(node1_id, node2_id)] = channel
        self.connections[(node2_id, node1_id)] = channel

        # Update node connections
        self.nodes[node1_id].add_neighbor(node2_id, channel)
        self.nodes[node2_id].add_neighbor(node1_id, channel)

        return True

    def remove_node(self, node_id: str) -> bool:
        """Remove a node from the quantum network.

        Args:
            node_id: Identifier of the node to remove

        Returns:
            True if node was removed successfully, False otherwise
        """
        if node_id not in self.nodes:
            return False

        # Remove connections to this node
        connections_to_remove = [
            conn for conn in self.connections.keys() if node_id in conn
        ]
        for conn in connections_to_remove:
            del self.connections[conn]

        # Remove node from other nodes' neighbor lists
        for node in self.nodes.values():
            if node_id in node.neighbors:
                del node.neighbors[node_id]

        # Remove the node
        del self.nodes[node_id]
        return True

    def get_shortest_path(self, source: str, destination: str) -> list[str]:
        """Find the shortest path between two nodes using Dijkstra's algorithm.

        Args:
            source: Source node identifier
            destination: Destination node identifier

        Returns:
            List of node identifiers representing the shortest path
        """
        if source not in self.nodes:
            raise ValueError(f"Source node {source} not found")
        if destination not in self.nodes:
            raise ValueError(f"Destination node {destination} not found")

        # Initialize distances and previous nodes
        distances = {node_id: float("inf") for node_id in self.nodes}
        previous = dict.fromkeys(self.nodes)
        distances[source] = 0

        # Set of unvisited nodes
        unvisited = set(self.nodes.keys())

        while unvisited:
            # Find node with minimum distance
            current = min(unvisited, key=lambda node: distances[node])
            unvisited.remove(current)

            # If we reached the destination, break
            if current == destination:
                break

            # Update distances to neighbors
            for neighbor_id in self.nodes[current].neighbors:
                if neighbor_id in unvisited:
                    # Distance is 1 for each hop (simplified)
                    alt_distance = distances[current] + 1
                    if alt_distance < distances[neighbor_id]:
                        distances[neighbor_id] = alt_distance
                        previous[neighbor_id] = current

        # Reconstruct path
        path = []
        current_node: str | None = destination
        while current_node is not None:
            path.append(current_node)
            prev = previous.get(current_node)
            current_node = prev if isinstance(prev, str | type(None)) else None

        path.reverse()

        # Return empty list if no path exists or path is empty
        return path if path and path[0] == source else []

    def establish_key_between_nodes(
        self, node1_id: str, node2_id: str, key_length: int = 128
    ) -> list[int] | None:
        """Establish a quantum key between two nodes in the network.

        Args:
            node1_id: Identifier of the first node
            node2_id: Identifier of the second node
            key_length: Desired length of the key

        Returns:
            Generated key if successful, None otherwise
        """
        if node1_id not in self.nodes:
            raise ValueError(f"Node {node1_id} not found")
        if node2_id not in self.nodes:
            raise ValueError(f"Node {node2_id} not found")

        # Check hardware status
        if (
            self.nodes[node1_id].hardware_status == "failed"
            or self.nodes[node2_id].hardware_status == "failed"
        ):
            return None

        # Find path between nodes
        path = self.get_shortest_path(node1_id, node2_id)
        if len(path) < 2:
            return None

        # For direct connection, use the protocol directly
        if len(path) == 2:
            # Get the channel between the nodes
            channel_key = (node1_id, node2_id)
            if channel_key in self.connections:
                channel = self.connections[channel_key]
                # Update the protocol with the actual channel
                self.nodes[node1_id].protocol.channel = channel

                # Execute the protocol
                try:
                    results = self.nodes[node1_id].protocol.execute()
                    if results.get("is_secure", False):
                        final_key = results.get("final_key", [])
                        # Ensure we return a list of integers
                        if isinstance(final_key, list):
                            key = [int(bit) for bit in final_key]
                            # Store the key
                            self.nodes[node1_id].store_key(node2_id, key)
                            self.nodes[node2_id].store_key(node1_id, key)
                            self.total_keys_generated += 1
                            return key
                except Exception:
                    pass

        # For multi-hop, implement entanglement swapping
        return self._establish_multihop_key(path, key_length)

    def _establish_multihop_key(
        self, path: list[str], key_length: int
    ) -> list[int] | None:
        """Establish a key across multiple hops using entanglement swapping.

        Args:
            path: List of node identifiers representing the path
            key_length: Desired length of the final key

        Returns:
            Generated key if successful, None otherwise
        """
        if len(path) < 3:
            return None

        # For each hop, establish pairwise keys
        hop_keys = []
        for i in range(len(path) - 1):
            node1_id, node2_id = path[i], path[i + 1]

            # Check hardware status
            if (
                self.nodes[node1_id].hardware_status == "failed"
                or self.nodes[node2_id].hardware_status == "failed"
            ):
                return None

            # Get the channel between the nodes
            channel_key = (node1_id, node2_id)
            if channel_key not in self.connections:
                return None

            channel = self.connections[channel_key]
            # Update the protocol with the actual channel
            self.nodes[node1_id].protocol.channel = channel

            # Execute the protocol
            try:
                results = self.nodes[node1_id].protocol.execute()
                if results.get("is_secure", False):
                    final_key = results.get("final_key", [])
                    # Ensure we return a list of integers
                    if isinstance(final_key, list) and len(final_key) > 0:
                        hop_keys.append([int(bit) for bit in final_key])
                    else:
                        return None
                else:
                    return None
            except Exception:
                return None

        # Perform entanglement swapping to create end-to-end key
        # In a real implementation, this would involve Bell measurements
        # For this simulation, we'll use a simplified approach:
        # XOR all hop keys together, truncated to the desired length
        if not hop_keys:
            return None

        # Start with the first key
        final_key = hop_keys[0].copy()

        # XOR with subsequent keys
        for i in range(1, len(hop_keys)):
            # Extend shorter keys with zeros or truncate longer ones
            max_len = min(len(final_key), len(hop_keys[i]))
            for j in range(max_len):
                final_key[j] ^= hop_keys[i][j]

        # Truncate or extend to desired length
        if len(final_key) > key_length:
            final_key = final_key[:key_length]
        elif len(final_key) < key_length:
            # Extend with random bits
            extension = [
                np.random.randint(0, 2) for _ in range(key_length - len(final_key))
            ]
            final_key.extend(extension)

        # Store the key at both end nodes
        self.nodes[path[0]].store_key(path[-1], final_key)
        self.nodes[path[-1]].store_key(path[0], final_key)
        self.total_keys_generated += 1

        return final_key

    def update_network_status(self) -> None:
        """Update the overall network status based on node health."""
        operational_nodes = 0
        total_nodes = len(self.nodes)

        for node in self.nodes.values():
            if node.hardware_status == "operational":
                operational_nodes += 1

        if total_nodes == 0:
            self.network_status = "failed"
            return

        operational_ratio = operational_nodes / total_nodes

        if operational_ratio < 0.3:
            self.network_status = "failed"
        elif operational_ratio < 0.7:
            self.network_status = "degraded"
        else:
            self.network_status = "operational"

    def get_network_statistics(self) -> dict[str, Any]:
        """Get statistics about the quantum network.

        Returns:
            Dictionary with network statistics
        """
        # Update network status
        self.update_network_status()

        # Calculate network metrics
        num_nodes = len(self.nodes)
        num_connections = len(self.connections) // 2  # Divide by 2 for bidirectional

        # Calculate average degree
        total_degree = sum(len(node.neighbors) for node in self.nodes.values())
        avg_degree = total_degree / num_nodes if num_nodes > 0 else 0.0

        # Find network diameter (longest shortest path)
        diameter = 0
        if num_nodes > 1:
            for node1_id in self.nodes:
                for node2_id in self.nodes:
                    if node1_id != node2_id:
                        path = self.get_shortest_path(node1_id, node2_id)
                        diameter = max(diameter, len(path) - 1 if path else 0)

        # Calculate average node health
        avg_health = (
            np.mean([node.health for node in self.nodes.values()])
            if self.nodes
            else 0.0
        )

        # Calculate memory usage
        total_memory = sum(node.memory_capacity for node in self.nodes.values())
        used_memory = sum(node.memory_used for node in self.nodes.values())
        memory_usage = used_memory / total_memory if total_memory > 0 else 0.0

        return {
            "network_name": self.name,
            "network_status": self.network_status,
            "num_nodes": num_nodes,
            "num_connections": num_connections,
            "average_degree": avg_degree,
            "network_diameter": float(diameter),
            "node_list": list(self.nodes.keys()),
            "connection_list": list(self.connections.keys()),
            "average_node_health": float(avg_health),
            "memory_usage": float(memory_usage),
            "total_keys_generated": self.total_keys_generated,
            "total_qubits_processed": self.total_qubits_processed,
            "ambient_temperature": self.ambient_temperature,
            "electromagnetic_interference": self.electromagnetic_interference,
            "vibration_level": self.vibration_level,
            "network_throughput": self.network_throughput,
            "average_latency": self.average_latency,
            "network_reliability": self.network_reliability,
        }

    def calibrate_network(self) -> dict[str, Any]:
        """Calibrate all nodes in the network.

        Returns:
            Dictionary with calibration results
        """
        results = {
            "successful_calibrations": 0,
            "failed_calibrations": 0,
            "calibrated_nodes": [],
            "failed_nodes": [],
        }

        for node_id, node in self.nodes.items():
            if node.calibrate():
                results["successful_calibrations"] += 1
                results["calibrated_nodes"].append(node_id)
            else:
                results["failed_calibrations"] += 1
                results["failed_nodes"].append(node_id)

        return results

    def simulate_environmental_effects(self, time_step: float = 1.0) -> None:
        """Simulate environmental effects on the network.

        Args:
            time_step: Time step in seconds
        """
        # Update environmental factors
        # Add some random fluctuations
        self.ambient_temperature += np.random.normal(0, 0.1)
        self.electromagnetic_interference = max(
            0, self.electromagnetic_interference + np.random.normal(0, 0.01)
        )
        self.vibration_level = max(0, self.vibration_level + np.random.normal(0, 0.01))

        # Apply environmental effects to nodes
        for node in self.nodes.values():
            # Temperature affects detection efficiency
            temp_effect = 1.0 - abs(node.temperature - self.ambient_temperature) * 1e-3
            node.detection_efficiency = max(
                0.1, node.detection_efficiency * temp_effect
            )

            # Vibration affects jitter
            node.jitter = max(10e-12, node.jitter * (1.0 + self.vibration_level * 1e-3))

            # EMI affects dark count rate
            node.dark_count_rate = max(
                1e-7,
                node.dark_count_rate * (1.0 + self.electromagnetic_interference * 1e-3),
            )

            # Update hardware status
            node.update_hardware_status()
