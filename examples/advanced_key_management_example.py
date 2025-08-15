"""Example of using advanced key management features."""

import numpy as np

from qkdpy.core import QuantumChannel
from qkdpy.key_management import (
    AdvancedErrorCorrection,
    AdvancedPrivacyAmplification,
    QuantumKeyManager,
)


def advanced_key_management_example():
    """Demonstrates the advanced key management functionalities."""
    print("Advanced Key Management Example")
    print("===============================")

    # Create a quantum channel
    channel = QuantumChannel(loss=0.1, noise_model="depolarizing", noise_level=0.05)

    # 1. Quantum Key Manager
    print("\n1. Quantum Key Manager")
    key_manager = QuantumKeyManager(channel)

    # Generate keys for a session
    session_id = "secure_session_1"
    key_id1 = key_manager.generate_key(session_id, key_length=128, protocol="BB84")
    key_id2 = key_manager.generate_key(session_id, key_length=128, protocol="BB84")

    if key_id1 and key_id2:
        print(f"Generated key 1: {key_id1}")
        print(f"Generated key 2: {key_id2}")

        # Retrieve a key
        key = key_manager.get_key(key_id1)
        print(f"Retrieved key length: {len(key) if key else 0}")

        # Get session information
        session_keys = key_manager.get_session_keys(session_id)
        print(f"Keys in session: {len(session_keys)}")

        # Get statistics
        stats = key_manager.get_key_statistics()
        print(f"Total keys generated: {stats['total_keys_generated']}")
    else:
        print("Failed to generate keys")

    # 2. Advanced Error Correction
    print("\n2. Advanced Error Correction")
    alice_key = [int(x) for x in np.random.randint(0, 2, 100)]
    bob_key = alice_key.copy()

    # Introduce some errors
    for _ in range(5):
        error_pos = np.random.randint(0, 100)
        bob_key[error_pos] = 1 - bob_key[error_pos]

    print(f"Initial Alice key: {alice_key[:10]}...")
    print(f"Initial Bob key:   {bob_key[:10]}...")
    print(
        f"Initial error rate: {sum(a != b for a, b in zip(alice_key, bob_key, strict=False)) / len(alice_key):.4f}"
    )

    # Apply LDPC error correction
    corrected_alice, corrected_bob, success = (
        AdvancedErrorCorrection.low_density_parity_check(alice_key, bob_key)
    )
    print(f"LDPC correction success: {success}")
    print(f"Corrected Alice key: {corrected_alice[:10]}...")
    print(f"Corrected Bob key:   {corrected_bob[:10]}...")

    # 3. Advanced Privacy Amplification
    print("\n3. Advanced Privacy Amplification")
    long_key = [int(x) for x in np.random.randint(0, 2, 256)]
    print(f"Original key length: {len(long_key)}")

    # Apply different extraction methods
    xor_extracted = AdvancedPrivacyAmplification.randomness_extractor(
        long_key, 128, "xor"
    )
    print(f"XOR extracted key length: {len(xor_extracted)}")

    aes_extracted = AdvancedPrivacyAmplification.randomness_extractor(
        long_key, 128, "aes"
    )
    print(f"AES extracted key length: {len(aes_extracted)}")

    universal_extracted = AdvancedPrivacyAmplification.randomness_extractor(
        long_key, 128, "universal"
    )
    print(f"Universal extracted key length: {len(universal_extracted)}")

    # Apply strong extractor
    strong_extracted = AdvancedPrivacyAmplification.strong_extractor(
        long_key, 100, min_entropy=128
    )
    print(f"Strong extracted key length: {len(strong_extracted)}")


if __name__ == "__main__":
    advanced_key_management_example()
