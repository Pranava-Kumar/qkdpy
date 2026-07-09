"""Satellite QKD Demonstration.

This example demonstrates the intersection of:
- Space Technology: Satellite orbital mechanics and ground station links
- Quantum Computing: BB84 protocol over free-space optical channels
- AI/ML: Machine learning for channel prediction and optimization

Author: Pranava Kumar
"""

from qkdpy.network import (
    AtmosphericProfile,
    OrbitType,
    SatelliteQKD,
    simulate_satellite_qkd,
)


def main():
    """Run satellite QKD demonstration."""
    print("=" * 60)
    print("🛰️  SATELLITE QUANTUM KEY DISTRIBUTION DEMO")
    print("=" * 60)
    print()

    # === Part 1: Basic Satellite Pass Simulation ===
    print("📡 Part 1: Simulating LEO Satellite Pass")
    print("-" * 40)

    # Create satellite QKD system
    sat_qkd = SatelliteQKD(
        orbit_type=OrbitType.LEO,
        altitude_km=500,  # ISS-like altitude
        ground_station_lat=28.5,  # Cape Canaveral
        ground_station_lon=-80.6,
        protocol="BB84",
    )

    # Simulate pass with clear conditions
    clear_atmosphere = AtmosphericProfile(
        visibility_km=23.0,
        turbulence_cn2=1e-14,
        aerosol_optical_depth=0.1,
        cloud_optical_depth=0.0,
    )

    results = sat_qkd.simulate_pass(
        duration_seconds=300,
        time_steps=30,
        atmosphere=clear_atmosphere,
    )

    print("  Pass duration: 300 seconds")
    print(f"  Peak elevation: {max(results['elevation_angles']):.1f}°")
    print(f"  Min channel loss: {min(results['channel_losses_db']):.1f} dB")
    print(f"  Total key bits: {results['total_key_bits']:,.0f}")
    print()

    # === Part 2: Atmospheric Effects Comparison ===
    print("🌫️  Part 2: Atmospheric Effects Comparison")
    print("-" * 40)

    conditions = [
        ("Clear sky", AtmosphericProfile(visibility_km=23, turbulence_cn2=1e-14)),
        ("Hazy", AtmosphericProfile(visibility_km=10, turbulence_cn2=5e-14)),
        ("Turbulent", AtmosphericProfile(visibility_km=20, turbulence_cn2=1e-13)),
        ("Thin clouds", AtmosphericProfile(visibility_km=15, cloud_optical_depth=0.5)),
    ]

    for name, atm in conditions:
        result = sat_qkd.simulate_pass(atmosphere=atm)
        print(f"  {name:15} -> {result['total_key_bits']:>12,.0f} key bits")
    print()

    # === Part 3: ML-Based Channel Prediction ===
    print("🤖 Part 3: Training ML Channel Predictor")
    print("-" * 40)

    # Train on collected pass data
    training_result = sat_qkd.train_channel_predictor()

    if "error" not in training_result:
        print(f"  Epochs trained: {training_result['epochs_trained']}")
        print(f"  Final loss: {training_result['final_train_loss']:.4f}")

        # Predict for new conditions
        test_atmosphere = AtmosphericProfile(
            visibility_km=18,
            turbulence_cn2=3e-14,
            aerosol_optical_depth=0.15,
        )
        predicted_yield = sat_qkd.predict_key_yield(test_atmosphere, peak_elevation=75)
        print(f"  Predicted yield for test conditions: {predicted_yield:,.0f} bits")
    else:
        print(f"  {training_result['error']}")
    print()

    # === Part 4: Mission Summary ===
    print("📊 Part 4: Mission Summary")
    print("-" * 40)

    summary = sat_qkd.get_mission_summary()
    print(f"  Orbit type: {summary['orbit_type'].upper()}")
    print(f"  Altitude: {summary['altitude_km']} km")
    print(f"  Protocol: {summary['protocol']}")
    print(f"  Passes simulated: {summary['total_passes_simulated']}")
    print(f"  ML predictor trained: {summary['ml_predictor_trained']}")
    print()

    # === Part 5: Quick Simulation Function ===
    print("⚡ Part 5: Quick Multi-Pass Simulation")
    print("-" * 40)

    quick_results = simulate_satellite_qkd(
        altitude_km=600,
        ground_lat=51.5,  # London
        ground_lon=-0.1,
        num_passes=5,
    )

    print(f"  Total key bits across 5 passes: {quick_results['total_key_bits']:,.0f}")
    print(
        f"  Daily key capacity estimate: {quick_results['mission_summary']['estimated_daily_key_bits']:,.0f} bits"
    )
    print()

    print("=" * 60)
    print("✅ Demonstration Complete!")
    print("=" * 60)
    print()
    print("This demo showcased:")
    print("  • Space Tech: Orbital mechanics, atmospheric propagation")
    print("  • Quantum: BB84 protocol over free-space channels")
    print("  • AI/ML: Channel prediction using efficient neural networks")


if __name__ == "__main__":
    main()
