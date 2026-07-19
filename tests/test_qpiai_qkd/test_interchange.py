"""Tests for the ETSI-aligned interchange dataclasses."""

import json

from qkdpy.integrations.qpiai_qkd import (
    InterchangeStandard,
    KeyDelivery,
    KeyRequest,
    ProtocolExchange,
    ProtocolType,
    SAE2EStatus,
)


def test_key_request_roundtrip():
    req = KeyRequest(
        key_id="k1",
        sae_id="alice",
        target_sae_id="bob",
        number_of_keys=2,
        key_size=64,
    )
    parsed = KeyRequest.from_json(req.to_json())
    assert parsed.key_id == "k1"
    assert parsed.sae_id == "alice"
    assert parsed.target_sae_id == "bob"
    assert parsed.standard is InterchangeStandard.ETSI_GS_QKD_014


def test_key_delivery_roundtrip():
    delivery = KeyDelivery(
        key_id="k1",
        sae_id="alice",
        target_sae_id="bob",
        key="deadbeef",
        status="available",
    )
    parsed = KeyDelivery.from_json(delivery.to_json())
    assert parsed.key_id == "k1"
    assert parsed.key == "deadbeef"
    assert parsed.status.value == "available"


def test_sae2e_status_roundtrip():
    status = SAE2EStatus(source_sae_id="a", target_sae_id="b", relay="degraded")
    parsed = SAE2EStatus.from_json(status.to_json())
    assert parsed.relay.value == "degraded"
    assert parsed.standard is InterchangeStandard.ETSI_GS_QKD_015


def test_protocol_exchange_roundtrip():
    ex = ProtocolExchange(
        protocol=ProtocolType.E91,
        standard=InterchangeStandard.ETSI_GS_QKD_014,
        alice_bases=["Z", "X"],
        bob_bases=["X", "Z"],
        alice_bits=[0, 1],
        bob_bits=[1, 1],
        qber=0.25,
        chsh=2.6,
    )
    parsed = ProtocolExchange.from_json(ex.to_json())
    assert parsed.protocol is ProtocolType.E91
    assert parsed.qber == 0.25
    assert parsed.chsh == 2.6


def test_json_is_standards_tagged():
    delivery = KeyDelivery(key_id="k1", sae_id="a", target_sae_id="b")
    doc = json.loads(delivery.to_json())
    assert doc["standard"] == "ETSI_GS_QKD_014"
