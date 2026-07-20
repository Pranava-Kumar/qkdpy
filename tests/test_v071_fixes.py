"""Tests for fixes introduced in v0.7.1.

Covers:
- ChannelBase ABC
- QpiAI _require_sdk() guard
- MD5/SHA-1 rejection in cryptographic_hash
- Entanglement attack fidelity-based detection
- LDPC arctanh clamping (no RuntimeWarning)
- QuantumChannel noise_model validation
- toeplitz_hashing seed reproducibility
- EfficientQKDPredictor seeded reproducibility
"""

import warnings

import numpy as np
import pytest

# ---------------------------------------------------------------------------
# Fix 9 (from audit): ChannelBase ABC
# ---------------------------------------------------------------------------


class TestChannelBaseABC:
    """ChannelBase defines the abstract interface for all channels."""

    def test_quantum_channel_is_subclass(self):
        from qkdpy.core.channel_base import ChannelBase
        from qkdpy.core.channels import QuantumChannel

        assert issubclass(QuantumChannel, ChannelBase)

    def test_abstract_methods_enforced(self):
        from qkdpy.core.channel_base import ChannelBase

        # Cannot instantiate an ABC directly
        with pytest.raises(TypeError):
            ChannelBase()  # type: ignore[abstract]

    def test_custom_subclass_must_implement(self):
        from qkdpy.core.channel_base import ChannelBase

        class IncompleteChannel(ChannelBase):
            pass

        with pytest.raises(TypeError):
            IncompleteChannel()  # type: ignore[abstract]

    def test_custom_subclass_with_all_methods(self):
        from qkdpy.core.channel_base import ChannelBase
        from qkdpy.core.qubit import Qubit

        class PerfectChannel(ChannelBase):
            def __init__(self):
                self._stats = {
                    "transmitted": 0,
                    "lost": 0,
                    "received": 0,
                    "errors": 0,
                    "loss_rate": 0.0,
                    "error_rate": 0.0,
                    "eavesdropped": 0,
                    "eavesdropper_detected": False,
                }

            def transmit(self, qubit, timestamp=0.0):
                self._stats["transmitted"] += 1
                self._stats["received"] += 1
                return qubit

            def get_statistics(self):
                return self._stats

            def reset_statistics(self):
                for k in self._stats:
                    if isinstance(self._stats[k], int):
                        self._stats[k] = 0
                    elif isinstance(self._stats[k], float):
                        self._stats[k] = 0.0
                    else:
                        self._stats[k] = False

        ch = PerfectChannel()
        q = Qubit.zero()
        result = ch.transmit(q)
        assert result is q
        assert ch.get_statistics()["transmitted"] == 1
        ch.reset_statistics()
        assert ch.get_statistics()["transmitted"] == 0

    def test_channelbase_has_transmit_batch_default(self):
        """transmit_batch has a default implementation in the ABC."""
        from qkdpy.core.channel_base import ChannelBase

        assert hasattr(ChannelBase, "transmit_batch")
        assert hasattr(ChannelBase, "set_eavesdropper")

    def test_channelbase_exported_from_core(self):
        from qkdpy.core import ChannelBase

        assert ChannelBase is not None

    def test_channelbase_exported_from_top_level(self):
        from qkdpy import ChannelBase

        assert ChannelBase is not None


# ---------------------------------------------------------------------------
# Fix 2: QpiAI bridge guard
# ---------------------------------------------------------------------------


class TestQpiAISDKGuard:
    """_require_sdk() raises a clear error when the SDK is absent."""

    def test_require_sdk_raises_without_sdk(self):
        from qkdpy.integrations.qpiai_qkd._compat import (
            QpiAISDKError,
            qpiai_available,
        )
        from qkdpy.integrations.qpiai_qkd.bridge import _require_sdk

        if qpiai_available():
            pytest.skip("QpiAI SDK is installed; cannot test the missing-SDK path")

        with pytest.raises(QpiAISDKError, match="pip install qkdpy\\[qpiai\\]"):
            _require_sdk()

    def test_bridge_methods_raise_without_sdk(self):
        from qkdpy.integrations.qpiai_qkd._compat import (
            QpiAISDKError,
            qpiai_available,
        )
        from qkdpy.integrations.qpiai_qkd.bridge import QpiAIIntegration

        if qpiai_available():
            pytest.skip("QpiAI SDK is installed; cannot test the missing-SDK path")

        bridge = QpiAIIntegration()
        with pytest.raises(QpiAISDKError):
            bridge.create_bb84_circuit(num_qubits=2)
        with pytest.raises(QpiAISDKError):
            bridge.create_ghz_circuit(num_qubits=3)
        with pytest.raises(QpiAISDKError):
            bridge.statevector_from_array([1, 0])


# ---------------------------------------------------------------------------
# Fix 4: MD5/SHA-1 rejection in cryptographic_hash
# ---------------------------------------------------------------------------


class TestWeakHashRejection:
    """PrivacyAmplification.cryptographic_hash rejects weak algorithms."""

    def test_sha1_rejected(self):
        from qkdpy.key_management.privacy_amplification import PrivacyAmplification

        key = [1, 0, 1, 0] * 4
        with pytest.raises(ValueError, match="not permitted"):
            PrivacyAmplification.cryptographic_hash(key, 4, hash_algorithm="sha1")

    def test_md5_rejected(self):
        from qkdpy.key_management.privacy_amplification import PrivacyAmplification

        key = [1, 0, 1, 0] * 4
        with pytest.raises(ValueError, match="not permitted"):
            PrivacyAmplification.cryptographic_hash(key, 4, hash_algorithm="md5")

    def test_sha256_accepted(self):
        from qkdpy.key_management.privacy_amplification import PrivacyAmplification

        key = [1, 0, 1, 0] * 4
        result = PrivacyAmplification.cryptographic_hash(
            key, 4, hash_algorithm="sha256"
        )
        assert len(result) == 4
        assert all(b in (0, 1) for b in result)

    def test_sha512_accepted(self):
        from qkdpy.key_management.privacy_amplification import PrivacyAmplification

        key = [1, 0, 1, 0] * 4
        result = PrivacyAmplification.cryptographic_hash(
            key, 8, hash_algorithm="sha512"
        )
        assert len(result) == 8

    def test_blake2b_accepted(self):
        from qkdpy.key_management.privacy_amplification import PrivacyAmplification

        key = [1, 0, 1, 0] * 4
        result = PrivacyAmplification.cryptographic_hash(
            key, 4, hash_algorithm="blake2b"
        )
        assert len(result) == 4

    def test_unknown_algorithm_rejected(self):
        from qkdpy.key_management.privacy_amplification import PrivacyAmplification

        key = [1, 0, 1, 0] * 4
        with pytest.raises(ValueError, match="Unsupported"):
            PrivacyAmplification.cryptographic_hash(key, 4, hash_algorithm="whirlpool")


# ---------------------------------------------------------------------------
# Fix 7: Entanglement attack fidelity-based detection
# ---------------------------------------------------------------------------


class TestEntanglementAttackFidelity:
    """entanglement_attack uses physical fidelity for detection probability."""

    def test_detection_is_not_random_coin_flip(self):
        """The detection probability should be fidelity-based, not a random
        coin flip. The model applies random unitaries 50% of the time, and
        the average disturbance from a random unitary is ~50%, giving an
        overall detection rate of ~25% (not 50% as a coin flip would)."""
        from qkdpy.core.channels import QuantumChannel
        from qkdpy.core.qubit import Qubit

        detections = 0
        trials = 1000
        for _ in range(trials):
            q = Qubit.zero()
            _, detected = QuantumChannel.entanglement_attack(q)
            if detected:
                detections += 1

        detection_rate = detections / trials

        # The detection rate should be ~25% (50% Eve acts * 50% avg disturbance).
        # A coin flip would give ~50%. We check it's in the range [0.20, 0.30].
        assert 0.20 <= detection_rate <= 0.30, (
            f"Detection rate {detection_rate:.3f} is outside expected range [0.20, 0.30]. "
            "Expected ~25% (50% Eve interaction * 50% avg disturbance), "
            "not 50% as a coin flip would give."
        )

    def test_detection_is_state_dependent(self):
        """Superposition states should have higher detection probability
        than computational basis states because the CNOT entangles them."""
        from qkdpy.core.channels import QuantumChannel
        from qkdpy.core.qubit import Qubit

        # Run many trials on |+> state
        superposition_detections = 0
        trials = 200
        for _ in range(trials):
            q = Qubit.plus()
            _, detected = QuantumChannel.entanglement_attack(q)
            if detected:
                superposition_detections += 1

        # For |+>, the CNOT creates entanglement → significant disturbance.
        # Detection probability should be non-trivially above 0.
        # (Exact value depends on the random rotation Eve applies, but
        # it should be measurably non-zero for superposition states.)
        # We just verify it's not always 0 (which would indicate a broken model).
        # With 200 trials and ~25% average detection rate, P(0 detections) ≈ 0.
        assert superposition_detections > 0, (
            "Expected some detections for |+> state; "
            "fidelity-based model should detect superposition disturbance"
        )


# ---------------------------------------------------------------------------
# Fix 3: LDPC arctanh clamping
# ---------------------------------------------------------------------------


class TestLDPCClamping:
    """LDPC belief propagation should not produce arctanh divide-by-zero."""

    def test_ldpc_no_runtime_warning(self):
        from qkdpy.key_management.error_correction import ErrorCorrection

        # Create keys with high error rate to stress the belief propagation
        n = 64
        alice_key = [0] * n
        bob_key = [1] * n  # All wrong — extreme case

        with warnings.catch_warnings():
            warnings.simplefilter("error", RuntimeWarning)
            # Should NOT raise RuntimeWarning about divide by zero
            corrected_a, corrected_b = ErrorCorrection.ldpc(
                alice_key, bob_key, max_iterations=10
            )

        # Just verify it returned something sensible
        assert len(corrected_a) == n
        assert len(corrected_b) == n

    def test_low_density_parity_check_no_warning(self):
        from qkdpy.key_management.error_correction import ErrorCorrection

        n = 64
        alice_key = [0] * n
        bob_key = [1] * n

        with warnings.catch_warnings():
            warnings.simplefilter("error", RuntimeWarning)
            corrected_a, corrected_b, iters = ErrorCorrection.low_density_parity_check(
                alice_key, bob_key, code_rate=0.5, max_iterations=5
            )

        assert len(corrected_a) == n
        assert len(corrected_b) == n


# ---------------------------------------------------------------------------
# Fix 8: QuantumChannel noise_model validation
# ---------------------------------------------------------------------------


class TestNoiseModelValidation:
    """QuantumChannel rejects unknown noise models."""

    def test_valid_models_accepted(self):
        from qkdpy.core.channels import QuantumChannel

        for model in [
            "depolarizing",
            "bit_flip",
            "phase_flip",
            "phase_damping",
            "dephasing",
            "amplitude_damping",
        ]:
            ch = QuantumChannel(noise_model=model, noise_level=0.05)
            assert ch.noise_model == model

        # "none" only stays "none" when noise_level is 0
        ch_none = QuantumChannel(noise_model="none", noise_level=0.0)
        assert ch_none.noise_model == "none"

        # "none" with positive noise_level gets promoted to depolarizing
        ch_promoted = QuantumChannel(noise_model="none", noise_level=0.05)
        assert ch_promoted.noise_model == "depolarizing"

    def test_invalid_model_rejected(self):
        from qkdpy.core.channels import QuantumChannel

        with pytest.raises(ValueError, match="Unknown noise_model"):
            QuantumChannel(noise_model="typo_model")

    def test_invalid_model_error_message_lists_valid(self):
        from qkdpy.core.channels import QuantumChannel

        with pytest.raises(ValueError, match="depolarizing"):
            QuantumChannel(noise_model="foobar")


# ---------------------------------------------------------------------------
# Fix 6: toeplitz_hashing seed reproducibility
# ---------------------------------------------------------------------------


class TestToeplitzSeed:
    """toeplitz_hashing respects the seed parameter."""

    def test_same_seed_same_output(self):
        from qkdpy.key_management.privacy_amplification import PrivacyAmplification

        key = [1, 0, 1, 1, 0, 0, 1, 0] * 4
        r1 = PrivacyAmplification.toeplitz_hashing(key, 8, seed=42)
        r2 = PrivacyAmplification.toeplitz_hashing(key, 8, seed=42)
        assert r1 == r2

    def test_different_seed_different_output(self):
        from qkdpy.key_management.privacy_amplification import PrivacyAmplification

        key = [1, 0, 1, 1, 0, 0, 1, 0] * 4
        r1 = PrivacyAmplification.toeplitz_hashing(key, 8, seed=42)
        r2 = PrivacyAmplification.toeplitz_hashing(key, 8, seed=99)
        # Different seeds should (almost certainly) produce different outputs
        assert r1 != r2

    def test_no_seed_produces_output(self):
        from qkdpy.key_management.privacy_amplification import PrivacyAmplification

        key = [1, 0, 1, 1, 0, 0, 1, 0] * 4
        result = PrivacyAmplification.toeplitz_hashing(key, 8)
        assert len(result) == 8
        assert all(b in (0, 1) for b in result)


# ---------------------------------------------------------------------------
# Fix 5: EfficientQKDPredictor seeded reproducibility
# ---------------------------------------------------------------------------


class TestEfficientPredictorSeeding:
    """EfficientQKDPredictor produces reproducible results with a seed."""

    def test_same_seed_same_weights(self):
        from qkdpy.ml.efficient_models import EfficientQKDPredictor

        p1 = EfficientQKDPredictor(input_dim=5, seed=123)
        p2 = EfficientQKDPredictor(input_dim=5, seed=123)

        for w1, w2 in zip(p1.weights, p2.weights, strict=True):
            np.testing.assert_array_equal(w1, w2)

    def test_different_seed_different_weights(self):
        from qkdpy.ml.efficient_models import EfficientQKDPredictor

        p1 = EfficientQKDPredictor(input_dim=5, seed=123)
        p2 = EfficientQKDPredictor(input_dim=5, seed=456)

        any_different = any(
            not np.array_equal(w1, w2)
            for w1, w2 in zip(p1.weights, p2.weights, strict=True)
        )
        assert any_different, "Different seeds should produce different weights"

    def test_no_seed_still_works(self):
        from qkdpy.ml.efficient_models import EfficientQKDPredictor

        p = EfficientQKDPredictor(input_dim=5)
        assert len(p.weights) > 0

    def test_training_reproducible_with_seed(self):
        from qkdpy.ml.efficient_models import EfficientQKDPredictor

        rng = np.random.default_rng(42)
        X = rng.standard_normal((50, 5)).astype(np.float32)
        y = (X[:, 0] + X[:, 1]).astype(np.float32)

        p1 = EfficientQKDPredictor(input_dim=5, seed=99, enable_pruning=False)
        r1 = p1.fit(X.copy(), y.copy(), epochs=5)

        p2 = EfficientQKDPredictor(input_dim=5, seed=99, enable_pruning=False)
        r2 = p2.fit(X.copy(), y.copy(), epochs=5)

        assert r1["final_train_loss"] == r2["final_train_loss"]


# ---------------------------------------------------------------------------
# Fix 1: Version consistency
# ---------------------------------------------------------------------------


class TestVersionConsistency:
    """__version__ matches pyproject.toml."""

    def test_version_is_071(self):
        import qkdpy

        assert qkdpy.__version__ == "0.7.1"

    def test_pyproject_version_matches(self):
        """Check pyproject.toml version matches __version__."""
        import tomllib

        with open("pyproject.toml", "rb") as f:
            data = tomllib.load(f)

        import qkdpy

        assert data["project"]["version"] == qkdpy.__version__


# ---------------------------------------------------------------------------
# Fix 2 (audit): Python 3.10 classifier removed
# ---------------------------------------------------------------------------


class TestPyPIClassifiers:
    """Python 3.10 classifier should not be present."""

    def test_no_python_310_classifier(self):
        import tomllib

        with open("pyproject.toml", "rb") as f:
            data = tomllib.load(f)

        classifiers = data["project"]["classifiers"]
        python_classifiers = [c for c in classifiers if "Python :: 3." in c]
        assert "Programming Language :: Python :: 3.10" not in python_classifiers
        assert "Programming Language :: Python :: 3.11" in python_classifiers
        assert "Programming Language :: Python :: 3.12" in python_classifiers

    def test_requires_python_311(self):
        import tomllib

        with open("pyproject.toml", "rb") as f:
            data = tomllib.load(f)

        assert data["project"]["requires-python"] == ">=3.11"


# ---------------------------------------------------------------------------
# Fix 7 (audit): mypy visualization overrides removed
# ---------------------------------------------------------------------------


class TestMypyOverridesRemoved:
    """The visualization mypy ignore_errors overrides should be gone."""

    def test_no_visualization_override(self):
        import tomllib

        with open("pyproject.toml", "rb") as f:
            data = tomllib.load(f)

        overrides = data.get("tool", {}).get("mypy", {}).get("overrides", [])
        for override in overrides:
            modules = override.get("module", [])
            assert "qkdpy.utils.visualization" not in modules
            assert "qkdpy.utils.advanced_visualization" not in modules
