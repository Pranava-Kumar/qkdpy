#!/usr/bin/env python3
"""
QKDpy v0.8.0 Feature Showcase

This example demonstrates the major new features in version 0.8.0:
1. Density Matrix module for mixed state simulation
2. Quantum Circuit model for composing operations
3. Secret Key Rate calculator for protocol analysis
"""

import numpy as np
from qkdpy import (
    Circuit,
    DensityMatrix,
    SecretKeyRate,
    ChannelParameters,
    DecoyStateParameters,
    Qubit,
    Qudit,
)


def demo_density_matrix():
    """Demonstrate density matrix functionality."""
    print("=" * 60)
    print("DENSITY MATRIX MODULE")
    print("=" * 60)

    # Create pure states
    print("\n1. Pure States:")
    rho_0 = DensityMatrix.from_pure(Qubit.zero())
    rho_1 = DensityMatrix.from_pure(Qubit.one())
    rho_plus = DensityMatrix.from_pure(Qubit.plus())

    print(f"   |0⟩ purity: {rho_0.purity():.4f} (should be 1.0)")
    print(f"   |0⟩ entropy: {rho_0.entropy():.4f} bits (should be 0.0)")

    # Maximally mixed state
    print("\n2. Maximally Mixed State:")
    rho_mixed = DensityMatrix.maximally_mixed(2)
    print(f"   I/2 purity: {rho_mixed.purity():.4f} (should be 0.5)")
    print(f"   I/2 entropy: {rho_mixed.entropy():.4f} bits (should be 1.0)")

    # Mixed state from probabilities
    print("\n3. Mixed State from Ensemble:")
    rho_mixed_ensemble = DensityMatrix.from_probabilities(
        states=[Qubit.zero(), Qubit.one()],
        probabilities=[0.7, 0.3]
    )
    print(f"   0.7|0⟩⟨0| + 0.3|1⟩⟨1| purity: {rho_mixed_ensemble.purity():.4f}")
    print(f"   Expected: 0.7² + 0.3² = {0.7**2 + 0.3**2:.4f}")

    # Quantum channels
    print("\n4. Quantum Channels (CPTP Maps):")
    from qkdpy.core import (
        depolarizing_channel,
        amplitude_damping_channel,
        phase_damping_channel,
        bit_flip_channel,
    )

    # Depolarizing channel
    kraus_depol = depolarizing_channel(0.3)
    rho_after_depol = rho_plus.apply_channel(kraus_depol)
    print(f"   After depolarizing (p=0.3):")
    print(f"     Purity: {rho_after_depol.purity():.4f} (decreased from 1.0)")

    # Amplitude damping
    kraus_amp = amplitude_damping_channel(0.2)
    rho_after_amp = rho_1.apply_channel(kraus_amp)
    print(f"   After amplitude damping (γ=0.2):")
    print(f"     ρ[0,0] = {rho_after_amp.matrix[0,0].real:.4f} (|0⟩ population)")
    print(f"     ρ[1,1] = {rho_after_amp.matrix[1,1].real:.4f} (|1⟩ population)")

    # Phase damping
    kraus_phase = phase_damping_channel(0.4)
    rho_after_phase = rho_plus.apply_channel(kraus_phase)
    print(f"   After phase damping (γ=0.4):")
    print(f"     Coherence ρ[0,1]: {rho_after_phase.matrix[0,1].real:.4f}")

    # Fidelity and trace distance
    print("\n5. Distance Measures:")
    fid = rho_0.fidelity(rho_1)
    print(f"   F(|0⟩, |1⟩) = {fid:.4f} (orthogonal states)")

    fid_mixed = rho_0.fidelity(rho_mixed)
    print(f"   F(|0⟩, I/2) = {fid_mixed:.4f}")

    td = rho_0.trace_distance(rho_1)
    print(f"   T(|0⟩, |1⟩) = {td:.4f}")

    # Partial trace
    print("\n6. Partial Trace (Entanglement):")
    # Create Bell state |Φ+⟩ = (|00⟩ + |11⟩)/√2
    bell_state = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)
    rho_bell = DensityMatrix.from_pure(bell_state)
    print(f"   Bell state purity: {rho_bell.purity():.4f} (pure)")

    # Trace out second qubit
    rho_reduced = rho_bell.partial_trace([2, 2], keep=[0])
    print(f"   Reduced state (after tracing qubit 1):")
    print(f"     Purity: {rho_reduced.purity():.4f} (should be 0.5 = maximally mixed)")
    print(f"     Entropy: {rho_reduced.entropy():.4f} bits (should be 1.0)")


def demo_circuit():
    """Demonstrate quantum circuit functionality."""
    print("\n" + "=" * 60)
    print("QUANTUM CIRCUIT MODEL")
    print("=" * 60)

    # Simple circuit
    print("\n1. Bell State Circuit:")
    circuit = Circuit(2)
    circuit.h(0)
    circuit.cx(0, 1)

    print(f"   Circuit: {circuit}")
    print(f"   Depth: {circuit.depth()}")
    print(f"   Operations: {circuit.count_ops()}")

    # Simulate
    state = circuit.simulate()
    print(f"   Final state: {state}")

    # GHZ state
    print("\n2. GHZ State (3 qubits):")
    ghz = Circuit(3)
    ghz.h(0)
    ghz.cx(0, 1)
    ghz.cx(0, 2)

    print(f"   Circuit: {ghz}")
    state_ghz = ghz.simulate()
    print(f"   |000⟩ amplitude: {state_ghz[0]:.4f}")
    print(f"   |111⟩ amplitude: {state_ghz[7]:.4f}")

    # Custom gates
    print("\n3. Custom Gates:")
    custom_circuit = Circuit(2)
    custom_gate = np.array([
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 0, 1],
        [0, 0, 1, 0]
    ], dtype=complex)
    custom_circuit.custom_gate(custom_gate, [0, 1])
    print(f"   Applied custom CNOT gate")
    print(f"   Operations: {custom_circuit.count_ops()}")

    # Circuit composition
    print("\n4. Circuit Composition:")
    c1 = Circuit(2)
    c1.h(0)
    c1.h(1)

    c2 = Circuit(2)
    c2.cx(0, 1)

    combined = c1.compose(c2)
    print(f"   Circuit 1: {c1}")
    print(f"   Circuit 2: {c2}")
    print(f"   Combined: {combined}")

    # OpenQASM export
    print("\n5. OpenQASM Export:")
    qasm_circuit = Circuit(2)
    qasm_circuit.h(0)
    qasm_circuit.cx(0, 1)

    qasm = qasm_circuit.to_qasm()
    print(f"   Generated {len(qasm.splitlines())} lines of QASM code")
    print(f"   First few lines:")
    for line in qasm.splitlines()[:5]:
        print(f"     {line}")


def demo_secret_key_rate():
    """Demonstrate secret key rate calculations."""
    print("\n" + "=" * 60)
    print("SECRET KEY RATE CALCULATOR")
    print("=" * 60)

    # BB84 protocol
    print("\n1. BB84 Protocol:")
    params = ChannelParameters(
        distance_km=50,
        channel_loss_db_km=0.2,
        detector_efficiency=0.6,
        dark_count_prob=1e-6,
        misalignment_error=0.02
    )

    rate_bb84 = SecretKeyRate.bb84(params)
    print(f"   Distance: {params.distance_km} km")
    print(f"   Loss: {params.channel_loss_db_km} dB/km")
    print(f"   Detector efficiency: {params.detector_efficiency}")
    print(f"   QBER: {params.qber:.4f}")
    print(f"   Key rate: {rate_bb84:.6f} bits/pulse")

    # Decoy-state BB84
    print("\n2. Decoy-State BB84:")
    decoy_params = DecoyStateParameters(
        distance_km=50,
        channel_loss_db_km=0.2,
        detector_efficiency=0.6,
        dark_count_prob=1e-6,
        misalignment_error=0.02,
        mean_photon_number=0.5,
        fraction_signal=0.5,
        fraction_decoy=0.5,
        decoy_intensity=0.1
    )

    rate_decoy = SecretKeyRate.decoy_bb84(decoy_params)
    print(f"   Mean photon number: {decoy_params.mean_photon_number}")
    print(f"   Key rate: {rate_decoy:.6f} bits/pulse")

    # Compare protocols
    print("\n3. Protocol Comparison at 50 km:")
    protocols = {
        'BB84': SecretKeyRate.bb84,
        'E91': SecretKeyRate.e91,
        'SARG04': SecretKeyRate.sarg04,
    }

    for name, rate_func in protocols.items():
        rate = rate_func(params)
        print(f"   {name:8s}: {rate:.6f} bits/pulse")

    # Distance scaling
    print("\n4. Distance Scaling (BB84):")
    distances = [10, 25, 50, 75, 100, 150]
    print(f"   {'Distance (km)':>15} | {'Key Rate':>12}")
    print(f"   {'-'*15}-+-{'-'*12}")
    for d in distances:
        p = ChannelParameters(distance_km=d, channel_loss_db_km=0.2)
        rate = SecretKeyRate.bb84(p)
        print(f"   {d:15d} | {rate:12.6f}")

    # Maximum secure distance
    print("\n5. Maximum Secure Distance:")
    max_dist = SecretKeyRate.max_distance(
        protocol='bb84',
        channel_loss_db_km=0.2,
        detector_efficiency=0.6,
        dark_count_prob=1e-6,
        threshold_rate=1e-6
    )
    print(f"   Protocol: BB84")
    print(f"   Threshold rate: 1e-6 bits/pulse")
    print(f"   Maximum distance: {max_dist:.1f} km")


def demo_integration():
    """Demonstrate integration between modules."""
    print("\n" + "=" * 60)
    print("INTEGRATION: CIRCUITS + DENSITY MATRICES")
    print("=" * 60)

    # Create a circuit
    print("\n1. Noisy Circuit Simulation:")
    circuit = Circuit(1)
    circuit.h(0)

    # Simulate to get statevector
    state = circuit.simulate()
    print(f"   Circuit output (statevector): {state}")

    # Convert to density matrix
    rho = DensityMatrix.from_pure(state)
    print(f"   As density matrix, purity: {rho.purity():.4f}")

    # Apply noise
    from qkdpy.core import depolarizing_channel
    kraus = depolarizing_channel(0.1)
    rho_noisy = rho.apply_channel(kraus)
    print(f"   After depolarizing noise (p=0.1):")
    print(f"     Purity: {rho_noisy.purity():.4f}")
    print(f"     Fidelity with original: {rho.fidelity(rho_noisy):.4f}")

    # Connection to key rate
    print("\n2. Connection to Key Rate:")
    print(f"   QBER due to noise: {1 - rho.fidelity(rho_noisy):.4f}")
    print(f"   This QBER would reduce the secure key rate")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 60)
    print("QKDpy v0.8.0 FEATURE SHOWCASE")
    print("=" * 60)
    print("\nThis example demonstrates the major new features in v0.8.0:")
    print("  1. Density Matrix module for mixed state simulation")
    print("  2. Quantum Circuit model for composing operations")
    print("  3. Secret Key Rate calculator for protocol analysis")

    try:
        demo_density_matrix()
        demo_circuit()
        demo_secret_key_rate()
        demo_integration()

        print("\n" + "=" * 60)
        print("DEMONSTRATION COMPLETE")
        print("=" * 60)
        print("\nKey Takeaways:")
        print("  • Density matrices enable realistic noise modeling")
        print("  • Circuits provide intuitive quantum programming")
        print("  • Key rate calculator supports protocol optimization")
        print("  • All modules integrate seamlessly")

    except Exception as e:
        print(f"\nError during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
