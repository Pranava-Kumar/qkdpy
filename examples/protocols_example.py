"""Example of using the QKD protocols in QKDpy."""

from qkdpy.core import QuantumChannel
from qkdpy.protocols import BB84, E91, SARG04


def protocols_example() -> None:
    """Demonstrates the execution of different QKD protocols."""
    print("QKDpy Protocols Example")
    print("=======================")

    # Create a quantum channel to be used by the protocols
    channel = QuantumChannel(loss=0.1, noise_model="depolarizing", noise_level=0.05)

    # 1. BB84 Protocol
    print("\n1. Running BB84 Protocol")
    bb84 = BB84(channel, key_length=50)
    bb84_results = bb84.execute()
    print(f"  - BB84 complete: {bb84.is_complete}")
    print(f"  - BB84 secure: {bb84.is_secure}")
    print(f"  - BB84 QBER: {bb84_results['qber']:.4f}")
    print(f"  - BB84 final key length: {len(bb84_results['final_key'])}")

    # 2. E91 Protocol
    print("\n2. Running E91 Protocol")
    # For E91, we use a less noisy channel to ensure Bell's inequality is violated
    e91_channel = QuantumChannel(
        loss=0.05, noise_model="depolarizing", noise_level=0.02
    )
    e91 = E91(e91_channel, key_length=50)
    e91_results = e91.execute()
    bell_results = e91.test_bell_inequality()
    print(f"  - E91 complete: {e91.is_complete}")
    print(f"  - E91 secure: {e91.is_secure}")
    print(f"  - E91 Bell violation: {bell_results['violation']}")
    print(f"  - E91 S-value: {bell_results['S_value']:.4f}")
    print(f"  - E91 final key length: {len(e91_results['final_key'])}")

    # 3. SARG04 Protocol
    print("\n3. Running SARG04 Protocol")
    sarg04 = SARG04(channel, key_length=50)
    sarg04_results = sarg04.execute()
    print(f"  - SARG04 complete: {sarg04.is_complete}")
    print(f"  - SARG04 secure: {sarg04.is_secure}")
    print(f"  - SARG04 QBER: {sarg04_results['qber']:.4f}")
    print(f"  - SARG04 final key length: {len(sarg04_results['final_key'])}")


if __name__ == "__main__":
    protocols_example()
