#!/usr/bin/env python3
"""Test script for qkdpy modules — UTF-8 safe for Windows consoles."""

import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

#!/usr/bin/env python3
"""Blackbox tester for qkdpy v0.6.0 — Crypto + Enterprise modules.

Tests every public class/method in the crypto and enterprise packages
and reports all numerical output.
"""

import json
import os
import sys

# Ensure premium tier for full enterprise access
os.environ["QKDPY_PRODUCT_TIER"] = "premium"
os.environ["QKDPY_HSM_ENABLED"] = "true"

# Insert source path
sys.path.insert(0, "E:/opensource/qkdpy/src")
print(f"Python: {sys.version}")
print("sys.path includes: E:/opensource/qkdpy/src")

SEP = "=" * 78
DASH = "-" * 78


def section(title):
    print(f"\n{SEP}")
    print(f"  {title}")
    print(SEP)


def subsection(title):
    print(f"\n{DASH}")
    print(f"  {title}")
    print(DASH)


# =====================================================================
#  IMPORTS
# =====================================================================
section("IMPORTS")

try:
    from qkdpy.crypto.advanced_crypto import (
        QuantumCommitment,
        QuantumHash,
        QuantumZeroKnowledge,
    )

    print("[OK] qkdpy.crypto.advanced_crypto")
except Exception as e:
    print(f"[FAIL] qkdpy.crypto.advanced_crypto: {e}")

try:
    from qkdpy.crypto.authentication import QuantumAuth

    print("[OK] qkdpy.crypto.authentication")
except Exception as e:
    print(f"[FAIL] qkdpy.crypto.authentication: {e}")

try:
    from qkdpy.crypto.encryption import OneTimePad

    print("[OK] qkdpy.crypto.encryption")
except Exception as e:
    print(f"[FAIL] qkdpy.crypto.encryption: {e}")

try:
    from qkdpy.crypto.decryption import OneTimePadDecrypt

    print("[OK] qkdpy.crypto.decryption")
except Exception as e:
    print(f"[FAIL] qkdpy.crypto.decryption: {e}")

try:
    from qkdpy.crypto.key_exchange import QuantumKeyExchange

    print("[OK] qkdpy.crypto.key_exchange")
except Exception as e:
    print(f"[FAIL] qkdpy.crypto.key_exchange: {e}")

try:
    from qkdpy.crypto.quantum_auth import QuantumAuthenticator

    print("[OK] qkdpy.crypto.quantum_auth")
except Exception as e:
    print(f"[FAIL] qkdpy.crypto.quantum_auth: {e}")

try:
    from qkdpy.crypto.quantum_rng import QuantumRandomNumberGenerator

    print("[OK] qkdpy.crypto.quantum_rng")
except Exception as e:
    print(f"[FAIL] qkdpy.crypto.quantum_rng: {e}")

try:
    from qkdpy.crypto.enhanced_security import (
        QuantumAuthentication,
        QuantumKeyValidation,
        QuantumSideChannelProtection,
    )

    print("[OK] qkdpy.crypto.enhanced_security")
except Exception as e:
    print(f"[FAIL] qkdpy.crypto.enhanced_security: {e}")

try:
    from qkdpy.enterprise.hsm_interface import HSMProvider, get_hsm

    print("[OK] qkdpy.enterprise.hsm_interface")
except Exception as e:
    print(f"[FAIL] qkdpy.enterprise.hsm_interface: {e}")

try:
    from qkdpy.enterprise.compliance import (
        ComplianceChecker,
        ComplianceStandard,
    )

    print("[OK] qkdpy.enterprise.compliance")
except Exception as e:
    print(f"[FAIL] qkdpy.enterprise.compliance: {e}")

try:
    from qkdpy.enterprise.audit import AuditEventType, AuditLogger

    print("[OK] qkdpy.enterprise.audit")
except Exception as e:
    print(f"[FAIL] qkdpy.enterprise.audit: {e}")

try:
    from qkdpy.enterprise.licensing import (
        Feature,
        ProductTier,
        feature_available,
        get_active_tier,
        require_feature,
        set_active_tier,
    )

    print("[OK] qkdpy.enterprise.licensing")
except Exception as e:
    print(f"[FAIL] qkdpy.enterprise.licensing: {e}")

try:
    from qkdpy.enterprise.quantum_safe import (
        QuantumSafeAssessment,
        classic_enterprise_profile,
        generate_roadmap,
    )

    print("[OK] qkdpy.enterprise.quantum_safe")
except Exception as e:
    print(f"[FAIL] qkdpy.enterprise.quantum_safe: {e}")

try:
    from qkdpy.core import QuantumChannel

    print("[OK] qkdpy.core.QuantumChannel")
except Exception as e:
    print(f"[FAIL] qkdpy.core.QuantumChannel: {e}")

try:
    from qkdpy.utils import random_bit_string

    print("[OK] qkdpy.utils helpers")
except Exception as e:
    print(f"[FAIL] qkdpy.utils helpers: {e}")

try:
    from qkdpy.config import (
        QKDConfig,
        SecurityConfig,
        SecurityMode,
    )

    print("[OK] qkdpy.config")
except Exception as e:
    print(f"[FAIL] qkdpy.config: {e}")

try:
    import numpy as np

    print(f"[OK] numpy {np.__version__}")
except Exception as e:
    print(f"[FAIL] numpy: {e}")

# =====================================================================
# 1. QUANTUM HASH
# =====================================================================
section("1. QUANTUM HASH")

qh = QuantumHash()

# 1a. SHA3-256 with empty input
subsection("1a. SHA3-256 empty input")
data_empty = b""
h_empty = qh.sha3_256_hash(data_empty)
print(f"  Input bytes       : {data_empty!r}")
print(f"  Output hash (hex) : {h_empty.hex()}")
print(f"  Hash length       : {len(h_empty)} bytes ({len(h_empty)*8} bits)")
assert len(h_empty) == 32, "SHA3-256 should be 32 bytes"

# 1b. SHA3-256 with small message
subsection("1b. SHA3-256 small message")
data_small = b"Hello, QKD World!"
h_small = qh.sha3_256_hash(data_small)
print(f"  Input bytes       : {data_small!r}")
print(f"  Output hash (hex) : {h_small.hex()}")
print(f"  Hash length       : {len(h_small)} bytes ({len(h_small)*8} bits)")

# 1c. SHA3-256 with large message
subsection("1c. SHA3-256 large message (100KB)")
data_large = os.urandom(102400)
h_large = qh.sha3_256_hash(data_large)
print(f"  Input bytes       : {len(data_large)} bytes")
print(f"  Output hash (hex) : {h_large.hex()}")
print(f"  Hash length       : {len(h_large)} bytes ({len(h_large)*8} bits)")

# 1d. SHAKE-256 with variable length
subsection("1d. SHAKE-256 extendable output")
data_shake = b"Quantum-resistant hashing"
for out_len in [16, 32, 64]:
    h_shake = qh.shake_256_hash(data_shake, out_len)
    print(f"  Input : {data_shake!r}")
    print(f"  Output length : {out_len} bytes")
    print(f"  Output (hex)  : {h_shake.hex()[:64]}...")

# 1e. quantum_hash (bit-level)
subsection("1e. quantum_hash (bit-level)")
test_bits = [1, 0, 1, 1, 0, 0, 1, 1] * 10
h_bits = qh.quantum_hash(test_bits)
print(f"  Input bits  : {len(test_bits)} bits")
print(f"  Output bits : {len(h_bits)} bits")
print(f"  First 16    : {h_bits[:16]}")

# 1f. Merkle tree
subsection("1f. Merkle tree hash")
leaves = [
    [1, 0, 1, 1, 0, 0, 1, 1],
    [0, 1, 1, 0, 1, 0, 0, 1],
    [1, 1, 1, 1, 0, 0, 0, 0],
    [0, 0, 0, 0, 1, 1, 1, 1],
]
root = qh.merkle_tree_hash(leaves)
print(f"  Number of leaves : {len(leaves)}")
print(f"  Root hash bits   : {len(root)} bits")
print(f"  Root hash (first 16) : {root[:16]}")

# 1g. Hash chain
subsection("1g. Hash chain")
seed = [1, 0, 0, 1, 1, 0, 1, 0]
chain = qh.hash_chain(seed, length=5)
print(f"  Seed bits      : {seed}")
print(f"  Chain length   : {len(chain)}")
for i, c in enumerate(chain):
    print(f"    chain[{i}]     : {c[:8]}... ({len(c)} bits)")


# =====================================================================
# 2. QUANTUM COMMITMENT
# =====================================================================
section("2. QUANTUM COMMITMENT")

qc = QuantumCommitment()

subsection("2a. Commit and open")
value = "TopSecretData:QKD-2024-SESSION-42"
commit_id, opening_key = qc.commit(value)
print(f"  Value committed    : {value!r}")
print(f"  Commitment ID      : {commit_id}")
print(f"  Opening key (first 16) : {opening_key[:16]}...")

# Open successfully
opened = qc.open_commitment(commit_id, opening_key)
print(f"  Open success       : {opened is not None}")
print(f"  Revealed value     : {opened['value'] if opened else 'FAILED'}")
print(f"  Commitment hash    : {opened['commitment'][:32] if opened else 'N/A'}...")

# Open with wrong key
subsection("2b. Open with wrong key")
wrong_key = "deadbeef" + opening_key[8:]
opened_wrong = qc.open_commitment(commit_id, wrong_key)
print(f"  Opening key (first 8) : {wrong_key[:8]}...")
print(f"  Open success (expect False) : {opened_wrong is not None}")

# Verify commitment
subsection("2c. verify_commitment")
commit_info = qc.commitments.get(commit_id, {})
verify_ok = qc.verify_commitment(
    commit_id, value, commit_info.get("salt", ""), opening_key
)
print(f"  Verified correctly : {verify_ok}")

verify_bad = qc.verify_commitment(
    commit_id, "wrong_value", commit_info.get("salt", ""), opening_key
)
print(f"  Verify with wrong value : {verify_bad}")

# Get commitment info (redacted)
subsection("2d. get_commitment_info (redacted)")
info = qc.get_commitment_info(commit_id)
if info:
    print(f"  Keys present       : {list(info.keys())}")
    print(f"  'value' in info    : {'value' in info}")
    print(f"  'opening_key' in info : {'opening_key' in info}")


# =====================================================================
# 3. QUANTUM ZERO KNOWLEDGE
# =====================================================================
section("3. QUANTUM ZERO KNOWLEDGE")

zk = QuantumZeroKnowledge()

subsection("3a. Schnorr proof")
# Use a small modulus for faster computation; the real default is 2**255 - 19
secret = 42
modulus = 2**127 - 1  # Mersenne prime, smaller for speed
generator = 5
public = pow(generator, secret, modulus)
print(f"  Secret             : {secret}")
print(f"  Generator          : {generator}")
print(f"  Modulus            : {modulus}")
print(f"  Public (g^s mod p) : {public}")

challenge, response = zk.schnorr_proof(secret, public, generator, modulus)
print(f"  Challenge          : {challenge}")
print(f"  Response           : {response}")
print(
    f"  Proof size (challenge+response bytes) : {challenge.bit_length() // 8 + response.bit_length() // 8}"
)

valid = zk.verify_schnorr_proof(public, challenge, response, generator, modulus)
print(f"  Verification       : {valid}")

# Test with wrong public key
subsection("3b. Schnorr proof — rejection test")
wrong_public = public + 1  # wrong key
valid_wrong = zk.verify_schnorr_proof(
    wrong_public, challenge, response, generator, modulus
)
print(f"  Wrong public verify (expect False) : {valid_wrong}")

# Hash-based commitment ZK
subsection("3c. Hash-based commitment (ZK)")
zk_value = "zkp_witness_value_42"
zk_commit, decommit_path = zk.hash_based_commitment(zk_value)
print(f"  Value              : {zk_value!r}")
print(f"  Commitment (hex)   : {zk_commit}")
print(f"  Decommit path      : {decommit_path!r}")

zk_verify_ok = zk.verify_hash_commitment(zk_commit, zk_value, decommit_path)
print(f"  Verification       : {zk_verify_ok}")

zk_verify_bad = zk.verify_hash_commitment(zk_commit, "wrong_value", decommit_path)
print(f"  Verify wrong value : {zk_verify_bad}")


# =====================================================================
# 4. AUTHENTICATION / QUANTUMAUTH
# =====================================================================
section("4. AUTHENTICATION (QuantumAuth)")

from qkdpy.utils import random_bit_string

# Generate a 256-bit key as list[int]
auth_key = random_bit_string(256)
auth_msg = "Alice sends 42 QKD photons to Bob"

subsection("4a. Generate and verify MAC")
mac = QuantumAuth.generate_mac(auth_msg, auth_key)
print(f"  Message            : {auth_msg!r}")
print(f"  Key bits (first 16): {auth_key[:16]}")
print(f"  Key length         : {len(auth_key)} bits")
print(f"  MAC (hex)          : {mac}")
print(f"  MAC length         : {len(mac)} hex chars")

mac_valid = QuantumAuth.verify_mac(auth_msg, mac, auth_key)
print(f"  MAC valid          : {mac_valid}")

# Tampered message
subsection("4b. MAC verification — tampered message")
tampered_msg = "Alice sends 43 QKD photons to Bob"
mac_tampered = QuantumAuth.verify_mac(tampered_msg, mac, auth_key)
print(f"  Tampered msg       : {tampered_msg!r}")
print(f"  MAC valid (expect False) : {mac_tampered}")

# Authenticator
subsection("4c. Challenge-response authenticator")
auth_token = QuantumAuth.generate_authenticator(auth_key)
print(f"  Authenticator (hex): {auth_token}")
print(f"  Length             : {len(auth_token)} hex chars")

# Verify with known challenge
challenge_str = "a1b2c3d4e5f6g7h8"
auth2 = QuantumAuth.generate_authenticator(auth_key, challenge_str)
auth2_valid = QuantumAuth.verify_authenticator(auth_key, challenge_str, auth2)
print(f"  Challenge          : {challenge_str!r}")
print(f"  Authenticator      : {auth2}")
print(f"  Verify valid       : {auth2_valid}")

auth2_bad = QuantumAuth.verify_authenticator(auth_key, "wrong_challenge", auth2)
print(f"  Wrong challenge    : {auth2_bad}")

# Key fingerprint
subsection("4d. Key fingerprint")
fp = QuantumAuth.generate_key_fingerprint(auth_key)
fp_sha512 = QuantumAuth.generate_key_fingerprint(auth_key, "sha512")
print(f"  Fingerprint (SHA256): {fp}")
print(f"  Fingerprint (SHA512): {fp_sha512[:64]}...")

# Commitment via QuantumAuth
subsection("4e. QuantumAuth commitment")
comm_result = QuantumAuth.generate_commitment("bid_value_1000", auth_key)
print(f"  Commitment dict    : {comm_result}")
comm_verify = QuantumAuth.verify_commitment(
    "bid_value_1000", comm_result["commitment"], auth_key, comm_result["nonce"]
)
print(f"  Verify commitment  : {comm_verify}")
comm_verify_bad = QuantumAuth.verify_commitment(
    "bid_value_9999", comm_result["commitment"], auth_key, comm_result["nonce"]
)
print(f"  Verify wrong value : {comm_verify_bad}")


# =====================================================================
# 5. ENCRYPTION (OneTimePad)
# =====================================================================
section("5. ENCRYPTION (OneTimePad)")

otp_enc = OneTimePad()
plaintext = "QKD is information-theoretically secure when the key is truly random and never reused."
# Need enough key bits: 8 bits per character
plaintext_bits = OneTimePad._text_to_bits(plaintext)
key_bits = random_bit_string(len(plaintext_bits))

subsection("5a. Encrypt")
ciphertext, remaining_key = otp_enc.encrypt(plaintext, key_bits)
print(f"  Plaintext          : {plaintext!r}")
print(f"  Plaintext chars    : {len(plaintext)}")
print(f"  Plaintext bits     : {len(plaintext_bits)}")
print(f"  Key bits used      : {len(key_bits[:len(plaintext_bits)])}")
print(f"  Ciphertext bits    : {len(ciphertext)}")
print(f"  Ciphertext (first 32): {ciphertext[:32]}")
print(f"  Remaining key bits : {len(remaining_key)}")

# Manually decrypt with XOR to validate
message_bits_dec = [
    (c + k) % 2 for c, k in zip(ciphertext, key_bits[: len(plaintext_bits)])
]
decrypted_text = OneTimePadDecrypt._bits_to_text(message_bits_dec)
decrypt_result = decrypted_text
print(f"  Decrypted via XOR  : {decrypt_result}")
print(f"  Roundtrip match    : {decrypt_result == plaintext}")

# Show the XOR pattern visually
print("\n  XOR demonstration (first 3 chars):")
for i, c in enumerate(plaintext[:3]):
    m_bits = OneTimePad._text_to_bits(c)
    k_bits_slice = key_bits[i * 8 : (i + 1) * 8]
    c_bits = ciphertext[i * 8 : (i + 1) * 8]
    print(f"    '{c}' -> bits={m_bits}, key={k_bits_slice}, cipher={c_bits}")


# =====================================================================
# 6. DECRYPTION (OneTimePadDecrypt)
# =====================================================================
section("6. DECRYPTION (OneTimePadDecrypt)")

otp_dec = OneTimePadDecrypt()

subsection("6a. Decrypt ciphertext")
# Reuse the ciphertext from encryption test
decrypted = otp_dec.decrypt(ciphertext, key_bits)
print(f"  Ciphertext bits    : {len(ciphertext)}")
print(f"  Key bits available : {len(key_bits)}")
print(f"  Decrypted text     : {decrypted!r}")
print(f"  Roundtrip match    : {decrypted == plaintext}")

subsection("6b. Decrypt with wrong key")
wrong_key_bits = [1 - b for b in key_bits[: len(ciphertext)]]  # flip all bits
decrypted_wrong = otp_dec.decrypt(ciphertext, wrong_key_bits)
print(f"  Wrong key len      : {len(wrong_key_bits)}")
print(f"  Decrypted (garbled): {decrypted_wrong!r}")
print(f"  Match original     : {decrypted_wrong == plaintext}")

subsection("6c. Key too short error")
try:
    short_key = [0, 1, 0, 1]
    otp_dec.decrypt(ciphertext, short_key)
    print("  ERROR: Should have raised ValueError")
except ValueError as e:
    print(f"  Correctly rejected : {e}")


# =====================================================================
# 7. KEY EXCHANGE (QuantumKeyExchange)
# =====================================================================
section("7. KEY EXCHANGE")

channel = QuantumChannel(distance=1.0, loss_coefficient=0.2)
kex = QuantumKeyExchange(channel)

subsection("7a. Initiate key exchange")
session_id = kex.initiate_key_exchange("Alice", "Bob", key_length=128, protocol="BB84")
print(f"  Session ID         : {session_id}")

if session_id:
    subsection("7b. Execute key exchange")
    success = kex.execute_key_exchange(session_id)
    print(f"  Exchange success   : {success}")

    shared_key = kex.get_shared_key(session_id)
    print(f"  Shared key length  : {len(shared_key) if shared_key else 0} bits")
    print(f"  Shared key (first 32): {shared_key[:32] if shared_key else 'N/A'}")

    # Exchange statistics
    stats = kex.get_exchange_statistics()
    print(f"  Exchange stats     : {stats}")

    # Session info
    sess_info = kex.get_session_info(session_id)
    if sess_info:
        print(f"  Session info keys  : {list(sess_info.keys())}")
        print(f"  Status             : {sess_info.get('status')}")
        print(f"  QBER               : {sess_info.get('qber')}")

    # Verify key exchange
    subsection("7c. Verify key exchange (authenticate)")
    verify_token = kex.verify_key_exchange(session_id, "Alice")
    print(f"  Verification token : {verify_token is not None}")

    # Key rotation
    subsection("7d. Key rotation")
    rotated = kex.rotate_key(session_id, new_key_length=256)
    print(f"  Rotation success   : {rotated}")

    if rotated:
        rotated_key = kex.get_shared_key(session_id)
        print(f"  Rotated key length : {len(rotated_key) if rotated_key else 0} bits")
        print(
            f"  Rotated key differs: {rotated_key != shared_key if (rotated_key and shared_key) else 'N/A'}"
        )

else:
    print("  SKIP: Key exchange session could not be created")


# =====================================================================
# 8. QUANTUM RNG
# =====================================================================
section("8. QUANTUM RNG")

qkd_channel = QuantumChannel(distance=1.0)
qrng = QuantumRandomNumberGenerator(channel=qkd_channel)

subsection("8a. Generate random bytes (request 1024)")
random_bytes = qrng.generate_random_bytes(1024)
print("  Requested bytes    : 1024")
print(f"  Received bytes     : {len(random_bytes)}  (XOR extractor halves raw bits)")
print(f"  First 16 bytes (hex): {random_bytes[:16].hex()}")
print(f"  Last 16 bytes (hex) : {random_bytes[-16:].hex()}")
print(f"  Total bits gen.    : {qrng.bits_generated}")

# Frequency test: count zeros and ones
all_bits_from_bytes = []
for byte in random_bytes:
    for i in range(8):
        all_bits_from_bytes.append((byte >> (7 - i)) & 1)

ones = sum(all_bits_from_bytes)
zeros = len(all_bits_from_bytes) - ones
total = len(all_bits_from_bytes)

print(f"\n  Frequency test on {total} bits:")
print(f"    Ones  count      : {ones}")
print(f"    Zeros count      : {zeros}")
print(f"    Ratio (ones/total): {ones/total:.6f}")
print("    Expected ~=       : 0.5")

# Chi-square test for uniform distribution
expected = total / 2
chi_sq = ((ones - expected) ** 2 / expected) + ((zeros - expected) ** 2 / expected)
print(f"    Chi-square stat   : {chi_sq:.4f}")
print("    Chi-square crit   : 3.841 (p=0.05, df=1)")
print(f"    Passes test       : {chi_sq < 3.841}")

# Generate random int
subsection("8b. generate_random_int")
rand_vals = [qrng.generate_random_int(0, 255) for _ in range(20)]
print(f"  20 random ints (0-255): {rand_vals}")
print(f"  Min = {min(rand_vals)}, Max = {max(rand_vals)}")

# Generate random string
subsection("8c. generate_random_string")
rand_str = qrng.generate_random_string(32, charset="alphanumeric")
print(f"  Alphanumeric (32)  : {rand_str}")
rand_hex = qrng.generate_random_string(32, charset="hex")
print(f"  Hex (32)           : {rand_hex}")

# Calibrate
subsection("8d. Calibration and stats")
cal_ok = qrng.calibrate()
print(f"  Calibration        : {cal_ok}")
rng_stats = qrng.get_statistics()
print(f"  RNG stats          : {json.dumps(rng_stats, indent=2)}")


# =====================================================================
# 9. ENHANCED SECURITY
# =====================================================================
section("9. ENHANCED SECURITY")

# 9a. QuantumAuthentication (MAC)
subsection("9a. QuantumAuthentication MAC")
qs_key = random_bit_string(256)
qs_msg = b"Enhanced security test message"
qs_mac = QuantumAuthentication.generate_message_authentication_code(qs_key, qs_msg)
print(f"  MAC (hex)          : {qs_mac}")
print(f"  MAC length         : {len(qs_mac)} hex chars")

qs_verify = QuantumAuthentication.verify_message_authentication_code(
    qs_key, qs_msg, qs_mac
)
print(f"  MAC verify         : {qs_verify}")

qs_verify_bad = QuantumAuthentication.verify_message_authentication_code(
    qs_key, b"tampered", qs_mac
)
print(f"  MAC verify tampered: {qs_verify_bad}")

# 9b. QuantumKeyValidation
subsection("9b. QuantumKeyValidation — statistical tests")
test_key = random_bit_string(1024)
stats_result = QuantumKeyValidation.statistical_randomness_test(test_key)
print(f"  Key length              : {stats_result['key_length']}")
print(f"  Frequency test p-value  : {stats_result['frequency_test_p_value']:.6f}")
print(f"  Runs test p-value       : {stats_result['runs_test_p_value']:.6f}")
print(f"  Longest run length      : {stats_result['longest_run_length']}")
print(f"  Ones proportion         : {stats_result['ones_proportion']:.6f}")
print(f"  Block frequency stat    : {stats_result['block_frequency_stat']}")

# Entropy test
entropy = QuantumKeyValidation.entropy_test(test_key)
print(f"\n  Entropy (0-1)        : {entropy:.6f}")

# Correlation test
corr = QuantumKeyValidation.correlation_test(test_key, lag=1)
print(f"  Correlation (lag=1)  : {corr:.6f}")

# 9c. QuantumSideChannelProtection
subsection("9c. Side-channel protection")
key_a = random_bit_string(256)
key_b = key_a.copy()  # same
key_c = random_bit_string(256)  # different

cmp_same = QuantumSideChannelProtection.constant_time_compare(key_a, key_b)
cmp_diff = QuantumSideChannelProtection.constant_time_compare(key_a, key_c)
print(f"  constant_time_compare same  : {cmp_same}")
print(f"  constant_time_compare diff  : {cmp_diff}")

# Key splitting
subsection("9d. Key splitting (secret sharing)")
split_parts = QuantumSideChannelProtection.secure_key_splitting(key_a, num_parts=5)
print(f"  Original key length : {len(key_a)} bits")
print(f"  Number of parts     : {len(split_parts)}")
print(f"  Part lengths        : {[len(p) for p in split_parts]}")

reconstructed = QuantumSideChannelProtection.reconstruct_key(split_parts)
print(f"  Reconstructed match : {reconstructed == key_a}")


# =====================================================================
# 10. HSM INTERFACE
# =====================================================================
section("10. HSM INTERFACE")

try:
    hsm = get_hsm(HSMProvider.SOFTWARE, config={"mode": "testing"})
    print(f"  HSM available      : {hsm.is_available()}")
    print(f"  HSM type           : {type(hsm).__name__}")

    subsection("10a. Generate key")
    key_handle = hsm.generate_key("test_key_001", key_length=256)
    print(f"  Key ID             : {key_handle.key_id}")
    print(f"  Key type           : {key_handle.key_type}")
    print(f"  Created at         : {key_handle.created_at}")
    print(f"  Expires at         : {key_handle.expires_at}")
    print(f"  Is expired         : {key_handle.is_expired()}")

    subsection("10b. Import key")
    imported_material = os.urandom(32)
    import_handle = hsm.import_key(
        "imported_key_001", imported_material, metadata={"source": "test"}
    )
    print(f"  Imported key ID    : {import_handle.key_id}")
    print(f"  Metadata           : {import_handle.metadata}")

    subsection("10c. Encrypt / Decrypt")
    plaintext_data = b"SECRET: QKD session key material for AES-256-GCM encryption"
    encrypted = hsm.encrypt("test_key_001", plaintext_data)
    print(f"  Plaintext bytes    : {len(plaintext_data)}")
    print(f"  Ciphertext bytes   : {len(encrypted)}")
    print("  Ciphertext format  : nonce(12) || ct+tag")
    print(f"  Ciphertext hex     : {encrypted[:32].hex()}...")

    decrypted = hsm.decrypt("test_key_001", encrypted)
    print(f"  Decrypted bytes    : {len(decrypted)}")
    print(f"  Decrypted matches  : {decrypted == plaintext_data}")

    subsection("10d. Wrap / Unwrap key")
    wrapped = hsm.wrap_key("test_key_001", imported_material)
    print(f"  Wrapped key bytes  : {len(wrapped)}")
    unwrap_handle = hsm.unwrap_key("test_key_001", wrapped, "unwrapped_key_001")
    print(f"  Unwrapped key ID   : {unwrap_handle.key_id}")

    subsection("10e. List and delete keys")
    all_keys = hsm.list_keys()
    print(f"  Keys in HSM        : {len(all_keys)}")
    for k in all_keys:
        print(f"    - {k.key_id} ({k.key_type})")

    del_ok = hsm.delete_key("imported_key_001")
    print(f"  Delete imported     : {del_ok}")
    print(f"  Keys after delete   : {len(hsm.list_keys())}")

    hsm.close()
    print(f"  HSM closed         : {not hsm.is_available()}")

except Exception as e:
    print(f"  HSM Error: {type(e).__name__}: {e}")


# =====================================================================
# 11. COMPLIANCE
# =====================================================================
section("11. COMPLIANCE")

subsection("11a. Create ComplianceChecker with multiple standards")
# Use a custom config that passes all enterprise checks
from qkdpy.config import (
    EnterpriseConfig,
    LoggingConfig,
    QKDConfig,
    SecurityConfig,
)

test_config = QKDConfig(
    logging=LoggingConfig(redact_secrets=True, audit_enabled=True),
    security=SecurityConfig(
        mode=SecurityMode.PRODUCTION,
        min_key_length=128,
        require_authentication=True,
        enable_key_rotation=True,
        key_rotation_interval_seconds=1800,  # < 3600, passes ETSI check
        enable_audit_logging=True,
        max_qber_threshold=0.11,
    ),
    enterprise=EnterpriseConfig(enable_hsm=True, product_tier="premium"),
)

standards_list = [
    ComplianceStandard.NIST_SP_800_57,
    ComplianceStandard.FIPS_140_2,
    ComplianceStandard.ETSI_GS_QKD_014,
    ComplianceStandard.ISO_27001,
]

checker = ComplianceChecker(standards=standards_list, config=test_config)
print(f"  Standards checked  : {[s.value for s in standards_list]}")

report = checker.check_compliance()
print(f"\n  Report ID          : {report.report_id}")
print(f"  Generated at       : {report.generated_at}")
print(f"  Total checks       : {report.total_checks}")
print(f"  Passed checks      : {report.passed_checks}")
print(f"  Failed checks      : {report.failed_checks}")
print(f"  Overall compliant  : {report.overall_compliant}")

# Per-standard breakdown
from collections import defaultdict

by_standard = defaultdict(list)
for c in report.checks:
    by_standard[c.standard.value].append(c)

for std_name, std_checks in sorted(by_standard.items()):
    n_pass = sum(1 for c in std_checks if c.passed)
    n_fail = len(std_checks) - n_pass
    print(
        f"    {std_name}: {n_pass}/{len(std_checks)} passed ({n_pass/len(std_checks)*100:.0f}%)"
    )

# Detailed failures
if report.failed_checks > 0:
    subsection("11b. Failed check details")
    for c in report.get_failed_checks():
        print(f"  - [{c.check_id}] {c.requirement}: {c.severity}")
        print(f"    {c.description}")
        if c.details:
            print(f"    Details: {c.details}")
        if c.recommendation:
            print(f"    Rec: {c.recommendation}")

# Markdown export
subsection("11c. Export as Markdown (first 500 chars)")
md = report.export_markdown()
print(f"  Markdown length    : {len(md)} chars")
print(md[:500])
print("  ...")

# HTML export
subsection("11d. Export as HTML (first 500 chars)")
try:
    html = report.export_html()
    print(f"  HTML length        : {len(html)} chars")
    print(html[:500])
    print("  ...")
except Exception as e:
    print(f"  HTML export failed : {e}")

# Compliance rate per standard
subsection("11e. Summary dict")
summary = report.get_summary()
print(f"  Summary            : {json.dumps(summary, indent=2)}")


# =====================================================================
# 12. AUDIT
# =====================================================================
section("12. AUDIT")

audit = AuditLogger(enable_chain_verification=True)

subsection("12a. Log various events")

e1 = audit.log_event(
    AuditEventType.KEY_GENERATED,
    "Generated AES-256 key for session",
    actor="alice@qkdpy.dev",
    resource="key:session-001",
    result="success",
    details={"key_length": 256, "algorithm": "AES-256-GCM"},
)
print(f"  Event 1: {e1.event_id} — {e1.event_type.value} — {e1.result}")

e2 = audit.log_event(
    AuditEventType.KEY_DISTRIBUTED,
    "Distributed key to Bob",
    actor="alice@qkdpy.dev",
    resource="key:session-001",
    result="success",
    details={"recipient": "bob@qkdpy.dev", "method": "BB84"},
)
print(f"  Event 2: {e2.event_id} — {e2.event_type.value} — {e2.result}")

e3 = audit.log_event(
    AuditEventType.PROTOCOL_EXECUTED,
    "Executed BB84 protocol",
    actor="system",
    resource="protocol:BB84:session-001",
    result="success",
    details={"qber": 0.035, "key_rate": 0.85},
)
print(f"  Event 3: {e3.event_id} — {e3.event_type.value} — {e3.result}")

e4 = audit.log_event(
    AuditEventType.ACCESS_DENIED,
    "Unauthorized access attempt",
    actor="unknown@malicious.com",
    resource="key:session-001",
    result="denied",
    details={"ip_address": "192.168.1.100", "reason": "invalid_auth_token"},
)
print(f"  Event 4: {e4.event_id} — {e4.event_type.value} — {e4.result}")

e5 = audit.log_event(
    AuditEventType.KEY_ROTATED,
    "Rotated key for session",
    actor="system",
    resource="key:session-001",
    result="success",
    details={"old_key_id": "key-001-v1", "new_key_id": "key-001-v2"},
)
print(f"  Event 5: {e5.event_id} — {e5.event_type.value} — {e5.result}")

subsection("12b. Query by event type")
key_events = audit.get_events(event_type=AuditEventType.KEY_GENERATED)
print(f"  KEY_GENERATED events : {len(key_events)}")
for ev in key_events:
    print(f"    {ev.event_id} @ {ev.timestamp}")

security_events = audit.get_events(event_type=AuditEventType.ACCESS_DENIED)
print(f"  ACCESS_DENIED events : {len(security_events)}")

subsection("12c. Query by time range")
from datetime import (
    UTC,
    datetime,
    timedelta,
)

recent = audit.get_events(since=datetime.now(UTC) - timedelta(hours=1))
print(f"  Events in last hour : {len(recent)}")

future = audit.get_events(until=datetime.now(UTC) + timedelta(hours=1))
print(f"  Events before +1hr  : {len(future)}")

subsection("12d. Stats")
audit_stats = audit.get_statistics()
print(f"  Total events        : {audit_stats['total_events']}")
print(f"  Chain valid         : {audit_stats['chain_valid']}")
print(f"  By type             : {json.dumps(audit_stats['events_by_type'], indent=2)}")

subsection("12e. Chain integrity")
chain_valid, chain_errors = audit.verify_chain_integrity()
print(f"  Chain valid         : {chain_valid}")
print(f"  Chain errors        : {chain_errors}")

subsection("12f. Tamper evidence test — simulate tampering")
# Export before tampering
export_json = audit.export_events("json")
print(f"  Export JSON length  : {len(export_json)} chars")

# Modify the last event in memory to simulate tampering
if audit._events:
    original_hash = audit._events[-1].previous_hash
    # Modify the event's details
    audit._events[-1].details["tampered"] = True
    new_hash = audit._events[-1].compute_hash()
    # The previous_hash reference is now wrong

    chain_valid2, chain_errors2 = audit.verify_chain_integrity()
    print(f"  Chain valid after tamper : {chain_valid2}")
    print(f"  Chain errors             : {chain_errors2}")
    if chain_errors2:
        print(f"  TAMPER DETECTED at index {audit._events.index(audit._events[-1])}")

# CEF export
subsection("12g. CEF export sample")
cef_export = audit.export_events("cef")
print(f"  CEF lines           : {len(cef_export.split(chr(10)))}")
for line in cef_export.split(chr(10))[:2]:
    print(f"    {line}")

# LEEF export
leef_export = audit.export_events("leef")
print(f"\n  LEEF lines          : {len(leef_export.split(chr(10)))}")
for line in leef_export.split(chr(10))[:2]:
    print(f"    {line}")


# =====================================================================
# 13. LICENSING
# =====================================================================
section("13. LICENSING")

subsection("13a. FREE tier")
set_active_tier(ProductTier.FREE)
print(f"  Active tier        : {get_active_tier().value}")

for f in Feature:
    avail = feature_available(f)
    print(f"    {f.value:35s} : {'AVAILABLE' if avail else 'LOCKED'}")

subsection("13b. ENTERPRISE tier")
set_active_tier(ProductTier.ENTERPRISE)
print(f"  Active tier        : {get_active_tier().value}")
for f in Feature:
    avail = feature_available(f)
    print(f"    {f.value:35s} : {'AVAILABLE' if avail else 'LOCKED'}")

subsection("13c. PREMIUM tier")
set_active_tier(ProductTier.PREMIUM)
print(f"  Active tier        : {get_active_tier().value}")
for f in Feature:
    avail = feature_available(f)
    print(f"    {f.value:35s} : {'AVAILABLE' if avail else 'LOCKED'}")

# require_feature decorator
subsection("13d. require_feature decorator test")


@require_feature(Feature.QUANTUM_SAFE_MIGRATION)
def quantum_safe_migration():
    return "Quantum safe migration executed"


@require_feature(Feature.COMPLIANCE_REPORTING)
def compliance_reporting():
    return "Compliance reporting executed"


# Should work with PREMIUM
try:
    result = quantum_safe_migration()
    print(f"  QUANTUM_SAFE_MIGRATION @ PREMIUM : {result}")
except Exception as e:
    print(f"  QUANTUM_SAFE_MIGRATION @ PREMIUM : FAILED: {e}")

# Switch to FREE and try again
set_active_tier(ProductTier.FREE)
try:
    result = compliance_reporting()
    print(f"  COMPLIANCE_REPORTING @ FREE     : {result}")
except Exception as e:
    print(f"  COMPLIANCE_REPORTING @ FREE     : LOCKED: {e}")

# Switch back to PREMIUM for remaining tests
set_active_tier(ProductTier.PREMIUM)


# =====================================================================
# 14. QUANTUM SAFE
# =====================================================================
section("14. QUANTUM SAFE")

subsection("14a. classic_enterprise_profile")
profile = classic_enterprise_profile()
print(f"  Scanned at         : {profile.scanned_at}")
print(f"  System description : {profile.system_description}")
print(f"  Total assets       : {profile.total_assets}")
print(f"  Vulnerable count   : {profile.vulnerable_count}")
print(f"  Risk score         : {profile.risk_score:.4f}")

print("\n  Asset breakdown:")
for asset in profile.assets:
    print(
        f"    {asset.name:25s} | {asset.algorithm_type.value:13s} | {asset.key_size_bits:4d} bits | {asset.resistance.value:15s}"
    )

summary = profile.get_summary()
print(f"\n  Summary            : {json.dumps(summary, indent=2)}")

subsection("14b. Generate migration roadmap")
roadmap = generate_roadmap(profile)
print(f"  Generated at       : {roadmap.generated_at}")
print(f"  Target completion  : {roadmap.target_completion}")
print(f"  Total steps        : {len(roadmap.steps)}")
print(f"  Risk score         : {roadmap.inventory.risk_score:.4f}")
print(f"  Vulnerable assets  : {roadmap.inventory.vulnerable_count}")

print("\n  Roadmap phases:")
for step in roadmap.steps:
    print(f"    [{step.phase.value:7s}] P{step.priority} | {step.title}")
    print(f"           Effort: {step.estimated_effort}")
    if step.depends_on:
        print(f"           Depends on: {', '.join(step.depends_on)}")

roadmap_summary = roadmap.get_summary()
print(f"\n  Roadmap summary    : {json.dumps(roadmap_summary, indent=2)}")

subsection("14c. QuantumSafeAssessment")
assessment = QuantumSafeAssessment(inventory=profile, roadmap=roadmap)
assessment_dict = assessment.to_dict()
print(f"  Assessed at        : {assessment_dict['assessed_at']}")
print(f"  Inventory summary  : {json.dumps(assessment_dict['inventory'], indent=2)}")
print(f"  Roadmap summary    : {json.dumps(assessment_dict['roadmap'], indent=2)}")
print(f"  Recommendations    : ({len(assessment_dict['recommendations'])} total)")
for i, rec in enumerate(assessment_dict["recommendations"], 1):
    print(f"    {i}. {rec}")

# Print first 5 recommendations
print("\n  First 5 recommendations:")
recs = assessment._recommendations()
for i, rec in enumerate(recs[:5], 1):
    print(f"    {i}. {rec}")


# =====================================================================
# 15. QUANTUM AUTHENTICATOR (quantum_auth module)
# =====================================================================
section("15. QUANTUM AUTHENTICATOR")

qauth_channel = QuantumChannel(distance=1.0)
qa = QuantumAuthenticator(qauth_channel)

subsection("15a. Register party + authenticate")
reg_ok = qa.register_party("party_alice", shared_key_length=128)
print(f"  Register Alice     : {reg_ok}")

if reg_ok:
    token_id = qa.authenticate_party("party_alice")
    print(f"  Auth token ID      : {token_id}")

    if token_id:
        # Need the original challenge to verify
        token_info = qa.auth_tokens.get(token_id, {})
        challenge = token_info.get("challenge", "")
        verify_ok = qa.verify_authentication("party_alice", token_id, challenge)
        print(f"  Verify auth        : {verify_ok}")

        subsection("15b. Quantum signature")
        sig_result = qa.generate_quantum_signature(
            "party_alice", "QKD protocol message v2.0"
        )
        if sig_result:
            signature, sig_ts = sig_result
            print(f"  Signature (hex)    : {signature[:48]}...")
            print(f"  Signature ts       : {sig_ts}")

            sig_verify = qa.verify_quantum_signature(
                "party_alice", "QKD protocol message v2.0", signature, sig_ts
            )
            print(f"  Signature verify   : {sig_verify}")

            sig_verify_bad = qa.verify_quantum_signature(
                "party_alice", "TAMPERED_MESSAGE", signature, sig_ts
            )
            print(f"  Sig verify tampered: {sig_verify_bad}")

    # Party info
    subsection("15c. Party info")
    info = qa.get_party_info("party_alice")
    print(f"  Party info keys    : {list(info.keys()) if info else 'N/A'}")
    print(f"  'shared_key' present: {'shared_key' in info if info else 'N/A'}")

    # Remove party
    rem_ok = qa.remove_party("party_alice")
    print(f"  Remove party       : {rem_ok}")
    print(f"  Party count        : {len(qa.authenticated_parties)}")
else:
    print("  SKIP: Party registration failed (BB84 may need more qubits)")


# =====================================================================
# SUMMARY
# =====================================================================
section("TEST SUMMARY")

print("""
Tests executed:
  1.  QuantumHash (SHA3-256, SHAKE-256, Merkle tree, hash chain)
  2.  QuantumCommitment (commit, open, verify, info)
  3.  QuantumZeroKnowledge (Schnorr proof, hash-based ZK)
  4.  Authentication/QuantumAuth (MAC, authenticator, fingerprint, commitment)
  5.  Encryption (OneTimePad)
  6.  Decryption (OneTimePadDecrypt)
  7.  KeyExchange (initiate, execute, verify, rotate)
  8.  QuantumRNG (random bytes, frequency test, random int/string)
  9.  EnhancedSecurity (MAC, statistical tests, key splitting)
  10. HSM Interface (key gen, encrypt/decrypt, wrap/unwrap)
  11. Compliance (multi-standard, markdown, HTML export)
  12. Audit (log events, query, chain integrity, tamper detection)
  13. Licensing (FREE/ENTERPRISE/PREMIUM tiers, feature gating)
  14. QuantumSafe (profile, roadmap, assessment)
  15. QuantumAuthenticator (party registration, auth, signatures)
""")

print("Test script completed successfully.")
