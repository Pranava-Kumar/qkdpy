"""Example of a full QKD scenario using QKDpy."""

from qkdpy.core import QuantumChannel
from qkdpy.crypto import OneTimePad, OneTimePadDecrypt, QuantumAuth
from qkdpy.protocols import BB84


def full_qkd_scenario() -> None:
    """Demonstrates a full QKD scenario from key generation to secure communication."""
    print("QKDpy Full Scenario Example")
    print("===========================")

    # 1. Establish a secure key using BB84
    print("\n1. Establishing a secure key with BB84...")
    channel = QuantumChannel(loss=0.1, noise_model="depolarizing", noise_level=0.05)
    bb84 = BB84(channel, key_length=256)
    results = bb84.execute()

    if not results["is_secure"]:
        print("QKD protocol failed to establish a secure key. Aborting.")
        return

    final_key = results["final_key"]
    print(f"Secure key established with length: {len(final_key)}")

    # 2. Encrypt and Decrypt a message
    print("\n2. Encrypting and decrypting a message...")
    message = "Hello, Quantum World!"
    print(f"Original message: {message}")

    ciphertext, key_after_encryption = OneTimePad.encrypt(message, final_key)
    print(f"Ciphertext: {[int(bit) for bit in ciphertext]}")

    decrypted_message = OneTimePadDecrypt.decrypt(ciphertext, final_key)
    print(f"Decrypted message: {decrypted_message}")

    assert message == decrypted_message
    print("Message successfully encrypted and decrypted.")

    # 3. Authenticate a message
    print("\n3. Authenticating a message...")
    auth_message = "This message is authentic."
    print(f"Message to authenticate: {auth_message}")

    mac = QuantumAuth.generate_mac(auth_message, key_after_encryption)
    print(f"Generated MAC: {mac}")

    is_valid = QuantumAuth.verify_mac(auth_message, mac, key_after_encryption)
    print(f"MAC verification result: {is_valid}")

    assert is_valid
    print("Message successfully authenticated.")


if __name__ == "__main__":
    full_qkd_scenario()
