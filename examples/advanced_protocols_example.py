"""Example of using advanced protocols."""

import numpy as np

from qkdpy.core import QuantumChannel
from qkdpy.protocols import B92, CVQKD, DeviceIndependentQKD, TwistedPairQKD


def advanced_protocols_example():
    """Demonstrates the advanced QKD protocols."""
    print("Advanced QKD Protocols Example")
    print("==============================")

    # Create a quantum channel
    channel = QuantumChannel(loss=0.1, noise_model="depolarizing", noise_level=0.05)

    # 1. B92 Protocol
    print("\n1. B92 Protocol")
    b92 = B92(channel, key_length=50)
    b92_results = b92.execute()
    print(f"  - B92 complete: {b92.is_complete}")
    print(f"  - B92 secure: {b92_results['is_secure']}")
    print(f"  - B92 QBER: {b92_results['qber']:.4f}")
    print(f"  - B92 final key length: {len(b92_results['final_key'])}")

    # 2. Device-Independent QKD
    print("\n2. Device-Independent QKD")
    # For DI-QKD, we use a less noisy channel to ensure Bell's inequality can be violated
    di_channel = QuantumChannel(
        loss=0.05, noise_model="depolarizing", noise_level=0.02
    )
    di_qkd = DeviceIndependentQKD(di_channel, key_length=50)
    di_results = di_qkd.execute()
    bell_results = di_qkd.test_bell_inequality()
    print(f"  - DI-QKD complete: {di_qkd.is_complete}")
    print(f"  - DI-QKD secure: {di_qkd.is_secure()}")
    print(f"  - DI-QKD Bell violation: {bell_results['is_violated']}")
    print(f"  - DI-QKD S-value: {bell_results['s_value']:.4f}")
    print(f"  - DI-QKD final key length: {len(di_results['final_key'])}")

    # 3. Continuous-Variable QKD
    print("\n3. Continuous-Variable QKD")
    cv_qkd = CVQKD(channel, key_length=50)
    cv_results = cv_qkd.execute()
    print(f"  - CV-QKD complete: {cv_qkd.is_complete}")
    print(f"  - CV-QKD secure: {cv_results['is_secure']}")
    print(f"  - CV-QKD error variance: {cv_results['qber']:.4f}")
    print(f"  - CV-QKD final key length: {len(cv_results['final_key'])}")

    # 4. Twisted Pair QKD
    print("\n4. Twisted Pair QKD")
    tp_qkd = TwistedPairQKD(channel, key_length=50)
    tp_results = tp_qkd.execute()
    print(f"  - Twisted Pair QKD complete: {tp_qkd.is_complete}")
    print(f"  - Twisted Pair QKD secure: {tp_results['is_secure']}")
    print(f"  - Twisted Pair QKD QBER: {tp_results['qber']:.4f}")
    print(f"  - Twisted Pair QKD final key length: {len(tp_results['final_key'])}")

    # 5. Compare protocol efficiency
    print("\n5. Protocol Efficiency Comparison")
    protocols = [
        ("BB84", b92_results),
        ("B92", b92_results),
        ("Device-Independent", di_results),
        ("CV-QKD", cv_results),
        ("Twisted Pair", tp_results),
    ]

    for name, results in protocols:
        key_rate = (
            len(results["final_key"]) / len(results["raw_key"])
            if results["raw_key"]
            else 0
        )
        print(f"  - {name}: {key_rate:.4f} key rate")


if __name__ == "__main__":
    advanced_protocols_example()