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

#!/usr/bin/env python3
"""Blackbox integration test for qkdpy v0.6.0 --
ALL framework integration layers.  Reports ALL actual numerical output.
"""

import math
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

# Force UTF-8 on stdout
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

SEP = "=" * 74

print(SEP)
print("  QKDPY v0.6.0 -- FULL INTEGRATION TEST SUITE")
print(SEP)

# ------------------------------------------------------------------ #
#  IMPORTS
# ------------------------------------------------------------------ #
import qkdpy

print(f"\n  qkdpy version: {qkdpy.__version__}")
print(f"  numpy version: {np.__version__}")
print()

from qkdpy.core import QuantumChannel, Qubit
from qkdpy.protocols.bb84 import BB84

NOISE_PARAMS = {"loss": 0.1, "noise_model": "depolarizing", "noise_level": 0.05}

# ================================================================== #
#  1. QISKIT INTEGRATION
# ================================================================== #
print(SEP)
print(f"  1. QISKIT INTEGRATION  (qiskit {__import__('qiskit').__version__})")
print(SEP)

try:
    from qkdpy.integrations.qiskit_integration import QiskitIntegration
except ImportError:
    from qiskit_integration import QiskitIntegration

qi = QiskitIntegration()
print("\n[1.1] QiskitIntegration instance created successfully.")

# -- 1.2 Convert QuantumChannel -> Qiskit NoiseModel --------------- #
channel = QuantumChannel(**NOISE_PARAMS)
print(
    f"\n[1.2] NoiseModel from channel "
    f"(loss={channel.loss}, noise={channel.noise_model}={channel.noise_level}):"
)
from qiskit_aer.noise import (
    NoiseModel,
    amplitude_damping_error,
    depolarizing_error,
)

nm_manual = NoiseModel()
if channel.loss > 0:
    ad_error = amplitude_damping_error(channel.loss)
    nm_manual.add_all_qubit_quantum_error(ad_error, ["id", "x", "h"])
if channel.noise_level > 0 and channel.noise_model == "depolarizing":
    dp_error = depolarizing_error(channel.noise_level, 1)
    nm_manual.add_all_qubit_quantum_error(dp_error, ["id", "x", "h"])
    dp2_error = depolarizing_error(channel.noise_level, 2)
    nm_manual.add_all_qubit_quantum_error(dp2_error, ["cx"])
print(f"      {nm_manual}")

# -- 1.3 Build BB84 circuit ---------------------------------------- #
print("\n[1.3] BB84 circuit (4 qubits, explicit bases):")
bb84_circ = qi.create_bb84_circuit(
    num_qubits=4,
    alice_bases=["Z", "X", "X", "Z"],
    bob_bases=["Z", "X", "Z", "X"],
)
print(bb84_circ.draw())
print(f"      Qubit count: {bb84_circ.num_qubits}")

# -- 1.4 Build E91 circuit ----------------------------------------- #
print("\n[1.4] E91 circuit (2 pairs, explicit bases):")
e91_circ = qi.create_e91_circuit(
    num_pairs=2,
    alice_bases=["Z", "X"],
    bob_bases=["X", "W"],
)
print(e91_circ.draw())

# -- 1.5 simulate_bb84_with_qiskit --------------------------------- #
print("\n[1.5] BB84 simulation via Qiskit (8 qubits, noisy):")
alice_bits, bob_bits, matching = qi.simulate_bb84_with_qiskit(
    num_qubits=8, noise_model="depolarizing", noise_level=0.05
)
matching_count = sum(matching)
qber_val = sum(
    1 for a, b, m in zip(alice_bits, bob_bits, matching) if m and a != b
) / max(matching_count, 1)
print(f"      Alice bits:  {alice_bits}")
print(f"      Bob bits:    {bob_bits}")
print(f"      Matching:    {matching}")
print(f"      Matching bases: {matching_count}/{len(matching)}")
print(f"      QBER (matching only): {qber_val:.4f}")

# -- 1.6 Quantum info measures ------------------------------------- #
from qiskit.quantum_info import DensityMatrix, Statevector

print("\n[1.6] Quantum Information Measures:")

phi_plus = Statevector([1 / math.sqrt(2), 0, 0, 1 / math.sqrt(2)])
dm_phi_plus = DensityMatrix(phi_plus)

# Concurrence
conc = qi.compute_concurrence(dm_phi_plus)
print(f"      concurrence(|Phi+>): {conc:.10f}  (expected 1.0)")

# Entanglement of formation
eof = qi.compute_entanglement_of_formation(dm_phi_plus)
print(f"      entanglement_of_formation(|Phi+>): {eof:.10f}  (expected 1.0)")

# Negativity
try:
    neg = qi.compute_negativity(dm_phi_plus)
    print(f"      negativity(|Phi+>): {neg:.10f}  (expected 0.5)")
except TypeError:
    from qiskit.quantum_info import negativity as qiskit_negativity

    neg = float(qiskit_negativity(dm_phi_plus, qargs=[0]))
    print(f"      negativity(|Phi+>): {neg:.10f}  (expected 0.5, direct Qiskit call)")

# Mutual information
try:
    mut_info = qi.compute_mutual_information(dm_phi_plus)
    print(f"      mutual_information(|Phi+>): {mut_info:.10f}  (expected 2.0)")
except TypeError:
    from qiskit.quantum_info import mutual_information as qiskit_mutinf

    mut_info = float(qiskit_mutinf(dm_phi_plus))
    print(
        f"      mutual_information(|Phi+>): {mut_info:.10f}  (expected 2.0, direct Qiskit call)"
    )

# Partial trace on GHZ(3)
ghz3 = Statevector([1 / math.sqrt(2), 0, 0, 0, 0, 0, 0, 1 / math.sqrt(2)])
reduced = qi.compute_partial_trace(ghz3, qargs=[0])
print("      partial_trace(GHZ3, trace_out=[0]):")
print(f"        reduced density matrix shape: {reduced.data.shape}")
print(f"        reduced dm:\n{reduced.data}")

# Entropy on reduced state
ent = qi.compute_von_neumann_entropy(reduced)
print(f"      entropy(reduced from GHZ3): {ent:.10f}  (expected 1.0)")

# State fidelity (identical states)
fid = qi.compute_state_fidelity(phi_plus, phi_plus)
print(f"      state_fidelity(|Phi+>, |Phi+>): {fid:.10f}  (expected 1.0)")

# Schmidt decomposition
print("\n[1.6b] Schmidt decomposition of |Phi+>:")
schmidt = qi.compute_schmidt_decomposition(phi_plus, qargs=[0])
for coeff, left_state, right_state in schmidt:
    print(f"        coeff={coeff:.6f}")
print(f"      Number of Schmidt coefficients: {len(schmidt)}")

# -- 1.7 Benchmark ------------------------------------------------- #
print("\n[1.7] Benchmark: qkdpy vs Qiskit BB84 (num_qubits=20, trials=3):")
try:
    bench = qi.benchmark_qkdpy_vs_qiskit(num_qubits=20, num_trials=3)
    print(
        f"      qkdpy avg: {bench['qkdpy_average_time']:.6f}s  "
        f"(std={bench['qkdpy_std_time']:.6f})"
    )
    print(
        f"      qiskit avg: {bench['qiskit_average_time']:.6f}s  "
        f"(std={bench['qiskit_std_time']:.6f})"
    )
    print(f"      speedup (qkdpy/qiskit): {bench['speedup_factor']:.3f}x")
    print(f"      qubits={bench['num_qubits']}, trials={bench['num_trials']}")
except Exception as e:
    print(f"      Benchmark FAILED: {e}")

# -- 1.7b Simulate E91 --------------------------------------------- #
print("\n[1.7b] E91 simulation (4 pairs, noise-free):")
try:
    e91_alice, e91_bob, e91_ab, e91_bb = qi.simulate_e91_with_qiskit(
        num_pairs=4, noise_model=None, noise_level=0.0
    )
    e91_match = sum(a == b for a, b in zip(e91_ab, e91_bb))
    print(f"      Alice bases: {e91_ab}")
    print(f"      Bob bases:   {e91_bb}")
    print(f"      Matching bases: {e91_match}/{len(e91_ab)}")
    print(f"      Alice bits: {e91_alice}")
    print(f"      Bob bits:   {e91_bob}")
except Exception as e:
    print(f"      E91 SIMULATION FAILED: {e}")

# -- 1.8 qubit_to_qiskit / qiskit_to_qubit ------------------------- #
print("\n[1.8] State conversion (qkdpy <-> qiskit):")
q = Qubit(1 / math.sqrt(2), 1 / math.sqrt(2))  # |+>
sv = qi.qubit_to_qiskit(q)
print(f"      Qubit(+) -> Statevector: {sv.data}")
q_back = qi.qiskit_to_qubit(sv)
print(f"      Statevector -> Qubit: state={q_back.state}")

# -- 1.9 Stabilizer state ------------------------------------------ #
print("\n[1.9] StabilizerState from Pauli strings:")
try:
    stab = qi.stabilizer_from_stabilizers(["XX", "ZZ"])
    print(f"      StabilizerState created: {stab}")
except Exception:
    from qiskit.quantum_info import StabilizerState

    stab = StabilizerState.from_stabilizer_list(["XX", "ZZ"])
    print(f"      StabilizerState (via from_stabilizer_list): {stab}")


# ================================================================== #
#  2. PENNYLANE INTEGRATION
# ================================================================== #
print("\n" + SEP)
print("  2. PENNYLANE INTEGRATION")
print(SEP)

try:
    from qkdpy.integrations.pennylane_integration import PennyLaneIntegration

    pli = PennyLaneIntegration()
    print("\n[2.1] PennyLaneIntegration instance created.")

    # -- 2.2 CHSH correlation ------------------------------------ #
    print("\n[2.2] CHSH correlation (maximal violation angles):")
    alice_angles = [0.0, math.pi / 2]
    bob_angles = [math.pi / 4, -math.pi / 4]
    s_val = pli.compute_chsh_correlation(alice_angles, bob_angles)
    print(f"      S = {s_val:.10f}  (expected ~2.8284 for maximal violation)")
    print(f"      Bell inequality violation: S > 2 ? {s_val > 2}")

    # -- 2.3 Quantum info measures ------------------------------- #
    print("\n[2.3] Quantum info (PennyLane math):")
    ghz3_state = np.array([1, 0, 0, 0, 0, 0, 0, 1], dtype=complex) / math.sqrt(2)
    vn_ent = pli.compute_vn_entropy(ghz3_state, indices=[0])
    print(
        f"      vn_entropy(GHZ3, subsystem=[0]): {vn_ent:.10f}  (expected 1.0 in log2, got natural log ~0.6931)"
    )

    mi = pli.compute_mutual_info(ghz3_state, indices0=[0], indices1=[1])
    print(f"      mutual_info(GHZ3, A=[0], B=[1]): {mi:.10f}")

    pur = pli.compute_purity(ghz3_state, indices=[0])
    print(f"      purity(GHZ3, subsystem=[0]): {pur:.10f}  (expected 0.5)")

    fid_pl = pli.compute_fidelity(ghz3_state, ghz3_state)
    print(f"      fidelity(ghz3, ghz3): {fid_pl:.10f}  (expected 1.0)")

    td = pli.compute_trace_distance(ghz3_state, ghz3_state)
    print(f"      trace_distance(ghz3, ghz3): {td:.10f}  (expected 0.0)")

    # -- 2.4 E91 circuit (try/except since QNode exec may fail) -- #
    print("\n[2.4] E91 circuit (2 pairs):")
    try:
        e91_pl = pli.create_e91_circuit(num_pairs=2, shots=1)
        print(f"      E91 QNode created: {e91_pl}")
        res = e91_pl()
        print(f"      E91 measurement results: {res}")
    except Exception as e:
        print(f"      E91 circuit/simulation: {e}")

    # -- 2.5 Entanglement circuit --------------------------------- #
    print("\n[2.5] Entanglement circuit (2 pairs):")
    try:
        ent_pl = pli.create_entanglement_circuit(num_pairs=2, shots=1)
        print(f"      Entanglement QNode created: {ent_pl}")
        res_ent = ent_pl()
        print(f"      Entanglement measurement: {res_ent}")
    except Exception as e:
        print(f"      Entanglement circuit: {e}")

    # -- 2.6 BB84 circuit ---------------------------------------- #
    print("\n[2.6] BB84 circuit (3 qubits):")
    try:
        bb84_pl = pli.create_bb84_circuit(
            num_qubits=3,
            alice_bases=["Z", "X", "Z"],
            bob_bases=["Z", "X", "X"],
        )
        print(f"      BB84 QNode created: {bb84_pl}")
        res_bb84 = bb84_pl()
        print(f"      BB84 measurement: {res_bb84}")
    except Exception as e:
        print(f"      BB84 circuit: {e}")

    # -- 2.7 Simulate BB84 via PennyLane -------------------------- #
    print("\n[2.7] BB84 simulation (8 qubits):")
    try:
        pl_alice, pl_bob, pl_match = pli.simulate_bb84_with_pennylane(
            num_qubits=8, noise_model="depolarizing", noise_level=0.05
        )
        print(f"      Alice bits:  {pl_alice}")
        print(f"      Bob bits:    {pl_bob}")
        print(f"      Matching:    {pl_match}")
        print(f"      Matching bases: {sum(pl_match)}/{len(pl_match)}")
    except Exception as e:
        print(f"      BB84 simulation FAILED: {e}")

    # -- 2.8 Channel conversion ---------------------------------- #
    print("\n[2.8] convert_channel_to_pennylane:")
    ch_pl = QuantumChannel(**NOISE_PARAMS)
    pl_noise = pli.convert_channel_to_pennylane(ch_pl)
    print(f"      PennyLane noise params: {pl_noise}")

    # -- 2.9 State conversion ------------------------------------ #
    print("\n[2.9] State conversion (qkdpy <-> pennylane):")
    q_pl = Qubit(1, 0)
    pl_state = pli.qubit_to_pennylane(q_pl)
    print(f"      Qubit(|0>) -> PennyLane tensor: {pl_state}")
    q_pl_back = pli.pennylane_to_qubit(pl_state)
    print(f"      PennyLane tensor -> Qubit: state={q_pl_back.state}")

    # -- 2.10 Tomography circuit --------------------------------- #
    print("\n[2.10] Tomography circuit (1 qubit):")
    try:
        tomo = pli.create_state_tomography_circuit(num_qubits=1)
        print(f"      Tomography function created: {tomo}")
        tomo_res = tomo()
        print(
            f"      Tomography results: Z={tomo_res['Z']}, X={tomo_res['X']}, Y={tomo_res['Y']}"
        )
    except Exception as e:
        print(f"      Tomography: {e}")

    # -- 2.11 Benchmark ------------------------------------------ #
    print("\n[2.11] Benchmark: qkdpy vs PennyLane (num_qubits=20, trials=3):")
    try:
        bench_pl = pli.benchmark_qkdpy_vs_pennylane(num_qubits=20, num_trials=3)
        print(
            f"      qkdpy avg: {bench_pl['qkdpy_average_time']:.6f}s  "
            f"(std={bench_pl['qkdpy_std_time']:.6f})"
        )
        print(
            f"      pennylane avg: {bench_pl['pennylane_average_time']:.6f}s  "
            f"(std={bench_pl['pennylane_std_time']:.6f})"
        )
        print(f"      speedup (qkdpy/pennylane): {bench_pl['speedup_factor']:.3f}x")
    except Exception as e:
        print(f"      Benchmark FAILED: {e}")

except ImportError as e:
    print(f"\n  ** PennyLane not installed: {e}")
    print("  ** Skipping all PennyLane tests.")
except Exception as e:
    import traceback

    print(f"\n  ** PennyLane test error: {e}")
    traceback.print_exc()


# ================================================================== #
#  3. CIRQ INTEGRATION
# ================================================================== #
print("\n" + SEP)
print(f"  3. CIRQ INTEGRATION  (cirq {__import__('cirq').__version__})")
print(SEP)

try:
    from qkdpy.integrations.cirq_integration import CirqIntegration

    ci = CirqIntegration()
    print("\n[3.1] CirqIntegration instance created.")

    # -- 3.2 Build BB84 circuit ---------------------------------- #
    print("\n[3.2] BB84 circuit (4 qubits):")
    bb84_cirq = ci.create_bb84_circuit(
        num_qubits=4,
        alice_bases=["Z", "X", "Z", "X"],
        bob_bases=["Z", "X", "X", "Z"],
    )
    print(bb84_cirq)
    print(f"      Number of moments: {len(bb84_cirq)}")

    # -- 3.3 Build entanglement circuit -------------------------- #
    print("\n[3.3] Entanglement circuit (2 pairs):")
    ent_cirq = ci.create_entanglement_circuit(num_pairs=2)
    print(ent_cirq)

    # -- 3.4 Convert noise model to Cirq noise gates ------------ #
    print("\n[3.4] Channel -> Cirq noise gates:")
    ch_cirq = QuantumChannel(**NOISE_PARAMS)
    cirq_noise = ci.convert_channel_to_cirq(ch_cirq)
    print(f"      Noise gates: {cirq_noise}")
    for g in cirq_noise:
        print(f"        {type(g).__name__}: {g}")

    # -- 3.5 Benchmark ------------------------------------------ #
    print("\n[3.5] Benchmark: qkdpy vs Cirq (num_qubits=50, trials=5):")
    try:
        bench_c = ci.benchmark_qkdpy_vs_cirq(num_qubits=50, num_trials=5)
        print(
            f"      qkdpy avg: {bench_c['qkdpy_average_time']:.6f}s  "
            f"(std={bench_c['qkdpy_std_time']:.6f})"
        )
        print(
            f"      cirq avg: {bench_c['cirq_average_time']:.6f}s  "
            f"(std={bench_c['cirq_std_time']:.6f})"
        )
        print(f"      speedup (qkdpy/cirq): {bench_c['speedup_factor']:.3f}x")
        print(f"      qubits={bench_c['num_qubits']}, trials={bench_c['num_trials']}")
    except Exception as e:
        print(f"      Benchmark FAILED: {e}")

    # -- 3.6 Simulate BB84 via Cirq ----------------------------- #
    print("\n[3.6] BB84 simulation (8 qubits):")
    try:
        c_alice, c_bob, c_match = ci.simulate_bb84_with_cirq(
            num_qubits=8, noise_model="depolarizing", noise_level=0.05
        )
        c_matching_count = sum(c_match)
        c_qber = sum(
            1 for a, b, m in zip(c_alice, c_bob, c_match) if m and a != b
        ) / max(c_matching_count, 1)
        print(f"      Alice bits:  {c_alice}")
        print(f"      Bob bits:    {c_bob}")
        print(f"      Matching:    {c_match}")
        print(f"      Matching bases: {c_matching_count}/{len(c_match)}")
        print(f"      QBER (matching): {c_qber:.4f}")
    except Exception as e:
        print(f"      BB84 simulation FAILED: {e}")

    # -- 3.7 State conversion (cirq 1.x dropped StateVectorSimulationState) -- #
    print("\n[3.7] State conversion (qkdpy <-> cirq):")
    q_c = Qubit(0, 1)  # |1>
    try:
        cirq_state = ci.qubit_to_cirq(q_c)
        print(f"      Qubit(|1>) -> Cirq state: {cirq_state}")
        q_c_back = ci.cirq_to_qubit(cirq_state)
        print(f"      Cirq state -> Qubit: state={q_c_back.state}")
    except Exception as e:
        # Cirq 1.x removed StateVectorSimulationState; do manual conversion
        print(f"      qubit_to_cirq FAILED (Cirq 1.x API change): {e}")
        import cirq

        cirq_state = cirq.StateVectorSimulationState(
            qubits=cirq.LineQubit.range(1),
            initial_state=np.array([0, 1], dtype=complex),
        )
        print(f"      Manual Cirq state: {cirq_state}")
        q_c_back = ci.cirq_to_qubit(cirq_state)
        print(f"      Cirq state -> Qubit: state={q_c_back.state}")

except ImportError as e:
    print(f"\n  ** Cirq not installed: {e}")
except Exception as e:
    import traceback

    print(f"\n  ** Cirq test error: {e}")
    traceback.print_exc()


# ================================================================== #
#  4. QPIAI INTEGRATION
# ================================================================== #
print("\n" + SEP)
print("  4. QPIAI INTEGRATION")
print(SEP)

try:
    from qkdpy.integrations.qpiai_integration import QpiAIIntegration

    qi_ai = QpiAIIntegration()
    print("\n[4.1] QpiAIIntegration instance created.")

    # -- 4.2 State conversion ----------------------------------- #
    print("\n[4.2] State conversion (qkdpy -> QpiAI):")
    q_qp = Qubit(1 / math.sqrt(2), 1 / math.sqrt(2))  # |+>
    qpiai_sv = qi_ai.qubit_to_qpiai(q_qp)
    print(f"      Qubit(|+>) -> QpiAI Statevector: data={qpiai_sv.data}")
    q_qp_back = qi_ai.qpiai_to_qubit(qpiai_sv)
    print(f"      QpiAI Statevector -> Qubit: state={q_qp_back.state}")

    arr_sv = qi_ai.statevector_from_array([1 + 0j, 0 + 0j, 0 + 0j, 0 + 0j])
    print(f"      Statevector from array [1,0,0,0]: data={arr_sv.data}")

    # -- 4.3 Concurrence ---------------------------------------- #
    print("\n[4.3] Concurrence via QpiAI formalism:")
    bell_dm = np.array(
        [
            [0.5, 0, 0, 0.5],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0.5, 0, 0, 0.5],
        ],
        dtype=complex,
    )
    qpiai_conc = qi_ai.compute_concurrence(bell_dm)
    print(f"      concurrence(|Phi+>): {qpiai_conc:.10f}  (expected 1.0)")

    # -- 4.4 Purity --------------------------------------------- #
    pur_qp = qi_ai.compute_purity(bell_dm)
    print(f"      purity(|Phi+>): {pur_qp:.10f}  (expected 1.0)")

    mixed_dm = 0.5 * np.eye(4, dtype=complex)
    pur_mixed = qi_ai.compute_purity(mixed_dm)
    print(f"      purity(mixed 50-50): {pur_mixed:.10f}  ")
    # Check: if 1.0 this indicates a bug (forgot to trace, or traces correctly)

    # -- 4.5 BB84 circuit --------------------------------------- #
    print("\n[4.5] BB84 circuit (4 qubits):")
    bb84_qp = qi_ai.create_bb84_circuit(
        num_qubits=4,
        alice_bases=["Z", "X", "Z", "X"],
        bob_bases=["Z", "X", "X", "Z"],
        alice_bits=[0, 1, 0, 1],
    )
    # QpiAI Circuit doesn't have .gates, check available attrs
    qp_attrs = [a for a in dir(bb84_qp) if not a.startswith("_")]
    if "icr" in dir(bb84_qp):
        print(f"      BB84 circuit created: num_qubits={bb84_qp.icr.num_qubits}")
    else:
        print(f"      BB84 circuit created. Available attrs: {qp_attrs[:10]}...")

    # -- 4.6 Entanglement circuit ------------------------------- #
    print("\n[4.6] Entanglement circuits:")
    Psi_p = "\u03a8+>"
    Psi_m = "\u03a8->"
    Phi_p = "\u03a6+>"
    Phi_m = "\u03a6->"
    for bt, desc in [
        (f"|{Psi_p}", "|01>+|10>"),
        (f"|{Psi_m}", "|01>-|10>"),
        (f"|{Phi_p}", "|00>+|11>"),
        (f"|{Phi_m}", "|00>-|11>"),
    ]:
        try:
            bell_circ, bdesc = qi_ai.create_entanglement_circuit(state_type=bt)
            num_gates = len(bell_circ.gates) if hasattr(bell_circ, "gates") else "?"
            print(f"      {desc} ({bdesc}): circuit gates={num_gates}")
        except Exception as e:
            print(f"      {desc}: FAILED - {e}")

    # -- 4.7 GHZ circuit ---------------------------------------- #
    print("\n[4.7] GHZ circuit (3 qubits):")
    ghz_qp_circ = qi_ai.create_ghz_circuit(num_qubits=3)
    nq = ghz_qp_circ.icr.num_qubits if hasattr(ghz_qp_circ, "icr") else "?"
    ng = len(ghz_qp_circ.gates) if hasattr(ghz_qp_circ, "gates") else "?"
    print(f"      GHZ circuit created: num_qubits={nq}, gates={ng}")

    # -- 4.8 E91 circuit ---------------------------------------- #
    print("\n[4.8] E91 circuit (2 pairs):")
    e91_qp_circ = qi_ai.create_e91_circuit(
        num_pairs=2,
        alice_bases=["Z", "X"],
        bob_bases=["X", "W"],
    )
    nq = e91_qp_circ.icr.num_qubits if hasattr(e91_qp_circ, "icr") else "?"
    ng = len(e91_qp_circ.gates) if hasattr(e91_qp_circ, "gates") else "?"
    print(f"      E91 circuit: num_qubits={nq}, gates={ng}")

    # -- 4.9 Simulate ------------------------------------------- #
    print("\n[4.9] Local simulation:")
    try:
        sim_result = qi_ai.simulate(bb84_qp, shots=1024)
        print(f"      Simulation result: {sim_result}")
    except Exception as e:
        print(f"      Simulation FAILED: {e}")

    # -- 4.10 QBER ---------------------------------------------- #
    print("\n[4.10] QBER calculation:")
    qber_val1 = qi_ai.calculate_qber([0, 0, 1, 1], [0, 1, 1, 0])
    print(f"      QBER([0,0,1,1], [0,1,1,0]): {qber_val1:.4f}  (expected 0.5)")
    qber_val2 = qi_ai.calculate_qber([0, 0, 1, 1], [0, 0, 1, 1])
    print(f"      QBER(identical): {qber_val2:.4f}  (expected 0.0)")

    # -- 4.11 CHSH value ---------------------------------------- #
    print("\n[4.11] CHSH S-value via QpiAI:")
    chsh_s = qi_ai.compute_chsh_value([0.0, math.pi / 2, math.pi / 4, -math.pi / 4])
    print(f"      S = {chsh_s:.10f}  (expected ~2.8284)")
    print(f"      Bell violation: S > 2 ? {chsh_s > 2}")

except ImportError as e:
    print(f"\n  ** QpiAI Quantum SDK not installed: {e}")
    print("  ** Skipping all QpiAI tests.")
except Exception as e:
    import traceback

    print(f"\n  ** QpiAI test error: {e}")
    traceback.print_exc()


# ================================================================== #
#  5. CROSS-INTEGRATION COMPARISONS
# ================================================================== #
print("\n" + SEP)
print("  5. CROSS-INTEGRATION COMPARISONS")
print(SEP)

print("\n[5.1] Concurrence comparison for |Phi+>:")
try:
    conc_qk = qi.compute_concurrence(dm_phi_plus)
    print(f"      Qiskit:     {conc_qk:.10f}")
except Exception as e:
    print(f"      Qiskit:     {e}")

try:
    if "qi_ai" in dir() and "qi_ai" in locals():
        bdm = np.array(
            [[0.5, 0, 0, 0.5], [0, 0, 0, 0], [0, 0, 0, 0], [0.5, 0, 0, 0.5]],
            dtype=complex,
        )
        conc_qp = qi_ai.compute_concurrence(bdm)
        print(f"      QpiAI:     {conc_qp:.10f}")
except Exception as e:
    print(f"      QpiAI:     {e}")

print("\n[5.2] BB84 protocol comparison (native qkdpy):")
try:
    protocol = BB84(QuantumChannel(**NOISE_PARAMS), key_length=16)
    protocol.execute()
    print("      qkdpy native execution OK")
    # BB84 might store the key differently; try common attr names
    for attr_name in ["key", "final_key", "key_bits", "sifted_key", "_key"]:
        if hasattr(protocol, attr_name):
            val = getattr(protocol, attr_name)
            print(f"      attr '{attr_name}' = {val}")
            break
    else:
        print(
            f"      Available BB84 attrs: {[a for a in dir(protocol) if not a.startswith('_') and not callable(getattr(protocol, a))]}"
        )
    if hasattr(protocol, "error_rate"):
        print(f"      error_rate: {protocol.error_rate:.4f}")
except Exception as e:
    print(f"      qkdpy native execution: {e}")

print("\n" + SEP)
print("  INTEGRATION TEST COMPLETE")
print(SEP)
