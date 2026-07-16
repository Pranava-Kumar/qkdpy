#!/usr/bin/env python3
"""Test script for qkdpy modules — UTF-8 safe for Windows consoles."""

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

"""QKDPY Blackbox Test - Extended analysis of CHSH and Fidelity results."""
import math
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
np.set_printoptions(precision=6, suppress=True)

from qkdpy import (
    BB84,
    MultiQubitState,
    QuantumChannel,
    Qubit,
)
from qkdpy.core.gates import (
    CNOT,
    Hadamard,
    Ry,
)
from qkdpy.core.measurements import Measurement as Meas

print("=" * 72)
print("QKDPY EXTENDED ANALYSIS")
print("=" * 72)

# =====================================================================
# CHSH Analysis: Why direct user's angles give S ~ 0
# =====================================================================
print("\n[ANALYSIS] CHSH — Why Ry(pi/4) and Ry(-pi/4) give S ~ 0")
print("-" * 72)
print("For |Phi+>, E(a,b) = P(00)+P(11)-P(01)-P(10) = cos(a-b)")
print("With a,b in {pi/4, -pi/4}:")
print("  E(pi/4, pi/4)   = cos(0)    =  1.0")
print("  E(pi/4, -pi/4)  = cos(pi/2) =  0.0")
print("  E(-pi/4, pi/4)  = cos(pi/2) =  0.0")
print("  E(-pi/4, -pi/4) = cos(0)    =  1.0")
print("  S = 1 + 0 + 0 - 1 = 0")
print("The quantum prediction with these angles IS S=0, not 2*sqrt(2).")
print("S=2*sqrt(2) requires different angles (e.g. 0, pi/4, pi/2, 3pi/4).")

# =====================================================================
# Correct CHSH test with standard angles
# =====================================================================
print("\n[CORRECTED] CHSH with standard angles (0, pi/2, pi/4, 3pi/4)")
print("-" * 72)
n_shots = 500

# Alice angles: 0, pi/2
# Bob angles: pi/4, 3pi/4
# CHSH S = E(0, pi/4) - E(0, 3pi/4) + E(pi/2, pi/4) + E(pi/2, 3pi/4)
# Expected: S = 4/sqrt(2) = 2*sqrt(2) ≈ 2.828

angles_chsh = [
    (0.0, math.pi / 4, "E(0, pi/4)"),
    (0.0, 3 * math.pi / 4, "E(0, 3pi/4)"),
    (math.pi / 2, math.pi / 4, "E(pi/2, pi/4)"),
    (math.pi / 2, 3 * math.pi / 4, "E(pi/2, 3pi/4)"),
]

Es_chsh = []
for a_angle, b_angle, label in angles_chsh:
    c00, c11, c01, c10 = 0, 0, 0, 0
    for _ in range(n_shots):
        bell = MultiQubitState.zeros(2)
        bell.apply_gate(Hadamard().matrix, 0)
        bell.apply_gate(CNOT().matrix, [0, 1])
        bell.apply_gate(Ry(a_angle).matrix, 0)
        bell.apply_gate(Ry(b_angle).matrix, 1)
        r0, collapsed = bell.measure(0)
        if collapsed is not None:
            r1, _ = collapsed.measure(0)
        else:
            r1 = -1
        if r0 == 0 and r1 == 0:
            c00 += 1
        elif r0 == 1 and r1 == 1:
            c11 += 1
        elif r0 == 0 and r1 == 1:
            c01 += 1
        elif r0 == 1 and r1 == 0:
            c10 += 1
    total = c00 + c11 + c01 + c10
    E = (c00 + c11 - c01 - c10) / total if total > 0 else 0
    Es_chsh.append(E)
    p_same = (c00 + c11) / total
    p_diff = (c01 + c10) / total
    print(
        f"  {label:20s} = {E:+.6f}  "
        f"P(same)={p_same:.4f} P(diff)={p_diff:.4f}  N={total}"
    )

S_chsh = Es_chsh[0] - Es_chsh[1] + Es_chsh[2] + Es_chsh[3]
print(
    f"\n  S = {Es_chsh[0]:+.4f} - ({Es_chsh[1]:+.4f}) + "
    f"{Es_chsh[2]:+.4f} + {Es_chsh[3]:+.4f}"
)
print(f"  S = {S_chsh:.6f}")
print(f"  2*sqrt(2) = {2 * math.sqrt(2):.6f}")
print(f"  Deviation: {abs(S_chsh - 2 * math.sqrt(2)):.6f}")
print(f"  Bell violation (|S| > 2)? {abs(S_chsh) > 2}")

# =====================================================================
# Fidelity Analysis: Why fidelity at noise_level=0 is ~0.6
# =====================================================================
print("\n[ANALYSIS] Fidelity — Why fidelity ~0.6 at noise_level=0")
print("-" * 72)
print("The QuantumChannel has ALWAYS-ON physical effects even when")
print("noise_model='none' and noise_level=0:")
print("  - Polarization drift (rate=0.02)")
print("  - Phase fluctuations (rate=0.05)")
print("  - Misalignment errors (prob=0.01)")
print("  - Thermal noise")
print("These combine to give fidelity ~0.6 for |+> state.")

# Let's verify by creating a zero-noise channel explicitly
print("\n  --- Fidelity with all physical effects minimized ---")
ch_ideal = QuantumChannel(
    distance=0,
    loss_coefficient=0,
    noise_model="none",
    noise_level=0.0,
    misalignment_error=0.0,
    phase_fluctuation_rate=0.0,
    polarization_drift_rate=0.0,
    temperature=0.0,
)
fidelities = []
for trial in range(100):
    q = Qubit.plus()
    result = ch_ideal.transmit(q, timestamp=float(trial))
    if result is not None:
        fid = Meas.measure_state_fidelity(result, Qubit.plus().state)
        fidelities.append(fid)
avg_fid = float(np.mean(fidelities)) if fidelities else 0
print(f"  Minimal-noise channel: avg fidelity = {avg_fid:.6f}")

# Quick test: fidelity at each step of the channel pipeline
print("\n  --- Effect of individual channel components ---")
q_ref = Qubit.plus()
q_test = Qubit.plus()
# Just transmit with the default channel once
ch_def = QuantumChannel(distance=1, noise_model="none", noise_level=0.0)
for trial in range(20):
    q = Qubit.plus()
    r = ch_def.transmit(q, timestamp=float(trial))
    if r is not None:
        print(
            f"    trial {trial}: fidelity={Meas.measure_state_fidelity(r, Qubit.plus().state):.4f}  "
            f"state=({r.state[0]:.4f},{r.state[1]:.4f})"
        )

# =====================================================================
# Entropy: base-2 vs natural log
# =====================================================================
print("\n[ANALYSIS] Entropy — Why result is 1.0 not log(2)=0.693")
print("-" * 72)
print("The library uses base-2 logarithm for von Neumann entropy.")
print("For a maximally mixed single qubit: rho = I/2")
print("  eigenvalues = [0.5, 0.5]")
print("  S = -0.5*log2(0.5) - 0.5*log2(0.5)")
print("  S = -0.5*(-1) - 0.5*(-1) = 1.0")
print("Using natural log: S = -0.5*ln(0.5) - 0.5*ln(0.5) = ln(2) = 0.693")
print("Both are correct, just different units (bits vs nats).")

# =====================================================================
# BB84 extended analysis
# =====================================================================
print("\n[ANALYSIS] BB84 — QBER vs Noise Level")
print("-" * 72)
print("Note: BB84 protocol has its own noise handling and does not use")
print("the QuantumChannel's always-on physical effects for key generation.")
print("The QBER values increase with noise_level but remain under 11%")
print("threshold even at noise_level=0.12 due to error correction.")

# Run multiple times at high noise
print("\n  --- BB84 at noise_level=0.15 (near threshold) ---")
for i in range(5):
    ch = QuantumChannel(distance=10, noise_model="depolarizing", noise_level=0.15)
    bb84 = BB84(ch, key_length=50)
    r = bb84.execute()
    print(
        f"  run {i + 1}: QBER={r['qber']:.4f}  secure={r['is_secure']}  "
        f"final_key_len={len(r['final_key'])}"
    )

print("\n" + "=" * 72)
print("EXTENDED ANALYSIS COMPLETE")
print("=" * 72)
