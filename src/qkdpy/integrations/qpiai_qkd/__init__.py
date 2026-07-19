"""qpiai-qkd: qkdpy <-> QpiAI Quantum SDK companion package.

A standalone, pip-installable companion (``pip install qkdpy[qpiai]``) that maps
qkdpy QKD protocols to the QpiAI Quantum SDK and models the interchange with
IEC/ETSI QKD standards.

Public API:
  * :class:`QpiAIIntegration` — the protocol<->SDK bridge.
  * :class:`Protocols` — researcher-facing protocol/circuit facade.
  * interchange dataclasses (ETSI GS QKD 014/015): :class:`KeyRequest`,
    :class:`KeyDelivery`, :class:`SAE2EStatus`, :class:`ProtocolExchange`.
  * :func:`map_satellite_link` — free-space link physics summary.
  * :func:`optimize_protocol` / :func:`detect_anomaly` — ML optimizer bridge.
"""

from __future__ import annotations

from ._compat import QpiAISDKError, qpiai_available
from .bridge import QpiAIIntegration
from .interchange import (
    InterchangeStandard,
    KeyDelivery,
    KeyRequest,
    ProtocolExchange,
    ProtocolType,
    SAE2EStatus,
)
from .optimizer import (
    AnomalyReport,
    OptimizerResult,
    detect_anomaly,
    list_strategies,
    optimize_protocol,
)
from .physics import LinkPhysics, map_satellite_link
from .protocols import Protocols

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "QpiAIIntegration",
    "Protocols",
    "InterchangeStandard",
    "ProtocolType",
    "KeyRequest",
    "KeyDelivery",
    "SAE2EStatus",
    "ProtocolExchange",
    "LinkPhysics",
    "map_satellite_link",
    "optimize_protocol",
    "detect_anomaly",
    "list_strategies",
    "OptimizerResult",
    "AnomalyReport",
    "QpiAISDKError",
    "qpiai_available",
]
