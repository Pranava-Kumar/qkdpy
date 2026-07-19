"""IEC/ETSI-aligned QKD interchange model for the qpiai-qkd companion.

These dataclasses model the wire-level documents a QKD Key Management Entity
(KME) exchanges with a Shared Authority (SAE), following the ETSI GS QKD series:

* **ETSI GS QKD 014** — Key delivery API (key request / key delivery objects).
* **ETSI GS QKD 015** — SAE-to-SAE status / relay exchanges.

They are intentionally plain, serialisable containers: a qkdpy protocol run can
be mapped onto a :class:`ProtocolExchange`, serialised with ``to_json()`` (or
``model_dump_json()``), and re-parsed with ``from_json()``. The shapes mirror
the ETSI field names so they slot into an interchange layer without silent
renaming.

This module does NOT claim certification under any ETSI specification — it is a
faithful *modelling* of the documented field layout, suitable for interop
testing and tooling.
"""

from __future__ import annotations

import json
from dataclasses import (
    asdict,
    dataclass,
    field,
)
from enum import StrEnum
from typing import Any


class InterchangeStandard(StrEnum):
    """Standards a key-delivery document is tagged against."""

    ETSI_GS_QKD_014 = "ETSI_GS_QKD_014"  # Key delivery API
    ETSI_GS_QKD_015 = "ETSI_GS_QKD_015"  # SAE-to-SAE status


class ProtocolType(StrEnum):
    """QKD protocols the companion can map to an interchange document."""

    BB84 = "BB84"
    E91 = "E91"
    ENTANGLEMENT = "ENTANGLEMENT"
    GHZ = "GHZ"


class KeyStatus(StrEnum):
    """Lifecycle status of a delivered key (ETSI GS QKD 014)."""

    CREATED = "created"
    AVAILABLE = "available"
    IN_USE = "in_use"
    DISCARDED = "discarded"
    EXPIRED = "expired"


class SAE2ERelay(StrEnum):
    """SAE-to-SAE relay status (ETSI GS QKD 015)."""

    OK = "ok"
    DEGRADED = "degraded"
    FAILED = "failed"


@dataclass
class KeyRequest:
    """ETSI GS QKD 014 key request payload.

    Sent by an SAE to a KME to ask for key material. ``qos`` expresses the
    requested Quality of Service (e.g. minimum key size / rate).
    """

    key_id: str
    sae_id: str
    target_sae_id: str
    number_of_keys: int = 1
    key_size: int = 32  # bits
    qos: int = 1
    standard: InterchangeStandard = InterchangeStandard.ETSI_GS_QKD_014

    def to_json(self) -> str:
        return json.dumps(_to_public(self), indent=2, sort_keys=True)

    @classmethod
    def from_json(cls, payload: str | dict[str, Any]) -> KeyRequest:
        data = payload if isinstance(payload, dict) else json.loads(payload)
        data = _coerce(data, {"standard": InterchangeStandard})
        return cls(**data)


@dataclass
class KeyDelivery:
    """ETSI GS QKD 014 key delivery payload (the key material response)."""

    key_id: str
    sae_id: str
    target_sae_id: str
    status: KeyStatus = KeyStatus.AVAILABLE
    key: str | None = None  # hex-encoded key material (omitted in-band in real deploys)
    key_size: int = 32
    extension: dict[str, Any] = field(default_factory=dict)
    standard: InterchangeStandard = InterchangeStandard.ETSI_GS_QKD_014

    def to_json(self) -> str:
        return json.dumps(_to_public(self), indent=2, sort_keys=True)

    @classmethod
    def from_json(cls, payload: str | dict[str, Any]) -> KeyDelivery:
        data = payload if isinstance(payload, dict) else json.loads(payload)
        data = _coerce(data, {"status": KeyStatus})
        return cls(**data)


@dataclass
class SAE2EStatus:
    """ETSI GS QKD 015 SAE-to-SAE status / relay document."""

    source_sae_id: str
    target_sae_id: str
    relay: SAE2ERelay = SAE2ERelay.OK
    keys_available: int = 0
    keys_delivered: int = 0
    standard: InterchangeStandard = InterchangeStandard.ETSI_GS_QKD_015

    def to_json(self) -> str:
        return json.dumps(_to_public(self), indent=2, sort_keys=True)

    @classmethod
    def from_json(cls, payload: str | dict[str, Any]) -> SAE2EStatus:
        data = payload if isinstance(payload, dict) else json.loads(payload)
        data = _coerce(data, {"relay": SAE2ERelay, "standard": InterchangeStandard})
        data = _coerce(data, {"relay": SAE2ERelay})
        return cls(**data)


@dataclass
class ProtocolExchange:
    """A full protocol run captured as an interchange document.

    Wraps the protocol metadata plus the measurement basis/bit logs and any
    computed figures (concurrence, QBER, CHSH), so a whole qkdpy↔QpiAI run can
    be serialised for audit or interop testing.
    """

    protocol: ProtocolType
    alice_bases: list[str] = field(default_factory=list)
    bob_bases: list[str] = field(default_factory=list)
    alice_bits: list[int] = field(default_factory=list)
    bob_bits: list[int] = field(default_factory=list)
    concurrence: float | None = None
    qber: float | None = None
    chsh: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    standard: InterchangeStandard = InterchangeStandard.ETSI_GS_QKD_014

    def to_json(self) -> str:
        return json.dumps(_to_public(self), indent=2, sort_keys=True)

    @classmethod
    def from_json(cls, payload: str | dict[str, Any]) -> ProtocolExchange:
        data = payload if isinstance(payload, dict) else json.loads(payload)
        data = _coerce(
            data, {"protocol": ProtocolType, "standard": InterchangeStandard}
        )
        return cls(**data)


# --------------------------------------------------------------------------- #
#  Serialisation helpers (enums -> plain strings, dataclasses -> plain dicts)
# --------------------------------------------------------------------------- #
def _to_public(obj: Any) -> Any:
    out: dict[str, Any] = {}
    for key, value in asdict(obj).items():
        if isinstance(value, StrEnum):
            out[key] = value.value
        else:
            out[key] = value
    return out


def _coerce(data: dict[str, Any], enums: dict[str, type[StrEnum]]) -> dict[str, Any]:
    out = dict(data)
    for field_name, enum_cls in enums.items():
        if field_name in out and not isinstance(out[field_name], enum_cls):
            out[field_name] = enum_cls(out[field_name])
    return out
