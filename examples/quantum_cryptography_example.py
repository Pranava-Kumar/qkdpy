"""Example of using quantum cryptography features."""

import numpy as np

from qkdpy.core import QuantumChannel
from qkdpy.crypto import (
    QuantumAuthenticator,
    QuantumKeyExchange,
    QuantumRandomNumberGenerator,
)


def quantum_cryptography_example():
    """Demonstrates the quantum cryptography functionalities."""
    print("Quantum Cryptography Example")
    print("============================")

    # Create a quantum channel
    channel = QuantumChannel(loss=0.1, noise_model="depolarizing", noise_level=0.05)

    # 1. Quantum Random Number Generator
    print("\n1. Quantum Random Number Generator")
    qrng = QuantumRandomNumberGenerator(channel)

    # Generate random bits
    random_bits = qrng.generate_random_bits(50)
    print(f"Random bits: {random_bits}")

    # Generate random bytes
    random_bytes = qrng.generate_random_bytes(10)
    print(f"Random bytes: {random_bytes.hex()}")

    # Generate random integer
    random_int = qrng.generate_random_int(1, 100)
    print(f"Random integer (1-100): {random_int}")

    # Generate random string
    random_string = qrng.generate_random_string(20, "alphanumeric")
    print(f"Random string: {random_string}")

    # Get statistics
    stats = qrng.get_statistics()
    print(f"Bits generated: {stats['bits_generated']}")
    print(f"Entropy level: {stats['entropy_level']:.4f}")

    # 2. Quantum Authenticator
    print("\n2. Quantum Authenticator")
    authenticator = QuantumAuthenticator(channel)

    # Register parties
    party_a = "Alice"
    party_b = "Bob"

    if authenticator.register_party(party_a, shared_key_length=128):
        print(f"Registered party: {party_a}")

    if authenticator.register_party(party_b, shared_key_length=128):
        print(f"Registered party: {party_b}")

    # Authenticate parties
    challenge = "random_challenge_string"
    token_a = authenticator.authenticate_party(party_a, challenge)
    token_b = authenticator.authenticate_party(party_b, challenge)

    if token_a:
        print(f"Authentication token for {party_a}: {token_a}")

    if token_b:
        print(f"Authentication token for {party_b}: {token_b}")

    # Verify authentication
    if token_a:
        is_valid = authenticator.verify_authentication(party_a, token_a, challenge)
        print(f"Authentication verification for {party_a}: {is_valid}")

    # Generate and verify digital signatures
    message = "This is a secure message"
    signature_result = authenticator.generate_quantum_signature(party_a, message)

    if signature_result:
        signature, timestamp = signature_result
        print(f"Digital signature for message: {signature[:32]}...")

        # Verify signature
        is_valid = authenticator.verify_quantum_signature(
            party_a, message, signature, timestamp
        )
        print(f"Signature verification: {is_valid}")

    # 3. Quantum Key Exchange
    print("\n3. Quantum Key Exchange")
    key_exchange = QuantumKeyExchange(channel)

    # Initiate key exchange
    session_id = key_exchange.initiate_key_exchange(
        party_a, party_b, key_length=128, protocol="BB84"
    )

    if session_id:
        print(f"Key exchange session initiated: {session_id}")

        # Execute key exchange
        success = key_exchange.execute_key_exchange(session_id)
        print(f"Key exchange execution: {'Success' if success else 'Failed'}")

        # Get shared key
        shared_key = key_exchange.get_shared_key(session_id)
        if shared_key:
            print(f"Shared key length: {len(shared_key)}")
            print(f"First 10 bits of shared key: {[int(bit) for bit in shared_key[:10]]}")

        # Verify key exchange
        auth_token = key_exchange.verify_key_exchange(session_id, party_a, challenge)
        if auth_token:
            print(f"Key exchange verification token: {auth_token}")

        # Get session info
        session_info = key_exchange.get_session_info(session_id)
        if session_info:
            print(f"Session status: {session_info['status']}")
            print(f"Protocol used: {session_info['protocol']}")

        # Get exchange statistics
        exchange_stats = key_exchange.get_exchange_statistics()
        print(f"Successful exchanges: {exchange_stats['successful_exchanges']}")
        print(f"Failed exchanges: {exchange_stats['failed_exchanges']}")


if __name__ == "__main__":
    quantum_cryptography_example()