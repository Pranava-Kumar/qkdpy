# qpiai-qkd — qkdpy ↔ QpiAI Quantum SDK companion

A companion package that maps **qkdpy** QKD protocols onto the **QpiAI Quantum
SDK** and models the interchange in IEC/ETSI QKD terms. Install it together with
qkdpy:

```bash
pip install qkdpy[qpiai]
```

It is importable as `qkdpy.integrations.qpiai_qkd`. (The standalone class
`QpiAIIntegration` is still importable from its historical path
`qkdpy.integrations.qpiai_integration`.)

> **Honesty note.** This package wraps the real `qpiai_quantum` SDK as it exists
> locally. Local circuit simulation needs a `QPIAI_API_KEY` (or `API_KEY`). The
> QpiAI **cloud** backend requires `QPIAI_API_KEY`; we surface the SDK's real
> errors rather than masking them, and we do **not** claim cloud runs are
> verified here — there is no backend credential in this repository. The physics
> and optimizer modules are models with stated assumptions; they estimate, they
> do not guarantee, secret-key rates.

---

## 1. Protocols implemented

| Protocol | What it models | Builder |
|----------|----------------|---------|
| **BB84** | Prepare-and-measure, Alice & Bob choose Z/X bases | `create_bb84_circuit` |
| **E91** | Entanglement-based, Z/X/W bases, CHSH test | `create_e91_circuit` |
| **Bell / entanglement** | One of Ψ⁺, Ψ⁻, Φ⁺, Φ⁻ | `create_entanglement_circuit` |
| **GHZ** | Multi-party `(\|0…0⟩ + \|1…1⟩)/√2` | `create_ghz_circuit` |

Each builder returns a real `qpiai_quantum.Circuit`; you can simulate it or
submit it. The companion also computes the figures a QKD researcher reads off a
run:

- **QBER** — `calculate_qber(alice_bits, bob_bits)`
- **CHSH** — `compute_chsh_value([a, a', b, b'])` (Tsirelson bound `2√2 ≈ 2.828`)
- **Concurrence** — `compute_concurrence(state)` (Wootters formula; 1.0 for a
  Bell state, 0.0 for a separable state)
- **Purity** — `compute_purity(state)` (`Tr(ρ²)`; 1.0 = pure)

```python
from qkdpy.integrations.qpiai_qkd import QpiAIIntegration, Protocols

qi = QpiAIIntegration()
circuit = qi.create_bb84_circuit(num_qubits=4)
result = qi.simulate(circuit)            # needs QPIAI_API_KEY

p = Protocols(qi)
bell, desc = p.bell("|Φ+>")
print(desc, "concurrence:", p.concurrence(bell_over_dm))
print("CHSH S:", p.chsh([0, np.pi/4, np.pi/8, 3*np.pi/8]))
```

---

## 2. Satellite / atmospheric physics

Free-space QKD link performance is bounded by turbulence and beam propagation.
`map_satellite_link` wraps qkdpy's real physics modules:

- `core.atmospheric.turbulence` — Hufnagel–Valley `Cn²`, Fried parameter `r₀`,
  Rytov variance, scintillation index.
- `network.atmospheric_physics` — MODTRAN band transmittance, stray-light count
  rate, up/down-link direction factor.

```python
from qkdpy.integrations.qpiai_qkd import map_satellite_link

link = map_satellite_link(
    wavelength_nm=1550,
    slant_range_km=1000,
    telescope_diameter_m=0.3,
    is_night=True,
)
print(link.total_link_loss_db, link.fried_parameter_m)
```

**Model assumptions (stated, not hidden):** single-scattering / Kolmogorov
turbulence, clear-sky MODTRAN band, representative point `Cn²` at the path
midpoint. The result is an *estimate of expected loss*, not a guaranteed key
rate. Validate against measured link budgets before relying on it.

---

## 3. QpiAI bridge

What maps to the QpiAI Quantum SDK:

| qkdpy concept | QpiAI SDK object |
|---------------|------------------|
| Qubit `[|0⟩, |1⟩]` amplitudes | `Statevector` |
| 2-qubit state | `DensityMatrix` (for purity/concurrence math) |
| Protocol circuit | `Circuit` (gates `X/H/CX/Z/ry/MEASURE`) |
| Local simulation | `Statevector(circuit)` |
| Cloud execution | `JobManager().submit_and_wait_for_results_qasm(...)` |

Two run modes:

- **Local simulator** — set `QPIAI_API_KEY`, call `simulate(circuit)`. Without a
  key, `simulate` returns an inspection metadata dict (it never crashes on a
  missing key).
- **Cloud** — `submit_to_cloud(circuit, device_name=...)` uses the real
  `JobManager` API. Without a key it raises `ValueError`; if the SDK rejects the
  submission it raises `QpiAISDKError` with the underlying message. We do **not**
  add fake SDK methods (`DensityMatrix.concurrence`, `JobManager.run_circuit`)
  that the real SDK lacks — concurrence is computed from first principles.

---

## 4. ML optimizer

`optimize_protocol` wraps qkdpy's `QKDOptimizer`, which supports several
strategies. The executed strategy is always returned in the result so no
strategy is claimed without being the one that ran:

```python
from qkdpy.integrations.qpiai_qkd import optimize_protocol, list_strategies

print(list_strategies())  # ['bayesian', 'genetic', 'neural', 'gradient']

def secret_key_rate(params):
    return -((params["detector_efficiency"] - 0.8) ** 2)

res = optimize_protocol(
    "BB84",
    parameter_space={"detector_efficiency": (0.1, 0.99)},
    objective_function=secret_key_rate,
    num_iterations=50,
    method="bayesian",
)
print(res["best_params"], res["method"])
```

`detect_anomaly(metrics, history, threshold)` flags anomalous link behaviour via
`QKDAnomalyDetector` (Z-score against a baseline).

---

## 5. IEC / ETSI interchange

The companion models the wire documents a Key Management Entity (KME)
exchanges with a Shared Authority (SAE), following the ETSI GS QKD series. These
are plain, JSON-serialisable dataclasses — this is a faithful *modelling* of the
documented field layout, not a certification under any ETSI specification.

- **ETSI GS QKD 014** — key delivery: `KeyRequest`, `KeyDelivery`
- **ETSI GS QKD 015** — SAE-to-SAE status: `SAE2EStatus`
- **Protocol run** — `ProtocolExchange` (bases, bits, concurrence/QBER/CHSH)

```python
from qkdpy.integrations.qpiai_qkd import KeyDelivery, ProtocolExchange, ProtocolType

kd = KeyDelivery(key_id="k1", sae_id="alice", target_sae_id="bob", key="deadbeef")
payload = kd.to_json()              # standards-tagged JSON
kd2 = KeyDelivery.from_json(payload)

ex = ProtocolExchange(
    protocol=ProtocolType.BB84,
    alice_bits=[0, 1, 1, 0],
    bob_bits=[0, 1, 0, 0],
    qber=0.25,
)
ex.to_json()
```

---

## 6. Install / quick start

```bash
pip install qkdpy[qpiai]
export QPIAI_API_KEY=<your-key>     # for local simulation / cloud

python - <<'PY'
from qkdpy.integrations.qpiai_qkd import QpiAIIntegration
qi = QpiAIIntegration()
c = qi.create_e91_circuit(num_pairs=2)
print(qi.simulate(c))
PY
```

If `qpiai_quantum` is not on PyPI in your environment, install it from the
sibling SDK path and ensure it is importable:

```bash
pip install -e /path/to/qpiai-quantum-sdk
```

---

## 7. Product Tiers

The companion's QpiAI bridge, protocol mapping, physics and optimizer are
available in all qkdpy tiers — they are core research tooling, not gated
features. Tiering applies only to a few enterprise conveniences in the wider
qkdpy project (compliance reporting, HSM integration, ML *feature flags*):

| Tier | qpiai-qkd companion | Notes |
|------|---------------------|-------|
| **FREE** | Fully available | All protocols, physics, optimizer, interchange. |
| **ENTERPRISE** | Fully available | Adds compliance reporting & HSM integration elsewhere in qkdpy. |
| **PREMIUM** | Fully available | Adds quantum-safe migration & crypto inventory elsewhere in qkdpy. |

No protocol, circuit, or interchange capability is withheld behind a tier.
