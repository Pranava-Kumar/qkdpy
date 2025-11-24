import sys
import time

from qkdpy.core import QuantumChannel
from qkdpy.protocols import BB84


class TestPerformance:
    """Performance benchmarks for QKDpy."""

    def test_key_generation_rate(self):
        """Benchmark key generation rate (bits/second)."""
        channel = QuantumChannel(
            loss=0.0, noise_level=0.0
        )  # Ideal channel for max speed
        key_length = 1000
        bb84 = BB84(channel, key_length=key_length)

        start_time = time.time()
        results = bb84.execute()
        end_time = time.time()

        duration = end_time - start_time
        final_key_len = len(results["final_key"])
        rate = final_key_len / duration

        print(f"\nKey Rate: {rate:.2f} bits/sec")

        # Basic threshold check (adjust based on environment)
        # This is just to ensure it's not abysmally slow (e.g., < 10 bits/sec)
        assert rate > 10, "Key generation rate is too slow!"

    def test_memory_usage_simulation(self):
        """Estimate memory usage for a simulation run."""
        # This is a rough check using sys.getsizeof, which isn't perfect for deep objects
        # but gives an idea.
        channel = QuantumChannel()
        bb84 = BB84(channel, key_length=500)

        # Check size before execution
        _ = sys.getsizeof(bb84)

        bb84.execute()

        # Check size after (should hold key material)
        size_after = sys.getsizeof(bb84)

        # Just ensure it doesn't explode (e.g., > 100MB for 500 bits)
        # 500 bits is tiny, so overhead dominates.
        assert (
            size_after < 10 * 1024 * 1024
        ), "Memory usage seems excessive for small simulation"
