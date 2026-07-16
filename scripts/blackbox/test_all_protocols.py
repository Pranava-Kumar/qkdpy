#!/usr/bin/env python3
"""
Blackbox test of all 10 QKD protocols in qkdpy v0.6.0.

Tests each protocol individually, captures ALL numerical output,
and handles errors gracefully so all 10 protocols are attempted.
"""

import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from qkdpy.core import QuantumChannel
from qkdpy.protocols import (
    B92,
    BB84,
    CVQKD,
    E91,
    HDQKD,
    SARG04,
    DecoyStateBB84,
    DeviceIndependentQKD,
    EnhancedCVQKD,
    TwistedPairQKD,
)


def section(title):
    print()
    print("=" * 78)
    print("  " + title)
    print("=" * 78)
    sys.stdout.flush()


def subsection(title):
    print()
    print("  --- " + title + " ---")
    sys.stdout.flush()


def fmt_key(key):
    if not key:
        return "[] (empty)"
    show = key[:10]
    s = ", ".join(str(b) for b in show)
    if len(key) > 10:
        s += ", ... (" + str(len(key)) + " total)"
    else:
        s += " (" + str(len(key)) + " total)"
    return "[" + s + "]"


def fmt_stats(stats):
    lines = []
    for k, v in stats.items():
        if isinstance(v, float):
            lines.append("    " + k + ": " + f"{v:.6f}")
        else:
            lines.append("    " + k + ": " + str(v))
    return "\n".join(lines)


total_start = time.perf_counter()

# ===========================================================================
# 1. BB84
# ===========================================================================
section("1. BB84 Protocol")
try:
    subsection("BB84 at noise_level=0.03 (baseline)")
    t0 = time.perf_counter()
    channel = QuantumChannel(distance=10, noise_model="depolarizing", noise_level=0.03)
    bb84 = BB84(channel, key_length=100)
    r = bb84.execute()
    t1 = time.perf_counter()
    print(f"  Runtime:              {t1 - t0:.4f} s")
    print("  QBER:                 {:.6f}".format(r["qber"]))
    print("  Is Secure:            {}".format(r["is_secure"]))
    print("  Final Key Length:     {}".format(len(r["final_key"])))
    print("  Sifted Key Length:    {}".format(len(r["sifted_key"])))
    print("  Raw Key Length:       {}".format(len(r["raw_key"])))
    print("  Final Key (first 20): {}".format(fmt_key(r["final_key"])))
    print("  Channel Stats:\n{}".format(fmt_stats(r["channel_stats"])))

    subsection("BB84 noise sweep: 0.0, 0.03, 0.05, 0.08, 0.11, 0.15")
    for nl in [0.0, 0.03, 0.05, 0.08, 0.11, 0.15]:
        t0 = time.perf_counter()
        chan = QuantumChannel(distance=10, noise_model="depolarizing", noise_level=nl)
        p = BB84(chan, key_length=100)
        r2 = p.execute()
        t1 = time.perf_counter()
        print(
            "  noise_level={:.2f} -> QBER={:.6f}, secure={}, "
            "final_key_len={}, runtime={:.4f}s".format(
                nl, r2["qber"], r2["is_secure"], len(r2["final_key"]), t1 - t0
            )
        )
except Exception as e:
    print(f"  ERROR in BB84: {e}")
    traceback.print_exc()

# ===========================================================================
# 2. B92
# ===========================================================================
section("2. B92 Protocol")
for nl in [0.0, 0.03, 0.08]:
    try:
        subsection(f"B92 at noise_level={nl:.2f}")
        t0 = time.perf_counter()
        channel = QuantumChannel(
            distance=10, noise_model="depolarizing", noise_level=nl
        )
        b92 = B92(channel, key_length=100)
        r = b92.execute()
        t1 = time.perf_counter()
        print(f"  Runtime:             {t1 - t0:.4f} s")
        print("  QBER:                {:.6f}".format(r["qber"]))
        print("  Is Secure:           {}".format(r["is_secure"]))
        print("  Final Key Length:    {}".format(len(r["final_key"])))
        print("  Sifted Key Len:      {}".format(len(r["sifted_key"])))
        print("  Raw Key Len:         {}".format(len(r["raw_key"])))
        print("  Final Key:           {}".format(fmt_key(r["final_key"])))
        print("  Channel Stats:\n{}".format(fmt_stats(r["channel_stats"])))

        # Key differences from BB84
        print(
            f"  B92 num_qubits:      {b92.num_qubits} (vs BB84 key_length*4={100 * 4})"
        )
        print(f"  B92 threshold:       {b92.security_threshold:.2f} (vs BB84 0.11)")
    except Exception as e:
        print(f"  ERROR in B92 nl={nl}: {e}")
        traceback.print_exc()

# ===========================================================================
# 3. E91
# ===========================================================================
section("3. E91 Protocol")
for nl in [0.0, 0.05]:
    try:
        subsection(f"E91 at noise_level={nl:.2f}")
        t0 = time.perf_counter()
        channel = QuantumChannel(
            distance=10, noise_model="depolarizing", noise_level=nl
        )
        e91 = E91(channel, key_length=50)
        r = e91.execute()
        t1 = time.perf_counter()
        print(f"  Runtime:              {t1 - t0:.4f} s")
        print("  QBER:                 {:.6f}".format(r["qber"]))
        print("  Is Secure:            {}".format(r["is_secure"]))
        print("  Final Key Length:     {}".format(len(r["final_key"])))
        print("  Raw Key Length:       {}".format(r.get("raw_key_length", "N/A")))

        bell = r.get("bell_test", {})
        if bell:
            print("  Bell S-value:         {:.6f}".format(bell.get("s_value", 0.0)))
            print("  Bell Violated:        {}".format(bell.get("is_violated", "N/A")))
            print(
                "  Bell Est. QBER:       {}".format(bell.get("estimated_qber", "N/A"))
            )
            print(
                "  Bell Correlations:    {}".format(
                    bell.get("correlation_values", "N/A")
                )
            )
        print(f"  E91 Alice angles:     {e91.alice_angles}")
        print(f"  E91 Bob angles:       {e91.bob_angles}")
        print(f"  E91 num_pairs:        {e91.num_pairs}")
    except Exception as e:
        print(f"  ERROR in E91 nl={nl}: {e}")
        traceback.print_exc()

# ===========================================================================
# 4. SARG04
# ===========================================================================
section("4. SARG04 Protocol")
for nl in [0.0, 0.05]:
    try:
        subsection(f"SARG04 at noise_level={nl:.2f}")
        t0 = time.perf_counter()
        channel = QuantumChannel(
            distance=10, noise_model="depolarizing", noise_level=nl
        )
        sarg = SARG04(channel, key_length=100)
        r = sarg.execute()
        t1 = time.perf_counter()
        print(f"  Runtime:              {t1 - t0:.4f} s")
        print("  QBER:                 {:.6f}".format(r["qber"]))
        print("  Is Secure:            {}".format(r["is_secure"]))
        print("  Final Key Length:     {}".format(len(r["final_key"])))
        print("  Sifted Key Len:       {}".format(len(r["sifted_key"])))
        print("  Raw Key Len:          {}".format(len(r["raw_key"])))
        print("  Channel Stats:\n{}".format(fmt_stats(r["channel_stats"])))
        print(
            f"  SARG04 num_qubits:    {sarg.num_qubits} (BB84 sends 5x, SARG04 sends 6x)"
        )
    except Exception as e:
        print(f"  ERROR in SARG04 nl={nl}: {e}")
        traceback.print_exc()

# ===========================================================================
# 5. DI-QKD
# ===========================================================================
section("5. Device-Independent QKD Protocol")
try:
    subsection("DI-QKD (default)")
    t0 = time.perf_counter()
    channel = QuantumChannel(distance=10, noise_model="depolarizing", noise_level=0.01)
    di_qkd = DeviceIndependentQKD(channel, key_length=50)
    r = di_qkd.execute()
    t1 = time.perf_counter()
    print(f"  Runtime:              {t1 - t0:.4f} s")
    print("  QBER:                 {:.6f}".format(r["qber"]))
    print("  Is Secure:            {}".format(r["is_secure"]))
    print("  Final Key Length:     {}".format(len(r["final_key"])))
    print("  Raw Key Length:       {}".format(r.get("raw_key_length", "N/A")))
    print(f"  DI num_pairs:         {di_qkd.num_pairs}")
    print(f"  DI Alice angles:      {di_qkd.alice_angles}")
    print(f"  DI Bob angles:        {di_qkd.bob_angles}")
    bell = r.get("bell_test", {})
    if bell:
        print("  Bell S-value:         {:.6f}".format(bell.get("s_value", 0.0)))
        print("  Bell Violated:        {}".format(bell.get("is_violated", "N/A")))
        print("  Bell Est. QBER:       {}".format(bell.get("estimated_qber", "N/A")))
        print("  E00:                  {}".format(bell.get("e00", "N/A")))
        print("  E01:                  {}".format(bell.get("e01", "N/A")))
        print("  E10:                  {}".format(bell.get("e10", "N/A")))
        print("  E11:                  {}".format(bell.get("e11", "N/A")))
except Exception as e:
    print(f"  ERROR in DI-QKD: {e}")
    traceback.print_exc()

# ===========================================================================
# 6. CV-QKD
# ===========================================================================
section("6. Continuous-Variable QKD Protocol")
try:
    subsection("CV-QKD (default)")
    t0 = time.perf_counter()
    channel = QuantumChannel(distance=10, noise_model="depolarizing", noise_level=0.01)
    cvqkd = CVQKD(channel, key_length=100)
    r = cvqkd.execute()
    t1 = time.perf_counter()
    print(f"  Runtime:                {t1 - t0:.4f} s")
    print("  QBER (bit_error):       {:.6f}".format(r["qber"]))
    print("  Is Secure:              {}".format(r["is_secure"]))
    print("  Final Key Length:       {}".format(len(r["final_key"])))
    print("  Raw Key Length:         {}".format(r.get("raw_key_length", "N/A")))
    print("  SNR:                    {}".format(r.get("snr", "N/A")))
    print("  Theoretical Capacity:   {}".format(r.get("theoretical_capacity", "N/A")))
    print("  Final Key:              {}".format(fmt_key(r["final_key"])))
    print(f"  CV block_size:          {cvqkd.block_size}")
    print(f"  CV modulation_variance: {cvqkd.modulation_variance}")
    print(f"  CV homodyne_efficiency: {cvqkd.homodyne_efficiency}")
    print(f"  CV excess_noise:        {cvqkd.excess_noise}")
except Exception as e:
    print(f"  ERROR in CV-QKD: {e}")
    traceback.print_exc()

# ===========================================================================
# 7. HD-QKD
# ===========================================================================
section("7. High-Dimensional QKD Protocol")
for d in [4, 3, 5]:
    try:
        subsection(f"HD-QKD dimension={d}")
        t0 = time.perf_counter()
        channel = QuantumChannel(
            distance=10, noise_model="depolarizing", noise_level=0.02
        )
        hdqkd = HDQKD(channel, key_length=100, dimension=d)
        r = hdqkd.execute()
        t1 = time.perf_counter()
        print(f"  Runtime:              {t1 - t0:.4f} s")
        print(f"  Dimension:            {d}")
        print("  QBER:                 {:.6f}".format(r["qber"]))
        print("  Is Secure:            {}".format(r["is_secure"]))
        print("  Final Key Length:     {}".format(len(r["final_key"])))
        print("  Sifted Key Len:       {}".format(len(r["sifted_key"])))
        print("  Raw Key Len:          {}".format(len(r["raw_key"])))
        print("  Channel Stats:\n{}".format(fmt_stats(r["channel_stats"])))
        print(f"  HD num_qudits:        {hdqkd.num_qudits}")
        print(f"  HD threshold:         {hdqkd.security_threshold:.2f}")
        # Check if MUBs are full or fallback
        print(
            "  HD MUBs count:        {}".format(
                len(hdqkd.mubs) if hasattr(hdqkd, "mubs") and hdqkd.mubs else "N/A"
            )
        )
    except Exception as e:
        print(f"  ERROR in HD-QKD d={d}: {type(e).__name__}: {e}")
        traceback.print_exc()

# ===========================================================================
# 8. DecoyState BB84
# ===========================================================================
section("8. Decoy-State BB84 Protocol")
for nl in [0.0, 0.05, 0.11]:
    try:
        subsection(f"DecoyState BB84 at noise_level={nl:.2f}")
        t0 = time.perf_counter()
        channel = QuantumChannel(
            distance=10, noise_model="depolarizing", noise_level=nl
        )
        ds = DecoyStateBB84(channel, key_length=100)
        r = ds.execute()
        t1 = time.perf_counter()
        print(f"  Runtime:              {t1 - t0:.4f} s")
        print("  QBER:                 {:.6f}".format(r["qber"]))
        print("  Is Secure:            {}".format(r["is_secure"]))
        print("  Final Key Length:     {}".format(len(r["final_key"])))
        print("  Sifted Key Len:       {}".format(len(r["sifted_key"])))
        print("  Raw Key Len:          {}".format(len(r["raw_key"])))
        print("  Channel Stats:\n{}".format(fmt_stats(r["channel_stats"])))
        print(f"  Signal Intensity:     {ds.signal_intensity:.6f}")
        print(f"  Decoy Intensity:      {ds.decoy_intensity:.6f}")
        print(f"  Num Pulses:           {ds.num_pulses}")

        # Decoy analysis
        da = ds.analyze_decoy_states()
        print("  Decoy Analysis:")
        for k, v in da.items():
            if isinstance(v, float):
                print(f"    {k}: {v:.6f}")
            else:
                print(f"    {k}: {v}")
        print(f"  Secure Key Rate:      {ds.calculate_secure_key_rate():.6f}")
        print(f"  Basis Recon Rate:     {ds.get_basis_reconciliation_rate():.6f}")
    except Exception as e:
        print(f"  ERROR in DecoyState BB84 nl={nl}: {e}")
        traceback.print_exc()

# ===========================================================================
# 9. TwistedPair
# ===========================================================================
section("9. Twisted Pair QKD Protocol")
for nl in [0.0, 0.05]:
    try:
        subsection(f"TwistedPair at noise_level={nl:.2f}")
        t0 = time.perf_counter()
        channel = QuantumChannel(
            distance=10, noise_model="depolarizing", noise_level=nl
        )
        tp = TwistedPairQKD(channel, key_length=100)
        r = tp.execute()
        t1 = time.perf_counter()
        print(f"  Runtime:              {t1 - t0:.4f} s")
        print("  QBER:                 {:.6f}".format(r["qber"]))
        print("  Is Secure:            {}".format(r["is_secure"]))
        print("  Final Key Length:     {}".format(len(r["final_key"])))
        print("  Sifted Key Len:       {}".format(len(r["sifted_key"])))
        print("  Raw Key Len:          {}".format(len(r["raw_key"])))
        print("  Channel Stats:\n{}".format(fmt_stats(r["channel_stats"])))
        print(f"  Twist Factor:         {tp.twist_factor}")
        print(f"  Twist Efficiency:     {tp.get_twist_efficiency():.6f}")
        print(f"  TP num_qubits:        {tp.num_qubits}")
        print(f"  TP bases:             {tp.bases}")
    except Exception as e:
        print(f"  ERROR in TwistedPair nl={nl}: {e}")
        traceback.print_exc()

# ===========================================================================
# 10. EnhancedCVQKD
# ===========================================================================
section("10. Enhanced CV-QKD Protocol")
for nl in [0.01, 0.05]:
    try:
        subsection(f"EnhancedCVQKD at noise_level={nl:.2f}")
        t0 = time.perf_counter()
        channel = QuantumChannel(
            distance=10, noise_model="depolarizing", noise_level=nl
        )
        ecv = EnhancedCVQKD(channel, key_length=100)
        r = ecv.execute()
        t1 = time.perf_counter()
        print(f"  Runtime:                {t1 - t0:.4f} s")
        print("  QBER:                   {:.6f}".format(r["qber"]))
        print("  Is Secure:              {}".format(r["is_secure"]))
        print("  Final Key Length:       {}".format(len(r["final_key"])))
        print("  Sifted Key Len:         {}".format(len(r["sifted_key"])))
        print("  Raw Key Len:            {}".format(len(r["raw_key"])))
        print("  Channel Stats:\n{}".format(fmt_stats(r["channel_stats"])))
        print(f"  Secret Fraction:        {ecv.calculate_secret_fraction():.6f}")
        print(f"  Excess Noise Est:       {ecv.get_excess_noise():.6f}")
        print(f"  Key Rate:               {ecv.get_key_rate():.6f}")
        print(f"  ECV num_signals:        {ecv.num_signals}")
        print(f"  ECV modulation_variance: {ecv.modulation_variance}")
        print(f"  ECV detection_efficiency: {ecv.detection_efficiency}")
        print(f"  ECV excess_noise:       {ecv.excess_noise}")
        print(f"  ECV transmission_t:     {ecv.transmission_t}")
    except Exception as e:
        print(f"  ERROR in EnhancedCVQKD nl={nl}: {e}")
        traceback.print_exc()

# ===========================================================================
# SUMMARY
# ===========================================================================
total_elapsed = time.perf_counter() - total_start
section("SUMMARY - All Protocols Completed")
print(f"  Total runtime: {total_elapsed:.4f} s")
print(f"  Python: {sys.version}")
print("  Script: scripts/blackbox/test_all_protocols.py")
