"""
Educational Example: Quantum Key Distribution with QKDpy

This script demonstrates the basic concepts of Quantum Key Distribution
using the QKDpy library. It's designed for educational purposes to help
students understand how QKD works.
"""

import matplotlib.pyplot as plt
import numpy as np

# Import QKDpy modules
from qkdpy import BB84, E91, QuantumChannel, Qubit
from qkdpy.utils import BlochSphere


def demonstrate_bb84_concept():
    """
    Demonstrate the basic concept of the BB84 protocol.

    This function explains the BB84 protocol step by step and shows
    how it works in principle.
    """
    print("=" * 60)
    print("QUANTUM KEY DISTRIBUTION: BB84 PROTOCOL DEMONSTRATION")
    print("=" * 60)

    print("\n1. BASIC PRINCIPLE:")
    print("   - Alice sends qubits to Bob in random quantum states")
    print("   - Bob measures the qubits in random bases")
    print("   - Alice and Bob publicly compare their bases")
    print("   - They keep only the bits where they used the same basis")
    print("   - The remaining bits form their shared secret key")

    print("\n2. STEP-BY-STEP PROCESS:")

    # Step 1: Alice prepares random bits and bases
    alice_bits = [0, 1, 1, 0, 1, 0, 1, 1]
    alice_bases = [
        "Z",
        "X",
        "Z",
        "X",
        "X",
        "Z",
        "X",
        "Z",
    ]  # Z = computational, X = Hadamard

    print(f"\n   Alice's random bits:     {alice_bits}")
    print(f"   Alice's random bases:    {alice_bases}")

    # Step 2: Alice prepares qubits based on her bits and bases
    print("\n   Alice prepares qubits:")
    for _i, (bit, basis) in enumerate(zip(alice_bits, alice_bases, strict=False)):
        if basis == "Z":
            state = "|0⟩" if bit == 0 else "|1⟩"
        else:  # X basis
            state = "|+⟩" if bit == 0 else "|-⟩"
        print(f"     Bit {bit} in {basis} basis → {state}")

    # Step 3: Bob measures in random bases
    bob_bases = ["X", "Z", "Z", "X", "X", "Z", "Z", "X"]
    # For demonstration, let's assume perfect measurements
    # In reality, Bob would get probabilistic outcomes
    bob_results = [1, 1, 1, 0, 1, 0, 0, 1]

    print(f"\n   Bob's measurement bases: {bob_bases}")
    print(f"   Bob's measurement results: {bob_results}")

    # Step 4: Public comparison of bases
    print("\n   Public comparison of bases:")
    matching_indices = []
    for i, (a_basis, b_basis) in enumerate(zip(alice_bases, bob_bases, strict=False)):
        match = "✓" if a_basis == b_basis else "✗"
        print(f"     Position {i}: Alice {a_basis} vs Bob {b_basis} {match}")
        if a_basis == b_basis:
            matching_indices.append(i)

    # Step 5: Sifted key
    alice_sifted = [alice_bits[i] for i in matching_indices]
    bob_sifted = [bob_results[i] for i in matching_indices]

    print(f"\n   Sifted key (Alice): {alice_sifted}")
    print(f"   Sifted key (Bob):   {bob_sifted}")

    # Step 6: Check for eavesdropping (QBER)
    errors = sum(1 for a, b in zip(alice_sifted, bob_sifted, strict=False) if a != b)
    qber = errors / len(alice_sifted) if alice_sifted else 0

    print(f"\n   Errors in sifted key: {errors}/{len(alice_sifted)}")
    print(f"   Quantum Bit Error Rate (QBER): {qber:.2%}")

    if qber > 0.11:  # Security threshold for BB84
        print("   ⚠️  HIGH QBER: Possible eavesdropping detected!")
        print("   Alice and Bob should abort and try again.")
    else:
        print("   ✅ Low QBER: Communication appears secure.")
        print("   Alice and Bob can proceed with error correction")
        print("   and privacy amplification to generate the final key.")


def simulate_real_bb84():
    """
    Simulate a real BB84 protocol execution with QKDpy.
    """
    print("\n" + "=" * 60)
    print("REAL BB84 PROTOCOL SIMULATION WITH QKDpy")
    print("=" * 60)

    # Create a realistic quantum channel
    print("\nCreating quantum channel...")
    channel = QuantumChannel(
        loss=0.1,  # 10% photon loss
        noise_model="depolarizing",
        noise_level=0.05,  # 5% depolarizing noise
    )

    # Create BB84 protocol instance
    print("Initializing BB84 protocol...")
    bb84 = BB84(channel, key_length=128)

    # Execute the protocol
    print("Executing BB84 protocol...")
    results = bb84.execute()

    # Display results
    print("\nProtocol Results:")
    print(f"  • Generated key length: {len(results['final_key'])}")
    print(f"  • Quantum Bit Error Rate (QBER): {results['qber']:.4f}")
    print(f"  • Is communication secure: {results['is_secure']}")
    print(f"  • Execution time: {results.get('execution_time', 0):.4f} seconds")

    # Show first part of the final key
    if results["final_key"]:
        print(f"  • Final key (first 20 bits): {results['final_key'][:20]}")

    return bb84, results


def visualize_quantum_states():
    """
    Visualize quantum states on the Bloch sphere.
    """
    print("\n" + "=" * 60)
    print("VISUALIZING QUANTUM STATES")
    print("=" * 60)

    # Create different quantum states
    states = [
        ("|0⟩", Qubit.zero()),
        ("|1⟩", Qubit.one()),
        ("|+⟩", Qubit.plus()),
        ("|-⟩", Qubit.minus()),
        ("|+i⟩", Qubit(1 / np.sqrt(2), 1j / np.sqrt(2))),
        ("|-i⟩", Qubit(1 / np.sqrt(2), -1j / np.sqrt(2))),
    ]

    print("Common quantum states and their Bloch vector representations:")
    for name, qubit in states:
        x, y, z = qubit.bloch_vector()
        print(f"  {name:<4}: (x={x:5.2f}, y={y:5.2f}, z={z:5.2f})")

    # Visualize on Bloch sphere (if matplotlib is available)
    try:
        BlochSphere.plot_multiple_qubits(
            [qubit for _, qubit in states],
            [name for name, _ in states],
            title="Common Quantum States on Bloch Sphere",
        )
        plt.show()
    except Exception as e:
        print(f"Could not display Bloch sphere visualization: {e}")


def compare_protocols():
    """
    Compare different QKD protocols.
    """
    print("\n" + "=" * 60)
    print("COMPARING DIFFERENT QKD PROTOCOLS")
    print("=" * 60)

    # Create a quantum channel
    channel = QuantumChannel(loss=0.1, noise_model="depolarizing", noise_level=0.05)

    # Define protocols to compare
    protocols = [
        ("BB84", BB84(channel, key_length=100)),
        ("E91", E91(channel, key_length=100)),
    ]

    # Execute each protocol and collect results
    print("\nExecuting protocols and collecting performance data...")
    results = {}

    for name, protocol in protocols:
        try:
            result = protocol.execute()
            results[name] = {
                "key_length": len(result["final_key"]),
                "qber": result["qber"],
                "is_secure": result["is_secure"],
                "execution_time": result.get("execution_time", 0),
            }
            print(f"  {name}: Completed successfully")
        except Exception as e:
            print(f"  {name}: Failed with error: {e}")
            results[name] = None

    # Display comparison
    print("\nProtocol Comparison:")
    print("-" * 50)
    for name, result in results.items():
        if result:
            print(
                f"  {name:4}: Key={result['key_length']:3d} bits, "
                f"QBER={result['qber']:5.3f}, "
                f"Secure={'Yes' if result['is_secure'] else 'No':3s}, "
                f"Time={result['execution_time']:6.3f}s"
            )
        else:
            print(f"  {name:4}: Failed to execute")


def demonstrate_security_features():
    """
    Demonstrate security features of QKD.
    """
    print("\n" + "=" * 60)
    print("DEMONSTRATING QKD SECURITY FEATURES")
    print("=" * 60)

    # 1. Eavesdropping detection
    print("\n1. Eavesdropping Detection:")
    print("   QKD protocols can detect the presence of eavesdroppers")
    print("   due to the no-cloning theorem of quantum mechanics.")
    print("   Any eavesdropping attempt introduces errors that")
    print("   Alice and Bob can detect by measuring the QBER.")

    # 2. Information-theoretic security
    print("\n2. Information-Theoretic Security:")
    print("   Unlike classical cryptography which relies on")
    print("   computational hardness assumptions, QKD provides")
    print("   information-theoretic security based on the laws")
    print("   of quantum physics.")

    # 3. Forward secrecy
    print("\n3. Forward Secrecy:")
    print("   Each session key is independent, so compromising")
    print("   one key does not affect past or future keys.")

    # 4. Example with high QBER indicating eavesdropping
    print("\n4. Example - High QBER Detection:")
    channel_with_eavesdropper = QuantumChannel(
        loss=0.3,  # High loss indicating possible eavesdropping
        noise_model="depolarizing",
        noise_level=0.2,  # High noise
    )

    bb84 = BB84(channel_with_eavesdropper, key_length=100)
    results = bb84.execute()

    print(f"   QBER with suspicious channel: {results['qber']:.4f}")
    if results["qber"] > 0.11:  # BB84 security threshold
        print("   ⚠️  HIGH QBER DETECTED - POSSIBLE EAVESDROPPING!")
        print("   Alice and Bob would abort this key exchange.")
    else:
        print("   QBER is within acceptable range.")


def main():
    """
    Main function to run all demonstrations.
    """
    print("Welcome to the QKDpy Educational Demo!")
    print(
        "This script will demonstrate the principles and usage of Quantum Key Distribution."
    )

    # Run demonstrations
    demonstrate_bb84_concept()
    bb84_protocol, results = simulate_real_bb84()
    visualize_quantum_states()
    compare_protocols()
    demonstrate_security_features()

    print("\n" + "=" * 60)
    print("EDUCATIONAL DEMO COMPLETED")
    print("=" * 60)
    print("\nFor more advanced features and customization options,")
    print("please refer to the QKDpy documentation and examples.")


if __name__ == "__main__":
    main()
