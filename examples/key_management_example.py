"""Example of using the key management features of QKDpy."""

import numpy as np

from qkdpy.key_management import ErrorCorrection, PrivacyAmplification


def key_management_example() -> None:
    """Demonstrates the key management functionalities of QKDpy."""
    print("QKDpy Key Management Example")
    print("============================")

    # 1. Error Correction
    print("\n1. Error Correction")
    alice_key = [int(x) for x in np.random.randint(0, 2, 100)]
    bob_key = alice_key.copy()
    # Introduce some errors
    for _ in range(5):
        error_pos = np.random.randint(0, 100)
        bob_key[error_pos] = 1 - bob_key[error_pos]

    print(f"Initial Alice key: {alice_key}")
    print(f"Initial Bob key:   {bob_key}")
    error_rate = ErrorCorrection.error_rate(alice_key, bob_key)
    print(f"Initial error rate: {error_rate:.4f}")

    alice_corrected, bob_corrected = ErrorCorrection.cascade(alice_key, bob_key)
    print(f"Corrected Alice key: {alice_corrected}")
    print(f"Corrected Bob key:   {bob_corrected}")
    final_error_rate = ErrorCorrection.error_rate(alice_corrected, bob_corrected)
    print(f"Final error rate: {final_error_rate:.4f}")

    # 2. Privacy Amplification
    print("\n2. Privacy Amplification")
    long_key = [int(x) for x in np.random.randint(0, 2, 256)]
    print(f"Original key length: {len(long_key)}")

    short_key = PrivacyAmplification.universal_hashing(long_key, output_length=128)
    print(f"Amplified key length: {len(short_key)}")
    print(f"Amplified key: {[int(bit) for bit in short_key]}")


if __name__ == "__main__":
    key_management_example()
