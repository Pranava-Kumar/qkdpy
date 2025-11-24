import time

from qkdpy.core import QuantumChannel
from qkdpy.protocols.e91 import E91


def test_e91_benchmark():
    """Benchmark E91 execution time and key rate."""
    channel = QuantumChannel(loss=0.1, noise_model="depolarizing", noise_level=0.01)
    key_length = 100

    start_time = time.time()
    e91 = E91(channel, key_length=key_length)
    results = e91.execute()
    end_time = time.time()

    duration = end_time - start_time
    key_rate = len(results["final_key"]) / duration if duration > 0 else 0

    print("\nE91 Benchmark Results:")
    print(f"Duration: {duration:.4f}s")
    print(f"Final Key Length: {len(results['final_key'])}")
    print(f"Key Rate: {key_rate:.2f} bits/s")
    print(f"QBER: {results['qber']:.4f}")

    if "bell_test" in results:
        print(f"S-value: {results['bell_test'].get('s_value', 'N/A')}")


if __name__ == "__main__":
    test_e91_benchmark()
