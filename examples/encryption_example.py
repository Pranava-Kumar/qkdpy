"""Example of using quantum keys for encryption."""

from qkdpy import BB84, OneTimePad, OneTimePadDecrypt, QuantumChannel


def encryption_example():
    """Example of using a quantum key for encryption and decryption."""
    print("Quantum Encryption Example")
    print("=========================")

    # Create a quantum channel with some noise and loss
    channel = QuantumChannel(loss=0.1, noise_model="depolarizing", noise_level=0.05)

    # Create a BB84 protocol instance
    bb84 = BB84(channel, key_length=256)  # Generate a longer key for encryption

    # Execute the protocol
    results = bb84.execute()

    # Print the results
    print(f"Generated key length: {len(results['final_key'])}")
    print(f"QBER: {results['qber']:.4f}")
    print(f"Is secure: {results['is_secure']}")

    if not results["is_secure"]:
        print("Key is not secure. Aborting encryption example.")
        return

    # Get the final key
    key = results["final_key"]

    # Message to encrypt
    message = "This is a secret message encrypted with a quantum key!"

    print(f"\nOriginal message: {message}")

    # Encrypt the message
    try:
        ciphertext, remaining_key = OneTimePad.encrypt(message, key)
        print(f"Encrypted message: {ciphertext}")
        print(f"Remaining key length: {len(remaining_key)}")

        # Decrypt the message
        decrypted_message = OneTimePadDecrypt.decrypt(ciphertext, key)
        print(f"Decrypted message: {decrypted_message}")

        # Verify that the decrypted message matches the original
        if decrypted_message == message:
            print("\nEncryption and decryption successful!")
        else:
            print("\nError: Decrypted message does not match the original!")
    except ValueError as e:
        print(f"\nError during encryption/decryption: {e}")

    # Example with file encryption
    print("\nFile Encryption Example")
    print("======================")

    # Create a test file
    test_file = "test_file.txt"
    with open(test_file, "w") as f:
        f.write("This is a test file for quantum encryption.\n")
        f.write("It contains multiple lines of text.\n")
        f.write("The content will be encrypted using a quantum key.\n")

    print(f"Created test file: {test_file}")

    # Encrypt the file
    try:
        encrypted_file, _ = OneTimePad.encrypt_file(test_file, remaining_key)
        print(f"Encrypted file: {encrypted_file}")

        # Decrypt the file
        decrypted_file = OneTimePadDecrypt.decrypt_file(encrypted_file, remaining_key)
        print(f"Decrypted file: {decrypted_file}")

        # Verify that the decrypted file matches the original
        with open(test_file) as f1, open(decrypted_file) as f2:
            original_content = f1.read()
            decrypted_content = f2.read()

            if original_content == decrypted_content:
                print("\nFile encryption and decryption successful!")
            else:
                print("\nError: Decrypted file does not match the original!")
    except ValueError as e:
        print(f"\nError during file encryption/decryption: {e}")

    return key


if __name__ == "__main__":
    encryption_example()
