"""Utility functions and visualization tools for QKDpy."""

from .advanced_quantum_visualization import (
    InteractiveQuantumVisualizer,
    ProtocolExecutionVisualizer,
    QuantumStateVisualizer,
)
from .advanced_visualization import AdvancedKeyRateAnalyzer, AdvancedProtocolVisualizer
from .helpers import (
    apply_permutation,
    binary_entropy,
    bits_to_bytes,
    bits_to_int,
    bytes_to_bits,
    calculate_qber,
    generate_random_permutation,
    hamming_distance,
    int_to_bits,
    mutual_information,
    random_bit_string,
)
from .instrumentation import (
    OperationSpan,
    instrument,
    record_ml_training,
    record_protocol_execution,
    record_qber_diagnostic,
)
from .logging_config import (
    QKDLogger,
    configure_default_logger,
    get_logger,
    log_debug,
    log_error,
    log_info,
    log_security,
    log_warning,
)
from .quantum_simulator import QuantumNetworkAnalyzer, QuantumSimulator
from .validation import (
    validate_binary_key,
    validate_density_matrix,
    validate_key_length,
    validate_normalized_state,
    validate_not_empty,
    validate_positive,
    validate_probability,
    validate_qber,
    validate_range,
    validate_type,
    validate_unitary,
)
from .visualization import (
    BlochSphere,
    KeyRateAnalyzer,
    ProtocolVisualizer,
)

__all__ = [
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
    "random_bit_string",
    "bits_to_bytes",
    "bytes_to_bits",
    "bits_to_int",
    "int_to_bits",
    "hamming_distance",
    "binary_entropy",
    "calculate_qber",
    "mutual_information",
    "generate_random_permutation",
    "apply_permutation",
    # Logging
    "QKDLogger",
    "get_logger",
    "configure_default_logger",
    "log_debug",
    "log_info",
    "log_warning",
    "log_error",
    "log_security",
    # Instrumentation
    "OperationSpan",
    "instrument",
    "record_protocol_execution",
    "record_ml_training",
    "record_qber_diagnostic",
    # Validation
    "validate_range",
    "validate_type",
    "validate_positive",
    "validate_probability",
    "validate_not_empty",
    "validate_key_length",
    "validate_binary_key",
    "validate_qber",
    "validate_unitary",
    "validate_normalized_state",
    "validate_density_matrix",
]
