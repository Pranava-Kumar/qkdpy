"""Advanced quantum network simulation for multi-party QKD."""

import time

import numpy as np

from ..core import QuantumChannel
from ..protocols import BaseProtocol
from ..protocols.bb84 import BB84


class QuantumNetwork:
    """Represents a quantum network with multiple nodes and connections."""

    def __init__(self, name: str = "Quantum Network"):
        """Initialize a quantum network.

        Args:
            name: Name of the quantum network
        """
        self.name = name
        self.nodes: dict[str, QuantumNode] = {}
        self.connections: dict[tuple[str, str], QuantumChannel] = {}
        self.network_topology = {}
        self.routing_table = {}

    def add_node(self, node_id: str, protocol: BaseProtocol | None = None):
        """Add a node to the quantum network.

        Args:
            node_id: Unique identifier for the node
            protocol: QKD protocol for the node (default: BB84)
        """
        if node_id in self.nodes:
            raise ValueError(f"Node {node_id} already exists in the network")

        if protocol is None:
            # Create a default BB84 protocol with a noiseless channel
            channel = QuantumChannel()
            protocol = BB84(channel)

        self.nodes[node_id] = QuantumNode(node_id, protocol)

    def add_connection(
        self, node1_id: str, node2_id: str, channel: QuantumChannel | None = None
    ):
        """Add a quantum connection between two nodes.

        Args:
            node1_id: Identifier of the first node
            node2_id: Identifier of the second node
            channel: Quantum channel for the connection (default: noiseless)
        """
        if node1_id not in self.nodes:
            raise ValueError(f"Node {node1_id} not found in the network")
        if node2_id not in self.nodes:
            raise ValueError(f"Node {node2_id} not found in the network")

        if channel is None:
            channel = QuantumChannel()

        # Add bidirectional connection
        self.connections[(node1_id, node2_id)] = channel
        self.connections[(node2_id, node1_id)] = channel

        # Update node connections
        self.nodes[node1_id].add_neighbor(node2_id, channel)
        self.nodes[node2_id].add_neighbor(node1_id, channel)

    def remove_node(self, node_id: str):
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
        current = destination
        while current is not None:
            path.append(current)
            current = previous[current]

        path.reverse()

        # Return empty list if no path exists
        return path if path[0] == source else []

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
                        return results.get("final_key", [])
                except Exception:
                    pass

        # For multi-hop, we would need to implement key relay protocols
        # This is a simplified implementation that just returns None for multi-hop
        return None

    def get_network_statistics(self) -> dict:
        """Get statistics about the quantum network.

        Returns:
            Dictionary with network statistics
        """
        # Calculate network metrics
        num_nodes = len(self.nodes)
        num_connections = len(self.connections) // 2  # Divide by 2 for bidirectional

        # Calculate average degree
        total_degree = sum(len(node.neighbors) for node in self.nodes.values())
        avg_degree = total_degree / num_nodes if num_nodes > 0 else 0

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
            "network_diameter": diameter,
            "node_list": list(self.nodes.keys()),
            "connection_list": list(self.connections.keys()),
        }

    def simulate_network_performance(self, num_trials: int = 100) -> dict:
        """Simulate the performance of the quantum network.

        Args:
            num_trials: Number of simulation trials

        Returns:
            Dictionary with simulation results
        """
        # Track performance metrics
        successful_key_exchanges = 0
        total_key_bits = 0
        qber_values = []
        execution_times = []

        # Get all pairs of connected nodes
        node_pairs = []
        for node1, node2 in self.connections:
            if (node2, node1) not in node_pairs:  # Avoid duplicates
                node_pairs.append((node1, node2))

        if not node_pairs:
            return {"error": "No connections in the network"}

        # Run simulations
        for _ in range(num_trials):
            # Select a random pair of connected nodes
            node1_id, node2_id = node_pairs[np.random.randint(len(node_pairs))]

            # Measure execution time
            start_time = time.time()

            # Try to establish a key
            try:
                key = self.establish_key_between_nodes(node1_id, node2_id, 128)
                execution_time = time.time() - start_time

                if key is not None:
                    successful_key_exchanges += 1
                    total_key_bits += len(key)
                    execution_times.append(execution_time)

                    # For a more realistic simulation, we would track QBER
                    # This is a placeholder value
                    qber_values.append(np.random.uniform(0.01, 0.05))
            except Exception:
                execution_times.append(time.time() - start_time)
                qber_values.append(1.0)  # High QBER for failed attempts

        # Calculate statistics
        success_rate = successful_key_exchanges / num_trials if num_trials > 0 else 0
        avg_key_length = (
            total_key_bits / successful_key_exchanges
            if successful_key_exchanges > 0
            else 0
        )
        avg_qber = np.mean(qber_values) if qber_values else 0
        avg_execution_time = np.mean(execution_times) if execution_times else 0

        return {
            "num_trials": num_trials,
            "successful_key_exchanges": successful_key_exchanges,
            "success_rate": success_rate,
            "average_key_length": avg_key_length,
            "average_qber": avg_qber,
            "average_execution_time": avg_execution_time,
            "qber_std": np.std(qber_values) if qber_values else 0,
            "execution_time_std": np.std(execution_times) if execution_times else 0,
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

    def add_neighbor(self, neighbor_id: str, channel: QuantumChannel):
        """Add a neighbor to this node.

        Args:
            neighbor_id: Identifier of the neighbor node
            channel: Quantum channel to the neighbor
        """
        self.neighbors[neighbor_id] = channel

    def remove_neighbor(self, neighbor_id: str):
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

    def store_key(self, partner_id: str, key: list[int]):
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

    def remove_key(self, partner_id: str):
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
