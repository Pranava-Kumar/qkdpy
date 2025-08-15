"""Example demonstrating High-Dimensional QKD protocol."""

from qkdpy import HDQKD, QuantumChannel


def hd_qkd_example():
    """Example of using the HD-QKD protocol to generate a secure key."""
    print("High-Dimensional QKD Protocol Example")
    print("=====================================")

    # Create a quantum channel with some noise and loss
    channel = QuantumChannel(loss=0.1, noise_model="depolarizing", noise_level=0.05)

    # Create an HD-QKD protocol instance with 4-dimensional qudits
    hd_qkd = HDQKD(channel, key_length=100, dimension=4)

    # Execute the protocol
    results = hd_qkd.execute()

    # Print the results
    print(f"Raw key length: {len(results['raw_key'])}")
    print(f"Sifted key length: {len(results['sifted_key'])}")
    print(f"Final key length: {len(results['final_key'])}")
    print(f"QBER: {results['qber']:.4f}")
    print(f"Is secure: {results['is_secure']}")
    print(
        f"Final key (first 20 bits): {[int(bit) for bit in results['final_key'][:20]]}"
    )

    # Print channel statistics
    stats = results["channel_stats"]
    print("\nChannel Statistics:")
    print(f"Transmitted qudits: {stats['transmitted']}")
    print(f"Lost qudits: {stats['lost']} ({stats['loss_rate']:.2%})")
    print(f"Errors: {stats['errors']} ({stats['error_rate']:.2%})")

    # Print HD-QKD specific information
    print("\nHD-QKD Information:")
    print(f"Dimension: {hd_qkd.dimension}")
    print(f"Efficiency gain: {hd_qkd.get_dimension_efficiency():.2f}x")

    # Analyze basis distribution
    basis_dist = hd_qkd.get_basis_distribution()
    print(f"Basis distribution: {basis_dist}")

    return results


def compare_hd_qkd_with_bb84():
    """Compare HD-QKD with standard BB84 protocol."""
    print("\n\nComparison: HD-QKD vs BB84")
    print("==========================")

    from qkdpy import BB84

    # Create the same channel for both protocols
    channel = QuantumChannel(loss=0.1, noise_model="depolarizing", noise_level=0.05)

    # BB84 protocol
    bb84 = BB84(channel, key_length=100)
    bb84_results = bb84.execute()

    # HD-QKD protocol
    hd_qkd = HDQKD(channel, key_length=100, dimension=4)
    hd_qkd_results = hd_qkd.execute()

    print("BB84 Results:")
    print(f"  Final key length: {len(bb84_results['final_key'])}")
    print(f"  QBER: {bb84_results['qber']:.4f}")
    print(f"  Is secure: {bb84_results['is_secure']}")

    print("\nHD-QKD Results:")
    print(f"  Final key length: {len(hd_qkd_results['final_key'])}")
    print(f"  QBER: {hd_qkd_results['qber']:.4f}")
    print(f"  Is secure: {hd_qkd_results['is_secure']}")
    print(f"  Dimensional efficiency: {hd_qkd.get_dimension_efficiency():.2f}x")


if __name__ == "__main__":
    # Run the HD-QKD example
    hd_qkd_example()

    # Compare with BB84
    compare_hd_qkd_with_bb84()
