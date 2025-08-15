"""Example demonstrating enhanced security features."""

import numpy as np

from qkdpy.crypto.enhanced_security import (
    QuantumAuthentication,
    QuantumKeyValidation,
    QuantumSideChannelProtection,
)


def enhanced_security_example():
    """Example of using enhanced security features."""
    print("Enhanced Security Features Example")
    print("==================================")

    # Generate a quantum key (simulated)
    key = [np.random.randint(0, 2) for _ in range(128)]
    print(f"Generated quantum key length: {len(key)} bits")
    print(f"First 20 bits: {key[:20]}")

    # Message authentication
    print("\\n1. Message Authentication:")
    message = b"This is a secret message that needs authentication."
    print(f"Message: {message}")

    # Generate MAC
    mac = QuantumAuthentication.generate_message_authentication_code(key, message)
    print(f"Generated MAC: {mac}")

    # Verify MAC
    is_valid = QuantumAuthentication.verify_message_authentication_code(
        key, message, mac
    )
    print(f"MAC verification: {'Valid' if is_valid else 'Invalid'}")

    # Test with tampered message
    tampered_message = b"This is a TAMPERED message that needs authentication."
    is_valid_tampered = QuantumAuthentication.verify_message_authentication_code(
        key, tampered_message, mac
    )
    print(
        f"MAC verification with tampered message: {'Valid' if is_valid_tampered else 'Invalid'}"
    )

    # Key validation
    print("\\n2. Key Validation:")
    stats = QuantumKeyValidation.statistical_randomness_test(key)
    print(f"Frequency test p-value: {stats['frequency_test_p_value']:.4f}")
    print(f"Runs test p-value: {stats['runs_test_p_value']:.4f}")
    print(f"Longest run length: {stats['longest_run_length']}")
    print(f"Ones proportion: {stats['ones_proportion']:.4f}")

    # Entropy test
    entropy = QuantumKeyValidation.entropy_test(key)
    print(f"Key entropy: {entropy:.4f} (max = 1.0)")

    # Correlation test
    correlation = QuantumKeyValidation.correlation_test(key)
    print(f"Key correlation: {correlation:.4f}")

    # Side-channel protection
    print("\\n3. Side-Channel Protection:")

    # Constant time comparison
    key1 = [1, 0, 1, 1, 0, 0, 1, 0]
    key2 = [1, 0, 1, 1, 0, 0, 1, 0]
    key3 = [1, 0, 1, 1, 0, 0, 1, 1]

    result1 = QuantumSideChannelProtection.constant_time_compare(key1, key2)
    result2 = QuantumSideChannelProtection.constant_time_compare(key1, key3)
    print(f"Key comparison (same): {'Match' if result1 else 'No match'}")
    print(f"Key comparison (different): {'Match' if result2 else 'No match'}")

    # Secure key splitting
    original_key = [1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1, 1]
    print(f"\\nOriginal key: {original_key}")

    # Split into 3 parts
    parts = QuantumSideChannelProtection.secure_key_splitting(original_key, 3)
    print(f"Key split into {len(parts)} parts:")
    for i, part in enumerate(parts):
        print(f"  Part {i+1}: {part}")

    # Reconstruct the key
    reconstructed = QuantumSideChannelProtection.reconstruct_key(parts)
    print(f"Reconstructed key: {reconstructed}")
    print(f"Reconstruction successful: {original_key == reconstructed}")


if __name__ == "__main__":
    enhanced_security_example()
