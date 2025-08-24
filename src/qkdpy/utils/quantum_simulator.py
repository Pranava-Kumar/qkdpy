"""Advanced quantum simulation and analysis tools."""

import time
from typing import Any

import numpy as np
import scipy.stats as stats

from ..core import QuantumChannel, Qubit
from ..protocols import BaseProtocol


class QuantumSimulator:
    """Advanced quantum system simulator for QKD analysis."""

    def __init__(self) -> None:
        """Initialize the quantum simulator."""
        self.simulation_history: list[dict[str, Any]] = []
        self.performance_stats: dict[str, Any] = {}

    def simulate_channel_performance(
        self,
        channel: QuantumChannel,
        num_trials: int = 1000,
        initial_state: Qubit | None = None,
    ) -> dict[str, Any]:
        """Simulate the performance of a quantum channel.

        Args:
            channel: Quantum channel to simulate
            num_trials: Number of simulation trials
            initial_state: Initial qubit state (default: |0>)

        Returns:
            Dictionary with simulation results
        """
        if initial_state is None:
            initial_state = Qubit.zero()

        # Reset channel statistics
        channel.reset_statistics()

        # Track fidelity and other metrics
        fidelities: list[float] = []
        received_states: list[Qubit] = []

        # Run simulation trials
        for _ in range(num_trials):
            # Create a copy of the initial state
            qubit = Qubit(initial_state.state[0], initial_state.state[1])

            # Transmit through channel
            received = channel.transmit(qubit)

            if received is not None:
                # Calculate fidelity
                fidelity = abs(np.vdot(initial_state.state, received.state)) ** 2
                fidelities.append(fidelity)
                received_states.append(received)

        # Calculate statistics
        stats_result: dict[str, Any] = {
            "transmission_rate": channel.get_statistics()["received"] / num_trials,
            "average_fidelity": float(np.mean(fidelities)) if fidelities else 0.0,
            "fidelity_std": float(np.std(fidelities)) if fidelities else 0.0,
            "min_fidelity": float(np.min(fidelities)) if fidelities else 0.0,
            "max_fidelity": float(np.max(fidelities)) if fidelities else 0.0,
            "channel_stats": channel.get_statistics(),
        }

        # Store in history
        self.simulation_history.append(
            {
                "type": "channel_performance",
                "timestamp": time.time(),
                "parameters": {
                    "num_trials": num_trials,
                    "initial_state": initial_state.state.tolist(),
                },
                "results": stats_result,
            }
        )

        return stats_result

    def analyze_protocol_security(
        self,
        protocol: BaseProtocol,
        num_simulations: int = 100,
        eavesdropping_probability: float = 0.5,
    ) -> dict[str, Any]:
        """Analyze the security of a QKD protocol under eavesdropping.

        Args:
            protocol: QKD protocol to analyze
            num_simulations: Number of security analysis simulations
            eavesdropping_probability: Probability of eavesdropping

        Returns:
            Dictionary with security analysis results
        """
        # Store original channel
        original_channel = protocol.channel

        # Results tracking
        secure_executions = 0
        insecure_executions = 0
        qber_values: list[float] = []
        key_rates: list[float] = []

        # Run security analysis simulations
        for _ in range(num_simulations):
            # Create a new channel for this simulation
            channel = QuantumChannel(
                loss=original_channel.loss,
                noise_model=original_channel.noise_model,
                noise_level=original_channel.noise_level,
            )

            # Set eavesdropper with specified probability
            if np.random.random() < eavesdropping_probability:
                channel.set_eavesdropper(QuantumChannel.intercept_resend_attack)

            # Update protocol with new channel
            protocol.channel = channel

            # Execute protocol
            try:
                results = protocol.execute()

                # Check if execution was secure
                if results.get("is_secure", False):
                    secure_executions += 1
                else:
                    insecure_executions += 1

                # Collect metrics
                qber_val = results.get("qber", 1.0)
                qber_values.append(
                    float(qber_val)
                    if isinstance(qber_val, int | float)
                    and not isinstance(qber_val, bool)
                    else 1.0
                )

                final_key = results.get("final_key", [])
                raw_key = results.get("raw_key", [0])
                key_rate = (len(final_key) if isinstance(final_key, list) else 0) / max(
                    1, len(raw_key) if isinstance(raw_key, list) else 1
                )
                key_rates.append(float(key_rate))

            except Exception:
                # Count failed executions
                insecure_executions += 1
                qber_values.append(1.0)
                key_rates.append(0.0)

        # Restore original channel
        protocol.channel = original_channel

        # Calculate security metrics
        security_rate = secure_executions / num_simulations
        avg_qber = float(np.mean(qber_values))
        avg_key_rate = float(np.mean(key_rates))

        # Statistical analysis
        qber_std = float(np.std(qber_values))
        key_rate_std = float(np.std(key_rates))

        security_results: dict[str, Any] = {
            "security_rate": security_rate,
            "insecure_rate": insecure_executions / num_simulations,
            "average_qber": avg_qber,
            "qber_std": qber_std,
            "average_key_rate": avg_key_rate,
            "key_rate_std": key_rate_std,
            "confidence_interval": self._calculate_confidence_interval(qber_values),
            "secure_executions": secure_executions,
            "insecure_executions": insecure_executions,
        }

        # Store in history
        self.simulation_history.append(
            {
                "type": "protocol_security",
                "timestamp": time.time(),
                "parameters": {
                    "num_simulations": num_simulations,
                    "eavesdropping_probability": eavesdropping_probability,
                },
                "results": security_results,
            }
        )

        return security_results

    def _calculate_confidence_interval(
        self, data: list[float], confidence: float = 0.95
    ) -> tuple[float, float]:
        """Calculate confidence interval for a dataset.

        Args:
            data: List of data points
            confidence: Confidence level (default: 0.95)

        Returns:
            Tuple of (lower_bound, upper_bound)
        """
        if len(data) < 2:
            return (0.0, 0.0)

        mean = float(np.mean(data))
        std_err = float(stats.sem(data))
        ci = stats.t.interval(confidence, len(data) - 1, loc=mean, scale=std_err)

        return (float(ci[0]), float(ci[1]))

    def benchmark_protocols(
        self, protocols: list[BaseProtocol], num_trials: int = 50
    ) -> dict[str, Any]:
        """Benchmark multiple QKD protocols.

        Args:
            protocols: List of QKD protocols to benchmark
            num_trials: Number of trials for each protocol

        Returns:
            Dictionary with benchmark results
        """
        benchmark_results: dict[str, Any] = {}

        for i, protocol in enumerate(protocols):
            # Track execution times
            execution_times: list[float] = []
            key_lengths: list[int] = []
            qber_values: list[float] = []

            # Run benchmark trials
            for _ in range(num_trials):
                start_time = time.time()

                try:
                    results = protocol.execute()
                    end_time = time.time()

                    execution_times.append(end_time - start_time)
                    final_key = results.get("final_key", [])
                    key_lengths.append(
                        len(final_key) if isinstance(final_key, list) else 0
                    )
                    qber_val = results.get("qber", 1.0)
                    qber_values.append(
                        float(qber_val)
                        if isinstance(qber_val, int | float)
                        and not isinstance(qber_val, bool)
                        else 1.0
                    )

                except Exception:
                    # Failed execution
                    execution_times.append(time.time() - start_time)
                    key_lengths.append(0)
                    qber_values.append(1.0)

            # Calculate statistics
            benchmark_results[f"protocol_{i}"] = {
                "name": protocol.__class__.__name__,
                "avg_execution_time": float(np.mean(execution_times)),
                "execution_time_std": float(np.std(execution_times)),
                "avg_key_length": float(np.mean(key_lengths)),
                "key_length_std": float(np.std(key_lengths)),
                "avg_qber": float(np.mean(qber_values)),
                "qber_std": float(np.std(qber_values)),
                "success_rate": sum(1 for kl in key_lengths if kl > 0) / num_trials,
            }

        # Store in history
        self.simulation_history.append(
            {
                "type": "protocol_benchmark",
                "timestamp": time.time(),
                "parameters": {
                    "num_protocols": len(protocols),
                    "num_trials": num_trials,
                },
                "results": benchmark_results,
            }
        )

        return benchmark_results

    def get_simulation_history(self) -> list[dict]:
        """Get the history of all simulations.

        Returns:
            List of simulation records
        """
        return self.simulation_history.copy()

    def clear_simulation_history(self) -> None:
        """Clear the simulation history."""
        self.simulation_history = []

    def get_performance_statistics(self) -> dict[str, Any]:
        """Get overall performance statistics.

        Returns:
            Dictionary with performance statistics
        """
        if not self.simulation_history:
            return {}

        total_simulations = len(self.simulation_history)
        simulation_types: dict[str, int] = {}

        # Count simulations by type
        for sim in self.simulation_history:
            sim_type = sim["type"]
            simulation_types[sim_type] = simulation_types.get(sim_type, 0) + 1

        return {
            "total_simulations": total_simulations,
            "simulation_types": simulation_types,
            "first_simulation": self.simulation_history[0]["timestamp"],
            "last_simulation": self.simulation_history[-1]["timestamp"],
        }


class QuantumNetworkAnalyzer:
    """Analyzer for quantum networks and multi-party QKD."""

    def __init__(self) -> None:
        """Initialize the quantum network analyzer."""
        self.network_topology: dict[str, Any] = {}
        self.node_performance: dict[str, Any] = {}

    def analyze_network_topology(
        self, nodes: list[str], connections: list[tuple[str, str, float]]
    ) -> dict[str, Any]:
        """Analyze a quantum network topology.

        Args:
            nodes: List of node identifiers
            connections: List of (node1, node2, distance) tuples

        Returns:
            Dictionary with network analysis results
        """
        # Store network information
        self.network_topology = {"nodes": nodes, "connections": connections}

        # Calculate network metrics
        num_nodes = len(nodes)
        num_connections = len(connections)

        # Calculate average distance
        avg_distance = (
            float(np.mean([conn[2] for conn in connections])) if connections else 0.0
        )

        # Find maximum distance
        max_distance = (
            float(max([conn[2] for conn in connections])) if connections else 0.0
        )

        # Calculate network density
        max_possible_connections = num_nodes * (num_nodes - 1) / 2
        network_density = (
            num_connections / max_possible_connections
            if max_possible_connections > 0
            else 0.0
        )

        results: dict[str, Any] = {
            "num_nodes": num_nodes,
            "num_connections": num_connections,
            "average_distance": avg_distance,
            "max_distance": max_distance,
            "network_density": network_density,
            "is_connected": self._check_network_connectivity(nodes, connections),
        }

        return results

    def _check_network_connectivity(
        self, nodes: list[str], connections: list[tuple[str, str, float]]
    ) -> bool:
        """Check if the network is connected.

        Args:
            nodes: List of node identifiers
            connections: List of connections

        Returns:
            True if network is connected, False otherwise
        """
        if not nodes:
            return True

        if not connections:
            return len(nodes) <= 1

        # Build adjacency list
        adj_list: dict[str, list[str]] = {node: [] for node in nodes}
        for node1, node2, _ in connections:
            if node1 in adj_list and node2 in adj_list:
                adj_list[node1].append(node2)
                adj_list[node2].append(node1)

        # Check connectivity using BFS
        visited = set()
        queue = [nodes[0]]
        visited.add(nodes[0])

        while queue:
            current = queue.pop(0)
            for neighbor in adj_list[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        return len(visited) == len(nodes)

    def simulate_network_performance(
        self, node_performance: dict[str, Any]
    ) -> dict[str, Any]:
        """Simulate network performance based on node performance.

        Args:
            node_performance: Dictionary mapping nodes to performance metrics

        Returns:
            Dictionary with network performance results
        """
        self.node_performance = node_performance

        # Calculate network-wide metrics
        if not node_performance:
            return {}

        # Extract key metrics
        key_rates = [
            float(perf.get("key_rate", 0)) for perf in node_performance.values()
        ]
        qber_values = [
            float(perf.get("qber", 1.0)) for perf in node_performance.values()
        ]
        distances = [
            float(perf.get("distance", 0)) for perf in node_performance.values()
        ]

        results: dict[str, Any] = {
            "network_avg_key_rate": float(np.mean(key_rates)),
            "network_key_rate_std": float(np.std(key_rates)),
            "network_avg_qber": float(np.mean(qber_values)),
            "network_qber_std": float(np.std(qber_values)),
            "network_avg_distance": float(np.mean(distances)),
            "best_performing_node": max(
                node_performance.keys(),
                key=lambda k: float(node_performance[k].get("key_rate", 0)),
            ),
            "worst_performing_node": min(
                node_performance.keys(),
                key=lambda k: float(node_performance[k].get("key_rate", 0)),
            ),
        }

        return results

    def get_network_statistics(self) -> dict[str, Any]:
        """Get overall network statistics.

        Returns:
            Dictionary with network statistics
        """
        return {
            "topology": self.network_topology,
            "node_performance": self.node_performance,
            "num_topology_records": len(self.network_topology),
            "num_performance_records": len(self.node_performance),
        }
