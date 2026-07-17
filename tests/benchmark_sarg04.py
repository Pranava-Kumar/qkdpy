import time

from qkdpy.core import QuantumChannel
from qkdpy.protocols import SARG04


def benchmark_sarg04():
    """Benchmark the SARG04 protocol."""
    print("\n--- SARG04 Protocol Benchmark ---")

    # Setup
    key_length = 128
    channel = QuantumChannel(loss=0.0, noise_model="depolarizing", noise_level=0.0)
    sarg = SARG04(channel, key_length=key_length)

    # Execution
    start_time = time.time()
    results = sarg.execute()
    end_time = time.time()

    # Metrics
    final_key_len = len(results["final_key"])
    qber = results["qber"]
    sifting_efficiency = sarg.get_sifting_efficiency()

    print(f"Execution Time: {end_time - start_time:.4f}s")
    print(f"Requested Key Length: {key_length}")
    print(f"Final Key Length: {final_key_len}")
    print(f"QBER: {qber:.4f}")
    print(f"Sifting Efficiency: {sifting_efficiency:.4f}")

    # Verification
    # SARG04 sifting efficiency should be around 25% (0.25)
    # Because Bob matches basis 50% of time.
    # If basis matches:
    #   Alice sends |0> (Z). Announce {|0>, |->}.
    #   Bob measures Z. Gets 0. Orthogonal to neither. Inconclusive.
    #   Wait, if basis matches, Bob measures in same basis as Alice sent.
    #   Alice sent |0> (Z). Bob measures Z. Gets 0.
    #   Announced {|0>, |->}.
    #   Is 0 orthogonal to |0>? No.
    #   Is 0 orthogonal to |->? No.
    #   So if basis matches, result is INCONCLUSIVE?
    # Let's trace:
    #   Alice sends |0> (Z). Announce {|0>, |->}.
    #   Bob measures X. Gets + or -.
    #   If +: Orthogonal to |->. Conclusive! (Infers |0>).
    #   If -: Orthogonal to nothing. Inconclusive.
    # So Bob gets a result ONLY when he measures in the CONJUGATE basis?
    #   Yes! SARG04 works when bases MISMATCH.
    #   Alice sends Z basis. Bob measures X basis.
    #   Prob of conclusive result: 0.5 (if he gets the orthogonal outcome).
    #   Since Bob chooses X basis 50% of time, and gets orthogonal outcome 50% of time given X basis...
    #   Total efficiency = 0.5 * 0.5 = 0.25.

    print("Expected Efficiency: ~0.25")

    if final_key_len >= key_length:
        print("SUCCESS: Key generation successful.")
    else:
        print(
            "WARNING: Key length insufficient (expected for fixed num_qubits if efficiency is low)."
        )

    assert qber < 0.05, "QBER too high"
    assert (
        sifting_efficiency > 0.15 and sifting_efficiency < 0.35
    ), "Sifting efficiency deviation"


if __name__ == "__main__":
    benchmark_sarg04()
