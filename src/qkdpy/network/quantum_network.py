"""Advanced quantum network simulation for multi-party QKD."""

import time
from typing import Any

import numpy as np

from ..core import (
    QuantumChannel,
    TimingSynchronizer,
)
from ..protocols import BaseProtocol
from ..protocols.bb84 import BB84

# Import networkx if available, otherwise use a basic implementation
try:
    import networkx as nx

    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False

    # Use a simple graph implementation if networkx is not available
    class nx:
        @staticmethod
        def Graph():
            return SimpleGraph()

        @staticmethod
        def dijkstra_path(G, source, target):
            # Simple implementation of Dijkstra's algorithm
            return simple_dijkstra_path(G, source, target)


class SimpleGraph:
    """Simple graph implementation if networkx is not available."""

    def __init__(self):
        self.adjacency_list = {}

    def add_node(self, node):
        if node not in self.adjacency_list:
            self.adjacency_list[node] = set()

    def add_edge(self, node1, node2):
        self.add_node(node1)
        self.add_node(node2)
        self.adjacency_list[node1].add(node2)
        self.adjacency_list[node2].add(node1)

    def nodes(self):
        return self.adjacency_list.keys()

    def edges(self):
        edges = []
        for node1 in self.adjacency_list:
            for node2 in self.adjacency_list[node1]:
                if (node2, node1) not in edges:  # Avoid duplicate edges
                    edges.append((node1, node2))
        return edges

    def neighbors(self, node):
        return self.adjacency_list.get(node, set())


def simple_dijkstra_path(graph, source, target):
    """Simple implementation of Dijkstra's algorithm."""
    if not NETWORKX_AVAILABLE:
        # Initialize distances and previous nodes
        distances = {node: float("inf") for node in graph.nodes()}
        previous = dict.fromkeys(graph.nodes())
        distances[source] = 0
        unvisited = set(graph.nodes())

        while unvisited:
            # Find node with minimum distance
            current = min(unvisited, key=lambda node: distances[node])
            unvisited.remove(current)

            # If we reached the destination, break
            if current == target:
                break

            # Update distances to neighbors
            for neighbor in graph.neighbors(current):
                if neighbor in unvisited:
                    # Distance is 1 for each hop (simplified)
                    alt_distance = distances[current] + 1
                    if alt_distance < distances[neighbor]:
                        distances[neighbor] = alt_distance
                        previous[neighbor] = current

        # Reconstruct path
        path = []
        current_node = target
        while current_node is not None:
            path.append(current_node)
            current_node = previous[current_node]

        path.reverse()
        return path if path and path[0] == source else []
    else:
        # If networkx is available, this function won't be used
        return []


class QuantumNetwork:
    """Represents a quantum network with multiple nodes and connections."""

    def __init__(self, name: str = "Quantum Network", topology_type: str = "custom"):
        """Initialize a quantum network.

        Args:
            name: Name of the quantum network
            topology_type: Type of network topology ('custom', 'star', 'line', 'mesh', 'ring')
        """
        self.name = name
        self.topology_type = topology_type
        self.nodes: dict[str, QuantumNode] = {}
        self.connections: dict[tuple[str, str], QuantumChannel] = {}
        self.network_topology: dict[str, list[str]] = {}
        self.routing_table: dict[str, dict[str, list[str]]] = {}

        # Network-level timing synchronization
        self.timing_synchronizer = TimingSynchronizer()

        # Network topology graph
        self.graph = nx.Graph()

        # Network properties
        self.loss_budget: dict[tuple[str, str], float] = {}  # Track loss per connection
        self.latency_budget: dict[tuple[str, str], float] = (
            {}
        )  # Track latency per connection

    def add_node(
        self,
        node_id: str,
        protocol: BaseProtocol | None = None,
        position: tuple[float, float] = None,
    ) -> None:
        """Add a node to the quantum network.

        Args:
            node_id: Unique identifier for the node
            protocol: QKD protocol for the node (default: BB84)
            position: Geographic position as (latitude, longitude) or (x, y) coordinates
        """
        if node_id in self.nodes:
            raise ValueError(f"Node {node_id} already exists in the network")

        if protocol is None:
            # Create a default BB84 protocol with a noiseless channel
            channel = QuantumChannel()
            protocol = BB84(channel)

        self.nodes[node_id] = QuantumNode(node_id, protocol)
        self.graph.add_node(node_id, position=position)

    def add_connection(
        self,
        node1_id: str,
        node2_id: str,
        channel: QuantumChannel | None = None,
        distance: float = None,  # in km
        fiber_type: str = "standard",  # 'standard', 'dispersion-shifted', 'hollow-core'
        has_repeater: bool = False,
    ) -> None:
        """Add a quantum connection between two nodes.

        Args:
            node1_id: Identifier of the first node
            node2_id: Identifier of the second node
            channel: Quantum channel for the connection (default: noiseless)
            distance: Physical distance between nodes in km (if None, calculated from positions)
            fiber_type: Type of optical fiber ('standard', 'dispersion-shifted', 'hollow-core')
            has_repeater: Whether the connection has a quantum repeater
        """
        if node1_id not in self.nodes:
            raise ValueError(f"Node {node1_id} not found in the network")
        if node2_id not in self.nodes:
            raise ValueError(f"Node {node2_id} not found in the network")

        # Calculate distance if not provided
        if distance is None:
            pos1 = self.graph.nodes[node1_id].get("position")
            pos2 = self.graph.nodes[node2_id].get("position")
            if pos1 and pos2:
                # Calculate Euclidean distance between nodes
                distance = np.sqrt((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2)
            else:
                # Default distance if positions are not known
                distance = 10.0  # 10 km default

        # Set appropriate loss coefficient based on fiber type
        loss_coefficients = {
            "standard": 0.2,  # dB/km
            "dispersion-shifted": 0.18,
            "hollow-core": 0.1,
        }
        loss_coefficient = loss_coefficients.get(fiber_type, 0.2)

        if channel is None:
            # Create a channel with realistic properties based on distance and fiber type
            channel = QuantumChannel(
                distance=distance,
                loss_coefficient=loss_coefficient,
                detector_efficiency=0.1,
                misalignment_error=0.02,
                phase_fluctuation_rate=0.05,
                temperature=20.0,
            )

        # Add bidirectional connection
        self.connections[(node1_id, node2_id)] = channel
        self.connections[(node2_id, node1_id)] = channel

        # Update physical properties
        self.loss_budget[(node1_id, node2_id)] = channel.loss
        self.latency_budget[(node1_id, node2_id)] = (
            distance * 5.0e-6
        )  # 5 microsec/km approx
        if has_repeater:
            self.loss_budget[
                (node1_id, node2_id)
            ] /= 2  # Simplified model for repeaters

        # Update node connections
        self.nodes[node1_id].add_neighbor(node2_id, channel)
        self.nodes[node2_id].add_neighbor(node1_id, channel)

        # Add edge to network graph
        self.graph.add_edge(
            node1_id,
            node2_id,
            distance=distance,
            fiber_type=fiber_type,
            has_repeater=has_repeater,
        )

    def remove_node(self, node_id: str) -> None:
        """Remove a node from the quantum network.

        Args:
            node_id: Identifier of the node to remove
        """
        if node_id not in self.nodes:
            raise ValueError(f"Node {node_id} not found in the network")

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

    def get_shortest_path(
        self, source: str, destination: str, weight: str = "distance"
    ) -> list[str]:
        """Find the shortest path between two nodes using Dijkstra's algorithm.

        Args:
            source: Source node identifier
            destination: Destination node identifier
            weight: Weight attribute to use for path calculation ('distance', 'latency', or 'loss')

        Returns:
            List of node identifiers representing the shortest path
        """
        if source not in self.nodes:
            raise ValueError(f"Source node {source} not found")
        if destination not in self.nodes:
            raise ValueError(f"Destination node {destination} not found")

        # Use networkx to find shortest path based on given weight
        try:
            if weight == "distance":
                # Use physical distance as weight
                return nx.dijkstra_path(
                    self.graph, source, destination, weight="distance"
                )
            elif weight == "latency":
                # Calculate path based on latency (simplified model)
                # For now, use distance as proxy for latency
                return nx.dijkstra_path(
                    self.graph, source, destination, weight="distance"
                )
            elif weight == "loss":
                # Calculate path based on cumulative loss
                # For now, use distance as proxy for loss (longer distance = higher loss)
                return nx.dijkstra_path(
                    self.graph, source, destination, weight="distance"
                )
            else:
                # Use hop count as default
                return nx.dijkstra_path(self.graph, source, destination)
        except nx.NetworkXNoPath:
            # No path exists
            return []

    def establish_key_between_nodes(
        self,
        node1_id: str,
        node2_id: str,
        key_length: int = 128,
        path_type: str = "shortest",
        security_threshold: float = 0.11,  # BB84 security threshold
    ) -> dict[str, Any] | None:
        """Establish a quantum key between two nodes in the network.

        Args:
            node1_id: Identifier of the first node
            node2_id: Identifier of the second node
            key_length: Desired length of the key
            path_type: Type of path to use ('shortest', 'most_secure', 'lowest_loss')
            security_threshold: Maximum acceptable QBER for secure key

        Returns:
            Dictionary with key and metrics if successful, None otherwise
        """
        if node1_id not in self.nodes:
            raise ValueError(f"Node {node1_id} not found")
        if node2_id not in self.nodes:
            raise ValueError(f"Node {node2_id} not found")

        # Find appropriate path based on requirements
        if path_type == "shortest":
            path = self.get_shortest_path(node1_id, node2_id)
        elif path_type == "most_secure":
            path = self.get_shortest_path(node1_id, node2_id, weight="distance")
        elif path_type == "lowest_loss":
            path = self.get_shortest_path(node1_id, node2_id, weight="distance")
        else:
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
                protocol = self.nodes[node1_id].protocol
                protocol.channel = channel

                # Execute the protocol
                try:
                    results = protocol.execute()
                    if (
                        results.get("is_secure", False)
                        and results.get("qber", 1.0) < security_threshold
                    ):
                        final_key = results.get("final_key", [])
                        # Ensure we return a list of integers
                        if isinstance(final_key, list):
                            key_result = [int(bit) for bit in final_key[:key_length]]
                            return {
                                "key": key_result,
                                "qber": results.get("qber"),
                                "key_rate": (
                                    len(key_result) / protocol.key_length
                                    if protocol.key_length > 0
                                    else 0
                                ),
                                "path": path,
                                "security": results.get("is_secure"),
                            }
                except Exception as e:
                    print(f"Protocol execution failed: {e}")
                    return None
            return None

        # For multi-hop, implement entanglement swapping or other methods
        return self._establish_multihop_key(path, key_length, security_threshold)

    def _establish_multihop_key(
        self, path: list[str], key_length: int, security_threshold: float = 0.11
    ) -> dict[str, Any] | None:
        """Establish a key across multiple hops using realistic methods.

        Args:
            path: List of node identifiers representing the path
            key_length: Desired length of the final key
            security_threshold: Maximum acceptable QBER for secure key

        Returns:
            Dictionary with key and metrics if successful, None otherwise
        """
        if len(path) < 3:
            return None

        # For each hop, establish pairwise keys
        hop_results = []
        total_qber = 0.0
        all_secure = True

        for i in range(len(path) - 1):
            node1_id, node2_id = path[i], path[i + 1]

            # Get the channel between the nodes
            channel_key = (node1_id, node2_id)
            if channel_key not in self.connections:
                return None

            channel = self.connections[channel_key]
            # Update the protocol with the actual channel
            protocol = self.nodes[node1_id].protocol
            protocol.channel = channel

            # Execute the protocol
            try:
                results = protocol.execute()
                current_qber = results.get("qber", 1.0)
                total_qber += current_qber

                if (
                    results.get("is_secure", False)
                    and current_qber < security_threshold
                ):
                    final_key = results.get("final_key", [])
                    # Ensure we return a list of integers
                    if isinstance(final_key, list) and len(final_key) > 0:
                        hop_results.append(
                            {
                                "node_pair": (node1_id, node2_id),
                                "key": [int(bit) for bit in final_key[:key_length]],
                                "qber": current_qber,
                                "is_secure": True,
                            }
                        )
                    else:
                        all_secure = False
                        break
                else:
                    all_secure = False
                    break
            except Exception:
                all_secure = False
                break

        if not all_secure or not hop_results:
            return None

        # Combine hop keys with more realistic method
        # In a real quantum network, this would involve quantum repeaters and entanglement swapping
        # For this simulation, we'll create a combined key while considering accumulated errors
        avg_qber = total_qber / len(hop_results) if hop_results else 1.0

        # Create the final key by combining all hop keys
        if hop_results:
            # Start with the first key
            final_key = hop_results[0]["key"][:key_length].copy()

            # XOR in subsequent keys
            for i in range(1, len(hop_results)):
                hop_key = hop_results[i]["key"][: len(final_key)]  # Truncate to match
                for j in range(len(final_key)):
                    if j < len(hop_key):
                        final_key[j] ^= hop_key[j]

            # Adjust key length to desired size
            if len(final_key) > key_length:
                final_key = final_key[:key_length]
            elif len(final_key) < key_length:
                # Extend with random bits if needed
                extension = [
                    int(np.random.choice([0, 1]))
                    for _ in range(key_length - len(final_key))
                ]
                final_key.extend(extension)

            return {
                "key": final_key,
                "qber": min(avg_qber, 0.5),  # Cap at 0.5 for realistic bounds
                "path": path,
                "security": all_secure,
                "hop_results": hop_results,
            }

        return None

    def perform_entanglement_swapping(self, node1_id: str, node2_id: str) -> bool:
        """Perform entanglement swapping between two nodes.

        Args:
            node1_id: Identifier of the first node
            node2_id: Identifier of the second node

        Returns:
            True if successful, False otherwise
        """
        # Find path between nodes
        path = self.get_shortest_path(node1_id, node2_id)
        if len(path) < 3:  # Need at least one intermediate node
            return False

        # In a real implementation, this would involve:
        # 1. Creating entangled pairs between adjacent nodes
        # 2. Performing Bell measurements at intermediate nodes
        # 3. Communicating measurement results classically
        # 4. Applying corrections at the end nodes

        # For this simulation, we'll just verify that a path exists
        # and that all connections are functional
        for i in range(len(path) - 1):
            node_a, node_b = path[i], path[i + 1]
            channel_key = (node_a, node_b)
            if channel_key not in self.connections:
                return False

        return True

    def get_network_statistics(self) -> dict[str, Any]:
        """Get statistics about the quantum network.

        Returns:
            Dictionary with network statistics
        """
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

        return {
            "network_name": self.name,
            "num_nodes": num_nodes,
            "num_connections": num_connections,
            "average_degree": avg_degree,
            "network_diameter": float(diameter),
            "node_list": list(self.nodes.keys()),
            "connection_list": list(self.connections.keys()),
        }

    def simulate_network_performance(
        self,
        num_trials: int = 100,
        key_lengths: list[int] = None,
        path_selection: str = "random",
    ) -> dict[str, Any]:
        """Simulate the performance of the quantum network.

        Args:
            num_trials: Number of simulation trials
            key_lengths: List of key lengths to test (default: [64, 128, 256])
            path_selection: How to select paths ('random', 'shortest', 'all_pairs')

        Returns:
            Dictionary with simulation results
        """
        if key_lengths is None:
            key_lengths = [64, 128, 256]

        # Track performance metrics
        successful_key_exchanges = 0
        total_key_bits = 0
        qber_values: list[float] = []
        execution_times: list[float] = []
        key_rates: list[float] = []

        # Get all possible node pairs
        all_node_pairs = []
        if path_selection == "all_pairs":
            # Get all possible pairs of nodes
            node_ids = list(self.nodes.keys())
            for i, node1 in enumerate(node_ids):
                for node2 in node_ids[i + 1 :]:
                    if self.get_shortest_path(node1, node2):  # Make sure path exists
                        all_node_pairs.append((node1, node2))
        else:
            # Get all connected pairs
            for node1, node2 in self.connections:
                if (node2, node1) not in all_node_pairs:  # Avoid duplicates
                    all_node_pairs.append((node1, node2))

        if not all_node_pairs:
            return {"error": "No connections in the network"}

        # Run simulations
        for _trial in range(num_trials):
            # Select nodes based on path selection strategy
            node1_id, node2_id = all_node_pairs[np.random.randint(len(all_node_pairs))]

            # Select a random key length
            key_length = key_lengths[np.random.randint(len(key_lengths))]

            # Measure execution time
            start_time = time.time()

            # Try to establish a key
            try:
                result = self.establish_key_between_nodes(
                    node1_id, node2_id, key_length
                )
                execution_time = time.time() - start_time

                if result is not None and isinstance(result, dict) and "key" in result:
                    successful_key_exchanges += 1
                    total_key_bits += len(result["key"])
                    execution_times.append(execution_time)

                    # Track QBER
                    if "qber" in result:
                        qber_values.append(result["qber"])

                    # Track key rate
                    if "key_rate" in result:
                        key_rates.append(result["key_rate"])
                else:
                    execution_times.append(execution_time)
                    qber_values.append(1.0)  # High QBER for failed attempts
            except Exception:
                execution_times.append(time.time() - start_time)
                qber_values.append(1.0)  # High QBER for failed attempts

        # Calculate statistics
        success_rate = successful_key_exchanges / num_trials if num_trials > 0 else 0.0
        avg_key_length = (
            total_key_bits / successful_key_exchanges
            if successful_key_exchanges > 0
            else 0.0
        )
        avg_qber = float(np.mean(qber_values)) if qber_values else 0.0
        avg_execution_time = float(np.mean(execution_times)) if execution_times else 0.0
        avg_key_rate = float(np.mean(key_rates)) if key_rates else 0.0

        return {
            "num_trials": num_trials,
            "key_lengths_tested": key_lengths,
            "path_selection_strategy": path_selection,
            "successful_key_exchanges": successful_key_exchanges,
            "success_rate": success_rate,
            "average_key_length": avg_key_length,
            "average_qber": avg_qber,
            "average_key_rate": avg_key_rate,
            "average_execution_time": avg_execution_time,
            "qber_std": float(np.std(qber_values)) if qber_values else 0.0,
            "execution_time_std": (
                float(np.std(execution_times)) if execution_times else 0.0
            ),
            "key_rate_std": float(np.std(key_rates)) if key_rates else 0.0,
        }


class QuantumNode:
    """Represents a node in a quantum network."""

    def __init__(self, node_id: str, protocol: BaseProtocol):
        """Initialize a quantum node.

        Args:
            node_id: Unique identifier for the node
            protocol: QKD protocol for the node
        """
        self.node_id = node_id
        self.protocol = protocol
        self.neighbors: dict[str, QuantumChannel] = {}
        self.keys: dict[str, list[int]] = {}  # Shared keys with other nodes
        self.key_manager = None  # For key management

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

    def store_key(self, partner_id: str, key: list[int]) -> None:
        """Store a shared key with a partner node.

        Args:
            partner_id: Identifier of the partner node
            key: Shared key to store
        """
        self.keys[partner_id] = key

    def get_key(self, partner_id: str) -> list[int] | None:
        """Retrieve a shared key with a partner node.

        Args:
            partner_id: Identifier of the partner node

        Returns:
            Shared key if it exists, None otherwise
        """
        return self.keys.get(partner_id)

    def remove_key(self, partner_id: str) -> None:
        """Remove a shared key with a partner node.

        Args:
            partner_id: Identifier of the partner node
        """
        if partner_id in self.keys:
            del self.keys[partner_id]


class MultiPartyQKD:
    """Multi-party quantum key distribution protocols."""

    @staticmethod
    def conference_key_agreement(
        network: QuantumNetwork, participants: list[str], key_length: int = 128
    ) -> dict[str, list[int]] | None:
        """Implement a conference key agreement protocol for multiple parties.

        This is a simplified implementation that would use a hub-based approach
        in a real implementation.

        Args:
            network: Quantum network
            participants: List of participant node identifiers
            key_length: Desired length of the conference key

        Returns:
            Dictionary mapping participant IDs to their shares of the key,
            or None if the protocol fails
        """
        if len(participants) < 2:
            raise ValueError("At least 2 participants are required")

        # Check that all participants are in the network
        for participant in participants:
            if participant not in network.nodes:
                raise ValueError(f"Participant {participant} not found in network")

        # In a real implementation, we would use a true multi-party protocol
        # For this simplified version, we'll use a hub-based approach:
        # 1. Select a hub node (first participant)
        # 2. Hub establishes keys with all other participants
        # 3. Hub combines the keys to create a conference key
        # 4. Hub distributes shares of the key to participants

        hub_id = participants[0]
        other_participants = participants[1:]

        # Establish keys between hub and other participants
        shared_keys = {}
        for participant_id in other_participants:
            key = network.establish_key_between_nodes(
                hub_id, participant_id, key_length
            )
            if key is None:
                return None  # Failed to establish key with a participant
            shared_keys[participant_id] = key

        # Hub generates the conference key
        # In a real implementation, this would be done using quantum techniques
        conference_key = [np.random.randint(0, 2) for _ in range(key_length)]

        # Distribute shares of the key
        # In a real implementation, this would use quantum secret sharing
        key_shares = {}

        # Hub gets the master key
        key_shares[hub_id] = conference_key

        # Other participants get the key through secure channels
        for participant_id in other_participants:
            key_shares[participant_id] = conference_key

        return key_shares

    @staticmethod
    def quantum_secret_sharing(
        secret: list[int], num_shares: int, threshold: int
    ) -> list[list[int]]:
        """Implement quantum secret sharing to distribute a secret.

        This is a simplified classical implementation. A true quantum
        implementation would use quantum entanglement.

        Args:
            secret: Secret to share (list of bits)
            num_shares: Number of shares to create
            threshold: Minimum number of shares needed to reconstruct the secret

        Returns:
            List of secret shares
        """
        if threshold > num_shares:
            raise ValueError("Threshold cannot be greater than number of shares")
        if threshold < 1:
            raise ValueError("Threshold must be at least 1")

        # For this simplified implementation, we'll create a (n,n) scheme
        # where all shares are needed to reconstruct the secret
        # This is simpler and more reliable for demonstration purposes

        # Create random shares for the first (num_shares - 1) shares
        shares = []
        for _ in range(num_shares - 1):
            share = [np.random.randint(0, 2) for _ in range(len(secret))]
            shares.append(share)

        # Create the last share such that XOR of all shares equals the secret
        last_share = secret.copy()
        for share in shares:
            for j in range(len(secret)):
                last_share[j] ^= share[j]

        shares.append(last_share)

        return shares

    @staticmethod
    def reconstruct_secret(shares: list[list[int]]) -> list[int]:
        """Reconstruct a secret from its shares using XOR.

        Args:
            shares: List of secret shares

        Returns:
            Reconstructed secret
        """
        if not shares:
            raise ValueError("No shares provided")

        # XOR all shares to get the original secret
        secret = [0] * len(shares[0])
        for share in shares:
            for j in range(len(secret)):
                secret[j] ^= share[j]

        return secret
