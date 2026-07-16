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

"""Blackbox test script for qkdpy library.

Tests 5 features with actual numerical results.
"""
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
print("QKDPY BLACKBOX TEST — ACTUAL NUMERICAL RESULTS")
print("=" * 72)

# =====================================================================
# TEST 1: Bell State Creation
# =====================================================================
print("\n" + "=" * 72)
print("[TEST 1] Bell State |Phi+> Creation")
print("=" * 72)

bell = MultiQubitState.zeros(2)
bell.apply_gate(Hadamard().matrix, 0)
bell.apply_gate(CNOT().matrix, [0, 1])

sv = bell.state
print(f"  Statevector: {sv}")
amp_00 = sv[0]
amp_11 = sv[-1]
print(f"  |00> amplitude: {amp_00:.8f}")
print(f"  |11> amplitude: {amp_11:.8f}")
expected = 1.0 / math.sqrt(2)
match_00 = abs(abs(amp_00) - expected) < 1e-10
match_11 = abs(abs(amp_11) - expected) < 1e-10
print(f"  |00> amplitude matches 1/sqrt(2): {match_00}")
print(f"  |11> amplitude matches 1/sqrt(2): {match_11}")
print(f"  Is |Phi+> state: {match_00 and match_11}")

# 1000-shot measurement using proper sequential measurement (collapsed state)
print("\n  --- 1000-shot measurement (proper sequential collapse) ---")
same = 0
diff = 0
for trial in range(1000):
    q = MultiQubitState.zeros(2)
    q.apply_gate(Hadamard().matrix, 0)
    q.apply_gate(CNOT().matrix, [0, 1])
    r0, collapsed = q.measure(0)
    if collapsed is not None:
        r1, _ = collapsed.measure(0)
    else:
        r1 = -1
    if r0 == r1:
        same += 1
    else:
        diff += 1
pct_same = 100.0 * same / 1000
pct_diff = 100.0 * diff / 1000
print(f"  same={same} ({pct_same:.1f}%), diff={diff} ({pct_diff:.1f}%)")
print(f"  P(same) vs P(different):  {same / 1000:.4f}  vs  {diff / 1000:.4f}")
print("  Perfect correlation (quantum prediction): 100% same")

# Also show what happens WITHOUT proper collapse (the "wrong" way)
print("\n  --- 1000-shot measurement (independent, no collapse) ---")
same2 = 0
diff2 = 0
for trial in range(1000):
    q2 = MultiQubitState.zeros(2)
    q2.apply_gate(Hadamard().matrix, 0)
    q2.apply_gate(CNOT().matrix, [0, 1])
    r0_ind = q2.measure(0)[0]  # no collapse of original state
    r1_ind = q2.measure(1)[0]  # measures from original state
    if r0_ind == r1_ind:
        same2 += 1
    else:
        diff2 += 1
pct_same2 = 100.0 * same2 / 1000
pct_diff2 = 100.0 * diff2 / 1000
print(f"  same={same2} ({pct_same2:.1f}%), diff={diff2} ({pct_diff2:.1f}%)")
print(f"  P(same) vs P(different):  {same2 / 1000:.4f}  vs  {diff2 / 1000:.4f}")
print("  (Note: library does not collapse original state in-place)")
print("  (Proper quantum mechanical prediction: 100% same)")

# =====================================================================
# TEST 2: CHSH Inequality
# =====================================================================
print("\n" + "=" * 72)
print("[TEST 2] CHSH Inequality (Bell Test)")
print("=" * 72)

n_shots = 500
angles_list = [
    (math.pi / 4, math.pi / 4, "E(pi/4, pi/4)"),
    (math.pi / 4, -math.pi / 4, "E(pi/4, -pi/4)"),
    (-math.pi / 4, math.pi / 4, "E(-pi/4, pi/4)"),
    (-math.pi / 4, -math.pi / 4, "E(-pi/4, -pi/4)"),
]

Es = []
for a_angle, b_angle, label in angles_list:
    counts_00 = 0
    counts_11 = 0
    counts_01 = 0
    counts_10 = 0
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
            counts_00 += 1
        elif r0 == 1 and r1 == 1:
            counts_11 += 1
        elif r0 == 0 and r1 == 1:
            counts_01 += 1
        elif r0 == 1 and r1 == 0:
            counts_10 += 1
    total = counts_00 + counts_11 + counts_01 + counts_10
    E = (counts_00 + counts_11 - counts_01 - counts_10) / total if total > 0 else 0
    Es.append(E)
    print(f"  {label:30s} = {E:+.6f}  (N={total})")

S = Es[0] + Es[1] + Es[2] - Es[3]
S_quantum = 2 * math.sqrt(2)
print("\n  S = E(pi/4, pi/4) + E(pi/4, -pi/4) + E(-pi/4, pi/4) - E(-pi/4, -pi/4)")
print(f"  S = {Es[0]:+.4f} + {Es[1]:+.4f} + {Es[2]:+.4f} - ({Es[3]:+.4f})")
print(f"  S = {S:.6f}")
print(f"  2*sqrt(2) = {S_quantum:.6f}")
print(f"  Deviation from 2*sqrt(2): {abs(S - S_quantum):.6f}")
print(f"  Bell violation (|S| > 2)? {abs(S) > 2}")
print("  Predicted: S = 2.828 (for |Phi+> with ideal measurements)")

# Also run the E91 protocol's built-in CHSH test
print("\n  --- E91 Protocol Built-in Bell Test ---")
from qkdpy.protocols.e91 import E91

ch_e91 = QuantumChannel(distance=1, noise_model="none", noise_level=0.0)
e91 = E91(ch_e91, key_length=50)
e91.num_pairs = 1000
e91.measure_states([Qubit.zero()] * e91.num_pairs)
bell_stats = e91.test_bell_inequality()
print(f"  E91 S-value: {bell_stats['s_value']:.6f}")
print(f"  E91 Bell violated: {bell_stats['is_violated']}")
print(f"  E91 Correlations: {bell_stats['correlation_values']}")

# =====================================================================
# TEST 3: QuantumChannel Noise Impact
# =====================================================================
print("\n" + "=" * 72)
print("[TEST 3] QuantumChannel Depolarizing Noise Impact")
print("=" * 72)

for nl in [0.0, 0.1, 0.5]:
    ch = QuantumChannel(distance=1, noise_model="depolarizing", noise_level=nl)
    fidelities = []
    surviving = 0
    for trial in range(100):
        q = Qubit.plus()
        result = ch.transmit(q, timestamp=float(trial))
        if result is not None:
            fid = Meas.measure_state_fidelity(result, Qubit.plus().state)
            fidelities.append(fid)
            surviving += 1
    avg_fid = float(np.mean(fidelities)) if fidelities else 0.0
    print(
        f"  noise_level={nl:.1f}:  avg fidelity={avg_fid:.6f}  "
        f"(surviving={surviving}/100)"
    )

# =====================================================================
# TEST 4: Entanglement Entropy
# =====================================================================
print("\n" + "=" * 72)
print("[TEST 4] GHZ(3) Entanglement Entropy")
print("=" * 72)

ghz3 = MultiQubitState.ghz(3)
print(f"  GHZ(3) statevector: {ghz3.state}")
entropy = ghz3.entanglement_entropy([0])
log2_val = math.log(2)
print(f"  Entanglement entropy S(rho_0) = {entropy:.8f}")
print(f"  Expected (log 2)              = {log2_val:.8f}")
print(f"  Match (within 1e-6): {abs(entropy - log2_val) < 1e-6}")
print(f"  Deviation: {abs(entropy - log2_val):.2e}")

# Also compute entropy of two qubits (should be the same for GHZ)
entropy_2 = ghz3.entanglement_entropy([0, 1])
print(f"  Entanglement entropy S(rho_01) = {entropy_2:.8f}")
print(f"  Expected for 2 qubits (log 2)  = {log2_val:.8f}")
print(f"  Match: {abs(entropy_2 - log2_val) < 1e-6}")

# =====================================================================
# TEST 5: BB84 Protocol
# =====================================================================
print("\n" + "=" * 72)
print("[TEST 5] BB84 Protocol with Real Quantum Channel")
print("=" * 72)

channel = QuantumChannel(distance=10, noise_model="depolarizing", noise_level=0.05)
bb84 = BB84(channel, key_length=50)
result = bb84.execute()

qber_val = result.get("qber", "N/A")
is_secure = result.get("is_secure", "N/A")
final_key = result.get("final_key", [])
raw_key = result.get("raw_key", [])
sifted_key = result.get("sifted_key", [])
channel_stats = result.get("channel_stats", {})

print(f"  QBER:                {qber_val}")
print(f"  Is secure:           {is_secure}")
print(f"  Final key length:    {len(final_key)}")
print(f"  Raw key length:      {len(raw_key)}")
print(f"  Sifted key length:   {len(sifted_key)}")
print(f"  Final key (first 20): {str(final_key[:20])}")
print(f"  Channel stats:       {channel_stats}")

# Run BB84 with different noise levels
print("\n  --- BB84 at varying noise levels ---")
for nl in [0.0, 0.02, 0.05, 0.08, 0.12]:
    ch2 = QuantumChannel(distance=10, noise_model="depolarizing", noise_level=nl)
    bb84_2 = BB84(ch2, key_length=50)
    res2 = bb84_2.execute()
    print(
        f"  noise={nl:.2f}:  QBER={res2['qber']:.4f}  "
        f"secure={res2['is_secure']}  "
        f"final_key_len={len(res2['final_key'])}"
    )

print("\n" + "=" * 72)
print("ALL QKDPY BLACKBOX TESTS COMPLETE")
print("=" * 72)
