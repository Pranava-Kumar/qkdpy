"""Regression tests for CSPRNG usage in the key-distillation pipeline."""

from qkdpy.core.secure_random import secure_sample, secure_shuffle
from qkdpy.key_management.advanced_privacy_amplification import (
    AdvancedPrivacyAmplification,
)
from qkdpy.key_management.error_correction import ErrorCorrection


def test_secure_sample_unique_and_in_range():
    sample = secure_sample(list(range(100)), 10)
    assert len(sample) == 10
    assert len(set(sample)) == 10
    assert all(0 <= x < 100 for x in sample)


def test_secure_shuffle_is_permutation():
    original = list(range(50))
    shuffled = original.copy()
    secure_shuffle(shuffled)
    assert sorted(shuffled) == sorted(original)
    assert len(shuffled) == len(original)


def test_xor_extract_runs_with_secure_swap():
    result = AdvancedPrivacyAmplification.xor_extract([1, 0, 1, 1, 0, 1, 0, 1])
    assert isinstance(result, list)
    assert len(result) > 0


def test_error_correction_runs_with_secure_swap():
    alice = [0, 1, 1, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0, 1]
    bob = alice.copy()
    # Introduce a single error for cascade to reconcile
    bob[5] = 1 - bob[5]
    a, b = ErrorCorrection.cascade(alice, bob)
    assert len(a) == len(alice) and len(b) == len(bob)
    assert a == b

    alice2 = [0, 1, 1, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0, 1]
    bob2 = alice2.copy()
    bob2[3] = 1 - bob2[3]
    ErrorCorrection.winnow(alice2, bob2)

    ErrorCorrection.ldpc(alice, bob)
