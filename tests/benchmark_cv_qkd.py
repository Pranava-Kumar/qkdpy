import time

from qkdpy.core import QuantumChannel
from qkdpy.protocols.cv_qkd import CVQKD


def test_cv_qkd_benchmark():
    """Benchmark CV-QKD execution time and key rate."""
    channel = QuantumChannel(loss=0.1, noise_model="depolarizing", noise_level=0.01)
    # Increase key length for meaningful benchmark
    key_length = 1000

    start_time = time.time()
    cv_qkd = CVQKD(channel, key_length=key_length)
    results = cv_qkd.execute()
    end_time = time.time()

    duration = end_time - start_time
    key_rate = len(results["final_key"]) / duration if duration > 0 else 0

    print("\nCV-QKD Benchmark Results:")
    print(f"Duration: {duration:.4f}s")
    print(f"Final Key Length: {len(results['final_key'])}")
    print(f"Key Rate: {key_rate:.2f} bits/s")
    print(f"QBER: {results['qber']:.4f}")
    print(f"Excess Noise: {cv_qkd.get_excess_noise():.4f}")


if __name__ == "__main__":
    test_cv_qkd_benchmark()
