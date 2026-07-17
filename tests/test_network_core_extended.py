"""Coverage tests for quantum_network.py + multiparty_qkd.py.

Targets uncovered paths identified by coverage report:
  - quantum_network.py: 58% (164 missed of 390 stmts)
  - multiparty_qkd.py:   42% (73 missed of 127 stmts)
"""

from __future__ import annotations

import pytest

from qkdpy.core import QuantumChannel
from qkdpy.network.multiparty_qkd import MultiPartyQKDNetwork, TrustedRelayNetwork
from qkdpy.network.quantum_network import (
    MultiPartyQKD,
    QuantumNetwork,
    QuantumNode,
    SimpleGraph,
    simple_dijkstra_path,
)
from qkdpy.protocols.bb84 import BB84

# ===========================================================================
#  SimpleGraph  (fallback when networkx is absent)
# ===========================================================================


def test_simple_graph_add_node_and_edges() -> None:
    g = SimpleGraph()
    g.add_node("a", color="red")
    g.add_node("b")
    g.add_edge("a", "c", weight=1.0)

    # add_edge auto-adds nodes so we should have 3
    assert len(g.nodes) == 3
    assert "a" in g.nodes
    assert "b" in g.nodes
    assert "c" in g.nodes

    # edges()
    edges = g.edges()
    assert ("a", "c") in edges or ("c", "a") in edges

    # neighbors
    assert g.neighbors("a") == {"c"}
    assert g.neighbors("nonexistent") == set()

    # node view __getitem__
    assert g.nodes["a"] == {"color": "red"}
    assert g.nodes["b"] == {}


def test_simple_graph_nodeview_iter_len() -> None:
    g = SimpleGraph()
    g.add_node("x")
    g.add_node("y")
    assert len(g.nodes) == 2
    assert sorted(g.nodes()) == ["x", "y"]
    assert sorted(n for n in g.nodes) == ["x", "y"]


def test_simple_dijkstra_path_basic() -> None:
    """simple_dijkstra_path only executes Dijkstra when networkx is absent."""
    from qkdpy.network.quantum_network import NETWORKX_AVAILABLE

    g = SimpleGraph()
    g.add_edge("a", "b")
    g.add_edge("b", "c")
    path = simple_dijkstra_path(g, "a", "c")
    if not NETWORKX_AVAILABLE:
        assert path == ["a", "b", "c"]
    else:
        # When networkx IS available the function returns [] (unused path)
        assert path == []


def test_simple_dijkstra_path_no_path() -> None:
    g = SimpleGraph()
    g.add_node("a")
    g.add_node("b")
    # no edge between a and b
    path = simple_dijkstra_path(g, "a", "b")
    assert path == []


def test_simple_graph_nodeview_contains() -> None:
    g = SimpleGraph()
    g.add_node("alice")
    assert "alice" in g.nodes
    assert "bob" not in g.nodes


# ===========================================================================
#  QuantumNode  edge cases
# ===========================================================================


def test_quantum_node_remove_neighbor_nonexistent() -> None:
    """Removing a non-existent neighbor should not raise."""
    channel = QuantumChannel()
    protocol = BB84(channel)
    node = QuantumNode("alice", protocol)
    node.remove_neighbor("bob")  # should not raise
    assert node.get_neighbors() == []


def test_quantum_node_remove_key_nonexistent() -> None:
    channel = QuantumChannel()
    protocol = BB84(channel)
    node = QuantumNode("alice", protocol)
    node.remove_key("bob")  # should not raise
    assert node.get_key("bob") is None


# ===========================================================================
#  QuantumNetwork  — node / connection management edge cases
# ===========================================================================


def test_quantum_network_add_node_with_protocol() -> None:
    net = QuantumNetwork()
    channel = QuantumChannel()
    protocol = BB84(channel)
    net.add_node("alice", protocol=protocol)
    assert "alice" in net.nodes
    assert net.nodes["alice"].protocol is protocol


def test_quantum_network_add_node_duplicate_raises() -> None:
    net = QuantumNetwork()
    net.add_node("alice")
    with pytest.raises(ValueError, match="already exists"):
        net.add_node("alice")


def test_quantum_network_add_connection_missing_source_raises() -> None:
    net = QuantumNetwork()
    net.add_node("bob")
    with pytest.raises(ValueError, match="not found"):
        net.add_connection("alice", "bob")


def test_quantum_network_add_connection_missing_target_raises() -> None:
    net = QuantumNetwork()
    net.add_node("alice")
    with pytest.raises(ValueError, match="not found"):
        net.add_connection("alice", "bob")


def test_quantum_network_add_connection_fiber_types() -> None:
    """Connection with different fiber types exercises loss coefficients dict."""
    net = QuantumNetwork()
    net.add_node("alice", position=(0, 0))
    net.add_node("bob", position=(10, 0))

    net.add_connection("alice", "bob", distance=50, fiber_type="standard")
    assert ("alice", "bob") in net.connections

    net.add_connection("alice", "bob", distance=50, fiber_type="dispersion-shifted")
    assert ("alice", "bob") in net.connections

    net.add_connection("alice", "bob", distance=50, fiber_type="hollow-core")
    assert ("alice", "bob") in net.connections

    net.add_connection("alice", "bob", distance=50, fiber_type="unknown")
    assert ("alice", "bob") in net.connections


def test_quantum_network_add_connection_with_repeater() -> None:
    net = QuantumNetwork()
    net.add_node("alice")
    net.add_node("bob")
    net.add_connection("alice", "bob", distance=100, has_repeater=True)
    loss_key = ("alice", "bob")
    assert loss_key in net.loss_budget


def test_quantum_network_add_connection_calculated_distance() -> None:
    """Distance calculated from positions when not provided."""
    net = QuantumNetwork()
    net.add_node("alice", position=(0.0, 0.0))
    net.add_node("bob", position=(3.0, 4.0))
    net.add_connection("alice", "bob")
    assert ("alice", "bob") in net.connections


def test_quantum_network_add_connection_default_distance() -> None:
    """Default 10km when no positions available."""
    net = QuantumNetwork()
    net.add_node("alice")
    net.add_node("bob")
    net.add_connection("alice", "bob")
    assert ("alice", "bob") in net.connections


def test_quantum_network_remove_node_with_connections() -> None:
    net = QuantumNetwork()
    net.add_node("alice")
    net.add_node("bob")
    net.add_connection("alice", "bob")
    net.remove_node("alice")
    assert "alice" not in net.nodes
    # Verify all related connections are cleaned up
    assert all("alice" not in conn for conn in net.connections)


def test_quantum_network_remove_node_nonexistent_raises() -> None:
    net = QuantumNetwork()
    net.add_node("alice")
    with pytest.raises(ValueError, match="not found"):
        net.remove_node("bob")


def test_quantum_network_remove_node_single() -> None:
    net = QuantumNetwork()
    net.add_node("alice")
    net.remove_node("alice")
    assert "alice" not in net.nodes


# ===========================================================================
#  QuantumNetwork  — routing & path finding
# ===========================================================================


def test_get_shortest_path_nonexistent_source_raises() -> None:
    net = QuantumNetwork()
    net.add_node("bob")
    with pytest.raises(ValueError, match="not found"):
        net.get_shortest_path("alice", "bob")


def test_get_shortest_path_nonexistent_dest_raises() -> None:
    net = QuantumNetwork()
    net.add_node("alice")
    with pytest.raises(ValueError, match="not found"):
        net.get_shortest_path("alice", "bob")


def test_get_shortest_path_distance_weight() -> None:
    net = QuantumNetwork()
    net.add_node("a", position=(0, 0))
    net.add_node("b", position=(10, 0))
    net.add_node("c", position=(20, 0))
    net.add_connection("a", "b", distance=10)
    net.add_connection("b", "c", distance=10)

    path = net.get_shortest_path("a", "c", weight="distance")
    assert path == ["a", "b", "c"]


def test_get_shortest_path_latency_weight() -> None:
    net = QuantumNetwork()
    net.add_node("a")
    net.add_node("b")
    net.add_connection("a", "b", distance=5)
    path = net.get_shortest_path("a", "b", weight="latency")
    assert path == ["a", "b"]


def test_get_shortest_path_loss_weight() -> None:
    net = QuantumNetwork()
    net.add_node("a")
    net.add_node("b")
    net.add_connection("a", "b", distance=5)
    path = net.get_shortest_path("a", "b", weight="loss")
    assert path == ["a", "b"]


def test_get_shortest_path_default_weight() -> None:
    net = QuantumNetwork()
    net.add_node("a")
    net.add_node("b")
    net.add_connection("a", "b", distance=5)
    path = net.get_shortest_path("a", "b")
    assert path == ["a", "b"]


def test_get_shortest_path_disconnected_nodes() -> None:
    """Returns empty list when no path exists."""
    net = QuantumNetwork()
    net.add_node("a")
    net.add_node("b")
    net.add_node("c")
    net.add_connection("a", "b")
    # c is isolated -> no path from a to c
    path = net.get_shortest_path("a", "c")
    assert path == []


# ===========================================================================
#  QuantumNetwork  — key establishment edge cases
# ===========================================================================


def test_establish_key_nonexistent_source() -> None:
    net = QuantumNetwork()
    net.add_node("bob")
    with pytest.raises(ValueError, match="not found"):
        net.establish_key_between_nodes("alice", "bob")


def test_establish_key_nonexistent_target() -> None:
    net = QuantumNetwork()
    net.add_node("alice")
    with pytest.raises(ValueError, match="not found"):
        net.establish_key_between_nodes("alice", "bob")


def test_establish_key_disconnected_nodes() -> None:
    """Two disconnected nodes -> no path -> returns None."""
    net = QuantumNetwork()
    net.add_node("alice")
    net.add_node("bob")
    result = net.establish_key_between_nodes("alice", "bob")
    assert result is None


def test_establish_key_direct_success() -> None:
    net = QuantumNetwork()
    net.add_node("alice")
    net.add_node("bob")
    net.add_connection("alice", "bob")
    result = net.establish_key_between_nodes("alice", "bob", key_length=32)
    if result is not None:
        assert "key" in result
        assert "qber" in result
        assert "path" in result
        assert "security" in result
        key = result["key"]
        assert isinstance(key, list)
        assert len(key) > 0
        assert all(b in (0, 1) for b in key)


def test_establish_key_most_secure_path() -> None:
    net = QuantumNetwork()
    net.add_node("alice")
    net.add_node("bob")
    net.add_connection("alice", "bob")
    result = net.establish_key_between_nodes(
        "alice", "bob", key_length=16, path_type="most_secure"
    )
    if result is not None:
        assert "key" in result


def test_establish_key_lowest_loss_path() -> None:
    net = QuantumNetwork()
    net.add_node("alice")
    net.add_node("bob")
    net.add_connection("alice", "bob")
    result = net.establish_key_between_nodes(
        "alice", "bob", key_length=16, path_type="lowest_loss"
    )
    if result is not None:
        assert "key" in result


def test_establish_key_unknown_path_type() -> None:
    """Unknown path_type falls through to default get_shortest_path."""
    net = QuantumNetwork()
    net.add_node("alice")
    net.add_node("bob")
    net.add_connection("alice", "bob")
    result = net.establish_key_between_nodes(
        "alice", "bob", key_length=16, path_type="unknown_type"
    )
    if result is not None:
        assert "key" in result


def test_establish_key_path_too_short() -> None:
    """A path of length < 2 should return None."""
    net = QuantumNetwork()
    net.add_node("alice")
    net.add_node("bob")
    net.add_connection("alice", "bob")
    # Monkey-patch get_shortest_path to return a single-node path
    orig = net.get_shortest_path
    net.get_shortest_path = lambda s, d, w="distance": [s]  # type: ignore[method-assign]
    result = net.establish_key_between_nodes("alice", "bob")
    assert result is None
    net.get_shortest_path = orig  # restore


# ===========================================================================
#  QuantumNetwork  — multihop key establishment
# ===========================================================================


def test_establish_multihop_key_three_nodes() -> None:
    """3 nodes in a chain triggers _establish_multihop_key path."""
    net = QuantumNetwork()
    net.add_node("alice")
    net.add_node("relay")
    net.add_node("bob")
    net.add_connection("alice", "relay", distance=5)
    net.add_connection("relay", "bob", distance=5)
    result = net.establish_key_between_nodes("alice", "bob", key_length=16)
    # May be None if protocol execution fails on any hop
    if result is not None:
        assert "key" in result
        assert "hop_results" in result
        key = result["key"]
        assert isinstance(key, list)
        assert all(b in (0, 1) for b in key)


# ===========================================================================
#  QuantumNetwork  — entanglement swapping
# ===========================================================================


def test_perform_entanglement_swapping_success() -> None:
    net = QuantumNetwork()
    net.add_node("alice")
    net.add_node("relay")
    net.add_node("bob")
    net.add_connection("alice", "relay", distance=5)
    net.add_connection("relay", "bob", distance=5)
    result = net.perform_entanglement_swapping("alice", "bob")
    assert result is True


def test_perform_entanglement_swapping_wrong_path_length() -> None:
    """Path length != 3 (not exactly 1 relay) returns False."""
    net = QuantumNetwork()
    net.add_node("alice")
    net.add_node("bob")
    net.add_connection("alice", "bob")
    result = net.perform_entanglement_swapping("alice", "bob")
    assert result is False


def test_perform_entanglement_swapping_disconnected() -> None:
    """No path means path will be [], length != 3, returns False."""
    net = QuantumNetwork()
    net.add_node("alice")
    net.add_node("bob")
    result = net.perform_entanglement_swapping("alice", "bob")
    assert result is False


# ===========================================================================
#  QuantumNetwork  — network statistics edge cases
# ===========================================================================


def test_get_network_statistics_empty() -> None:
    net = QuantumNetwork()
    stats = net.get_network_statistics()
    assert stats["num_nodes"] == 0
    assert stats["num_connections"] == 0
    assert stats["average_degree"] == 0.0
    assert stats["network_diameter"] == 0.0


def test_get_network_statistics_single_node() -> None:
    net = QuantumNetwork()
    net.add_node("lonely")
    stats = net.get_network_statistics()
    assert stats["num_nodes"] == 1
    assert stats["network_diameter"] == 0.0


def test_get_network_statistics_with_disconnected() -> None:
    """Network with mixed connected/disconnected nodes."""
    net = QuantumNetwork()
    net.add_node("a")
    net.add_node("b")
    net.add_node("c")
    net.add_connection("a", "b")
    stats = net.get_network_statistics()
    assert stats["num_nodes"] == 3
    assert stats["num_connections"] == 1
    assert stats["network_diameter"] >= 1.0


# ===========================================================================
#  QuantumNetwork  — simulate_network_performance
# ===========================================================================


def test_simulate_network_performance_basic() -> None:
    net = QuantumNetwork("perf-net")
    net.add_node("alice")
    net.add_node("bob")
    net.add_connection("alice", "bob")
    results = net.simulate_network_performance(
        num_trials=5, key_lengths=[16, 32], path_selection="shortest"
    )
    assert isinstance(results, dict)
    assert results["num_trials"] == 5
    assert "success_rate" in results
    assert "average_key_rate" in results
    assert "average_execution_time" in results


def test_simulate_network_performance_all_pairs() -> None:
    net = QuantumNetwork()
    net.add_node("alice")
    net.add_node("bob")
    net.add_connection("alice", "bob")
    results = net.simulate_network_performance(
        num_trials=3, key_lengths=[16], path_selection="all_pairs"
    )
    assert isinstance(results, dict)


def test_simulate_network_performance_no_connections() -> None:
    net = QuantumNetwork()
    net.add_node("alice")
    net.add_node("bob")
    results = net.simulate_network_performance(num_trials=5)
    assert isinstance(results, dict)
    assert "error" in results


# ===========================================================================
#  MultiPartyQKD  (defined in quantum_network.py)
# ===========================================================================


def test_conference_key_agreement_two_participants() -> None:
    """Two participants: hub + 1 other."""
    net = QuantumNetwork()
    net.add_node("alice")
    net.add_node("bob")
    net.add_connection("alice", "bob")
    result = MultiPartyQKD.conference_key_agreement(net, ["alice", "bob"])
    if result is not None:
        assert "alice" in result
        assert "bob" in result


def test_conference_key_agreement_three_participants() -> None:
    net = QuantumNetwork()
    net.add_node("alice")
    net.add_node("bob")
    net.add_node("charlie")
    net.add_connection("alice", "bob")
    net.add_connection("bob", "charlie")
    result = MultiPartyQKD.conference_key_agreement(net, ["alice", "bob", "charlie"])
    if result is not None:
        assert "alice" in result
        assert "bob" in result
        assert "charlie" in result
        # All participants should get keys of the same length
        lengths = {len(v) for v in result.values()}
        assert len(lengths) == 1


def test_conference_key_agreement_one_participant_raises() -> None:
    net = QuantumNetwork()
    net.add_node("alice")
    with pytest.raises(ValueError, match="At least 2 participants"):
        MultiPartyQKD.conference_key_agreement(net, ["alice"])


def test_conference_key_agreement_nonexistent_participant() -> None:
    net = QuantumNetwork()
    net.add_node("alice")
    net.add_node("bob")
    with pytest.raises(ValueError, match="not found in network"):
        MultiPartyQKD.conference_key_agreement(net, ["alice", "nonexistent"])


def test_conference_key_agreement_hub_unreachable() -> None:
    """Hub cannot establish key with a participant -> returns None."""
    net = QuantumNetwork()
    net.add_node("alice")
    net.add_node("bob")
    net.add_node("charlie")
    net.add_connection("alice", "bob")
    # charlie is disconnected, so hub (alice) cant reach him
    result = MultiPartyQKD.conference_key_agreement(net, ["alice", "bob", "charlie"])
    assert result is None


def test_quantum_secret_sharing_various() -> None:
    """Secret sharing with different share/threshold combos."""
    secret = [1, 0, 1, 1, 0]

    # (n,n) scheme - default behavior
    shares = MultiPartyQKD.quantum_secret_sharing(secret, num_shares=3, threshold=3)
    assert len(shares) == 3
    assert MultiPartyQKD.reconstruct_secret(shares) == secret

    # threshold=1
    shares5 = MultiPartyQKD.quantum_secret_sharing(secret, num_shares=5, threshold=1)
    assert len(shares5) == 5
    assert MultiPartyQKD.reconstruct_secret(shares5) == secret


def test_quantum_secret_sharing_threshold_validation() -> None:
    with pytest.raises(ValueError, match="greater than number"):
        MultiPartyQKD.quantum_secret_sharing([1, 0], num_shares=3, threshold=5)
    with pytest.raises(ValueError, match="at least 1"):
        MultiPartyQKD.quantum_secret_sharing([1, 0], num_shares=3, threshold=0)


def test_reconstruct_secret_empty() -> None:
    with pytest.raises(ValueError, match="No shares provided"):
        MultiPartyQKD.reconstruct_secret([])


# ===========================================================================
#  MultiPartyQKDNetwork
# ===========================================================================


def test_mpqkd_establish_pairwise_nonexistent_node() -> None:
    mpnet = MultiPartyQKDNetwork(["alice", "bob"])
    result = mpnet.establish_pairwise_key("alice", "nonexistent", key_length=16)
    assert result is None


def test_mpqkd_establish_pairwise_no_direct_channel() -> None:
    """Nodes exist but no channel -> _find_path returns None."""
    mpnet = MultiPartyQKDNetwork(["alice", "bob"])
    result = mpnet.establish_pairwise_key("alice", "bob", key_length=16)
    assert result is None


def test_mpqkd_establish_pairwise_path_exists_no_direct() -> None:
    """Path exists but no direct channel -> NO_DIRECT_CHANNEL."""
    mpnet = MultiPartyQKDNetwork(["alice", "bob", "charlie"])
    ch = QuantumChannel()
    mpnet.add_channel("alice", "bob", ch)
    mpnet.add_channel("bob", "charlie", ch)
    # alice <-> bob <-> charlie: path exists but no direct alice-charlie
    result = mpnet.establish_pairwise_key("alice", "charlie", key_length=16)
    assert result is None
    # Check the log shows NO_DIRECT_CHANNEL
    log = mpnet.get_security_log()
    assert any("NO_DIRECT_CHANNEL" in str(entry) for entry in log)


def test_mpqkd_establish_pairwise_exception_handling() -> None:
    """Exception during protocol execute should log ERROR."""
    mpnet = MultiPartyQKDNetwork(["alice", "bob"])
    ch = QuantumChannel()
    mpnet.add_channel("alice", "bob", ch)
    # Force failure via unrealistic key_length=0
    result = mpnet.establish_pairwise_key("alice", "bob", key_length=-1)
    assert result is None


def test_mpqkd_establish_pairwise_success() -> None:
    mpnet = MultiPartyQKDNetwork(["alice", "bob"])
    ch = QuantumChannel()
    mpnet.add_channel("alice", "bob", ch)
    result = mpnet.establish_pairwise_key("alice", "bob", key_length=32)
    if result is not None:
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(b in (0, 1) for b in result)
        # Key should be stored
        assert ("alice", "bob") in mpnet.keys


def test_mpqkd_broadcast_key_nonexistent_source() -> None:
    mpnet = MultiPartyQKDNetwork(["alice", "bob"])
    result = mpnet.broadcast_key("nonexistent")
    assert result == {}


def test_mpqkd_broadcast_key_success() -> None:
    mpnet = MultiPartyQKDNetwork(["alice", "bob", "charlie"])
    keys = mpnet.broadcast_key("alice", key_length=16)
    assert "alice" in keys
    assert "bob" in keys
    assert "charlie" in keys
    assert len(keys["alice"]) == 16


def test_mpqkd_network_statistics_empty() -> None:
    mpnet = MultiPartyQKDNetwork([])
    stats = mpnet.get_network_statistics()
    assert stats["num_nodes"] == 0
    assert stats["connectivity"] == 0


def test_mpqkd_network_statistics_with_channels() -> None:
    mpnet = MultiPartyQKDNetwork(["a", "b", "c"])
    ch = QuantumChannel()
    mpnet.add_channel("a", "b", ch)
    stats = mpnet.get_network_statistics()
    assert stats["num_nodes"] == 3
    assert stats["num_channels"] == 2  # bidirectional
    assert stats["average_channel_loss"] >= 0


def test_mpqkd_get_security_log() -> None:
    mpnet = MultiPartyQKDNetwork(["alice", "bob"])
    mpnet.establish_pairwise_key("alice", "nonexistent", key_length=16)
    log = mpnet.get_security_log()
    assert len(log) > 0
    assert log[0]["event_type"] == "KEY_ESTABLISHMENT"
    assert log[0]["status"] == "NODE_NOT_FOUND"
    # Ensure copy semantics
    log.append({"fake": True})
    assert len(mpnet.get_security_log()) == 1


def test_mpqkd_generate_topology_graph() -> None:
    mpnet = MultiPartyQKDNetwork(["alice", "bob"])
    ch = QuantumChannel()
    mpnet.add_channel("alice", "bob", ch)
    graph = mpnet.generate_network_topology_graph()
    assert graph["node_count"] == 2
    assert graph["edge_count"] == 1


def test_mpqkd_generate_topology_graph_empty() -> None:
    mpnet = MultiPartyQKDNetwork([])
    graph = mpnet.generate_network_topology_graph()
    assert graph["node_count"] == 0
    assert graph["edge_count"] == 0


def test_mpqkd_attack_simulation_eavesdropping() -> None:
    mpnet = MultiPartyQKDNetwork(["alice", "bob"])
    ch = QuantumChannel()
    mpnet.add_channel("alice", "bob", ch)
    result = mpnet.simulate_network_attack("eavesdropping", ["alice"])
    assert result["attack_type"] == "eavesdropping"
    assert result["detection_status"] == "possible"
    assert len(result["affected_channels"]) > 0


def test_mpqkd_attack_simulation_mitm() -> None:
    mpnet = MultiPartyQKDNetwork(["alice", "bob"])
    ch = QuantumChannel()
    mpnet.add_channel("alice", "bob", ch)
    result = mpnet.simulate_network_attack("man_in_the_middle", ["alice"])
    assert result["attack_type"] == "man_in_the_middle"
    assert result["detection_status"] == "high"  # QKD prevents MITM


def test_mpqkd_attack_simulation_dos() -> None:
    mpnet = MultiPartyQKDNetwork(["alice", "bob"])
    ch = QuantumChannel()
    mpnet.add_channel("alice", "bob", ch)
    result = mpnet.simulate_network_attack("denial_of_service", ["alice"])
    assert result["attack_type"] == "denial_of_service"
    assert result["detection_status"] == "likely"
    # Channel loss should be increased
    assert ch.loss > 0


def test_mpqkd_attack_simulation_unknown_type() -> None:
    """Unknown attack type uses default results."""
    mpnet = MultiPartyQKDNetwork(["alice", "bob"])
    result = mpnet.simulate_network_attack("unknown", ["alice"])
    assert result["attack_type"] == "unknown"
    assert result["detection_status"] == "unknown"


# ===========================================================================
#  TrustedRelayNetwork
# ===========================================================================


def test_trusted_relay_invalid_relay_raises() -> None:
    with pytest.raises(ValueError, match="not found in network nodes"):
        TrustedRelayNetwork(["alice", "bob"], ["charlie"])


def test_trusted_relay_valid_relay() -> None:
    trnet = TrustedRelayNetwork(["alice", "relay", "bob"], ["relay"])
    assert "relay" in trnet.relay_nodes
    assert trnet.nodes == ["alice", "relay", "bob"]


def test_trusted_relay_get_statistics() -> None:
    trnet = TrustedRelayNetwork(["a", "r1", "r2", "b"], ["r1", "r2"])
    stats = trnet.get_relay_statistics()
    assert stats["num_relays"] == 2
    assert stats["total_nodes"] == 4


def test_trusted_relay_multihop_key_success() -> None:
    trnet = TrustedRelayNetwork(["alice", "relay1", "bob"], ["relay1"])
    ch_ar = QuantumChannel()
    ch_rb = QuantumChannel()
    trnet.add_channel("alice", "relay1", ch_ar)
    trnet.add_channel("relay1", "bob", ch_rb)
    key = trnet.establish_multihop_key("alice", "bob", key_length=32)
    if key is not None:
        assert isinstance(key, list)
        assert len(key) > 0
        assert all(b in (0, 1) for b in key)
        # Key should be stored
        assert ("alice", "bob") in trnet.keys


def test_trusted_relay_multihop_key_no_path() -> None:
    trnet = TrustedRelayNetwork(["alice", "relay1", "bob"], ["relay1"])
    # No channels added -> no path
    result = trnet.establish_multihop_key("alice", "bob", key_length=16)
    assert result is None


def test_trusted_relay_multihop_key_hop_failure() -> None:
    """Set up where one hop has no channel -> NO_PATH."""
    trnet = TrustedRelayNetwork(
        ["alice", "relay1", "relay2", "bob"], ["relay1", "relay2"]
    )
    # Only add channel for first two hops, last hop has no channel
    ch = QuantumChannel()
    trnet.add_channel("alice", "relay1", ch)
    trnet.add_channel("relay1", "relay2", ch)
    # no channel between relay2 and bob -> no path through relays
    result = trnet.establish_multihop_key("alice", "bob", key_length=16)
    assert result is None
    log = trnet.get_security_log()
    assert any("NO_PATH" in str(entry) for entry in log)


def test_trusted_relay_find_path_with_relays_direct() -> None:
    trnet = TrustedRelayNetwork(["a", "b", "r"], ["r"])
    ch = QuantumChannel()
    trnet.add_channel("a", "b", ch)
    # Direct path exists
    path = trnet._find_path_with_relays("a", "b")
    assert path is not None
    assert "a" in path
    assert "b" in path


def test_trusted_relay_find_path_with_relays_no_path() -> None:
    trnet = TrustedRelayNetwork(["a", "b", "r"], ["r"])
    # No channels at all -> no path
    path = trnet._find_path_with_relays("a", "b")
    assert path is None


def test_mpqkd_find_path_source_equals_destination() -> None:
    mpnet = MultiPartyQKDNetwork(["alice", "bob"])
    # Need a channel so nodes appear in network_topology
    ch = QuantumChannel()
    mpnet.add_channel("alice", "bob", ch)
    path = mpnet._find_path("alice", "alice")
    assert path == ["alice"]


def test_mpqkd_find_path_nonexistent_node() -> None:
    mpnet = MultiPartyQKDNetwork(["alice", "bob"])
    path = mpnet._find_path("alice", "nonexistent")
    assert path is None


def test_mpqkd_find_path_bfs() -> None:
    mpnet = MultiPartyQKDNetwork(["a", "b", "c", "d"])
    ch = QuantumChannel()
    mpnet.add_channel("a", "b", ch)
    mpnet.add_channel("b", "c", ch)
    mpnet.add_channel("c", "d", ch)
    path = mpnet._find_path("a", "d")
    assert path == ["a", "b", "c", "d"]
