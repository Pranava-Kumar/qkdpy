"""QKDpy: A Python Package for Quantum Key Distribution.

QKDpy is a comprehensive library for Quantum Key Distribution (QKD) simulations,
implementing various QKD protocols, quantum simulators, and cryptographic tools.
"""

__version__ = "0.2.7"
__author__ = "Pranava Kumar"
__email__ = "pranavakumar.it@gmail.com"

# Import core components
from .core import (
    CNOT,
    CZ,
    SWAP,
    AttackType,
    DecoyStateSource,
    DetectorArray,
    GateUtils,
    Hadamard,
    Identity,
    Measurement,
    ParametricDownConversionSource,
    PauliX,
    PauliY,
    PauliZ,
    PhotonSource,
    PhotonSourceManager,
    PhotonTimingModel,
    ProtocolTimingManager,
    QBERAnalysis,
    QBERTimingAnalysis,
    QuantumChannel,
    QuantumDetector,
    Qubit,
    Qudit,
    Rx,
    Ry,
    Rz,
    S,
    SDag,
    SecurityAnalyzer,
    SideChannelAnalyzer,
    T,
    TDag,
    TimingSynchronizer,
    WeakCoherentSource,
)
from .core.extended_channels import ExtendedQuantumChannel
from .core.multiqubit import MultiQubitState

# Import crypto utilities
from .crypto import OneTimePad, QuantumAuth
from .crypto.enhanced_security import (
    QuantumAuthentication,
    QuantumKeyValidation,
    QuantumSideChannelProtection,
)
from .crypto.key_exchange import QuantumKeyExchange
from .crypto.quantum_auth import QuantumAuthenticator
from .crypto.quantum_rng import QuantumRandomNumberGenerator

# Import key management
from .key_management import (
    ErrorCorrection,
    KeyDistillation,
    PrivacyAmplification,
    QuantumErrorCorrection,
)
from .key_management.advanced_error_correction import AdvancedErrorCorrection
from .key_management.advanced_privacy_amplification import AdvancedPrivacyAmplification
from .key_management.key_manager import QuantumKeyManager

# Import ML tools
from .ml import QKDAnomalyDetector, QKDOptimizer

# Import network tools
from .network import (
    MultiPartyQKD,
    MultiPartyQKDNetwork,
    QuantumNetwork,
    QuantumNode,
    RealisticQuantumNetwork,
    RealisticQuantumNode,
)

# Import protocols
from .protocols import BB84, E91, SARG04, DecoyStateBB84
from .protocols.b92 import B92
from .protocols.cv_qkd import CVQKD
from .protocols.di_qkd import DeviceIndependentQKD
from .protocols.enhanced_cv_qkd import EnhancedCVQKD
from .protocols.hd_qkd import HDQKD
from .protocols.twisted_pair import TwistedPairQKD

# Import utilities
from .utils import BlochSphere, KeyRateAnalyzer, ProtocolVisualizer
from .utils.advanced_visualization import (
    AdvancedKeyRateAnalyzer,
    AdvancedProtocolVisualizer,
)
from .utils.quantum_simulator import QuantumNetworkAnalyzer, QuantumSimulator

__all__ = [
    # Core components
    "Qubit",
    "Qudit",
    "QuantumChannel",
    "QuantumDetector",
    "DetectorArray",
    "TimingSynchronizer",
    "PhotonTimingModel",
    "QBERTimingAnalysis",
    "ProtocolTimingManager",
    "PhotonSource",
    "WeakCoherentSource",
    "DecoyStateSource",
    "ParametricDownConversionSource",
    "PhotonSourceManager",
    "SecurityAnalyzer",
    "QBERAnalysis",
    "SideChannelAnalyzer",
    "AttackType",
    "ExtendedQuantumChannel",
    "MultiQubitState",
    "Measurement",
    "Identity",
    "PauliX",
    "PauliY",
    "PauliZ",
    "Hadamard",
    "S",
    "SDag",
    "T",
    "TDag",
    "Rx",
    "Ry",
    "Rz",
    "CNOT",
    "CZ",
    "SWAP",
    "GateUtils",
    # Protocols
    "BB84",
    "DecoyStateBB84",
    "E91",
    "SARG04",
    "B92",
    "CVQKD",
    "EnhancedCVQKD",
    "DeviceIndependentQKD",
    "TwistedPairQKD",
    "HDQKD",
    # Key management
    "ErrorCorrection",
    "AdvancedErrorCorrection",
    "PrivacyAmplification",
    "AdvancedPrivacyAmplification",
    "KeyDistillation",
    "QuantumKeyManager",
    "QuantumErrorCorrection",
    # Crypto utilities
    "OneTimePad",
    "QuantumAuth",
    "QuantumAuthenticator",
    "QuantumKeyExchange",
    "QuantumRandomNumberGenerator",
    "QuantumAuthentication",
    "QuantumKeyValidation",
    "QuantumSideChannelProtection",
    # Utilities
    "BlochSphere",
    "ProtocolVisualizer",
    "KeyRateAnalyzer",
    "AdvancedProtocolVisualizer",
    "AdvancedKeyRateAnalyzer",
    "QuantumStateVisualizer",
    "ProtocolExecutionVisualizer",
    "InteractiveQuantumVisualizer",
    "QuantumSimulator",
    "QuantumNetworkAnalyzer",
    # ML tools
    "QKDOptimizer",
    "QKDAnomalyDetector",
    # Network tools
    "QuantumNetwork",
    "QuantumNode",
    "RealisticQuantumNetwork",
    "RealisticQuantumNode",
    "MultiPartyQKD",
    "MultiPartyQKDNetwork",
    # Integrations
    "QiskitIntegration",
    "CirqIntegration",
    "PennyLaneIntegration",
]
