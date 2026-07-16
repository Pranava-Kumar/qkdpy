"""Coverage tests for qkdpy.network (was ~52%).

Exercises public APIs in QuantumNetwork, RealisticQuantumNetwork,
MultiPartyQKD, MultiPartyQKDNetwork, SatelliteQKD, and related classes.
"""

import pytest

from qkdpy.core import QuantumChannel
from qkdpy.network import (
    AtmosphericProfile,
    FreeSpaceOpticalChannel,
    MultiPartyQKD,
    MultiPartyQKDNetwork,
    OrbitType,
    QuantumNetwork,
    QuantumNode,
    RealisticQuantumNetwork,
    RealisticQuantumNode,
    SatellitePosition,
    SatelliteQKD,
    simulate_satellite_qkd,
)
from qkdpy.protocols.bb84 import BB84

# --------------------------------------------------------------------------- #
#  QuantumNode  (basic node building-block)
# --------------------------------------------------------------------------- #


def test_quantum_node_create_and_connect() -> None:
    channel = QuantumChannel()
    protocol = BB84(channel)
    node = QuantumNode("alice", protocol)
    assert node.node_id == "alice"
    assert node.get_neighbors() == []

    node.add_neighbor("bob", channel)
    assert "bob" in node.get_neighbors()
    assert node.get_key("bob") is None

    key = [0, 1, 0, 1]
    node.store_key("bob", key)
    assert node.get_key("bob") == key

    node.remove_key("bob")
    assert node.get_key("bob") is None

    node.remove_neighbor("bob")
    assert "bob" not in node.get_neighbors()


# --------------------------------------------------------------------------- #
#  QuantumNetwork  (topology + key establishment)
# --------------------------------------------------------------------------- #


def test_quantum_network_add_node_and_connection() -> None:
    net = QuantumNetwork("test-net", "line")

    net.add_node("alice")
    net.add_node("bob")
    assert "alice" in net.nodes
    assert "bob" in net.nodes

    net.add_connection("alice", "bob")
    assert ("alice", "bob") in net.connections


def test_quantum_network_establish_key() -> None:
    net = QuantumNetwork("test-net")
    net.add_node("alice")
    net.add_node("bob")
    net.add_connection("alice", "bob")

    result = net.establish_key_between_nodes("alice", "bob", key_length=32)
    # Returns a dict with "key", "qber", "key_rate", "path", "security"
    # or None if key establishment failed (e.g. high QBER).
    if result is not None:
        assert isinstance(result, dict)
        key = result.get("key", [])
        assert isinstance(key, list)
        assert all(b in (0, 1) for b in key)


def test_quantum_network_statistics() -> None:
    net = QuantumNetwork("stats-net", "star")
    net.add_node("alice")
    net.add_node("bob")
    net.add_node("charlie")
    net.add_connection("alice", "bob")
    net.add_connection("alice", "charlie")

    stats = net.get_network_statistics()
    assert stats["num_nodes"] == 3
    assert stats["num_connections"] == 2
    assert stats["network_name"] == "stats-net"


# --------------------------------------------------------------------------- #
#  RealisticQuantumNode  (hardware-constrained node)
# --------------------------------------------------------------------------- #


def test_realistic_quantum_node_hardware() -> None:
    channel = QuantumChannel()
    protocol = BB84(channel)
    node = RealisticQuantumNode("rsu-alice", protocol)

    assert node.node_id == "rsu-alice"
    assert node.hardware_status == "operational"
    assert node.health == 1.0

    node.update_hardware_status()
    assert node.hardware_status in ("operational", "degraded", "failed")

    perf = node.get_performance_metrics()
    assert perf["node_id"] == "rsu-alice"
    assert 0.0 <= perf["health"] <= 1.0


def test_realistic_quantum_node_key_ops() -> None:
    channel = QuantumChannel()
    protocol = BB84(channel)
    node = RealisticQuantumNode("rsu-bob", protocol)

    assert node.store_key("alice", [0, 1, 0, 1]) is True
    assert node.get_key("alice") == [0, 1, 0, 1]

    assert node.remove_key("nonexistent") is False
    assert node.remove_key("alice") is True
    assert node.get_key("alice") is None


# --------------------------------------------------------------------------- #
#  RealisticQuantumNetwork
# --------------------------------------------------------------------------- #


def test_realistic_network_add_and_statistics() -> None:
    rnet = RealisticQuantumNetwork("real-net")
    assert rnet.add_node("alice") is True
    assert rnet.add_node("bob") is True
    assert rnet.add_node("alice") is False  # duplicate

    channel = QuantumChannel()
    assert rnet.add_connection("alice", "bob", channel) is True
    assert rnet.add_connection("alice", "nonexistent", channel) is False

    stats = rnet.get_network_statistics()
    assert stats["num_nodes"] == 2
    assert stats["network_name"] == "real-net"


def test_realistic_network_key_establishment() -> None:
    rnet = RealisticQuantumNetwork("key-net")
    rnet.add_node("alice")
    rnet.add_node("bob")
    rnet.add_connection("alice", "bob")
    key = rnet.establish_key_between_nodes("alice", "bob", key_length=32)
    if key is not None:
        assert isinstance(key, list)
        assert all(b in (0, 1) for b in key)


def test_realistic_network_calibrate_and_status() -> None:
    rnet = RealisticQuantumNetwork("cal-net")
    rnet.add_node("alice")
    rnet.add_node("bob")

    cal = rnet.calibrate_network()
    assert cal["successful_calibrations"] == 2
    assert cal["failed_calibrations"] == 0

    rnet.simulate_environmental_effects(time_step=1.0)
    rnet.update_network_status()
    assert rnet.network_status in ("operational", "degraded", "failed")


def test_realistic_network_remove_node() -> None:
    rnet = RealisticQuantumNetwork("rm-net")
    rnet.add_node("alice")
    rnet.add_node("bob")
    rnet.add_connection("alice", "bob")
    assert rnet.remove_node("alice") is True
    assert rnet.remove_node("alice") is False  # already gone
    assert "alice" not in rnet.nodes


# --------------------------------------------------------------------------- #
#  MultiPartyQKD  (conference key + secret sharing)
# --------------------------------------------------------------------------- #


def test_quantum_secret_sharing_roundtrip() -> None:
    secret = [1, 0, 1, 1, 0, 1]
    shares = MultiPartyQKD.quantum_secret_sharing(secret, num_shares=5, threshold=5)
    assert len(shares) == 5
    for s in shares:
        assert len(s) == len(secret)

    reconstructed = MultiPartyQKD.reconstruct_secret(shares)
    assert reconstructed == secret


def test_quantum_secret_sharing_threshold_validation() -> None:
    with pytest.raises(ValueError, match="greater than number of shares"):
        MultiPartyQKD.quantum_secret_sharing([1, 0], num_shares=3, threshold=5)
    with pytest.raises(ValueError, match="at least 1"):
        MultiPartyQKD.quantum_secret_sharing([1, 0], num_shares=3, threshold=0)


def test_conference_key_agreement_fails_with_one_participant() -> None:
    net = QuantumNetwork("conf-net")
    net.add_node("alice")
    with pytest.raises(ValueError, match="At least 2 participants"):
        MultiPartyQKD.conference_key_agreement(net, ["alice"])


# --------------------------------------------------------------------------- #
#  MultiPartyQKDNetwork
# --------------------------------------------------------------------------- #


def test_multiparty_qkd_network_add_channel() -> None:
    mpnet = MultiPartyQKDNetwork(["alice", "bob", "charlie"])
    channel = QuantumChannel()
    assert mpnet.add_channel("alice", "bob", channel) is True
    assert mpnet.add_channel("alice", "nonexistent", channel) is False
    assert mpnet.add_channel("alice", "alice", channel) is False


def test_multiparty_qkd_network_pairwise_key() -> None:
    mpnet = MultiPartyQKDNetwork(["alice", "bob"])
    channel = QuantumChannel()
    mpnet.add_channel("alice", "bob", channel)

    key = mpnet.establish_pairwise_key("alice", "bob", key_length=32)
    if key is not None:
        assert isinstance(key, list)
        assert all(b in (0, 1) for b in key)


def test_multiparty_qkd_network_statistics() -> None:
    mpnet = MultiPartyQKDNetwork(["alice", "bob", "charlie"])
    channel = QuantumChannel()
    mpnet.add_channel("alice", "bob", channel)
    mpnet.add_channel("bob", "charlie", channel)

    stats = mpnet.get_network_statistics()
    assert stats["num_nodes"] == 3
    assert stats["num_channels"] == 4  # 2 bidirectional = 4 entries
    assert "average_channel_loss" in stats


def test_multiparty_qkd_network_attack_simulation() -> None:
    mpnet = MultiPartyQKDNetwork(["alice", "bob", "charlie"])
    channel = QuantumChannel()
    mpnet.add_channel("alice", "bob", channel)
    mpnet.add_channel("bob", "charlie", channel)

    result = mpnet.simulate_network_attack("eavesdropping", ["alice"])
    assert result["attack_type"] == "eavesdropping"
    assert result["detection_status"] == "possible"

    dos = mpnet.simulate_network_attack("denial_of_service", ["bob"])
    assert dos["attack_type"] == "denial_of_service"

    mitm = mpnet.simulate_network_attack("man_in_the_middle", ["charlie"])
    assert mitm["attack_type"] == "man_in_the_middle"


def test_multiparty_qkd_network_broadcast_key() -> None:
    mpnet = MultiPartyQKDNetwork(["alice", "bob", "charlie"])
    keys = mpnet.broadcast_key("alice", key_length=16)
    assert "alice" in keys
    assert "bob" in keys
    assert "charlie" in keys
    assert len(keys["alice"]) == 16


def test_multiparty_qkd_network_topology_graph() -> None:
    mpnet = MultiPartyQKDNetwork(["alice", "bob"])
    channel = QuantumChannel()
    mpnet.add_channel("alice", "bob", channel)
    graph = mpnet.generate_network_topology_graph()
    assert graph["node_count"] == 2
    assert graph["edge_count"] >= 1


# --------------------------------------------------------------------------- #
#  SatelliteQKD  +  FreeSpaceOpticalChannel
# --------------------------------------------------------------------------- #


def test_satellite_position_from_orbit() -> None:
    pos = SatellitePosition.from_orbit(
        altitude_km=500,
        ground_lat=28.5,
        ground_lon=-80.6,
        sat_lat=30.0,
        sat_lon=-75.0,
    )
    assert pos.altitude_km == 500
    assert pos.slant_range_km > 0


def test_free_space_optical_channel() -> None:
    pos = SatellitePosition.from_orbit(500, 28.5, -80.6, 30.0, -75.0)
    channel = FreeSpaceOpticalChannel(pos)
    assert channel.distance > 0
    assert 0.0 <= channel.loss <= 1.0

    metrics = channel.get_channel_metrics()
    assert "slant_range_km" in metrics
    assert "total_loss_db" in metrics


def test_atmospheric_profile_defaults() -> None:
    atm = AtmosphericProfile()
    assert atm.visibility_km == 23.0
    assert atm.turbulence_cn2 == 1e-14


def test_satellite_qkd_simulate_pass() -> None:
    sat = SatelliteQKD(
        orbit_type=OrbitType.LEO,
        altitude_km=500,
        ground_station_lat=28.5,
        ground_station_lon=-80.6,
    )
    results = sat.simulate_pass(duration_seconds=120, time_steps=10)
    assert "time_points" in results
    assert "elevation_angles" in results
    assert "key_rates_bps" in results
    assert len(results["time_points"]) == 10
    assert results["total_key_bits"] > 0


def test_satellite_qkd_mission_summary() -> None:
    sat = SatelliteQKD(
        orbit_type=OrbitType.LEO,
        altitude_km=500,
        ground_station_lat=28.5,
        ground_station_lon=-80.6,
    )
    summary = sat.get_mission_summary()
    assert summary["orbit_type"] == "leo"
    assert summary["altitude_km"] == 500
    assert summary["total_passes_simulated"] == 0


def test_simulate_satellite_qkd_convenience() -> None:
    result = simulate_satellite_qkd(altitude_km=500, num_passes=3)
    assert "mission_summary" in result
    assert "pass_results" in result
    assert len(result["pass_results"]) == 3
