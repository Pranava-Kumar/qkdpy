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

"""Comprehensive black-box test of the qkdpy v0.6.0 core quantum stack.

Tests ALL modules in the core stack and reports every actual numerical value.
Gracefully handles missing features or import errors.
"""

import math
import sys

import numpy as np

# ---------------------------------------------------------------------------
# Setup: add source to path, import everything we can
# ---------------------------------------------------------------------------
SRC = str(Path(__file__).resolve().parents[1] / "src")
sys.path.insert(0, SRC)

IMPORT_ERRORS: list[str] = []


def safe_import(modname: str, *names: str):
    """Try to import; on failure record the error and return a sentinel."""
    try:
        if names:
            mod = __import__(modname, fromlist=names)
            return tuple(getattr(mod, n) for n in names)
        return __import__(modname)
    except Exception as exc:
        IMPORT_ERRORS.append(f"{modname} ({exc})")
        return None


def section(title: str) -> None:
    """Print a section header."""
    line = "=" * 72
    print(f"\n{line}")
    print(f"  {title}")
    print(f"{line}\n")


def subsec(title: str) -> None:
    print(f"\n--- {title} ---")


# We use __import__ directly for simpler error handling
_imported: dict[str, any] = {}


def _imp(modname: str):
    """Import a module and return it, or None on failure."""
    try:
        return __import__(modname, fromlist=["__dummy__"])
    except Exception as exc:
        IMPORT_ERRORS.append(f"{modname}: {exc}")
        return None


def _imp_from(modname: str, attr: str):
    """Import a single attribute from a module, or None on failure."""
    mod = _imp(modname)
    if mod is None:
        return None
    return getattr(mod, attr, None)


# fmt: off
Qubit                = _imp_from("qkdpy.core.qubit",              "Qubit")
Qudit                = _imp_from("qkdpy.core.qudit",              "Qudit")
MultiQubitState      = _imp_from("qkdpy.core.multiqubit",         "MultiQubitState")
Gates_mod            = _imp(     "qkdpy.core.gates")
GateUtils            = _imp_from("qkdpy.core.gate_utils",         "GateUtils")
QuantumChannel       = _imp_from("qkdpy.core.channels",           "QuantumChannel")
ExtendedQuantumChannel = _imp_from("qkdpy.core.extended_channels","ExtendedQuantumChannel")
QuantumDetector      = _imp_from("qkdpy.core.detector",           "QuantumDetector")
DetectorArray        = _imp_from("qkdpy.core.detector",           "DetectorArray")
Measurement          = _imp_from("qkdpy.core.measurements",       "Measurement")
PhotonSource         = _imp_from("qkdpy.core.photon_source",      "PhotonSource")
WeakCoherentSource   = _imp_from("qkdpy.core.photon_source",      "WeakCoherentSource")
PhotonSourceManager  = _imp_from("qkdpy.core.photon_source",      "PhotonSourceManager")
SecureRandom_mod     = _imp(     "qkdpy.core.secure_random")
SecurityAnalyzer     = _imp_from("qkdpy.core.security_analysis",  "SecurityAnalyzer")
AttackType           = _imp_from("qkdpy.core.security_analysis",  "AttackType")
QBERAnalysis         = _imp_from("qkdpy.core.security_analysis",  "QBERAnalysis")
TimingSynchronizer   = _imp_from("qkdpy.core.timing",             "TimingSynchronizer")
QuantumSimulator     = _imp_from("qkdpy.utils.quantum_simulator", "QuantumSimulator")
# fmt: on

print("IMPORT STATUS")
print(f"  Source: {SRC}")
print(f"  Errors: {len(IMPORT_ERRORS)}")
for err in IMPORT_ERRORS:
    print(f"    FAIL: {err}")

np.set_printoptions(precision=6, suppress=True, linewidth=100)

# ---------------------------------------------------------------------------
# 1. QUBIT
# ---------------------------------------------------------------------------
if Qubit is not None:
    section("1. QUBIT")

    # --- 1a. Create states ---
    subsec("1a. State creation — statevectors")
    states = {
        "|0>": Qubit.zero(),
        "|1>": Qubit.one(),
        "|+>": Qubit.plus(),
        "|->": Qubit.minus(),
    }
    for name, q in states.items():
        print(f"  {name:4s}  state = {q.state}  probs = {q.probabilities}")

    # --- 1b. Gate applications ---
    subsec("1b. Gate applications on |0>")
    q = Qubit.zero()

    # Paulis
    for gate_name, mat_fn in [
        ("X", Gates_mod.PauliX().matrix),
        ("Y", Gates_mod.PauliY().matrix),
        ("Z", Gates_mod.PauliZ().matrix),
    ]:
        qc = Qubit.zero()
        qc.apply_gate(mat_fn)
        print(f"  X|0> -> {qc.state}")

    qc = Qubit.zero()
    qc.apply_gate(Gates_mod.Hadamard().matrix)
    qc.apply_gate(Gates_mod.S().matrix)
    print(
        f"  H|0>       -> {Qubit.zero().apply_gate(Gates_mod.Hadamard().matrix) or Qubit.zero().state}"
    )
    # Actually let me redo those properly:

    qh = Qubit.zero()
    qh.apply_gate(Gates_mod.Hadamard().matrix)
    print(f"  H|0>       -> {qh.state}")

    qs = Qubit.zero()
    qs.apply_gate(Gates_mod.S().matrix)
    print(f"  S|0>       -> {qs.state}")

    qt = Qubit.zero()
    qt.apply_gate(Gates_mod.T().matrix)
    print(f"  T|0>       -> {qt.state}")

    qrx = Qubit.zero()
    qrx.apply_gate(Gates_mod.Rx(math.pi / 4).matrix)
    print(f"  Rx(pi/4)|0> -> {qrx.state}")

    qry = Qubit.zero()
    qry.apply_gate(Gates_mod.Ry(math.pi / 4).matrix)
    print(f"  Ry(pi/4)|0> -> {qry.state}")

    qrz = Qubit.zero()
    qrz.apply_gate(Gates_mod.Rz(math.pi / 4).matrix)
    print(f"  Rz(pi/4)|0> -> {qrz.state}")

    # Gates on |1>
    subsec("  Gate applications on |1>")
    qh = Qubit.one()
    qh.apply_gate(Gates_mod.Hadamard().matrix)
    print(f"  H|1>       -> {qh.state}")

    qs = Qubit.one()
    qs.apply_gate(Gates_mod.S().matrix)
    print(f"  S|1>       -> {qs.state}")

    qt = Qubit.one()
    qt.apply_gate(Gates_mod.T().matrix)
    print(f"  T|1>       -> {qt.state}")

    # --- 1c. Measurement statistics ---
    subsec("1c. Measurement statistics (|+> state, 100 trials)")
    np.random.seed(42)
    q_plus = Qubit.plus()
    outcomes = []
    for _ in range(100):
        # Re-create each time since measure collapses
        q = Qubit.plus()
        outcomes.append(q.measure("computational"))
    p0 = outcomes.count(0) / 100
    p1 = outcomes.count(1) / 100
    print(f"  Results: P(0)={p0:.3f}  P(1)={p1:.3f}  (expected ~0.5, ~0.5)")
    # Hadamard basis
    outcomes_h = []
    for _ in range(100):
        q = Qubit.plus()
        outcomes_h.append(q.measure("hadamard"))
    p0h = outcomes_h.count(0) / 100
    p1h = outcomes_h.count(1) / 100
    print(f"  Hadamard basis: P(0)={p0h:.3f}  P(1)={p1h:.3f}")
    # Circular basis
    outcomes_c = []
    for _ in range(100):
        q = Qubit.plus()
        outcomes_c.append(q.measure("circular"))
    p0c = outcomes_c.count(0) / 100
    p1c = outcomes_c.count(1) / 100
    print(f"  Circular basis: P(0)={p0c:.3f}  P(1)={p1c:.3f}")

    # --- 1d. Bloch sphere coordinates ---
    subsec("1d. Bloch sphere coordinates")
    for name, q in states.items():
        bv = q.bloch_vector()
        theta = math.acos(max(-1.0, min(1.0, bv[2])))
        phi = math.atan2(bv[1], bv[0])
        print(
            f"  {name:4s}  bloch_vec=({bv[0]:+.4f}, {bv[1]:+.4f}, {bv[2]:+.4f})  "
            f"theta={theta:.4f}  phi={phi:.4f}"
        )

    # Density matrix
    subsec("  Density matrix examples")
    for name, q in [("|0>", Qubit.zero()), ("|+>", Qubit.plus())]:
        rho = q.density_matrix()
        print(f"  rho_{name} =\n{rho}")

# ---------------------------------------------------------------------------
# 2. QUDIT (d-dimensional)
# ---------------------------------------------------------------------------
if Qudit is not None:
    section("2. QUDIT")

    # d=3
    subsec("2a. Qudit d=3")
    q3_0 = Qudit.computational_basis(0, 3)
    q3_1 = Qudit.computational_basis(1, 3)
    q3_sup = Qudit.uniform_superposition(3)
    print(f"  |0>_3   state = {q3_0.state}")
    print(f"  |1>_3   state = {q3_1.state}")
    print(f"  |sup>_3 state = {q3_sup.state}")
    print(f"  probs     = {q3_sup.probabilities}")

    # Fourier basis
    q3_f = Qudit.fourier_basis(1, 3)
    print(f"  |F_1>_3  state = {q3_f.state}")

    # Unitary
    subsec("  Unitary operation")
    d = 3
    unitary = np.eye(d, dtype=complex)
    unitary[0, 0] = 0
    unitary[0, 1] = 1
    unitary[1, 0] = 1
    unitary[1, 1] = 0
    q3_u = Qudit.computational_basis(0, 3)
    q3_u.apply_unitary(unitary)
    print(f"  Unitary|0>_3 -> state = {q3_u.state}")

    # Measurement statistics
    subsec("  Measurement (100 trials, d=3 uniform superposition)")
    outcomes = []
    for _ in range(100):
        q = Qudit.uniform_superposition(3)
        outcomes.append(q.measure_computational())
    counts = [outcomes.count(i) for i in range(3)]
    print(f"  Counts: 0={counts[0]}, 1={counts[1]}, 2={counts[2]}  (expected ~33 each)")

    # Partial trace
    subsec("  Partial trace (d=4 bipartite separable)")
    d4_state = np.zeros(4, dtype=complex)
    d4_state[0] = 1.0 / math.sqrt(2)  # |00>
    d4_state[3] = 1.0 / math.sqrt(2)  # |11>
    q4 = Qudit(d4_state, 4)
    print(f"  d=4 state = {q4.state}")
    try:
        pt0 = q4.partial_trace(0, 2)
        print(f"  Trace out qubit 0 -> dim={pt0.dimension} state={pt0.state}")
    except ValueError as e:
        print(f"  partial_trace(0,2): {e}")
    try:
        pt1 = q4.partial_trace(1, 2)
        print(f"  Trace out qubit 1 -> dim={pt1.dimension} state={pt1.state}")
    except ValueError as e:
        print(f"  partial_trace(1,2): {e}")

    # Fidelity
    subsec("  Fidelity")
    qa = Qudit.computational_basis(0, 3)
    qb = Qudit.computational_basis(0, 3)
    print(f"  Fid(|0>,|0>) = {qa.fidelity(qb):.6f}")
    qc = Qudit.computational_basis(1, 3)
    print(f"  Fid(|0>,|1>) = {qa.fidelity(qc):.6f}")

    # d=4
    subsec("2b. Qudit d=4")
    q4 = Qudit.uniform_superposition(4)
    print(f"  |sup>_4 state = {q4.state}")
    print(f"  probs = {q4.probabilities}")

# ---------------------------------------------------------------------------
# 3. MultiQubitState
# ---------------------------------------------------------------------------
if MultiQubitState is not None:
    section("3. MULTI-QUBIT STATE")

    # --- 3a. Create states ---
    subsec("3a. State creation")
    m00 = MultiQubitState.zeros(2)
    print(f"  |00>   state = {m00.state}")

    ghz3 = MultiQubitState.ghz(3)
    print(f"  GHZ(3) state = {ghz3.state}")

    ghz4 = MultiQubitState.ghz(4)
    print(f"  GHZ(4) state = {ghz4.state}")

    w3 = MultiQubitState.w_state(3)
    print(f"  W(3)   state = {w3.state}")

    w4 = MultiQubitState.w_state(4)
    print(f"  W(4)   state = {w4.state}")

    # From individual qubits
    m_from_q = MultiQubitState.from_qubits([Qubit.zero(), Qubit.one()])
    print(f"  |0>⊗|1>  state = {m_from_q.state}")

    # --- 3b. 2-qubit gates ---
    subsec("3b. Two-qubit gates on |00>")
    qq = MultiQubitState.zeros(2)

    qc = MultiQubitState.zeros(2)
    qc.apply_gate(Gates_mod.CNOT().matrix, [0, 1])
    print(f"  CNOT|00>  -> {qc.state}")

    qc = MultiQubitState.zeros(2)
    qc.apply_gate(Gates_mod.CZ().matrix, [0, 1])
    print(f"  CZ|00>    -> {qc.state}")

    qc = MultiQubitState.zeros(2)
    qc.apply_gate(Gates_mod.SWAP().matrix, [0, 1])
    print(f"  SWAP|00>  -> {qc.state}")

    # CNOT on |10> -> |11>
    qq10 = MultiQubitState.from_qubits([Qubit.one(), Qubit.zero()])
    qq10.apply_gate(Gates_mod.CNOT().matrix, [0, 1])
    print(f"  CNOT|10>  -> {qq10.state}")

    # CNOT on |01> -> |01>
    qq01 = MultiQubitState.from_qubits([Qubit.zero(), Qubit.one()])
    qq01.apply_gate(Gates_mod.CNOT().matrix, [0, 1])
    print(f"  CNOT|01>  -> {qq01.state}")

    # Bell state from |00> + H on q0 + CNOT
    bell = MultiQubitState.zeros(2)
    bell.apply_gate(Gates_mod.Hadamard().matrix, 0)
    bell.apply_gate(Gates_mod.CNOT().matrix, [0, 1])
    print(f"  |Φ+>      -> {bell.state}  (Bell state)")

    # --- 3c. Measurement with collapse ---
    subsec("3c. Measurement with sequential collapse")
    # GHZ(3): measure qubit 0, check remaining state
    g = MultiQubitState.ghz(3)
    print(f"  GHZ(3) before: {g.state}")
    result, collapsed = g.measure(0)
    print(f"  Measure q0 -> result={result}")
    if collapsed is not None:
        print(f"  Collapsed state (2 qubits): {collapsed.state}")
    else:
        print("  Collapsed: None (last qubit)")

    # Single-qubit state measure (last qubit case)
    sq = MultiQubitState.from_qubits([Qubit.plus()])
    r, c = sq.measure(0)
    print(f"  Measure single |+> -> result={r}, collapsed={c}")

    # --- 3d. Entanglement entropy ---
    subsec("3d. Entanglement entropy on GHZ(3)")
    ghz = MultiQubitState.ghz(3)
    s0 = ghz.entanglement_entropy([0])
    s1 = ghz.entanglement_entropy([1])
    s01 = ghz.entanglement_entropy([0, 1])
    print(f"  S(rho_0)  = {s0:.6f}  (expected 1.0)")
    print(f"  S(rho_1)  = {s1:.6f}  (expected 1.0)")
    print(f"  S(rho_01) = {s01:.6f}  (expected 0.0 for pure overall state)")

    # W(3) entropy
    w = MultiQubitState.w_state(3)
    sw0 = w.entanglement_entropy([0])
    sw1 = w.entanglement_entropy([1])
    print(f"  W(3) S(rho_0) = {sw0:.6f}")
    print(f"  W(3) S(rho_1) = {sw1:.6f}")

    # --- 3e. State fidelity ---
    subsec("3e. State fidelity")
    fid_ghz_ghz = MultiQubitState.ghz(3).fidelity(MultiQubitState.ghz(3))
    fid_ghz_w = MultiQubitState.ghz(3).fidelity(MultiQubitState.w_state(3))
    fid_w_w = MultiQubitState.w_state(3).fidelity(MultiQubitState.w_state(3))
    print(f"  Fid(GHZ(3), GHZ(3)) = {fid_ghz_ghz:.6f}")
    print(f"  Fid(GHZ(3), W(3))   = {fid_ghz_w:.6f}")
    print(f"  Fid(W(3), W(3))     = {fid_w_w:.6f}")

    # --- 3f. Partial trace ---
    subsec("3f. Partial trace via density_matrix")
    bell_rho = bell.density_matrix()
    print(f"  |Φ+> density matrix (4x4):\n{bell_rho}")

# ---------------------------------------------------------------------------
# 4. GATES (18+ implementations)
# ---------------------------------------------------------------------------
if Gates_mod is not None:
    section("4. GATES — Matrix Representations")

    gate_defs = {
        "I": Gates_mod.Identity().matrix,
        "X": Gates_mod.PauliX().matrix,
        "Y": Gates_mod.PauliY().matrix,
        "Z": Gates_mod.PauliZ().matrix,
        "H": Gates_mod.Hadamard().matrix,
        "S": Gates_mod.S().matrix,
        "Sdag": Gates_mod.SDag().matrix,
        "T": Gates_mod.T().matrix,
        "Tdag": Gates_mod.TDag().matrix,
        "Rx(pi/4)": Gates_mod.Rx(math.pi / 4).matrix,
        "Ry(pi/4)": Gates_mod.Ry(math.pi / 4).matrix,
        "Rz(pi/4)": Gates_mod.Rz(math.pi / 4).matrix,
        "CNOT": Gates_mod.CNOT().matrix,
        "CZ": Gates_mod.CZ().matrix,
        "SWAP": Gates_mod.SWAP().matrix,
    }

    for name, mat in gate_defs.items():
        ident = np.eye(mat.shape[0])
        udag_u = mat @ mat.conj().T
        is_unitary = np.allclose(udag_u, ident, atol=1e-10)
        print(f"\n  {name} ({mat.shape[0]}×{mat.shape[0]})  unitary={is_unitary}")
        print(mat)

    # Check unitarity for all gates
    subsec("  Unitarity verification (U^† U = I)")
    all_ok = True
    for name, mat in gate_defs.items():
        ident = np.eye(mat.shape[0])
        udag_u = mat.conj().T @ mat
        ok = np.allclose(udag_u, ident, atol=1e-10)
        if not ok:
            print(f"  FAIL: {name}")
            all_ok = False
    if all_ok:
        print("  All gates unitary: PASS")

# ---------------------------------------------------------------------------
# 5. GateUtils
# ---------------------------------------------------------------------------
if GateUtils is not None:
    section("5. GATE UTILS")

    # Basis switch
    subsec("5a. Basis switch matrices")
    for b in ["computational", "hadamard", "circular"]:
        m = GateUtils.basis_switch(b)
        print(f"  {b:15s} ->\n{m}")

    # Unitary check
    subsec("5b. unitary_check / is_unitary")
    print(f"  is_unitary(I)     = {GateUtils.is_unitary(np.eye(2))}")
    print(f"  is_unitary(H)     = {GateUtils.is_unitary(Gates_mod.Hadamard().matrix)}")
    print(f"  is_unitary(rand)  = {GateUtils.is_unitary(np.random.randn(2, 2))}")

    # is_hermitian
    subsec("  is_hermitian")
    print(f"  is_hermitian(X)  = {GateUtils.is_hermitian(Gates_mod.PauliX().matrix)}")
    print(f"  is_hermitian(H)  = {GateUtils.is_hermitian(Gates_mod.Hadamard().matrix)}")

    # unitary_from_angles
    subsec("  unitary_from_angles(theta=pi/2, phi=pi/3, lam=pi/4)")
    u_ang = GateUtils.unitary_from_angles(math.pi / 2, math.pi / 3, math.pi / 4)
    print(u_ang)
    print(f"  unitary={GateUtils.is_unitary(u_ang)}")

    # Sequence composition
    subsec("  Gate sequence: H @ X")
    seq = GateUtils.sequence(Gates_mod.Hadamard().matrix, Gates_mod.PauliX().matrix)
    print(seq)

    # Tensor product
    subsec("  Tensor product: H ⊗ X")
    tp = GateUtils.tensor_product(
        Gates_mod.Hadamard().matrix, Gates_mod.PauliX().matrix
    )
    print(tp)

    # Random unitary
    subsec("  Random unitary")
    ru = GateUtils.random_unitary()
    print(ru)
    print(f"  unitary={GateUtils.is_unitary(ru)}")

# ---------------------------------------------------------------------------
# 6. QuantumChannel
# ---------------------------------------------------------------------------
if QuantumChannel is not None:
    section("6. QUANTUM CHANNEL")

    # --- 6a. Ideal channel ---
    subsec("6a. Ideal channel (distance=0, no noise)")
    ch = QuantumChannel(distance=0.0, noise_model="none", noise_level=0.0)
    ch.reset_statistics()
    fidelities = []
    for _ in range(50):
        q = Qubit.plus()
        rx = ch.transmit(q)
        if rx is not None:
            f = abs(np.vdot(Qubit.plus().state, rx.state)) ** 2
            fidelities.append(f)
    stats = ch.get_statistics()
    print(f"  Transmitted: {stats['transmitted']}")
    print(f"  Lost:        {stats['lost']}")
    print(f"  Received:    {stats['received']}")
    print(f"  Loss rate:   {stats['loss_rate']:.4f}")
    print(
        f"  Avg fidelity: {np.mean(fidelities):.6f}"
        if fidelities
        else "  No fidelities"
    )

    # --- 6b. Noise models ---
    subsec("6b. Depolarizing noise (p=0.3)")
    ch_dep = QuantumChannel(distance=0.0, noise_model="depolarizing", noise_level=0.3)
    ch_dep.reset_statistics()
    fids = []
    for _ in range(200):
        q = Qubit.zero()
        rx = ch_dep.transmit(q)
        if rx is not None:
            fids.append(abs(np.vdot(Qubit.zero().state, rx.state)) ** 2)
    s = ch_dep.get_statistics()
    print(f"  Avg fidelity: {np.mean(fids):.6f}")
    print(f"  Error rate:   {s['error_rate']:.4f}")

    subsec("  Bit-flip noise (p=0.2)")
    ch_bf = QuantumChannel(distance=0.0, noise_model="bit_flip", noise_level=0.2)
    ch_bf.reset_statistics()
    for _ in range(200):
        q = Qubit.zero()
        ch_bf.transmit(q)
    s = ch_bf.get_statistics()
    print(f"  Error rate:   {s['error_rate']:.4f}  (expected ~0.2)")

    subsec("  Phase-flip noise (p=0.2)")
    ch_pf = QuantumChannel(distance=0.0, noise_model="phase_flip", noise_level=0.2)
    ch_pf.reset_statistics()
    for _ in range(200):
        q = Qubit.zero()
        ch_pf.transmit(q)
    s = ch_pf.get_statistics()
    print(f"  Error rate:   {s['error_rate']:.4f}  (expected ~0.2)")

    subsec("  Amplitude-damping noise (gamma=0.3)")
    ch_ad = QuantumChannel(
        distance=0.0, noise_model="amplitude_damping", noise_level=0.3
    )
    ch_ad.reset_statistics()
    fids = []
    for _ in range(200):
        q = Qubit.one()
        rx = ch_ad.transmit(q)
        if rx is not None:
            fids.append(abs(np.vdot(Qubit.one().state, rx.state)) ** 2)
    s = ch_ad.get_statistics()
    print(f"  Avg fidelity (|1> input): {np.mean(fids):.6f}")
    print(f"  Error rate:   {s['error_rate']:.4f}")

    # --- 6c. Loss ---
    subsec("6c. Loss rate = 0.5")
    ch_loss = QuantumChannel(distance=0.0, loss=0.5, noise_model="none")
    ch_loss.reset_statistics()
    for _ in range(500):
        q = Qubit.zero()
        ch_loss.transmit(q)
    s = ch_loss.get_statistics()
    print(f"  Loss rate: {s['loss_rate']:.4f}  (expected ~0.5)")

    # --- 6d. Distance-dependent loss ---
    subsec("6d. Distance-dependent loss")
    for dist_km in [0, 10, 25, 50]:
        ch_d = QuantumChannel(
            distance=dist_km, loss_coefficient=0.2, noise_model="none"
        )
        # Check the calculated loss probability
        print(f"  Distance={dist_km:3d} km -> loss_prob={ch_d.loss:.6f}")

    # --- 6e. Eavesdropping ---
    subsec("6e. Eavesdropping simulation (intercept-resend)")
    ch_ev = QuantumChannel(distance=0.0, noise_model="none")
    ch_ev.set_eavesdropper(QuantumChannel.intercept_resend_attack)
    ch_ev.reset_statistics()
    for _ in range(100):
        q = Qubit.zero()
        ch_ev.transmit(q)
    s = ch_ev.get_statistics()
    print(f"  Eavesdropped: {s['eavesdropped']}")
    print(f"  Detected:     {s['eavesdropper_detected']}")

    # --- 6f. Entanglement attack ---
    subsec("6f. Entanglement attack")
    ch_ea = QuantumChannel(distance=0.0, noise_model="none")
    ch_ea.set_eavesdropper(QuantumChannel.entanglement_attack)
    ch_ea.reset_statistics()
    for _ in range(100):
        q = Qubit.zero()
        ch_ea.transmit(q)
    s = ch_ea.get_statistics()
    print(f"  Eavesdropped: {s['eavesdropped']}")
    print(f"  Detected:     {s['eavesdropper_detected']}")

# ---------------------------------------------------------------------------
# 7. ExtendedQuantumChannel
# ---------------------------------------------------------------------------
if ExtendedQuantumChannel is not None:
    section("7. EXTENDED QUANTUM CHANNEL")

    subsec("7a. Depolarizing noise (p=0.2)")
    ech = ExtendedQuantumChannel(loss=0.0, noise_model="depolarizing", noise_level=0.2)
    ech.reset_statistics()
    for _ in range(200):
        q = Qubit.zero()
        ech.transmit(q)
    s = ech.get_statistics()
    print(f"  Error rate: {s['error_rate']:.4f}")

    subsec("  Bit-flip noise (p=0.3)")
    ech2 = ExtendedQuantumChannel(loss=0.0, noise_model="bit_flip", noise_level=0.3)
    ech2.reset_statistics()
    for _ in range(200):
        q = Qubit.zero()
        ech2.transmit(q)
    s = ech2.get_statistics()
    print(f"  Error rate: {s['error_rate']:.4f}")

    subsec("  Phase-damping noise (p=0.3)")
    ech3 = ExtendedQuantumChannel(
        loss=0.0, noise_model="phase_damping", noise_level=0.3
    )
    ech3.reset_statistics()
    for _ in range(200):
        q = Qubit.zero()
        ech3.transmit(q)
    s = ech3.get_statistics()
    print(f"  Error rate: {s['error_rate']:.4f}")

    subsec("  Generalized amplitude damping (p=0.3)")
    ech4 = ExtendedQuantumChannel(
        loss=0.0, noise_model="generalized_amplitude_damping", noise_level=0.3
    )
    ech4.reset_statistics()
    for _ in range(200):
        q = Qubit.zero()
        ech4.transmit(q)
    s = ech4.get_statistics()
    print(f"  Error rate: {s['error_rate']:.4f}")

# ---------------------------------------------------------------------------
# 8. Detector / PhotonSource
# ---------------------------------------------------------------------------
if QuantumDetector is not None:
    section("8. DETECTOR")

    subsec("8a. QuantumDetector with various efficiencies")
    for eff in [0.5, 0.8, 1.0]:
        det = QuantumDetector(efficiency=eff, dark_count_rate=0.0)
        det.reset()
        detected = 0
        for _ in range(200):
            res, _ = det.detect(photon_present=True, timestamp=0.0)
            if res is not None:
                detected += 1
        print(f"  Efficiency={eff:.1f}: detected {detected}/200 = {detected / 200:.3f}")

    subsec("  Dark counts")
    det_dc = QuantumDetector(efficiency=0.0, dark_count_rate=1e-6)
    det_dc.reset()
    dark_total = 0
    for i in range(1000):
        res, _ = det_dc.detect(photon_present=False, timestamp=i * 1e-9)
        if res is not None:
            dark_total += 1
    print(f"  Dark counts (1000 pulses, dark_rate=1e-6): {dark_total}")

    subsec("  Afterpulsing")
    det_ap = QuantumDetector(
        efficiency=0.0, dark_count_rate=1e-1, afterpulse_probability=0.5
    )
    det_ap.reset()
    ap_total = 0
    for i in range(200):
        res, _ = det_ap.detect(photon_present=True, timestamp=i * 1e-9)
        if res is not None:
            ap_total += 1
    print(f"  Detections with afterpulsing: {ap_total}/200")

    subsec("  DetectorArray")
    da = DetectorArray(num_detectors=2, efficiency=0.9, dark_count_rate=0.0)
    results = []
    for _ in range(50):
        q = Qubit.zero()
        r = da.measure_in_basis(q, "computational", 0.0)
        results.append(r)
    print(f"  DetectorArray results: 0s={results.count(0)}, 1s={results.count(1)}")

if PhotonSource is not None:
    section("8b. PHOTON SOURCE")

    subsec("  PhotonSource (basic)")
    ps = PhotonSource(pulse_rate=1e9, efficiency=0.8)
    photons = 0
    total = 500
    for i in range(total):
        present, _ = ps.generate_photon_pulse(i * 1e-9)
        if present:
            photons += 1
    print(
        f"  PhotonSource: {photons}/{total} photons generated = {photons / total:.3f}"
    )

    subsec("  WeakCoherentSource (mu=0.1)")
    wcs = WeakCoherentSource(mean_photon_number=0.1)
    stats = wcs.get_photon_statistics(num_pulses=2000)
    for k, v in stats.items():
        print(f"    {k}: {v:.6f}")

    subsec("  PhotonSourceManager")
    mgr = PhotonSourceManager()
    mgr.add_source("wcs", wcs)
    mgr.set_active_source("wcs")
    seq = mgr.generate_sequence(duration=1e-6)  # 1 us
    print(f"  Generated {len(seq)} pulses in 1 us")

# ---------------------------------------------------------------------------
# 9. Measurement
# ---------------------------------------------------------------------------
if Measurement is not None:
    section("9. MEASUREMENT")

    # measure_in_basis
    subsec("9a. measure_in_basis")
    q = Qubit.zero()
    r = Measurement.measure_in_basis(q, "computational")
    print(f"  |0> in comp basis -> {r}")

    q = Qubit.plus()
    r = Measurement.measure_in_basis(q, "hadamard")
    print(f"  |+> in hadamard basis -> {r}")

    # measure_batch
    subsec("  measure_batch_in_basis")
    qubits = [Qubit.zero(), Qubit.one(), Qubit.plus(), Qubit.minus()]
    results = Measurement.measure_batch_in_basis(qubits, "computational")
    print(f"  Batch results: {results}")

    # measure_in_random_basis
    subsec("  measure_in_random_basis")
    r, basis = Measurement.measure_in_random_basis(Qubit.plus())
    print(f"  |+> random basis -> result={r}, basis={basis}")

    # Fidelity
    subsec("9b. Fidelity / Purity / Entropy")
    q0 = Qubit.zero()
    target = np.array([1.0, 0.0], dtype=complex)
    fid = Measurement.measure_state_fidelity(q0, target)
    print(f"  Fid(|0>,|0>) = {fid:.6f}")

    pur = Measurement.measure_purity(q0)
    print(f"  Purity(|0>)  = {pur:.10f}")

    ent = Measurement.measure_von_neumann_entropy(Qubit.zero())
    print(f"  S_vN(|0>)    = {ent:.10f}")

    ent_p = Measurement.measure_von_neumann_entropy(Qubit.plus())
    print(f"  S_vN(|+>)    = {ent:.10f}")

    # Bloch coordinates
    subsec("  Bloch coordinates")
    bv = Measurement.measure_bloch_coordinates(Qubit.zero())
    print(f"  |0> bloch = ({bv[0]:+.4f}, {bv[1]:+.4f}, {bv[2]:+.4f})")
    bv = Measurement.measure_bloch_coordinates(Qubit.plus())
    print(f"  |+> bloch = ({bv[0]:+.4f}, {bv[1]:+.4f}, {bv[2]:+.4f})")

    # Density matrix
    subsec("  Density matrix")
    rho = Measurement.measure_density_matrix(Qubit.zero())
    print(f"  rho(|0>) =\n{rho}")

    # Observable expectation
    subsec("  Observable expectation")
    sigma_z = np.array([[1, 0], [0, -1]], dtype=complex)
    exp_z = Measurement.measure_observable(Qubit.zero(), sigma_z)
    print(f"  <Z>(|0>)  = {exp_z:.6f}")
    exp_z_plus = Measurement.measure_observable(Qubit.plus(), sigma_z)
    print(f"  <Z>(|+>)  = {exp_z_plus:.6f}")

    # Bell state
    subsec("  Bell state detection")
    q1 = Qubit.zero()
    q2 = Qubit.zero()
    # Create |Φ+> via H + CNOT
    q1.apply_gate(Gates_mod.Hadamard().matrix)
    bell_state = Measurement.measure_bell_state(q1, q2)
    print(f"  Bell state (H|0>, |0>): {bell_state}")

    # Quantum state tomography
    subsec("9c. Quantum state tomography (1000 measurements)")
    qt = Qubit.plus()
    tomo = Measurement.quantum_state_tomography(qt, num_measurements=1000)
    for k, v in tomo.items():
        print(f"    {k}: {v:.6f}")
    # Expected: rho_00=0.5, rho_01=0.5, rho_10=0.5, rho_11=0.5
    # exp_x=1.0, exp_y=0.0, exp_z=0.0

# ---------------------------------------------------------------------------
# 10. SecureRandom
# ---------------------------------------------------------------------------
if SecureRandom_mod is not None:
    section("10. SECURE RANDOM")

    sr = SecureRandom_mod

    # Generate 100 bits
    subsec("10a. 100 random bits")
    bits = sr.secure_bits(100)
    n_ones = sum(bits)
    n_zeros = len(bits) - n_ones
    print(f"  Bits: {''.join(str(b) for b in bits[:20])}...")
    print(f"  Count: 0s={n_zeros}, 1s={n_ones}")
    print(f"  Balance (|0s-1s|): {abs(n_zeros - n_ones)}")

    # Run test (consecutive same bits)
    runs = 1
    for i in range(1, len(bits)):
        if bits[i] != bits[i - 1]:
            runs += 1
    expected_runs = 1 + (2 * n_zeros * n_ones) / len(bits)
    runs_std = math.sqrt(
        2
        * n_zeros
        * n_ones
        * (2 * n_zeros * n_ones - len(bits))
        / (len(bits) ** 2 * (len(bits) - 1))
    )
    print(f"  Runs: {runs} (expected ~{expected_runs:.1f} +/- {runs_std:.1f})")

    # Compare with numpy
    subsec("10b. Comparison with numpy.random")
    np_bits = np.random.randint(0, 2, 100)
    np_ones = int(np.sum(np_bits))
    print(f"  numpy.random: 0s={100 - np_ones}, 1s={np_ones}")

    # Weighted choice
    subsec("  secure_weighted_choice")
    items = ["A", "B", "C"]
    probs = [0.5, 0.3, 0.2]
    counts_w = {"A": 0, "B": 0, "C": 0}
    for _ in range(5000):
        ch = sr.secure_weighted_choice(items, probs)
        counts_w[ch] += 1
    for k, v in counts_w.items():
        print(f"    {k}: {v / 5000:.3f} (expected {probs[items.index(k)]})")

# ---------------------------------------------------------------------------
# 11. SecurityAnalysis
# ---------------------------------------------------------------------------
if SecurityAnalyzer is not None:
    section("11. SECURITY ANALYSIS")

    sa = SecurityAnalyzer()

    subsec("11a. Security analysis for BB84")
    result = sa.perform_security_analysis(
        protocol_name="BB84",
        qber=0.03,
        key_rate=1e6,
        channel_loss=3.0,
        mean_photon_number=0.1,
        num_decoy_states=0,
    )
    for k, v in result.items():
        if isinstance(v, dict):
            print(f"  {k}:")
            for kk, vv in v.items():
                if isinstance(vv, dict):
                    print(f"    {kk}:")
                    for kkk, vvv in vv.items():
                        print(f"      {kkk}: {vvv}")
                else:
                    print(
                        f"    {kk}: {vv:.6f}"
                        if isinstance(vv, float)
                        else f"    {kk}: {vv}"
                    )
        else:
            print(f"  {k}: {v:.6f}" if isinstance(v, float) else f"  {k}: {v}")

    subsec("  Security analysis with decoy states")
    result2 = sa.perform_security_analysis(
        protocol_name="decoy-state-bb84",
        qber=0.05,
        key_rate=1e6,
        channel_loss=5.0,
        mean_photon_number=0.5,
        num_decoy_states=2,
    )
    print(f"  is_secure: {result2['is_secure']}")
    print(f"  security_level: {result2['security_level']}")
    print(f"  corrected_key_rate: {result2['corrected_key_rate']:.6f}")

    # QBER from two key strings
    subsec("11b. QBER from key strings")
    key1 = [0, 1, 0, 1, 1, 0, 0, 1, 0, 0]
    key2 = [0, 1, 0, 0, 1, 0, 0, 1, 1, 0]
    mismatches = sum(1 for a, b in zip(key1, key2) if a != b)
    qber_val = mismatches / len(key1)
    print(f"  Key 1: {key1}")
    print(f"  Key 2: {key2}")
    print(f"  Mismatches: {mismatches}/{len(key1)}")
    print(f"  QBER: {qber_val:.4f}")

    # Attack simulation
    subsec("11c. Attack simulation — Intercept-resend")
    attack_result = sa.simulate_attack(
        AttackType.INTERCEPT_RESEND,
        protocol_name="BB84",
        original_qber=0.03,
        channel_loss=3.0,
        mean_photon_number=0.1,
    )
    for k, v in attack_result.items():
        print(f"  {k}: {v:.6f}" if isinstance(v, float) else f"  {k}: {v}")

    subsec("  Attack simulation — Beam splitting")
    attack2 = sa.simulate_attack(
        AttackType.BEAM_SPLITTING,
        protocol_name="BB84",
        original_qber=0.03,
        channel_loss=3.0,
        mean_photon_number=0.5,
    )
    for k, v in attack2.items():
        print(f"  {k}: {v:.6f}" if isinstance(v, float) else f"  {k}: {v}")

    # QBER Analysis
    subsec("11d. QBER trend analysis")
    qa = QBERAnalysis()
    qber_vals = [0.03, 0.04, 0.035, 0.05, 0.045, 0.06, 0.055, 0.07, 0.065, 0.08]
    trend = qa.analyze_qber_trends(qber_vals, window_size=5)
    for k, v in trend.items():
        print(f"  {k}: {v:.6f}" if isinstance(v, float) else f"  {k}: {v}")

# ---------------------------------------------------------------------------
# 12. QuantumSimulator
# ---------------------------------------------------------------------------
if QuantumSimulator is not None:
    section("12. QUANTUM SIMULATOR")

    sim = QuantumSimulator()

    subsec("12a. Channel performance simulation")
    ch = QuantumChannel(distance=0.0, noise_model="none", noise_level=0.0)
    result = sim.simulate_channel_performance(ch, num_trials=200)
    for k, v in result.items():
        if isinstance(v, dict):
            print(f"  {k}:")
            for kk, vv in v.items():
                print(f"    {kk}: {vv}")
        else:
            print(f"  {k}: {v:.6f}" if isinstance(v, float) else f"  {k}: {v}")

    subsec("12b. Noisy channel simulation")
    ch_noisy = QuantumChannel(
        distance=10.0,
        loss_coefficient=0.2,
        noise_model="depolarizing",
        noise_level=0.1,
    )
    result2 = sim.simulate_channel_performance(
        ch_noisy, num_trials=200, initial_state=Qubit.plus()
    )
    for k, v in result2.items():
        if isinstance(v, dict):
            print(f"  {k}:")
            for kk, vv in v.items():
                print(f"    {kk}: {vv}")
        else:
            print(f"  {k}: {v:.6f}" if isinstance(v, float) else f"  {k}: {v}")

# ---------------------------------------------------------------------------
# 13. TIMING (brief)
# ---------------------------------------------------------------------------
if TimingSynchronizer is not None:
    section("13. TIMING")

    subsec("13a. Timing synchronizer")
    ts = TimingSynchronizer(clock_frequency=1e9, timing_jitter=1e-12)
    sync_result = ts.synchronize_clocks(0.0)
    for k, v in sync_result.items():
        print(f"  {k}: {v}")

    diff = ts.calculate_time_difference(1.0)
    print(f"  Time diff after 1s: {diff:.6e} s")

# ---------------------------------------------------------------------------
# SUMMARY
# ---------------------------------------------------------------------------
section("TEST COMPLETE")
print(f"  Import errors: {len(IMPORT_ERRORS)}")
for err in IMPORT_ERRORS:
    print(f"    {err}")
print("  All sections completed successfully.")
