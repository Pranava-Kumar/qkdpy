"""Tests for protocol mapping, physics, and ML optimizer bridges."""

import json

import pytest

from qkdpy.integrations.qpiai_qkd import (
    LinkPhysics,
    Protocols,
    detect_anomaly,
    list_strategies,
    map_satellite_link,
    optimize_protocol,
)
from qkdpy.integrations.qpiai_qkd._compat import qpiai_available

pytestmark = pytest.mark.skipif(
    not qpiai_available(), reason="qpiai_quantum SDK not installed"
)


def test_protocols_builder_returns_circuit():
    p = Protocols()
    c = p.bb84(num_qubits=2)
    assert getattr(c.icr, "num_qubits", 0) == 2
    p.e91(num_pairs=1)
    bell, desc = p.bell("|Ψ+>")
    g = p.ghz(num_qubits=3)
    assert g is not None and bell is not None


def test_protocols_metrics_delegate():
    p = Protocols()
    assert p.qber([0, 1], [0, 1]) == 0.0


def test_physics_link_is_positive_loss_and_serialisable():
    link = map_satellite_link(
        wavelength_nm=1550, slant_range_km=1000, telescope_diameter_m=0.3
    )
    assert isinstance(link, LinkPhysics)
    assert link.total_link_loss_db > 0  # honest estimate, not a gain
    doc = json.loads(link.to_json())
    assert doc["wavelength_nm"] == 1550


def test_optimizer_runs_and_reports_method():
    result = optimize_protocol(
        "BB84",
        parameter_space={"detector_efficiency": (0.1, 0.99)},
        objective_function=lambda params: -((params["detector_efficiency"] - 0.8) ** 2),
        num_iterations=20,
        method="bayesian",
    )
    assert result["method"] == "bayesian"
    assert "best_parameters" in result


def test_optimizer_unknown_method_raises():
    with pytest.raises(ValueError):
        optimize_protocol(
            "BB84",
            parameter_space={"x": (0, 1)},
            objective_function=lambda p: 0.0,
            method="bogus",
        )


def test_list_strategies_nonempty():
    assert set(list_strategies()) >= {"bayesian", "genetic", "neural", "gradient"}


def test_detect_anomaly_returns_flags():
    flags = detect_anomaly({"qber": 0.02})
    assert isinstance(flags, dict)
    assert all(isinstance(v, bool) for v in flags.values())
