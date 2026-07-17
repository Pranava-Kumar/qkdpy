"""Network simulation for QKD."""

from .atmospheric_physics import (
    background_stray_count_rate,
    link_direction_factor,
    modtran_band_transmittance,
)
from .multiparty_qkd import MultiPartyQKDNetwork
from .protocols import ChannelPredictor
from .quantum_network import (
    MultiPartyQKD,
    QuantumNetwork,
    QuantumNode,
)
from .realistic_quantum_network import RealisticQuantumNetwork, RealisticQuantumNode
from .satellite_qkd import (
    AtmosphericProfile,
    FreeSpaceOpticalChannel,
    OrbitType,
    SatellitePosition,
    SatelliteQKD,
    simulate_satellite_qkd,
)

__all__ = [
    "ChannelPredictor",
    "QuantumNetwork",
    "QuantumNode",
    "RealisticQuantumNetwork",
    "RealisticQuantumNode",
    "MultiPartyQKD",
    "MultiPartyQKDNetwork",
    # Satellite QKD
    "SatelliteQKD",
    "FreeSpaceOpticalChannel",
    "SatellitePosition",
    "AtmosphericProfile",
    "OrbitType",
    "simulate_satellite_qkd",
    # Atmospheric physics helpers
    "modtran_band_transmittance",
    "background_stray_count_rate",
    "link_direction_factor",
]
