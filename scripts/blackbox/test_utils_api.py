#!/usr/bin/env python3
"""Test script for qkdpy modules — UTF-8 safe for Windows consoles."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

#!/usr/bin/env python3
"""
Blackbox test for qkdpy v0.6.0 — utilities, visualization,
instrumentation, and public API surface.

Writes several PNG files to E:/opensource/qkdpy/ and reports every
numerical value obtained.
"""

import os
import sys

SRC = str(Path(__file__).resolve().parents[1] / "src")
sys.path.insert(0, SRC)

import warnings

warnings.filterwarnings("ignore")

IMPORT_ERRORS = []


def _size(path):
    if os.path.exists(path):
        return os.path.getsize(path)
    return None


def _exists(path):
    e = os.path.exists(path)
    ok = "OK" if e else "MISSING"
    print(f"    [{ok}] {path}  ({_size(path)} bytes)" if e else f"    [{ok}] {path}")
    return e


# ─────────────────────────────────────────────
#  1. Public API
# ─────────────────────────────────────────────
print("=" * 72)
print("SECTION 1: Public API (qkdpy)")
print("=" * 72)

import qkdpy

print(f"\n  qkdpy version: {qkdpy.__version__}")

all_names = [n for n in dir(qkdpy) if not n.startswith("_")]
print(f"\n  Total public exported names (non-dunder): {len(all_names)}")
for n in sorted(all_names):
    print(f"    {n}")

# Call key public functions
print("\n  --- Calling public functions ---")

cfg = qkdpy.get_config()
print(f"  get_config() -> QKDConfig (logging.level={cfg.logging.level.value})")

print(f"  is_debug_mode() -> {qkdpy.is_debug_mode()}")
print(f"  is_production_mode() -> {qkdpy.is_production_mode()}")

# set_config -- modify and read back
from qkdpy.config import (
    LogLevel,
    QKDConfig,
    reset_config,
)

new_cfg = QKDConfig()
new_cfg.logging.level = LogLevel.DEBUG
new_cfg.debug_mode = True
qkdpy.set_config(new_cfg)
cfg2 = qkdpy.get_config()
print(
    f"  After set_config: debug_mode={cfg2.debug_mode}, logging.level={cfg2.logging.level.value}"
)
reset_config()


# ─────────────────────────────────────────────
#  2. Config
# ─────────────────────────────────────────────
print("\n" + "=" * 72)
print("SECTION 2: Config")
print("=" * 72)

cfg = qkdpy.get_config()
print(f"  Default config type: {type(cfg).__name__}")

print("\n  --- Config sub-configs ---")
print(
    f"  Logging:   level={cfg.logging.level.value}, json={cfg.logging.json_output}, "
    f"audit={cfg.logging.audit_enabled}, file={cfg.logging.log_file}"
)
print(
    f"  Security:  mode={cfg.security.mode.value}, min_key_len={cfg.security.min_key_length}, "
    f"qber_threshold={cfg.security.max_qber_threshold}, auth={cfg.security.require_authentication}"
)
print(
    f"  Protocol:  default={cfg.protocol.default_protocol}, key_len={cfg.protocol.default_key_length}, "
    f"threshold={cfg.protocol.security_threshold}"
)
print(
    f"  Channel:   loss_coeff={cfg.channel.default_loss_coefficient}, "
    f"noise_model={cfg.channel.default_noise_model}, noise_level={cfg.channel.default_noise_level}"
)
print(
    f"  ML:        enabled={cfg.ml.enable_ml_optimization}, method={cfg.ml.default_optimization_method}, "
    f"max_iter={cfg.ml.max_iterations}, max_mem_mb={cfg.ml.max_memory_mb}"
)
print(
    f"  Enterprise:hsm={cfg.enterprise.enable_hsm}, tier={cfg.enterprise.product_tier}, "
    f"compliance={cfg.enterprise.compliance_standard}"
)
print(f"  General:   debug={cfg.debug_mode}, strict_val={cfg.strict_validation}")

# Modify a config value and verify
cfg2 = QKDConfig()
cfg2.protocol.default_key_length = 512
print(f"\n  Modified default_key_length: {cfg2.protocol.default_key_length}")

# Test config validation
from qkdpy.config import SecurityMode, validate_config
from qkdpy.exceptions import InvalidConfigError

warnings_list = validate_config(cfg)
print(f"  Validation warnings for default config: {warnings_list}")

# Test invalid: min_key_length < 64
bad_cfg = QKDConfig()
bad_cfg.security.min_key_length = 32
try:
    validate_config(bad_cfg)
    print("  ERROR: should have raised InvalidConfigError")
except InvalidConfigError as e:
    print(f"  Validation raised InvalidConfigError: {e}")
    print(f"    Error code: {e.error_code}")
    print(f"    Context: {e.context}")

# Test production + debug mode invalid
bad_cfg2 = QKDConfig()
bad_cfg2.security.mode = SecurityMode.PRODUCTION
bad_cfg2.debug_mode = True
try:
    validate_config(bad_cfg2)
    print("  ERROR: should have raised InvalidConfigError")
except InvalidConfigError as e:
    print(f"  Production+debug raised: {e}")

# Test HSM enabled without path
bad_cfg3 = QKDConfig()
bad_cfg3.enterprise.enable_hsm = True
bad_cfg3.enterprise.hsm_library_path = None
try:
    validate_config(bad_cfg3)
    print("  ERROR: should have raised InvalidConfigError")
except InvalidConfigError as e:
    print(f"  HSM without path raised: {e}")


# ─────────────────────────────────────────────
#  3. Exceptions
# ─────────────────────────────────────────────
print("\n" + "=" * 72)
print("SECTION 3: Exceptions")
print("=" * 72)

from qkdpy.exceptions import (
    AuthenticationError,
    ChannelCalibrationError,
    ChannelLossError,
    ChannelNoiseError,
    ConnectionError,
    CryptoError,
    DecryptionError,
    EncryptionError,
    InsufficientKeyError,
    IntegrityError,
    MissingConfigError,
    NetworkError,
    NodeNotFoundError,
    PathNotFoundError,
    ProtocolError,
    ProtocolSecurityError,
    ProtocolStateError,
    QKDException,
    wrap_exception,
)
from qkdpy.exceptions import InvalidConfigError as ICE

# Build and print hierarchy
hierarchy = {
    "QKDException": [],
    "  ProtocolError": [
        "ProtocolSecurityError",
        "ProtocolStateError",
        "InsufficientKeyError",
    ],
    "  ChannelError": [
        "ChannelLossError",
        "ChannelNoiseError",
        "ChannelCalibrationError",
    ],
    "  CryptoError": [
        "EncryptionError",
        "DecryptionError",
        "AuthenticationError",
        "IntegrityError",
    ],
    "  NetworkError": ["NodeNotFoundError", "ConnectionError", "PathNotFoundError"],
    "  ConfigurationError": ["InvalidConfigError", "MissingConfigError"],
}
print("\n  Exception hierarchy:")
for parent, children in hierarchy.items():
    print(f"    {parent}")
    for child in children:
        print(f"      -> {child}")

# Trigger each exception type
print("\n  --- Triggering each exception type ---")

exc1 = QKDException(
    "base error", error_code="TEST_001", context={"foo": "bar"}, recoverable=False
)
print(
    f"  QKDException: msg='{exc1}', code={exc1.error_code}, context={exc1.context}, "
    f"recoverable={exc1.recoverable}"
)
d = exc1.to_dict()
print(f"    to_dict(): {d}")

exc2 = ProtocolSecurityError(
    "eve detected", qber=0.15, threshold=0.11, attack_type="intercept-resend"
)
print(
    f"  ProtocolSecurityError: code={exc2.error_code}, qber={exc2.context['qber']}, "
    f"threshold={exc2.context['threshold']}, attack={exc2.context['attack_type']}"
)

exc3 = ProtocolStateError("invalid state")
print(f"  ProtocolStateError: code={exc3.error_code}")

exc4 = InsufficientKeyError("only 10 bits")
print(f"  InsufficientKeyError: code={exc4.error_code}")

exc5 = ChannelLossError("high loss", loss_rate=0.5, expected_rate=0.1)
print(
    f"  ChannelLossError: code={exc5.error_code}, loss_rate={exc5.context['loss_rate']}"
)

exc6 = ChannelNoiseError("noisy channel")
print(f"  ChannelNoiseError: code={exc6.error_code}")

exc7 = ChannelCalibrationError("calibration needed")
print(f"  ChannelCalibrationError: code={exc7.error_code}")

exc8 = EncryptionError("encryption failed")
print(f"  EncryptionError: code={exc8.error_code}")

exc9 = DecryptionError("decryption failed")
print(f"  DecryptionError: code={exc9.error_code}")

exc10 = AuthenticationError("auth failed")
print(f"  AuthenticationError: code={exc10.error_code}")

exc11 = IntegrityError("checksum mismatch")
print(f"  IntegrityError: code={exc11.error_code}")

exc12 = NetworkError("network failure")
print(f"  NetworkError: code={exc12.error_code}")

exc13 = NodeNotFoundError("node missing")
print(f"  NodeNotFoundError: code={exc13.error_code}")

exc14 = ConnectionError("cannot connect")
print(f"  ConnectionError: code={exc14.error_code}")

exc15 = PathNotFoundError("no route")
print(f"  PathNotFoundError: code={exc15.error_code}")

exc16 = ICE("bad value")
print(f"  InvalidConfigError: code={exc16.error_code}")

exc17 = MissingConfigError("missing param")
print(f"  MissingConfigError: code={exc17.error_code}")

# wrap_exception
try:
    raise ValueError("original failure")
except ValueError as ve:
    wrapped = wrap_exception(ve, ProtocolError, "wrapped protocol error")
    print(
        f"  wrap_exception: type={type(wrapped).__name__}, msg='{wrapped}', "
        f"cause='{wrapped.cause}', error_code={wrapped.error_code}"
    )

# Redaction test
exc_redact = QKDException(
    "test", context={"raw_key": "secret123", "key_rate": 0.5, "public": "ok"}
)
d_redact = exc_redact.to_dict()
print(f"  Redaction test: {d_redact['context']}")

exc_crypto = CryptoError("crypto base")
print(f"  CryptoError: code={exc_crypto.error_code}")


# ─────────────────────────────────────────────
#  4. Visualization
# ─────────────────────────────────────────────
print("\n" + "=" * 72)
print("SECTION 4: Visualization")
print("=" * 72)

import matplotlib

matplotlib.use("Agg")

try:
    from qkdpy.core import MultiQubitState, Qubit

    # Bloch sphere
    from qkdpy.utils.visualization import BlochSphere

    qubit = Qubit.plus()
    ax = BlochSphere.plot_qubit(qubit, title="Test Bloch Sphere")
    fig = ax.figure
    path_bloch = "$ROOT/scripts/blackbox/outputs/test_bloch.png"
    fig.savefig(path_bloch, dpi=100)
    import matplotlib.pyplot as plt

    plt.close(fig)
    print("\n  BlochSphere.plot_qubit:")
    _exists(path_bloch)

    # Multiple qubits on Bloch sphere
    qubits = [Qubit.zero(), Qubit.one(), Qubit.plus(), Qubit.minus()]
    fig2 = BlochSphere.plot_multiple_qubits(qubits, title="Multiple Qubits")
    path_multi = "$ROOT/scripts/blackbox/outputs/test_bloch_multi.png"
    fig2.savefig(path_multi, dpi=100)
    plt.close(fig2)
    print("\n  BlochSphere.plot_multiple_qubits:")
    _exists(path_multi)

    # State histogram via MultiQubitState
    mqs = MultiQubitState.ghz(3)
    probs = mqs.probabilities
    print(f"\n  GHZ(3) probabilities: {probs.tolist()}")
    print(f"  GHZ(3) num_qubits: {mqs.num_qubits}")

    # Plot state histogram using advanced_quantum_visualization
    from qkdpy.utils.advanced_quantum_visualization import QuantumStateVisualizer

    states_list = [Qubit.zero(), Qubit.one(), Qubit.plus()]
    fig3 = QuantumStateVisualizer.plot_quantum_state_histogram(
        states_list, measurement_axis="Z", title="Test Histogram"
    )
    path_hist = "$ROOT/scripts/blackbox/outputs/test_histogram.png"
    fig3.savefig(path_hist, dpi=100)
    plt.close(fig3)
    print("\n  QuantumStateVisualizer.plot_quantum_state_histogram:")
    _exists(path_hist)

    # ProtocolVisualizer
    from qkdpy.utils.visualization import KeyRateAnalyzer, ProtocolVisualizer

    alice_bits = [0, 1, 0, 1, 0, 1]
    alice_bases = [
        "computational",
        "hadamard",
        "computational",
        "computational",
        "hadamard",
        "hadamard",
    ]
    bob_bases = [
        "computational",
        "hadamard",
        "hadamard",
        "computational",
        "hadamard",
        "computational",
    ]
    bob_results = [0, 1, 1, 1, 0, 0]
    fig4 = ProtocolVisualizer.plot_bb84_protocol(
        alice_bits, alice_bases, bob_bases, bob_results
    )
    path_bb84 = "$ROOT/scripts/blackbox/outputs/test_bb84.png"
    fig4.savefig(path_bb84, dpi=100)
    plt.close(fig4)
    print("\n  ProtocolVisualizer.plot_bb84_protocol:")
    _exists(path_bb84)

    # E91 protocol
    fig5 = ProtocolVisualizer.plot_e91_protocol(
        [0, 1, 2], [0, 1, 0], [0, 1, 2], [1, 0, 1]
    )
    path_e91 = "$ROOT/scripts/blackbox/outputs/test_e91.png"
    fig5.savefig(path_e91, dpi=100)
    plt.close(fig5)
    print("\n  ProtocolVisualizer.plot_e91_protocol:")
    _exists(path_e91)

    # SARG04 protocol
    fig6 = ProtocolVisualizer.plot_sarg04_protocol(
        [0, 1, 0, 1],
        ["computational", "hadamard", "computational", "hadamard"],
        ["computational", "hadamard", "hadamard", "computational"],
        [0, 1, 1, 0],
        [0, 1, 0, 1],
    )
    path_sarg = "$ROOT/scripts/blackbox/outputs/test_sarg04.png"
    fig6.savefig(path_sarg, dpi=100)
    plt.close(fig6)
    print("\n  ProtocolVisualizer.plot_sarg04_protocol:")
    _exists(path_sarg)

    # KeyRateAnalyzer
    fig7 = KeyRateAnalyzer.plot_key_rate_vs_qber(
        [0.01, 0.03, 0.05, 0.07, 0.09, 0.11, 0.13],
        [0.9, 0.7, 0.5, 0.3, 0.15, 0.05, 0.0],
        "BB84",
    )
    path_kr_qber = "$ROOT/scripts/blackbox/outputs/test_keyrate_qber.png"
    fig7.savefig(path_kr_qber, dpi=100)
    plt.close(fig7)
    print("\n  KeyRateAnalyzer.plot_key_rate_vs_qber:")
    _exists(path_kr_qber)

    fig8 = KeyRateAnalyzer.plot_key_rate_vs_distance(
        [10, 20, 50, 100, 150, 200], [0.8, 0.6, 0.3, 0.08, 0.02, 0.005], "BB84"
    )
    path_kr_dist = "$ROOT/scripts/blackbox/outputs/test_keyrate_distance.png"
    fig8.savefig(path_kr_dist, dpi=100)
    plt.close(fig8)
    print("\n  KeyRateAnalyzer.plot_key_rate_vs_distance:")
    _exists(path_kr_dist)

    # compare_protocols with non-zero data to avoid div-by-zero bug
    fig9 = KeyRateAnalyzer.compare_protocols(
        {
            "BB84": ([0.01, 0.05, 0.09, 0.11], [0.9, 0.5, 0.1, 0.01]),
            "E91": ([0.01, 0.05, 0.09, 0.11], [0.85, 0.45, 0.08, 0.01]),
        }
    )
    path_comp = "$ROOT/scripts/blackbox/outputs/test_protocol_compare.png"
    fig9.savefig(path_comp, dpi=100)
    plt.close(fig9)
    print("\n  KeyRateAnalyzer.compare_protocols:")
    _exists(path_comp)

    # Density matrix visualization
    fig10 = QuantumStateVisualizer.plot_density_matrix(
        qubit, title="Density Matrix Test"
    )
    path_dm = "$ROOT/scripts/blackbox/outputs/test_density_matrix.png"
    fig10.savefig(path_dm, dpi=100)
    plt.close(fig10)
    print("\n  QuantumStateVisualizer.plot_density_matrix:")
    _exists(path_dm)

    # Bloch vector evolution
    evolved = [Qubit.zero(), Qubit.plus(), Qubit.one()]
    fig11 = QuantumStateVisualizer.plot_bloch_vector_evolution(
        evolved, time_points=[0, 1, 2], title="Bloch Evolution"
    )
    path_bve = "$ROOT/scripts/blackbox/outputs/test_bloch_evolution.png"
    fig11.savefig(path_bve, dpi=100)
    plt.close(fig11)
    print("\n  QuantumStateVisualizer.plot_bloch_vector_evolution:")
    _exists(path_bve)

except Exception as e:
    print(f"\n  Visualization section error: {type(e).__name__}: {e}")


# ─────────────────────────────────────────────
#  5. Advanced Visualization
# ─────────────────────────────────────────────
print("\n" + "=" * 72)
print("SECTION 5: Advanced Visualization")
print("=" * 72)

try:
    import matplotlib.pyplot as plt

    from qkdpy.core import Qubit
    from qkdpy.utils.advanced_visualization import (
        AdvancedKeyRateAnalyzer,
        AdvancedProtocolVisualizer,
    )

    # Quantum state evolution
    qubits_evol = [Qubit.zero(), Qubit.plus(), Qubit.one()]
    fig_adv1 = AdvancedProtocolVisualizer.plot_quantum_state_evolution(
        qubits_evol, title="State Evolution"
    )
    path_adv1 = "$ROOT/scripts/blackbox/outputs/test_adv_state_evolution.png"
    fig_adv1.savefig(path_adv1, dpi=100)
    plt.close(fig_adv1)
    print("\n  AdvancedProtocolVisualizer.plot_quantum_state_evolution:")
    _exists(path_adv1)

    # Protocol comparison bar chart
    fig_adv2 = AdvancedProtocolVisualizer.plot_protocol_comparison(
        {
            "BB84": {"key_rate": 0.8, "qber": 0.05, "efficiency": 0.7},
            "E91": {"key_rate": 0.6, "qber": 0.03, "efficiency": 0.5},
            "SARG04": {"key_rate": 0.5, "qber": 0.08, "efficiency": 0.4},
        },
        metric="key_rate",
    )
    path_adv2 = "$ROOT/scripts/blackbox/outputs/test_adv_protocol_compare.png"
    fig_adv2.savefig(path_adv2, dpi=100)
    plt.close(fig_adv2)
    print("\n  AdvancedProtocolVisualizer.plot_protocol_comparison:")
    _exists(path_adv2)

    # Security bounds
    fig_adv3 = AdvancedProtocolVisualizer.plot_security_bounds(
        [0.01 * i for i in range(26)], title="Security Bounds"
    )
    path_adv3 = "$ROOT/scripts/blackbox/outputs/test_adv_security_bounds.png"
    fig_adv3.savefig(path_adv3, dpi=100)
    plt.close(fig_adv3)
    print("\n  AdvancedProtocolVisualizer.plot_security_bounds:")
    _exists(path_adv3)

    # Entanglement verification
    fig_adv4 = AdvancedProtocolVisualizer.plot_entanglement_verification(
        {
            "correlations": {"A0B0": 0.7, "A0B1": 0.3, "A1B0": 0.4, "A1B1": -0.6},
            "s_value": 2.4,
        },
    )
    path_adv4 = "$ROOT/scripts/blackbox/outputs/test_adv_entanglement.png"
    fig_adv4.savefig(path_adv4, dpi=100)
    plt.close(fig_adv4)
    print("\n  AdvancedProtocolVisualizer.plot_entanglement_verification:")
    _exists(path_adv4)

    # Key rate vs parameters
    fig_adv5 = AdvancedKeyRateAnalyzer.plot_key_rate_vs_parameters(
        None,
        "channel_loss",
        [0.0, 0.1, 0.2, 0.3, 0.4, 0.5],
    )
    path_adv5 = "$ROOT/scripts/blackbox/outputs/test_adv_keyrate_params.png"
    fig_adv5.savefig(path_adv5, dpi=100)
    plt.close(fig_adv5)
    print("\n  AdvancedKeyRateAnalyzer.plot_key_rate_vs_parameters:")
    _exists(path_adv5)

    # Multi-dimensional analysis
    fig_adv6 = AdvancedKeyRateAnalyzer.plot_multi_dimensional_analysis(
        {
            "BB84": {"key_rate": 0.8, "qber": 0.05, "distance": 50},
            "E91": {"key_rate": 0.6, "qber": 0.03, "distance": 80},
            "SARG04": {"key_rate": 0.5, "qber": 0.08, "distance": 30},
        }
    )
    path_adv6 = "$ROOT/scripts/blackbox/outputs/test_adv_multi_dim.png"
    fig_adv6.savefig(path_adv6, dpi=100)
    plt.close(fig_adv6)
    print("\n  AdvancedKeyRateAnalyzer.plot_multi_dimensional_analysis:")
    _exists(path_adv6)

except Exception as e:
    print(f"\n  Advanced Visualization section error: {type(e).__name__}: {e}")


# ─────────────────────────────────────────────
#  6. Advanced Quantum Visualization
# ─────────────────────────────────────────────
print("\n" + "=" * 72)
print("SECTION 6: Advanced Quantum Visualization")
print("=" * 72)

try:
    import matplotlib.pyplot as plt

    from qkdpy.core import QuantumChannel, Qubit
    from qkdpy.utils.advanced_quantum_visualization import (
        InteractiveQuantumVisualizer,
        ProtocolExecutionVisualizer,
        QuantumStateVisualizer,
    )

    # Protocol execution timeline
    fig_aqv1 = ProtocolExecutionVisualizer.plot_protocol_execution_timeline(
        None, title="Execution Timeline"
    )
    path_aqv1 = "$ROOT/scripts/blackbox/outputs/test_aqv_timeline.png"
    fig_aqv1.savefig(path_aqv1, dpi=100)
    plt.close(fig_aqv1)
    print("\n  ProtocolExecutionVisualizer.plot_protocol_execution_timeline:")
    _exists(path_aqv1)

    # Key generation performance
    fig_aqv2 = ProtocolExecutionVisualizer.plot_key_generation_performance(
        [128, 256, 512],
        [0.5, 1.2, 2.5],
        [0.03, 0.05, 0.07],
    )
    path_aqv2 = "$ROOT/scripts/blackbox/outputs/test_aqv_key_perf.png"
    fig_aqv2.savefig(path_aqv2, dpi=100)
    plt.close(fig_aqv2)
    print("\n  ProtocolExecutionVisualizer.plot_key_generation_performance:")
    _exists(path_aqv2)

    # Security analysis
    fig_aqv3 = ProtocolExecutionVisualizer.plot_security_analysis(
        [0.02, 0.05, 0.08, 0.12, 0.15, 0.03, 0.06],
        secure_threshold=0.11,
    )
    path_aqv3 = "$ROOT/scripts/blackbox/outputs/test_aqv_security.png"
    fig_aqv3.savefig(path_aqv3, dpi=100)
    plt.close(fig_aqv3)
    print("\n  ProtocolExecutionVisualizer.plot_security_analysis:")
    _exists(path_aqv3)

    # Protocol comparison (advanced)
    fig_aqv4 = ProtocolExecutionVisualizer.plot_protocol_comparison(
        {
            "BB84": {"key_rate": 0.8, "qber": 0.05, "execution_time": 1.0},
            "E91": {"key_rate": 0.6, "qber": 0.03, "execution_time": 1.5},
        },
    )
    path_aqv4 = "$ROOT/scripts/blackbox/outputs/test_aqv_protocol_comp.png"
    fig_aqv4.savefig(path_aqv4, dpi=100)
    plt.close(fig_aqv4)
    print("\n  ProtocolExecutionVisualizer.plot_protocol_comparison:")
    _exists(path_aqv4)

    # Interactive Bloch sphere
    fig_aqv5 = InteractiveQuantumVisualizer.create_interactive_bloch_sphere(
        Qubit.plus(), title="Interactive Bloch"
    )
    path_aqv5 = "$ROOT/scripts/blackbox/outputs/test_aqv_interactive_bloch.png"
    fig_aqv5.savefig(path_aqv5, dpi=100)
    plt.close(fig_aqv5)
    print("\n  InteractiveQuantumVisualizer.create_interactive_bloch_sphere:")
    _exists(path_aqv5)

    # Animate qubit evolution
    states_anim = [Qubit.zero(), Qubit.plus(), Qubit.one(), Qubit.minus()]
    fig_aqv6 = InteractiveQuantumVisualizer.animate_qubit_evolution(
        states_anim, title="Animated Evolution"
    )
    path_aqv6 = "$ROOT/scripts/blackbox/outputs/test_aqv_animation.png"
    fig_aqv6.savefig(path_aqv6, dpi=100)
    plt.close(fig_aqv6)
    print("\n  InteractiveQuantumVisualizer.animate_qubit_evolution:")
    _exists(path_aqv6)

    # Quantum channel characteristics
    ch = QuantumChannel(loss=0.2, noise_model="depolarizing", noise_level=0.05)
    fig_aqv7 = QuantumStateVisualizer.plot_quantum_channel_characteristics(
        ch, title="Channel Characteristics"
    )
    path_aqv7 = "$ROOT/scripts/blackbox/outputs/test_aqv_channel.png"
    fig_aqv7.savefig(path_aqv7, dpi=100)
    plt.close(fig_aqv7)
    print("\n  QuantumStateVisualizer.plot_quantum_channel_characteristics:")
    _exists(path_aqv7)

except Exception as e:
    print(f"\n  Advanced Quantum Visualization section error: {type(e).__name__}: {e}")


# ─────────────────────────────────────────────
#  7. Instrumentation
# ─────────────────────────────────────────────
print("\n" + "=" * 72)
print("SECTION 7: Instrumentation")
print("=" * 72)

try:
    from qkdpy.utils.instrumentation import (
        OperationSpan,
        instrument,
        record_ml_training,
        record_protocol_execution,
        record_qber_diagnostic,
    )

    # --- OperationSpan ---
    print("\n  --- OperationSpan ---")
    with OperationSpan("test.operation", protocol="BB84", key_length=256) as span:
        import time

        time.sleep(0.01)
        span.set_metadata(qber=0.05, key_size=128)
    print("    OperationSpan completed (timing captured above in log)")

    # --- @instrument decorator ---
    print("\n  --- @instrument decorator ---")

    @instrument("test.decorated_func", level="info", log_args=True, log_result=True)
    def my_func(x, y):
        return x + y

    result = my_func(10, 20)
    print(f"    Decorated function result: {result}")

    # --- record_protocol_execution ---
    print("\n  --- record_protocol_execution ---")
    record_protocol_execution(
        protocol_name="BB84",
        key_length=256,
        qber=0.035,
        final_key_size=128,
        is_secure=True,
        duration_ms=150.5,
        channel_stats={"loss": 0.2, "noise": 0.01},
    )

    # --- record_ml_training ---
    print("\n  --- record_ml_training ---")
    record_ml_training(
        model_name="QKDRatePredictor",
        protocol="BB84",
        input_dim=10,
        training_samples=5000,
        training_time_ms=3200.7,
        final_loss=0.023,
        convergence_iterations=42,
    )

    # --- record_qber_diagnostic ---
    print("\n  --- record_qber_diagnostic ---")
    record_qber_diagnostic(
        protocol="BB84",
        qber=0.08,
        threshold=0.11,
        key_size=256,
        distance_km=50.0,
    )

    # Above threshold warning
    record_qber_diagnostic(
        protocol="BB84",
        qber=0.10,
        threshold=0.11,
        key_size=128,
        distance_km=75.0,
    )

    # --- Correlation IDs across nested spans ---
    print("\n  --- Nested OperationSpans ---")
    with OperationSpan("outer.span", correlation_id="corr-001") as outer:
        outer.set_metadata(step="begin")
        with OperationSpan(
            "inner.span", correlation_id="corr-001", parent="outer"
        ) as inner:
            inner.set_metadata(detail="nested work")
            time.sleep(0.005)
        outer.set_metadata(step="end")
    print("    Nested spans completed (see log output above)")

except Exception as e:
    print(f"\n  Instrumentation section error: {type(e).__name__}: {e}")


# ─────────────────────────────────────────────
#  8. Logging
# ─────────────────────────────────────────────
print("\n" + "=" * 72)
print("SECTION 8: Logging")
print("=" * 72)

try:
    from qkdpy.utils.logging_config import (
        configure_default_logger,
        get_logger,
        log_debug,
        log_error,
        log_info,
        log_security,
        log_warning,
    )

    logger = get_logger("test_logger")
    print(f"\n  Logger type: {type(logger).__name__}")
    print(f"  Logger name: {logger.name}")

    # Log at different levels
    print("\n  --- Logging at different levels ---")
    logger.debug("test debug message", component="test", value=42)
    logger.info("test info message", component="test", key_rate=0.85)
    logger.warning("test warning message", component="test", qber=0.10)
    logger.error("test error message", component="test", error_code="E001")

    # Security event via low-level log call
    print("\n  --- Security event (via QKDLogger._log) ---")
    logger._log("SECURITY", "test security event", component="test", threat_level="low")
    print("    Security event logged directly")

    # Audit event
    print("\n  --- Audit event ---")
    logger.audit(
        "key_generated", actor="alice", resource="sym_key_001", result="success"
    )

    # Module-level convenience functions
    print("\n  --- Module-level convenience loggers ---")
    log_debug("module debug", test_field=1)
    log_info("module info", test_field=2)
    log_warning("module warning", test_field=3)
    log_error("module error", test_field=4)
    log_security("module security", test_field=5)

    # bind/unbind
    print("\n  --- Logger bind/unbind ---")
    logger.bind(project="qkdpy_test", env="test")
    logger.info("bound context test", action="check")
    logger.unbind("project")
    logger.info("after unbind test", action="check")

    # configure_default_logger
    cfg_logger = configure_default_logger(level="DEBUG")
    print(f"  configure_default_logger returned: {type(cfg_logger).__name__}")

    # Verify structlog is available
    from qkdpy.utils.logging_config import STRUCTLOG_AVAILABLE

    print(f"\n  structlog available: {STRUCTLOG_AVAILABLE}")

except Exception as e:
    print(f"\n  Logging section error: {type(e).__name__}: {e}")


# ─────────────────────────────────────────────
#  9. Validation
# ─────────────────────────────────────────────
print("\n" + "=" * 72)
print("SECTION 9: Validation")
print("=" * 72)

try:
    import numpy as np

    from qkdpy.exceptions import (
        ParameterError,
        RangeError,
        TypeValidationError,
    )
    from qkdpy.utils.validation import (
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

    print("\n  --- @validate_positive ---")

    @validate_positive("x")
    def fn_positive(x):
        return x

    print(f"    fn_positive(5) = {fn_positive(5)}")
    try:
        fn_positive(-1)
        print("    ERROR: should have raised RangeError")
    except RangeError as e:
        print(f"    fn_positive(-1) -> RangeError: {e}")

    @validate_positive("x", allow_zero=True)
    def fn_positive_zero(x):
        return x

    print(f"    fn_positive_zero(0) = {fn_positive_zero(0)}")

    print("\n  --- @validate_range ---")

    @validate_range("x", min_value=0, max_value=10)
    def fn_range(x):
        return x

    print(f"    fn_range(5) = {fn_range(5)}")
    try:
        fn_range(15)
    except RangeError as e:
        print(f"    fn_range(15) -> RangeError: {e}")
    try:
        fn_range(-1)
    except RangeError as e:
        print(f"    fn_range(-1) -> RangeError: {e}")

    print("\n  --- @validate_type ---")

    @validate_type("x", int)
    def fn_type(x):
        return x

    print(f"    fn_type(42) = {fn_type(42)}")
    try:
        fn_type("hello")
    except TypeValidationError as e:
        print(f"    fn_type('hello') -> TypeValidationError: {e}")

    @validate_type("x", (int, float), allow_none=True)
    def fn_type_opt(x):
        return x

    print(f"    fn_type_opt(None) = {fn_type_opt(None)}")
    print(f"    fn_type_opt(3.14) = {fn_type_opt(3.14)}")

    print("\n  --- @validate_probability ---")

    @validate_probability("p")
    def fn_prob(p):
        return p

    print(f"    fn_prob(0.5) = {fn_prob(0.5)}")
    try:
        fn_prob(1.5)
    except RangeError as e:
        print(f"    fn_prob(1.5) -> RangeError: {e}")

    print("\n  --- @validate_not_empty ---")

    @validate_not_empty("items")
    def fn_not_empty(items):
        return len(items)

    print(f"    fn_not_empty([1,2,3]) = {fn_not_empty([1,2,3])}")
    try:
        fn_not_empty([])
    except ParameterError as e:
        print(f"    fn_not_empty([]) -> ParameterError: {e}")

    print("\n  --- validate_key_length ---")
    validate_key_length([0, 1, 0, 1, 0], min_length=3)
    print("    validate_key_length([0,1,0,1,0], 3) -> OK")
    try:
        validate_key_length([0, 1], min_length=5)
    except ParameterError as e:
        print(f"    validate_key_length([0,1], 5) -> ParameterError: {e}")

    print("\n  --- validate_binary_key ---")
    validate_binary_key([0, 1, 0, 1, 0])
    print("    validate_binary_key([0,1,0,1,0]) -> OK")
    try:
        validate_binary_key([0, 1, 2, 0])
    except ParameterError as e:
        print(f"    validate_binary_key([0,1,2,0]) -> ParameterError: {e}")

    print("\n  --- validate_qber ---")
    validate_qber(0.05)
    print("    validate_qber(0.05) -> OK")
    try:
        validate_qber(0.6)
    except RangeError as e:
        print(f"    validate_qber(0.6) -> RangeError: {e}")

    print("\n  --- validate_unitary ---")
    U = np.array([[1, 0], [0, -1]], dtype=complex)
    validate_unitary(U)
    print("    validate_unitary(PauliZ) -> OK")
    try:
        validate_unitary(np.array([[1, 0], [0, 2]], dtype=complex))
    except ParameterError as e:
        print(f"    validate_unitary(bad) -> ParameterError: {e}")

    print("\n  --- validate_normalized_state ---")
    psi = np.array([1.0, 0.0], dtype=complex)
    validate_normalized_state(psi)
    print("    validate_normalized_state([1,0]) -> OK")
    try:
        validate_normalized_state(np.array([1.0, 1.0], dtype=complex))
    except ParameterError as e:
        # Strip unicode if needed
        msg = str(e).encode("ascii", errors="replace").decode("ascii")
        print(f"    validate_normalized_state([1,1]) -> ParameterError: {msg}")

    print("\n  --- validate_density_matrix ---")
    rho = np.array([[0.5, 0], [0, 0.5]], dtype=complex)
    validate_density_matrix(rho)
    print("    validate_density_matrix(maximally mixed) -> OK")
    try:
        validate_density_matrix(np.array([[1, 0], [0, -1]], dtype=complex))
    except ParameterError as e:
        print(f"    validate_density_matrix(bad) -> ParameterError: {e}")

except Exception as e:
    print(f"\n  Validation section error: {type(e).__name__}: {e}")


# ─────────────────────────────────────────────
#  10. Helpers
# ─────────────────────────────────────────────
print("\n" + "=" * 72)
print("SECTION 10: Helpers")
print("=" * 72)

try:
    from qkdpy.utils.helpers import (
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

    print("\n  --- random_bit_string ---")
    bits = random_bit_string(16)
    print(f"    random_bit_string(16) = {bits}")

    print("\n  --- bits_to_bytes / bytes_to_bits ---")
    test_bits = [1, 0, 1, 0, 1, 0, 1, 0]
    b = bits_to_bytes(test_bits)
    print(f"    bits_to_bytes({test_bits}) = {b} (len={len(b)})")
    bits_back = bytes_to_bits(b)
    print(f"    bytes_to_bits({b}) = {bits_back}")
    print(f"    Round-trip match: {test_bits == bits_back[:len(test_bits)]}")

    test_bits2 = [1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 0, 0, 0, 0]
    b2 = bits_to_bytes(test_bits2)
    bits_back2 = bytes_to_bits(b2)
    print(f"    16-bit round-trip match: {test_bits2 == bits_back2[:len(test_bits2)]}")

    print("\n  --- bits_to_int / int_to_bits ---")
    val = bits_to_int([1, 0, 1, 0])
    print(f"    bits_to_int([1,0,1,0]) = {val}")
    bits_i = int_to_bits(10, length=8)
    print(f"    int_to_bits(10, 8) = {bits_i}")
    val2 = bits_to_int(bits_i)
    print(f"    bits_to_int(int_to_bits(10, 8)) = {val2}")

    print("\n  --- hamming_distance ---")
    d1 = hamming_distance([1, 0, 1, 0], [1, 1, 1, 1])
    print(f"    hamming_distance([1,0,1,0], [1,1,1,1]) = {d1}")
    try:
        hamming_distance([1, 0], [1, 0, 0])
    except ValueError as e:
        print(f"    hamming_distance different lengths -> ValueError: {e}")

    print("\n  --- binary_entropy ---")
    for p in [0.0, 0.5, 0.11, 1.0]:
        print(f"    binary_entropy({p}) = {binary_entropy(p):.6f}")

    print("\n  --- calculate_qber ---")
    alice = [1, 0, 1, 0, 1, 0, 1, 0]
    bob = [1, 0, 1, 1, 1, 0, 0, 0]
    qber_val = calculate_qber(alice, bob)
    print(f"    calculate_qber({alice}, {bob}) = {qber_val}")
    print(f"    Expected: 2/8 = 0.25 | Got: {qber_val}")

    print("\n  --- mutual_information ---")
    x = [0, 0, 1, 1, 0, 0, 1, 1]
    y = [0, 0, 1, 1, 0, 0, 1, 1]
    mi = mutual_information(x, y)
    print(f"    mutual_information(identical) = {mi:.6f} (expected ~1.0)")
    y_diff = [0, 1, 0, 1, 0, 1, 0, 1]
    mi2 = mutual_information(x, y_diff)
    print(f"    mutual_information(different) = {mi2:.6f} (expected ~0.0)")

    print("\n  --- generate_random_permutation ---")
    perm = generate_random_permutation(10)
    print(f"    generate_random_permutation(10) = {perm}")
    print(f"    Is valid permutation: {sorted(perm) == list(range(10))}")

    print("\n  --- apply_permutation ---")
    original = [1, 0, 1, 0, 1]
    perm_small = [2, 0, 4, 1, 3]
    applied = apply_permutation(original, perm_small)
    print(f"    apply_permutation({original}, {perm_small}) = {applied}")
    print("    Expected: [1, 1, 1, 0, 0]")

except Exception as e:
    print(f"\n  Helpers section error: {type(e).__name__}: {e}")


# ─────────────────────────────────────────────
#  11. Secure Random
# ─────────────────────────────────────────────
print("\n" + "=" * 72)
print("SECTION 11: Secure Random")
print("=" * 72)

try:
    from qkdpy.utils.secure_random import (
        SecureRandom,
        reseed_secure_rng,
        secure_bits,
        secure_choice,
        secure_normal,
        secure_randint,
        secure_random,
    )

    sr = SecureRandom()
    print(f"\n  SecureRandom instance: {type(sr).__name__}")

    print("\n  --- secure_randint ---")
    ri = secure_randint(0, 100)
    print(f"    secure_randint(0, 100) = {ri} (in [0, 99])")

    print("\n  --- secure_choice ---")
    items = ["A", "B", "C", "D"]
    ch = secure_choice(items)
    print(f"    secure_choice({items}) = '{ch}'")

    print("\n  --- secure_random ---")
    for _ in range(3):
        r = secure_random()
        print(f"    secure_random() = {r:.10f} (in [0,1))")

    print("\n  --- secure_normal ---")
    for _ in range(3):
        n = secure_normal(mean=0.0, std=1.0)
        print(f"    secure_normal(0, 1) = {n:.6f}")

    print("\n  --- secure_bits ---")
    sb = secure_bits(32)
    print(f"    secure_bits(32) = {sb}")
    print(f"    Length: {len(sb)}, Unique values: {set(sb)}")

    print("\n  --- Compare with core.secure_random ---")
    from qkdpy.core.secure_random import secure_bits as core_secure_bits
    from qkdpy.core.secure_random import secure_choice as core_secure_choice
    from qkdpy.core.secure_random import secure_normal as core_secure_normal
    from qkdpy.core.secure_random import secure_randint as core_secure_randint
    from qkdpy.core.secure_random import secure_random as core_secure_random

    core_r = core_secure_random()
    utils_r = secure_random()
    print(f"    core.secure_random() = {core_r:.10f}")
    print(f"    utils.secure_random() = {utils_r:.10f}")
    print(f"    Both produce floats in [0,1): {0 <= core_r < 1 and 0 <= utils_r < 1}")

    core_ri = core_secure_randint(0, 100)
    print(f"    core.secure_randint(0, 100) = {core_ri}")

    core_bits = core_secure_bits(16)
    print(f"    core.secure_bits(16) = {core_bits}")

    core_choice = core_secure_choice(["X", "Y", "Z"])
    print(f"    core.secure_choice(['X','Y','Z']) = '{core_choice}'")

    core_norm = core_secure_normal(1.0, 2.0)
    print(f"    core.secure_normal(1, 2) = {core_norm:.6f}")

    print("\n  --- reseed_secure_rng ---")
    reseed_secure_rng()
    r_after = secure_random()
    print(f"    After reseed, secure_random() = {r_after:.10f}")

except Exception as e:
    print(f"\n  Secure Random section error: {type(e).__name__}: {e}")


# ─────────────────────────────────────────────
#  12. QuantumSimulator
# ─────────────────────────────────────────────
print("\n" + "=" * 72)
print("SECTION 12: QuantumSimulator")
print("=" * 72)

try:
    from qkdpy.core import QuantumChannel, Qubit
    from qkdpy.utils.quantum_simulator import QuantumNetworkAnalyzer, QuantumSimulator

    sim = QuantumSimulator()
    print(f"\n  QuantumSimulator instance: {type(sim).__name__}")

    # --- Channel performance ---
    print("\n  --- simulate_channel_performance ---")
    ch = QuantumChannel(loss=0.1, noise_model="depolarizing", noise_level=0.02)
    perf = sim.simulate_channel_performance(ch, num_trials=500)
    print(f"    transmission_rate: {perf['transmission_rate']:.4f}")
    print(f"    average_fidelity:   {perf['average_fidelity']:.4f}")
    print(f"    fidelity_std:       {perf['fidelity_std']:.4f}")
    print(f"    min_fidelity:       {perf['min_fidelity']:.4f}")
    print(f"    max_fidelity:       {perf['max_fidelity']:.4f}")
    print(f"    channel_stats:      {perf['channel_stats']}")

    # --- Performance statistics ---
    stats = sim.get_performance_statistics()
    print("\n  --- get_performance_statistics ---")
    print(f"    total_simulations: {stats.get('total_simulations')}")
    print(f"    simulation_types:  {stats.get('simulation_types')}")

    # --- Simulation history ---
    history = sim.get_simulation_history()
    print("\n  --- get_simulation_history ---")
    print(f"    history length: {len(history)}")
    if history:
        print(f"    first record type: {history[0]['type']}")

    # --- Network Analyzer ---
    print("\n  --- QuantumNetworkAnalyzer ---")
    net = QuantumNetworkAnalyzer()
    result = net.analyze_network_topology(
        nodes=["Alice", "Bob", "Charlie", "Diana"],
        connections=[
            ("Alice", "Bob", 10.0),
            ("Bob", "Charlie", 15.0),
            ("Charlie", "Diana", 8.0),
            ("Alice", "Diana", 25.0),
        ],
    )
    print(f"    num_nodes:          {result['num_nodes']}")
    print(f"    num_connections:    {result['num_connections']}")
    print(f"    average_distance:   {result['average_distance']:.2f}")
    print(f"    max_distance:       {result['max_distance']:.2f}")
    print(f"    network_density:    {result['network_density']:.4f}")
    print(f"    is_connected:       {result['is_connected']}")

    # Network performance
    perf_result = net.simulate_network_performance(
        {
            "Alice": {"key_rate": 0.8, "qber": 0.03, "distance": 10},
            "Bob": {"key_rate": 0.6, "qber": 0.05, "distance": 15},
            "Charlie": {"key_rate": 0.4, "qber": 0.07, "distance": 8},
        }
    )
    print(
        f"\n    network_avg_key_rate:  {perf_result.get('network_avg_key_rate', 'N/A')}"
    )
    print(f"    network_avg_qber:      {perf_result.get('network_avg_qber', 'N/A')}")
    print(
        f"    best_performing_node:  {perf_result.get('best_performing_node', 'N/A')}"
    )

    # Network statistics
    net_stats = net.get_network_statistics()
    print(f"\n    num_topology_records:    {net_stats.get('num_topology_records')}")
    print(f"    num_performance_records: {net_stats.get('num_performance_records')}")

    # Clear simulation history
    sim.clear_simulation_history()
    print("\n  --- clear_simulation_history ---")
    print(f"    history after clear: {len(sim.get_simulation_history())}")

except Exception as e:
    print(f"\n  QuantumSimulator section error: {type(e).__name__}: {e}")


# ─────────────────────────────────────────────
#  13. Timing
# ─────────────────────────────────────────────
print("\n" + "=" * 72)
print("SECTION 13: Timing")
print("=" * 72)

try:
    import time

    from qkdpy.core import (
        PhotonTimingModel,
        ProtocolTimingManager,
        QBERTimingAnalysis,
        TimingSynchronizer,
    )

    print("\n  --- TimingSynchronizer ---")
    ts = TimingSynchronizer()
    print(f"    TimingSynchronizer created: {type(ts).__name__}")
    print(f"    clock_frequency: {ts.clock_frequency} Hz")
    print(f"    timing_jitter: {ts.timing_jitter} s")
    print(f"    synchronization_accuracy: {ts.synchronization_accuracy} s")
    print(f"    max_drift_rate: {ts.max_drift_rate}")
    print(f"    alice_clock_drift: {ts.alice_clock_drift:.10f}")
    print(f"    bob_clock_drift: {ts.bob_clock_drift:.10f}")
    print(f"    timing_measurements count: {len(ts.timing_measurements)}")

    # Synchronize
    sync_result = ts.synchronize_clocks(time.time())
    print(f"    synchronize_clocks result: {sync_result}")
    print(f"    post-sync alice_clock_offset: {ts.alice_clock_offset}")
    print(f"    post-sync bob_clock_offset: {ts.bob_clock_offset}")
    print(f"    timing_measurements count after sync: {len(ts.timing_measurements)}")

    # Time difference
    ref_t = time.time()
    time_diff = ts.calculate_time_difference(ref_t)
    print(f"    calculate_time_difference: {time_diff}")

    # Alice/Bob local times
    alice_t = ts.get_alice_time(ref_t)
    bob_t = ts.get_bob_time(ref_t)
    print(f"    get_alice_time: {alice_t}")
    print(f"    get_bob_time: {bob_t}")

    # Update clock drift
    ts.update_clock_drift()
    print(
        f"    after update_clock_drift: alice_drift={ts.alice_clock_drift:.10f}, bob_drift={ts.bob_clock_drift:.10f}"
    )

    print("\n  --- QBERTimingAnalysis ---")
    qta = QBERTimingAnalysis(timing_window=1e-9)
    print(f"    QBERTimingAnalysis created: {type(qta).__name__}")
    print(f"    timing_window: {qta.timing_window}")
    print(f"    max_temporal_drift: {qta.max_temporal_drift}")

    # Calculate temporal QBER
    alice_times = [100.0, 200.0, 300.0, 400.0, 500.0]
    bob_times = [100.5, 200.3, 301.0, 400.1, 501.5]
    temp_qber = qta.calculate_temporal_qber(alice_times, bob_times, expected_delay=0.5)
    print(f"    calculate_temporal_qber(5 pairs): {temp_qber:.4f}")

    # Update with drift
    drift_out = qta.update_with_drift(drift_rate=1e-9, time_elapsed=3600.0)
    print(f"    update_with_drift result: {drift_out:.10f} s")

    print("\n  --- PhotonTimingModel ---")
    phot = PhotonTimingModel(fiber_length=10000.0)  # 10 km fiber
    print(f"    PhotonTimingModel created: {type(phot).__name__}")
    print(f"    fiber_length: {phot.fiber_length} m")
    print(f"    detector_timing_resolution: {phot.detector_timing_resolution} s")
    print(f"    source_jitter: {phot.source_jitter} s")
    print(f"    propagation_time: {phot.propagation_time:.10f} s")
    print(f"    v_fiber: {phot.v_fiber:.1f} m/s")

    # Emit photon
    emit = phot.emit_photon(time.time())
    print(f"    emit_photon(now): {emit}")

    # Detect photon
    detect = phot.detect_photon(time.time())
    print(f"    detect_photon(now): {detect}")

    # Transit time
    transit = phot.photon_transit_time()
    print(f"    photon_transit_time: {transit:.10f} s")

    print("\n  --- ProtocolTimingManager ---")
    ptm = ProtocolTimingManager(synchronizer=ts, photon_model=phot, qber_analyzer=qta)
    print(f"    ProtocolTimingManager created: {type(ptm).__name__}")

    # Simple timing resolution test
    print("\n  --- Timing resolution ---")
    t0 = time.perf_counter()
    t1 = time.perf_counter()
    print(f"    perf_counter resolution delta: {(t1 - t0) * 1e9:.1f} ns")

    t0 = time.monotonic()
    t1 = time.monotonic()
    print(f"    monotonic resolution delta: {(t1 - t0) * 1e9:.1f} ns")

    t0 = time.perf_counter()
    time.sleep(0.001)
    t1 = time.perf_counter()
    print(f"    sleep(1ms) actual: {(t1 - t0) * 1000:.3f} ms")

except Exception as e:
    print(f"\n  Timing section error: {type(e).__name__}: {e}")


# ─────────────────────────────────────────────
#  14. Bell state circuit with QuantumSimulator
# ─────────────────────────────────────────────
print("\n" + "=" * 72)
print("SECTION 14: Bell State via QuantumSimulator")
print("=" * 72)

try:
    import math

    import numpy as np

    from qkdpy.core import (
        CNOT,
        Hadamard,
        MultiQubitState,
        QuantumChannel,
        Qubit,
    )

    # Create a Bell state |Phi+> = (|00> + |11>) / sqrt(2) using circuit
    print("\n  --- Bell state creation ---")
    mqs = MultiQubitState.zeros(2)
    print(f"    Initial state: {mqs}")
    H = Hadamard().matrix
    mqs.apply_gate(H, target_qubits=0)
    print(f"    After H on q0: probs={mqs.probabilities.tolist()}")
    cnot = CNOT().matrix
    mqs.apply_gate(cnot, target_qubits=[0, 1])
    print(f"    After CNOT: probs={mqs.probabilities.tolist()}")
    print(f"    State vector: {mqs.state.tolist()}")

    # Verify Bell state
    expected = np.array([1 / math.sqrt(2), 0, 0, 1 / math.sqrt(2)], dtype=complex)
    match = np.allclose(mqs.state, expected, atol=1e-10)
    print(f"    Matches Bell state: {match}")

    # Fidelity
    bell_ref = MultiQubitState(np.array([1, 0, 0, 1], dtype=complex) / math.sqrt(2))
    fid = mqs.fidelity(bell_ref)
    print(f"    Fidelity with reference Bell state: {fid:.10f}")

    # Measure one qubit
    print("\n  --- Measurement ---")
    result, collapsed = mqs.measure(0)
    print(f"    Measured qubit 0: {result}")
    if collapsed:
        print(f"    Collapsed state qubits: {collapsed.num_qubits}")
        print(f"    Collapsed state vector: {collapsed.state.tolist()}")

    # Entanglement entropy
    mqs2 = MultiQubitState.ghz(3)
    ee = mqs2.entanglement_entropy([0])
    print(f"\n    GHZ(3) entanglement entropy of qubit 0: {ee:.6f}")
    print("    Expected: ~1.0 (maximally entangled)")

    # W state
    w = MultiQubitState.w_state(3)
    print(f"\n    W(3) state: {w.state.tolist()}")
    w_probs = w.probabilities.tolist()
    print(f"    W(3) probabilities: {w_probs}")
    nonzero = [i for i, p in enumerate(w_probs) if p > 1e-10]
    print(f"    Non-zero basis states: {nonzero}")

except Exception as e:
    print(f"\n  Bell State section error: {type(e).__name__}: {e}")


# ─────────────────────────────────────────────
#  Summary
# ─────────────────────────────────────────────
print("\n" + "=" * 72)
print("TEST SUMMARY")
print("=" * 72)

print(f"\n  Import errors encountered: {len(IMPORT_ERRORS)}")
for mod, err in IMPORT_ERRORS:
    print(f"    - {mod}: {err}")

print("\n  Visualization files created:")
vis_dir = "E:/opensource/qkdpy/"
png_files = sorted(
    [f for f in os.listdir(vis_dir) if f.startswith("test_") and f.endswith(".png")]
)
for f in png_files:
    fp = os.path.join(vis_dir, f)
    sz = os.path.getsize(fp)
    print(f"    {f}: {sz} bytes")

print(f"\n  Total PNG files: {len(png_files)}")
print(f"  Python version: {sys.version}")
print("  All tests completed.")
