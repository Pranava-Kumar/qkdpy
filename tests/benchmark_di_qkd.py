import time

from qkdpy.core import QuantumChannel
from qkdpy.protocols.di_qkd import DeviceIndependentQKD


def test_di_qkd_benchmark():
    """Benchmark DI-QKD execution time and key rate."""
    channel = QuantumChannel(loss=0.1, noise_model="depolarizing", noise_level=0.01)
    # Increase key length for meaningful benchmark
    key_length = 100

    start_time = time.time()
    di_qkd = DeviceIndependentQKD(channel, key_length=key_length)
    results = di_qkd.execute()
    end_time = time.time()

    duration = end_time - start_time
    key_rate = len(results["final_key"]) / duration if duration > 0 else 0

    print("\nDI-QKD Benchmark Results:")
    print(f"Duration: {duration:.4f}s")
    print(f"Final Key Length: {len(results['final_key'])}")
    print(f"Key Rate: {key_rate:.2f} bits/s")
    print(f"QBER: {results['qber']:.4f}")

    # Check for Bell violation if present in results
    if "bell_test" in results:
        print(f"S-value: {results['bell_test'].get('s_value', 'N/A')}")


if __name__ == "__main__":
    test_di_qkd_benchmark()
