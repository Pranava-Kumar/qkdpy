"""Multi-party QKD network simulation."""

import time

import numpy as np

from ..core import QuantumChannel
from ..protocols.bb84 import BB84


class MultiPartyQKDNetwork:
    """Simulation of a multi-party QKD network."""

    def __init__(self, nodes: list[str]):
        """Initialize a multi-party QKD network.

        Args:
            nodes: List of node identifiers in the network
        """
        self.nodes = nodes
        self.channels: dict[tuple[str, str], QuantumChannel] = {}
        self.keys: dict[tuple[str, str], list[int]] = {}
        self.network_topology = {}
        self.routing_table = {}
        self.security_log = []

    def add_channel(self, node1: str, node2: str, channel: QuantumChannel) -> bool:
        """Add a quantum channel between two nodes.

        Args:
            node1: First node identifier
            node2: Second node identifier
            channel: Quantum channel connecting the nodes

        Returns:
            True if channel was added successfully, False otherwise
        """
        if node1 not in self.nodes or node2 not in self.nodes:
            return False

        if node1 == node2:
            return False

        # Add channel in both directions (assuming symmetric channels)
        self.channels[(node1, node2)] = channel
        self.channels[(node2, node1)] = channel

        # Update network topology
        if node1 not in self.network_topology:
            self.network_topology[node1] = []
        if node2 not in self.network_topology:
            self.network_topology[node2] = []

        if node2 not in self.network_topology[node1]:
            self.network_topology[node1].append(node2)
        if node1 not in self.network_topology[node2]:
            self.network_topology[node2].append(node1)

        return True

    def establish_pairwise_key(
        self, node1: str, node2: str, key_length: int = 128
    ) -> list[int] | None:
        """Establish a pairwise key between two nodes.

        Args:
            node1: First node identifier
            node2: Second node identifier
            key_length: Desired key length

        Returns:
            Generated key if successful, None otherwise
        """
        # Check if nodes exist
        if node1 not in self.nodes or node2 not in self.nodes:
            self._log_security_event(
                "KEY_ESTABLISHMENT", "NODE_NOT_FOUND", node1, node2
            )
            return None

        # Check if direct channel exists
        channel_key = (node1, node2)
        if channel_key not in self.channels:
            # Try to find a path
            path = self._find_path(node1, node2)
            if not path:
                self._log_security_event("KEY_ESTABLISHMENT", "NO_PATH", node1, node2)
                return None

            # For multi-hop, we would need trusted relay or entanglement swapping
            # For now, we'll only support direct connections
            self._log_security_event(
                "KEY_ESTABLISHMENT", "NO_DIRECT_CHANNEL", node1, node2
            )
            return None

        # Get the channel
        channel = self.channels[channel_key]

        # Create QKD protocol instance
        protocol = BB84(channel, key_length=key_length)

        # Execute protocol
        try:
            results = protocol.execute()

            # Check if key generation was successful
            if results["is_secure"] and len(results["final_key"]) > 0:
                key = results["final_key"]

                # Store the key
                self.keys[(node1, node2)] = key.copy()
                if (node2, node1) in self.keys:
                    # Update reverse direction key (should be same in real implementation)
                    self.keys[(node2, node1)] = key.copy()

                self._log_security_event("KEY_ESTABLISHMENT", "SUCCESS", node1, node2)
                return key
            else:
                self._log_security_event("KEY_ESTABLISHMENT", "INSECURE", node1, node2)
                return None

        except Exception as e:
            self._log_security_event("KEY_ESTABLISHMENT", "ERROR", node1, node2, str(e))
            return None

    def _find_path(self, source: str, destination: str) -> list[str] | None:
        """Find a path between two nodes using BFS.

        Args:
            source: Source node
            destination: Destination node

        Returns:
            List of nodes representing the path, or None if no path exists
        """
        if (
            source not in self.network_topology
            or destination not in self.network_topology
        ):
            return None

        if source == destination:
            return [source]

        # BFS to find shortest path
        visited = set()
        queue = [(source, [source])]

        while queue:
            current_node, path = queue.pop(0)

            if current_node == destination:
                return path

            if current_node in visited:
                continue

            visited.add(current_node)

            for neighbor in self.network_topology.get(current_node, []):
                if neighbor not in visited:
                    queue.append((neighbor, path + [neighbor]))

        return None

    def broadcast_key(self, source: str, key_length: int = 128) -> dict[str, list[int]]:
        """Broadcast a key from source node to all other nodes.

        Args:
            source: Source node identifier
            key_length: Desired key length

        Returns:
            Dictionary mapping node identifiers to keys
        """
        if source not in self.nodes:
            return {}

        # Generate a master key
        master_key = [np.random.randint(0, 2) for _ in range(key_length)]

        # Distribute key to all nodes (simplified implementation)
        distributed_keys = {source: master_key}

        for node in self.nodes:
            if node != source:
                # In a real implementation, we would establish pairwise keys
                # and use them to securely distribute the master key
                # For now, we'll just generate random keys for each node
                distributed_keys[node] = [
                    np.random.randint(0, 2) for _ in range(key_length)
                ]

        return distributed_keys

    def get_network_statistics(self) -> dict:
        """Get network statistics.

        Returns:
            Dictionary with network statistics
        """
        # Calculate network connectivity
        total_possible_connections = len(self.nodes) * (len(self.nodes) - 1) // 2
        actual_connections = len(self.channels) // 2  # Divide by 2 for bidirectional

        connectivity = (
            actual_connections / total_possible_connections
            if total_possible_connections > 0
            else 0
        )

        # Calculate average channel quality
        if self.channels:
            avg_loss = np.mean([channel.loss for channel in self.channels.values()])
            avg_noise = np.mean(
                [channel.noise_level for channel in self.channels.values()]
            )
        else:
            avg_loss = 0.0
            avg_noise = 0.0

        return {
            "num_nodes": len(self.nodes),
            "num_channels": len(self.channels),
            "connectivity": connectivity,
            "average_channel_loss": avg_loss,
            "average_channel_noise": avg_noise,
            "num_established_keys": len(self.keys),
            "nodes": self.nodes.copy(),
        }

    def _log_security_event(
        self, event_type: str, status: str, node1: str, node2: str, details: str = ""
    ):
        """Log a security event.

        Args:
            event_type: Type of security event
            status: Status of the event
            node1: First node involved
            node2: Second node involved
            details: Additional details
        """
        self.security_log.append(
            {
                "timestamp": time.time(),
                "event_type": event_type,
                "status": status,
                "nodes": (node1, node2),
                "details": details,
            }
        )

    def get_security_log(self) -> list[dict]:
        """Get the security event log.

        Returns:
            List of security events
        """
        return self.security_log.copy()

    def simulate_network_attack(
        self, attack_type: str, target_nodes: list[str]
    ) -> dict:
        """Simulate a network attack.

        Args:
            attack_type: Type of attack ('eavesdropping', 'man_in_the_middle', 'denial_of_service')
            target_nodes: Nodes targeted by the attack

        Returns:
            Dictionary with attack simulation results
        """
        results = {
            "attack_type": attack_type,
            "target_nodes": target_nodes,
            "affected_channels": [],
            "detection_status": "unknown",
        }

        if attack_type == "eavesdropping":
            # Simulate eavesdropping on channels connected to target nodes
            affected_channels = []
            for node1, node2 in self.channels:
                if node1 in target_nodes or node2 in target_nodes:
                    affected_channels.append((node1, node2))
                    # Add an eavesdropper to the channel
                    self.channels[(node1, node2)].set_eavesdropper(
                        QuantumChannel.intercept_resend_attack
                    )

            results["affected_channels"] = affected_channels
            results["detection_status"] = (
                "possible"  # QKD protocols can detect eavesdropping
            )

        elif attack_type == "man_in_the_middle":
            # This is a more sophisticated attack that QKD protocols are designed to prevent
            results["detection_status"] = "high"  # QKD protocols should detect this

        elif attack_type == "denial_of_service":
            # Simulate channel disruption
            affected_channels = []
            for node1, node2 in self.channels:
                if node1 in target_nodes or node2 in target_nodes:
                    affected_channels.append((node1, node2))
                    # Increase loss rate to simulate DoS
                    self.channels[(node1, node2)].loss = min(
                        1.0, self.channels[(node1, node2)].loss + 0.5
                    )

            results["affected_channels"] = affected_channels
            results["detection_status"] = "likely"

        # Log the attack simulation
        self._log_security_event(
            "NETWORK_ATTACK_SIMULATION",
            attack_type,
            str(target_nodes),
            "",
            f"Simulated {attack_type} attack",
        )

        return results

    def generate_network_topology_graph(self) -> dict:
        """Generate a representation of the network topology.

        Returns:
            Dictionary with nodes and edges for graph visualization
        """
        edges = []
        for node1, node2 in self.channels:
            # Only add each edge once (since channels are bidirectional)
            if (node2, node1) not in edges:
                edges.append((node1, node2))

        return {
            "nodes": self.nodes.copy(),
            "edges": edges,
            "node_count": len(self.nodes),
            "edge_count": len(edges),
        }


class TrustedRelayNetwork(MultiPartyQKDNetwork):
    """Multi-party QKD network with trusted relay nodes."""

    def __init__(self, nodes: list[str], relay_nodes: list[str]):
        """Initialize a trusted relay QKD network.

        Args:
            nodes: List of all nodes in the network
            relay_nodes: List of trusted relay nodes
        """
        super().__init__(nodes)
        self.relay_nodes = relay_nodes

        # Validate that relay nodes are part of the network
        for relay in relay_nodes:
            if relay not in nodes:
                raise ValueError(f"Relay node {relay} not found in network nodes")

    def establish_multihop_key(
        self, source: str, destination: str, key_length: int = 128
    ) -> list[int] | None:
        """Establish a key between two nodes using trusted relays.

        Args:
            source: Source node identifier
            destination: Destination node identifier
            key_length: Desired key length

        Returns:
            Generated key if successful, None otherwise
        """
        # Find path using relays
        path = self._find_path_with_relays(source, destination)
        if not path:
            self._log_security_event(
                "MULTIHOP_KEY_ESTABLISHMENT", "NO_PATH", source, destination
            )
            return None

        # Generate keys for each hop
        hop_keys = []
        for i in range(len(path) - 1):
            node1, node2 = path[i], path[i + 1]
            key = self.establish_pairwise_key(node1, node2, key_length)
            if key is None:
                self._log_security_event(
                    "MULTIHOP_KEY_ESTABLISHMENT", "HOP_FAILED", node1, node2
                )
                return None
            hop_keys.append(key)

        # Combine hop keys using XOR (simplified approach)
        # In a real implementation, this would be more sophisticated
        final_key = hop_keys[0].copy()
        for i in range(1, len(hop_keys)):
            for j in range(len(final_key)):
                final_key[j] ^= hop_keys[i][j]

        # Store the end-to-end key
        self.keys[(source, destination)] = final_key
        if (destination, source) in self.keys:
            self.keys[(destination, source)] = final_key

        self._log_security_event(
            "MULTIHOP_KEY_ESTABLISHMENT", "SUCCESS", source, destination
        )
        return final_key

    def _find_path_with_relays(self, source: str, destination: str) -> list[str] | None:
        """Find a path between two nodes using trusted relays.

        Args:
            source: Source node
            destination: Destination node

        Returns:
            List of nodes representing the path, or None if no path exists
        """
        # Try direct path first
        direct_path = self._find_path(source, destination)
        if direct_path:
            return direct_path

        # Try paths through relays
        for relay in self.relay_nodes:
            if relay == source or relay == destination:
                continue

            # Find path from source to relay
            path_to_relay = self._find_path(source, relay)
            if not path_to_relay:
                continue

            # Find path from relay to destination
            path_from_relay = self._find_path(relay, destination)
            if not path_from_relay:
                continue

            # Combine paths
            full_path = path_to_relay[:-1] + path_from_relay
            return full_path

        return None

    def get_relay_statistics(self) -> dict:
        """Get statistics about relay usage.

        Returns:
            Dictionary with relay statistics
        """
        return {
            "relay_nodes": self.relay_nodes.copy(),
            "num_relays": len(self.relay_nodes),
            "total_nodes": len(self.nodes),
        }
