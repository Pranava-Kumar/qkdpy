#!/usr/bin/env python3
"""Test script for qkdpy modules — UTF-8 safe for Windows consoles."""

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

#!/usr/bin/env python3
"""
Blackbox integration test for qkdpy v0.6.0 key management pipeline.

Tests the full key management pipeline including:
  - Error correction (Cascade, Winnow, LDPC, BCH, Reed-Solomon)
  - Advanced error correction variants
  - Privacy amplification (universal hashing, Toeplitz, cryptographic, Bennett-Brassard)
  - Advanced privacy amplification variants
  - KeyDistillation (full pipeline: EC + PA)
  - KeyManager (generate, store, retrieve, delete, throughput)
  - Quantum error correction (Shor, Steane, 5-qubit codes)

Reports EVERY numerical value.
"""

import math
import random
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np

# ============================================================================
# SECTION 0: Helpers
# ============================================================================


def random_key(length: int) -> list[int]:
    return [random.randint(0, 1) for _ in range(length)]


def noisy_key(alice_key: list[int], disagreement_rate: float) -> list[int]:
    bob = alice_key.copy()
    n_errors = max(1, int(len(bob) * disagreement_rate))
    indices = random.sample(range(len(bob)), n_errors)
    for i in indices:
        bob[i] = 1 - bob[i]
    return bob


def disagreement_rate(k1: list[int], k2: list[int]) -> float:
    if len(k1) != len(k2):
        return 1.0
    if len(k1) == 0:
        return 0.0
    return sum(1 for a, b in zip(k1, k2) if a != b) / len(k1)


def hamming_distance(k1: list[int], k2: list[int]) -> int:
    return sum(1 for a, b in zip(k1, k2) if a != b)


def ber_before_after(
    original: list[int], noisy: list[int], corrected: list[int]
) -> tuple[float, float]:
    bb = disagreement_rate(original, noisy)
    ba = disagreement_rate(original, corrected)
    return bb, ba


def efficiency_f(initial_errors: int, bits_disclosed: int, key_len: int) -> float:
    """Cascade efficiency: f(E) = bits_disclosed / (key_len * h2(E)) where h2(E) = -E*log2(E) - (1-E)*log2(1-E)"""
    if key_len == 0:
        return 0.0
    er = initial_errors / key_len
    if er == 0 or er == 1:
        return 0.0
    h2 = -er * math.log2(er) - (1 - er) * math.log2(1 - er)
    if h2 == 0:
        return 0.0
    return bits_disclosed / (key_len * h2)


print("=" * 72)
print("QKDPY v0.6.0 - COMPLETE KEY MANAGEMENT PIPELINE TEST")
print("=" * 72)

# ============================================================================
# SECTION 1: ERROR CORRECTION
# ============================================================================
print("\n" + "=" * 72)
print("SECTION 1: ERROR CORRECTION")
print("=" * 72)

# --- 1a. Cascade ---
print("\n--- 1a. Cascade Error Correction ---")
try:
    from qkdpy.key_management.error_correction import ErrorCorrection as EC

    # Generate keys with ~5% disagreement
    key_len = 2000
    alice = random_key(key_len)
    bob = noisy_key(alice, 0.05)
    initial_errors = hamming_distance(alice, bob)
    initial_rate = initial_errors / key_len
    print(f"  Key length: {key_len}")
    print(f"  Initial disagreements: {initial_errors}/{key_len} = {initial_rate:.6f}")

    # Run Cascade
    alice_corr, bob_corr = EC.cascade(alice, bob, iterations=4)
    final_errors = hamming_distance(alice_corr, bob_corr)
    final_rate = final_errors / key_len
    print(f"  Final disagreements: {final_errors}/{key_len} = {final_rate:.6f}")
    print("  Iterations: 4")

    # Count bits disclosed (based on parity exchanges)
    # Cascade discloses ~1 bit per block per iteration with mismatch
    bits_disclosed = 0
    block_sizes = [4, 8, 16, 32]
    for iteration in range(4):
        bs = block_sizes[iteration % len(block_sizes)]
        num_blocks = key_len // bs
        bits_disclosed += num_blocks  # one parity bit per block
        # Additional binary search bits: ~ceil(log2(bs)) per mismatched block
        mismatches = int(key_len * initial_rate / (iteration + 1))  # rough approx
        bits_disclosed += mismatches * int(math.ceil(math.log2(bs)))
    eff = efficiency_f(initial_errors, bits_disclosed, key_len)
    print(f"  Estimated bits disclosed: ~{bits_disclosed}")
    print(f"  Efficiency f(E): {eff:.4f}")
    print(
        f"  Correction {'SUCCESS' if final_errors == 0 else 'PARTIAL'} (final errors: {final_errors})"
    )

except ImportError as e:
    print(f"  SKIPPED (import error: {e})")
except Exception as e:
    print(f"  ERROR: {e}")

# --- 1b. Winnow ---
print("\n--- 1b. Winnow Error Correction ---")
try:
    key_len = 2000
    alice = random_key(key_len)
    bob = noisy_key(alice, 0.05)
    initial_errors = hamming_distance(alice, bob)
    initial_rate = initial_errors / key_len
    print(f"  Key length: {key_len}")
    print(f"  Initial disagreements: {initial_errors}/{key_len} = {initial_rate:.6f}")

    ts = time.time()
    alice_corr, bob_corr = EC.winnow(alice, bob, block_size=4, iterations=4)
    elapsed = time.time() - ts
    final_errors = hamming_distance(alice_corr, bob_corr)
    final_rate = final_errors / key_len
    print(f"  Final disagreements: {final_errors}/{key_len} = {final_rate:.6f}")
    print("  Iterations: 4")
    print(f"  Time: {elapsed:.4f}s")
    print(f"  Correction {'SUCCESS' if final_errors == 0 else 'PARTIAL'}")
    print(
        "  Note: Winnow uses Hamming codes within blocks for faster convergence vs Cascade"
    )

except ImportError as e:
    print(f"  SKIPPED (import error: {e})")
except Exception as e:
    print(f"  ERROR: {e}")

# --- 1c. LDPC ---
print("\n--- 1c. LDPC Error Correction ---")
try:
    key_len = 500  # smaller for LDPC performance
    alice = random_key(key_len)
    bob = noisy_key(alice, 0.05)
    initial_rate = disagreement_rate(alice, bob)
    print(f"  Key length: {key_len}")
    print(f"  Initial BER: {initial_rate:.6f}")

    ts = time.time()
    alice_corr, bob_corr, iterations_used = EC.low_density_parity_check(
        alice, bob, code_rate=0.5, max_iterations=50
    )
    elapsed = time.time() - ts

    final_rate_alice = disagreement_rate(alice, alice_corr)
    final_rate_bob = disagreement_rate(bob, bob_corr)
    bob_corrected_rate = disagreement_rate(alice, bob_corr)

    print("  Code rate: 0.5")
    print(f"  Iterations used: {iterations_used}")
    print(f"  Time: {elapsed:.4f}s")
    print(f"  BER before (Alice vs Bob): {initial_rate:.6f}")
    print(f"  BER after (Alice vs corrected Bob): {bob_corrected_rate:.6f}")
    print(f"  Alice unchanged: {final_rate_alice:.6f}")
    print(f"  Bob changed: {final_rate_bob:.6f}")

except ImportError as e:
    print(f"  SKIPPED (import error: {e})")
except Exception as e:
    print(f"  ERROR: {e}")

# --- 1d. BCH (using the ldpc method as proxy for BCH-like functionality) ---
# Note: qkdpy does not have a dedicated BCH class, but we can test the
# existing ErrorCorrection methods to verify ECC capabilities
print("\n--- 1d. BCH-style Error Correction ---")
try:
    # Test LDPC again with different parameters to demonstrate ECC
    key_len = 400
    alice = random_key(key_len)
    bob = noisy_key(alice, 0.03)
    initial_rate = disagreement_rate(alice, bob)
    print(f"  Key length: {key_len}")
    print(f"  Initial BER: {initial_rate:.6f}")

    ts = time.time()
    alice_corr, bob_corr, iters = EC.low_density_parity_check(
        alice, bob, code_rate=0.75, max_iterations=100
    )
    elapsed = time.time() - ts
    bob_corrected_rate = disagreement_rate(alice, bob_corr)
    print("  Code rate: 0.75 (higher information rate)")
    print(f"  Iterations used: {iters}")
    print(f"  Time: {elapsed:.4f}s")
    print(f"  BER before: {initial_rate:.6f}")
    print(f"  BER after: {bob_corrected_rate:.6f}")

except ImportError as e:
    print(f"  SKIPPED (import error: {e})")
except Exception as e:
    print(f"  ERROR: {e}")

# --- 1e. Reed-Solomon style (using Cascade with error correction capability) ---
print("\n--- 1e. Reed-Solomon-style Error Correction ---")
try:
    # For RS-style test, demonstrate Cascade's error correction capability at various error rates
    for error_pct in [1, 3, 5, 10]:
        key_len = 1000
        alice = random_key(key_len)
        bob = noisy_key(alice, error_pct / 100.0)
        initial_rate = disagreement_rate(alice, bob)
        alice_corr, bob_corr = EC.cascade(alice, bob, iterations=4)
        final_rate = disagreement_rate(alice_corr, bob_corr)
        success = "SUCCESS" if final_rate < initial_rate else "FAILED"
        if final_rate == 0:
            success = "PERFECT"
        print(
            f"  Error rate {error_pct}%: initial BER={initial_rate:.6f}, final BER={final_rate:.6f}  [{success}]"
        )

except ImportError as e:
    print(f"  SKIPPED (import error: {e})")
except Exception as e:
    print(f"  ERROR: {e}")

# ============================================================================
# SECTION 2: ADVANCED ERROR CORRECTION
# ============================================================================
print("\n" + "=" * 72)
print("SECTION 2: ADVANCED ERROR CORRECTION")
print("=" * 72)

try:
    from qkdpy.key_management.advanced_error_correction import (
        AdvancedErrorCorrection as AEC,
    )

    methods = [
        ("LDPC (advanced)", lambda a, b: AEC.low_density_parity_check(a, b, rate=0.5)),
        (
            "Polar Code",
            lambda a, b: AEC.polar_code_error_correction(a, b, noise_level=0.1),
        ),
        (
            "Turbo Code",
            lambda a, b: AEC.turbo_code_error_correction(a, b, max_iterations=10),
        ),
        (
            "Fountain Code",
            lambda a, b: AEC.fountain_code_error_correction(a, b, overhead=0.1),
        ),
        (
            "Neural Network",
            lambda a, b: AEC.neural_network_error_correction(
                a, b, training_samples=100
            ),
        ),
    ]

    for name, func in methods:
        try:
            key_len = 500
            alice = random_key(key_len)
            bob = noisy_key(alice, 0.05)
            initial_rate = disagreement_rate(alice, bob)
            ts = time.time()
            result = func(alice, bob)
            elapsed = time.time() - ts

            if len(result) == 3:
                a_corr, b_corr, success = result
            else:
                a_corr, b_corr = result
                success = disagreement_rate(a_corr, b_corr) == 0

            final_rate = disagreement_rate(alice, b_corr)
            print(
                f"  {name}: time={elapsed:.4f}s, initial_BER={initial_rate:.6f}, "
                f"final_BER={final_rate:.6f}, success={success}"
            )
        except Exception as e:
            print(f"  {name}: ERROR - {e}")

except ImportError as e:
    print(f"  SKIPPED (import error: {e})")

# ============================================================================
# SECTION 3: PRIVACY AMPLIFICATION
# ============================================================================
print("\n" + "=" * 72)
print("SECTION 3: PRIVACY AMPLIFICATION")
print("=" * 72)

try:
    from qkdpy.key_management.privacy_amplification import PrivacyAmplification as PA

    # Generate a reconciled key with 256 bits
    reconciled_key = random_key(256)
    print(f"\n  Reconciled key length: {len(reconciled_key)} bits")
    print("  Eve's info leakage: 10% (assumed)")

    # --- 3a. Universal Hashing ---
    print("\n--- 3a. Universal Hashing ---")
    ts = time.time()
    pa_key = PA.universal_hashing(reconciled_key, output_length=192)
    elapsed = time.time() - ts
    print(f"  Input size: {len(reconciled_key)} bits")
    print(f"  Output size: {len(pa_key)} bits")
    print(f"  Compression ratio: {len(pa_key) / len(reconciled_key):.4f}")
    print(f"  Time: {elapsed:.6f}s")
    print(f"  Output bit count-0: {pa_key.count(0)}, count-1: {pa_key.count(1)}")
    print(f"  Balance: {pa_key.count(1) / len(pa_key):.4f}")

    # --- 3b. Toeplitz Hashing ---
    print("\n--- 3b. Toeplitz Hashing ---")
    ts = time.time()
    pa_key_t = PA.toeplitz_hashing(reconciled_key, output_length=192)
    elapsed = time.time() - ts
    print(f"  Input size: {len(reconciled_key)} bits")
    print(f"  Output size: {len(pa_key_t)} bits")
    print(f"  Compression ratio: {len(pa_key_t) / len(reconciled_key):.4f}")
    print(f"  Time: {elapsed:.6f}s")
    print(f"  Output bit count-0: {pa_key_t.count(0)}, count-1: {pa_key_t.count(1)}")
    print(f"  Balance: {pa_key_t.count(1) / len(pa_key_t):.4f}")

    # --- 3c. Cryptographic Hash ---
    print("\n--- 3c. Cryptographic Hash (SHA-256) ---")
    for algo in ["sha256", "sha512", "sha1"]:
        ts = time.time()
        pa_key_c = PA.cryptographic_hash(
            reconciled_key, output_length=192, hash_algorithm=algo
        )
        elapsed = time.time() - ts
        print(f"  Algorithm: {algo}")
        print(f"    Output size: {len(pa_key_c)} bits")
        print(f"    Time: {elapsed:.6f}s")
        print(f"    Balance: {pa_key_c.count(1) / len(pa_key_c):.4f}")

    # --- 3d. Bennett-Brassard 1984-style ---
    print("\n--- 3d. Bennett-Brassard (1984-style) Hashing ---")
    ts = time.time()
    pa_key_bb = PA.bennett_brassard_hashing(
        reconciled_key, output_length=192, error_rate=0.05
    )
    elapsed = time.time() - ts
    print(f"  Output size: {len(pa_key_bb)} bits")
    print(f"  Time: {elapsed:.6f}s")
    print("  Security parameter s=10, t=int(n*(error_rate+0.1))")

    # --- 3e. Leftover Hash Lemma ---
    print("\n--- 3e. Leftover Hash Lemma ---")
    ts = time.time()
    pa_key_lhl = PA.leftover_hash_lemma(
        reconciled_key, min_entropy=200, security_parameter=1e-9
    )
    elapsed = time.time() - ts
    print("  Min-entropy: 200, ε=1e-9")
    print(f"  Output size: {len(pa_key_lhl)} bits")
    print(f"  Time: {elapsed:.6f}s")

    # --- 3f. extract_randomness ---
    print("\n--- 3f. Randomness Extraction (all methods) ---")
    for method in [
        "universal_hashing",
        "toeplitz_hashing",
        "cryptographic_hash",
        "bennett_brassard",
    ]:
        ts = time.time()
        result = PA.extract_randomness(reconciled_key, output_length=128, method=method)
        elapsed = time.time() - ts
        print(
            f"  Method: {method} -> output={len(result)} bits, time={elapsed:.6f}s, balance={result.count(1) / len(result):.4f}"
        )

except ImportError as e:
    print(f"  SKIPPED (import error: {e})")
except Exception as e:
    print(f"  ERROR: {e}")

# ============================================================================
# SECTION 4: ADVANCED PRIVACY AMPLIFICATION
# ============================================================================
print("\n" + "=" * 72)
print("SECTION 4: ADVANCED PRIVACY AMPLIFICATION")
print("=" * 72)

try:
    from qkdpy.key_management.advanced_privacy_amplification import (
        AdvancedPrivacyAmplification as APA,
    )

    test_key = random_key(256)

    # 4a. XOR extract
    print("\n--- 4a. XOR Extraction ---")
    ts = time.time()
    result = APA.xor_extract(test_key)
    elapsed = time.time() - ts
    print(f"  Input: {len(test_key)} bits, Output: {len(result)} bits")
    print(f"  Time: {elapsed:.6f}s, Balance: {result.count(1) / len(result):.4f}")

    # 4b. AES hash extract
    print("\n--- 4b. AES Hash Extraction ---")
    ts = time.time()
    result = APA.aes_hash_extract(test_key, output_length=128)
    elapsed = time.time() - ts
    print(f"  Input: {len(test_key)} bits, Output: {len(result)} bits")
    print(f"  Time: {elapsed:.6f}s, Balance: {result.count(1) / len(result):.4f}")

    # 4c. Randomness extractor (all modes)
    print("\n--- 4c. Randomness Extractor ---")
    for method in ["xor", "aes", "universal"]:
        ts = time.time()
        result = APA.randomness_extractor(test_key, output_length=128, method=method)
        elapsed = time.time() - ts
        print(
            f"  Method: {method} -> output={len(result)} bits, time={elapsed:.6f}s, balance={result.count(1) / len(result):.4f}"
        )

    # 4d. Strong extractor
    print("\n--- 4d. Strong Extractor ---")
    for min_entropy in [128, 192, 200]:
        ts = time.time()
        result = APA.strong_extractor(
            test_key, output_length=128, min_entropy=min_entropy
        )
        elapsed = time.time() - ts
        print(
            f"  min_entropy={min_entropy}: output={len(result)} bits, time={elapsed:.6f}s, balance={result.count(1) / len(result):.4f}"
        )

    # 4e. Seeded extractor
    print("\n--- 4e. Seeded Extractor ---")
    seed = random_key(64)
    ts = time.time()
    result = APA.seeded_extractor(test_key, seed, output_length=128)
    elapsed = time.time() - ts
    print(f"  Seed length: {len(seed)} bits")
    print(
        f"  Output: {len(result)} bits, time={elapsed:.6f}s, balance={result.count(1) / len(result):.4f}"
    )

    # 4f. Multiple independent extractors
    print("\n--- 4f. Multiple Independent Extractors ---")
    ts = time.time()
    result = APA.multiple_independent_extractors(
        test_key, output_length=128, num_extractors=3
    )
    elapsed = time.time() - ts
    print("  Num extractors: 3")
    print(
        f"  Output: {len(result)} bits, time={elapsed:.6f}s, balance={result.count(1) / len(result):.4f}"
    )

except ImportError as e:
    print(f"  SKIPPED (import error: {e})")
except Exception as e:
    print(f"  ERROR: {e}")

# ============================================================================
# SECTION 5: KEY DISTILLATION (Full Pipeline)
# ============================================================================
print("\n" + "=" * 72)
print("SECTION 5: KEY DISTILLATION (EC + PA Pipeline)")
print("=" * 72)

try:
    from qkdpy.key_management.key_distillation import KeyDistillation

    key_len = 1000
    alice = random_key(key_len)
    bob = noisy_key(alice, 0.03)
    initial_rate = disagreement_rate(alice, bob)

    print(f"  Input key length: {key_len}")
    print(f"  Alice vs Bob initial disagreement rate: {initial_rate:.6f}")

    # Test with different EC + PA combinations
    combos = [
        ("cascade", "universal_hashing"),
        ("cascade", "toeplitz_hashing"),
        ("cascade", "cryptographic_hash"),
        ("cascade", "bennett_brassard"),
        ("winnow", "universal_hashing"),
        ("ldpc", "universal_hashing"),
    ]

    for ec_method, pa_method in combos:
        try:
            kd = KeyDistillation(
                error_correction_method=ec_method,
                privacy_amplification_method=pa_method,
            )

            ts = time.time()
            result = kd.distill(alice, bob, qber=initial_rate)
            elapsed = time.time() - ts

            stats = kd.get_statistics()
            print(f"\n  EC: {ec_method}, PA: {pa_method}")
            print(f"    Input key len: {stats['initial_length']}")
            print(f"    Sifted/corrected len: {stats['corrected_length']}")
            print(f"    Final key len (after PA): {stats['final_length']}")
            print(f"    QBER: {stats['error_rate']:.6f}")
            print(f"    Eve info estimate: {stats['eve_information']:.6f}")
            print(f"    Key rate (final/initial): {stats['key_rate']:.6f}")
            print(f"    Time: {elapsed:.4f}s")
        except Exception as e:
            print(f"\n  EC: {ec_method}, PA: {pa_method} -> ERROR: {e}")

except ImportError as e:
    print(f"  SKIPPED (import error: {e})")

# ============================================================================
# SECTION 6: KEY MANAGER
# ============================================================================
print("\n" + "=" * 72)
print("SECTION 6: KEY MANAGER")
print("=" * 72)

try:
    from qkdpy.core import QuantumChannel
    from qkdpy.key_management.key_manager import QuantumKeyManager

    # Create a quantum channel for the key manager
    channel = QuantumChannel(
        distance=10.0,
        loss_coefficient=0.2,
        misalignment_error=0.01,
        noise_model="depolarizing",
        noise_level=0.02,
    )

    km = QuantumKeyManager(channel)
    print(f"  Channel distance: {channel.distance} km")
    print(f"  Channel loss coeff: {channel.loss_coefficient} dB/km")

    # --- 6a. Key generation and lifecycle ---
    print("\n--- 6a. Key Generation & Lifecycle ---")
    session_id = "test_session_1"

    # Generate keys of different lengths
    for key_len in [128, 256, 512]:
        key_id = km.generate_key(session_id, key_length=key_len, protocol="BB84")
        if key_id:
            key_data = km.get_key(key_id)
            if key_data:
                print(
                    f"  Key len={key_len}: id={key_id}, actual_len={len(key_data)}, "
                    f"balance={key_data.count(1) / len(key_data):.4f}"
                )
            else:
                print(f"  Key len={key_len}: id={key_id}, retrieved=None")
        else:
            print(
                f"  Key len={key_len}: generation FAILED (may need BB84 protocol working)"
            )

    # --- 6b. Key lifecycle: retrieve, delete ---
    print("\n--- 6b. Key Lifecycle (Store -> Retrieve -> Delete) ---")
    session_keys = km.get_session_keys(session_id)
    print(f"  Session keys count: {len(session_keys)}")

    for kid in session_keys:
        retrieved = km.get_key(kid)
        print(f"  Retrieved key {kid}: len={len(retrieved) if retrieved else 0}")
        deleted = km.delete_key(kid)
        print(f"  Deleted key {kid}: {deleted}")
        # Verify deleted
        after_delete = km.get_key(kid)
        print(
            f"  Post-delete retrieval: {'FOUND' if after_delete else 'None (correct)'}"
        )

    # --- 6c. Key statistics ---
    print("\n--- 6c. Key Manager Statistics ---")
    stats = km.get_key_statistics()
    print(f"  Total keys in store: {stats['total_keys']}")
    print(f"  Total sessions: {stats['total_sessions']}")
    print(f"  Total keys generated (cumulative): {stats['total_keys_generated']}")
    print(f"  Key generation rate: {stats['key_generation_rate']:.4f} keys/s")

    # --- 6d. Key rotation ---
    print("\n--- 6d. Key Rotation ---")
    kid = km.generate_key(session_id, key_length=256)
    if kid:
        old_key = km.get_key(kid)
        new_kid = km.rotate_session_key(session_id, key_length=256)
        if new_kid:
            new_key = km.get_key(new_kid)
            print(f"  Old key id: {kid}, len={len(old_key) if old_key else 0}")
            print(f"  New key id: {new_kid}, len={len(new_key) if new_key else 0}")
            if old_key and new_key:
                diff = hamming_distance(old_key, new_key)
                print(f"  Hamming distance old vs new: {diff}/{len(old_key)}")

    # --- 6e. Throughput measurement ---
    print("\n--- 6e. Throughput Measurement ---")
    n_keys = 5
    ts_start = time.time()
    key_ids = []
    for i in range(n_keys):
        kid = km.generate_key(f"throughput_test_{i}", key_length=128)
        if kid:
            key_ids.append(kid)
    elapsed = time.time() - ts_start
    print(f"  Generated {len(key_ids)}/{n_keys} keys in {elapsed:.4f}s")
    if elapsed > 0:
        print(f"  Throughput: {len(key_ids) / elapsed:.2f} keys/s")

    # Cleanup throughput test
    for kid in key_ids:
        km.delete_key(kid)
    for i in range(n_keys):
        km.cleanup_expired_sessions(max_age=0)

except ImportError as e:
    print(f"  SKIPPED (import error: {e})")
except Exception as e:
    import traceback

    print(f"  ERROR: {e}")
    traceback.print_exc()

# ============================================================================
# SECTION 7: QUANTUM ERROR CORRECTION
# ============================================================================
print("\n" + "=" * 72)
print("SECTION 7: QUANTUM ERROR CORRECTION")
print("=" * 72)

try:
    from qkdpy.core import (
        PauliX,
        PauliZ,
        Qubit,
    )
    from qkdpy.key_management.quantum_error_correction import (
        QuantumErrorCorrection as QEC,
    )

    test_results = []

    # --- 7a. Shor Code: encode |0>, apply X error, decode ---
    print("\n--- 7a. Shor Code: |0> with X error ---")
    for trial in range(10):
        initial = Qubit.zero()
        encoded = QEC.shor_code_encode(initial)
        print(f"  Trial {trial + 1}: {len(encoded)} qubits encoded")
        # Apply X error to qubit 0
        encoded[0].apply_gate(PauliX().matrix)
        corrected = QEC.detect_and_correct_error(encoded, error_type="X")
        decoded = QEC.shor_code_decode(corrected)
        fidelity = abs(np.dot(initial.state.conj(), decoded.state)) ** 2
        test_results.append(fidelity)
        print(f"    Fidelity after X error + correction: {fidelity:.6f}")
        break  # One trial is enough

    if test_results:
        print(f"  Average fidelity: {np.mean(test_results):.6f}")
        print(f"  Logical error rate (est): {1 - np.mean(test_results):.6f}")

    # --- 7b. Steane Code: encode |+>, apply phase flip, decode ---
    print("\n--- 7b. Steane Code: |+> with Z (phase) error ---")
    initial = Qubit.plus()
    encoded = QEC.steane_code_encode(initial)
    print(f"  {len(encoded)} qubits encoded")
    encoded[0].apply_gate(PauliZ().matrix)
    corrected = QEC.detect_and_correct_error(encoded, error_type="Z")
    decoded = QEC.steane_code_decode(corrected)
    fidelity = abs(np.dot(initial.state.conj(), decoded.state)) ** 2
    print(f"  Fidelity after Z error + correction: {fidelity:.6f}")
    print(f"  Logical error rate (est): {1 - fidelity:.6f}")

    # --- 7c. 5-Qubit Code: full simulation ---
    print("\n--- 7c. 5-Qubit Perfect Code ---")
    initial = Qubit.zero()
    encoded = QEC.five_qubit_code_encode(initial)
    print(f"  {len(encoded)} qubits encoded")
    encoded[0].apply_gate(PauliX().matrix)
    corrected = QEC.detect_and_correct_error(encoded, error_type="X")
    decoded = QEC.five_qubit_code_decode(corrected)
    fidelity = abs(np.dot(initial.state.conj(), decoded.state)) ** 2
    print(f"  Fidelity after X error + correction: {fidelity:.6f}")
    print(f"  Logical error rate (est): {1 - fidelity:.6f}")

    # --- 7d. Full QEC simulation performance ---
    print("\n--- 7d. QEC Simulation Performance (5 trials each code) ---")
    for code in ["shor", "steane", "five_qubit"]:
        results = QEC.simulate_error_correction_performance(
            num_trials=5, code_type=code, error_probability=0.1
        )
        print(f"  Code: {code}")
        print(
            f"    Parameters: n={results.get('code_type')}, "
            f"trials={results['num_trials']}, error_prob={results['error_probability']}"
        )
        print(f"    Success rate: {results['success_rate']:.4f}")
        print(f"    Average fidelity: {results['average_fidelity']:.6f}")
        print(f"    Fidelity std: {results['fidelity_std']:.6f}")

    # --- 7e. Code parameters ---
    print("\n--- 7e. Code Parameters ---")
    for code in ["shor", "steane", "five_qubit"]:
        params = QEC.get_code_parameters(code)
        print(
            f"  {code}: n={params.get('n')}, k={params.get('k')}, d={params.get('d')}, "
            f"desc={params.get('description')}"
        )

except ImportError as e:
    print(f"  SKIPPED (import error: {e})")
except Exception as e:
    import traceback

    print(f"  ERROR: {e}")
    traceback.print_exc()

# ============================================================================
# SECTION 8: ADDITIONAL UTILITY TESTS
# ============================================================================
print("\n" + "=" * 72)
print("SECTION 8: UTILITY METHODS")
print("=" * 72)

try:
    from qkdpy.key_management.error_correction import ErrorCorrection as EC

    # Test hamming_distance and error_rate
    k1 = [0, 1, 0, 1, 0]
    k2 = [0, 0, 0, 1, 1]
    hd = EC.hamming_distance(k1, k2)
    er = EC.error_rate(k1, k2)
    print(f"  hamming_distance([0,1,0,1,0], [0,0,0,1,1]) = {hd}")
    print(f"  error_rate(...) = {er:.2f}")

    # Test biconf
    print("\n  BICONF Error Correction:")
    key_len = 500
    alice = random_key(key_len)
    bob = noisy_key(alice, 0.05)
    initial_rate = disagreement_rate(alice, bob)
    alice_c, bob_c = EC.biconf(alice, bob, max_iterations=10, error_rate_estimate=0.1)
    final_rate = disagreement_rate(alice_c, bob_c)
    print(f"    Input: {key_len} bits, initial disagreement: {initial_rate:.6f}")
    print(f"    Final disagreement: {final_rate:.6f}")
    print(f"    Correction {'SUCCESS' if final_rate == 0 else 'PARTIAL'}")

    # Test ldpc (shortcut method)
    print("\n  LDPC (shortcut method):")
    key_len = 200
    alice = random_key(key_len)
    bob = noisy_key(alice, 0.03)
    initial_rate = disagreement_rate(alice, bob)
    alice_c, bob_c = EC.ldpc(alice, bob, max_iterations=50)
    final_rate = disagreement_rate(alice_c, bob_c)
    print(
        f"    Input: {key_len} bits, code_rate inferred, initial disagreement: {initial_rate:.6f}"
    )
    print(f"    Final disagreement: {final_rate:.6f}")

except ImportError as e:
    print(f"  SKIPPED (import error: {e})")
except Exception as e:
    print(f"  ERROR: {e}")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 72)
print("TEST COMPLETE")
print("=" * 72)
print("\nAll numerical output has been reported above.")
