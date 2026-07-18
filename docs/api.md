# API Reference

This page describes the **public API surface** of QKDpy — the objects
and entry points you interact with, with runnable examples for each
layer. All code snippets assume the necessary imports and a quantum
channel constructed as shown below.

> Full source lives on [GitHub](https://github.com/Pranava-Kumar/qkdpy).
> This is a usage reference, not a source dump.

---

## Setup

Almost every example needs a channel:

```python
from qkdpy import QuantumChannel

channel = QuantumChannel(
    loss=0.1,
    noise_model="depolarizing",
    noise_level=0.02,
    distance=1.0,
)
```

**QuantumChannel** accepts many more parameters for realistic
simulation:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `distance` | `1.0` | Channel length (km) |
| `loss` | `None` | Override loss (auto-calculated from distance otherwise) |
| `noise_model` | `"none"` | One of `"none"`, `"depolarizing"`, `"bit_flip"`, `"phase_flip"`, `"dephasing"`, `"amplitude_damping"` |
| `noise_level` | `0.0` | Strength of the selected noise model |
| `dark_count_rate` | `1e-6` | Dark count probability per gate |
| `detector_efficiency` | `0.1` | Detector efficiency (0–1) |
| `misalignment_error` | `0.01` | Optical misalignment probability |
| `eavesdropper` | `None` | Callback for intercept-resend attacks |

```python
# A high-loss, long-distance channel
long_channel = QuantumChannel(
    distance=50.0,
    loss=0.5,
    noise_model="amplitude_damping",
    noise_level=0.05,
    dark_count_rate=1e-7,
    detector_efficiency=0.15,
)

# Check channel statistics after a transmission
stats = channel.get_statistics()
# {"transmitted": 500, "lost": 47, "received": 453, "errors": 9, ...}
```

---

## Protocols

QKDpy ships 11 QKD protocols. Every protocol follows the same
lifecycle: construct → `execute()` → inspect result.

### BB84 — Standard Prepare-and-Measure

```python
from qkdpy import BB84

bb84 = BB84(channel, key_length=256, security_threshold=0.11)
result = bb84.execute()

print(f"Final key (hex):     {result['final_key'][:32]}")
print(f"Sifted key (hex):    {result['sifted_key'][:32]}")
print(f"QBER:                {result['qber']:.2%}")
print(f"Secure:              {result['is_secure']}")
print(f"Raw key length:      {result.get('raw_key_length', 'N/A')}")
```

The `security_threshold` argument controls the QBER cutoff — any
protocol run with QBER above this value aborts (`is_secure=False`).

```python
# Sweep noise and watch QBER degrade
for noise in [0.01, 0.05, 0.10, 0.15]:
    ch = QuantumChannel(noise_model="depolarizing", noise_level=noise)
    r = BB84(ch, key_length=128).execute()
    print(f"noise={noise:.2f}  QBER={r['qber']:.2%}  secure={r['is_secure']}")
```

### E91 — Entanglement-Based (Bell Pairs)

```python
from qkdpy.protocols import E91

e91 = E91(channel, key_length=128, security_threshold=0.10)
result = e91.execute()

# E91 runs a Bell-test alongside key generation
bell = result["bell_test"]
print(f"CHSH S-value:       {bell['s_value']:.3f}")
print(f"Bell inequality violated: {bell['is_violated']}")
print(f"Correlations:       {bell['correlation_values']}")
print(f"Final key:          {result['final_key'][:32]}")
```

The E91 protocol internally creates GHZ pairs
(`MultiQubitState.ghz(2)`), distributes them across the channel,
and uses three measurement angles per party (Alice: 0°, 45°, 90°;
Bob: 45°, 90°, 135°).

### B92 — Minimal Two-State Protocol

```python
from qkdpy.protocols import B92

b92 = B92(channel, key_length=128, security_threshold=0.25)
result = b92.execute()
print(f"QBER:     {result['qber']:.2%}")
print(f"Secure:   {result['is_secure']}")

# B92 uses only two non-orthogonal states (|0⟩ and |+⟩)
# Bob measures only in the Hadamard basis
sift_efficiency = b92.get_sifting_efficiency()
print(f"Sifting efficiency: {sift_efficiency:.2f}")
```

### SARG04 — Four-State with Stronger Basis Guarantee

```python
from qkdpy.protocols import SARG04

sarg = SARG04(channel, key_length=128)
result = sarg.execute()
print(f"QBER: {result['qber']:.2%}  Secure: {result['is_secure']}")

sift_eff = sarg.get_sifting_efficiency()
print(f"Sifting efficiency: {sift_eff:.2f}")  # ~0.33 vs BB84's ~0.5
```

### Six-State — Three-Basis Protocol

```python
from qkdpy.protocols import SixState

ss = SixState(channel, key_length=128, security_threshold=0.126)
result = ss.execute()
print(f"QBER: {result['qber']:.2%}  Secure: {result['is_secure']}")
# Tighter QBER bound (~12.6 %) than BB84 (~11 %)
```

### Decoy-State BB84 — PNS-Resistant

```python
from qkdpy.protocols import DecoyStateBB84

ds = DecoyStateBB84(
    channel,
    key_length=256,
    security_threshold=0.11,
    weak_pulse_intensity=0.1,
    decoy_intensity=0.05,
)
result = ds.execute()

# Decoy-state analysis provides detailed gain/yield breakdown
analysis = ds.analyze_decoy_states()
print(f"Signal gain:         {analysis['signal_gain']:.4e}")
print(f"Decoy gain:          {analysis['decoy_gain']:.4e}")
print(f"Signal yield:        {analysis['signal_yield']:.4e}")
print(f"Decoy yield:         {analysis['decoy_yield']:.4e}")

# Secure key rate with error-correction efficiency
skr = ds.calculate_secure_key_rate(f=1.2, eps=1e-10)
print(f"Secure key rate:     {skr:.4e}")
print(f"Secure key length:   {ds.secure_key_length()}")
```

### CV-QKD — Continuous-Variable

```python
from qkdpy.protocols import CVQKD

cv = CVQKD(
    channel,
    key_length=128,
    security_threshold=0.1,
    modulation_variance=4.0,   # variance of Gaussian modulation
    homodyne_efficiency=0.9,   # detector efficiency
    excess_noise=0.01,         # excess noise above shot noise
)
result = cv.execute()

print(f"Final key:            {result['final_key'][:32]}")
print(f"SNR:                  {result['snr']:.2f} dB")
print(f"Theoretical capacity: {result['theoretical_capacity']:.3f} bits/use")
print(f"QBER:                 {result['qber']:.2%}")
```

CV-QKD uses Gaussian-modulated coherent states and homodyne
detection — the security analysis follows the Devetak-Winter bound.

### Enhanced CV-QKD — Reconciliation-Enhanced

```python
from qkdpy.protocols import EnhancedCVQKD

ecv = EnhancedCVQKD(
    channel,
    key_length=128,
    modulation_variance=2.0,
    detection_efficiency=0.6,
)
result = ecv.execute()
print(f"Secret fraction: {ecv.calculate_secret_fraction():.4f}")
print(f"Excess noise:    {ecv.get_excess_noise():.4f}")
print(f"Key rate:        {ecv.get_key_rate():.4f} bits/use")
```

### HD-QKD — High-Dimensional Qudits

```python
from qkdpy.protocols import HDQKD

hd = HDQKD(channel, key_length=128, dimension=4, security_threshold=0.15)
result = hd.execute()

print(f"Final key:          {result['final_key'][:32]}")
print(f"Dimension:          {hd.get_dimension_efficiency():.1f} bits/qudit")
print(f"Basis distribution: {hd.get_basis_distribution()}")

# HD-QKD uses qudits (d=4, 8, 16…) instead of qubits
# Each qudit carries log2(d) bits of raw key
```

### MDI-QKD — Measurement-Device-Independent

```python
from qkdpy.protocols import MDIQKD
from qkdpy import QuantumChannel

ch_alice = QuantumChannel(loss=0.1, noise_model="depolarizing", noise_level=0.02)
ch_bob   = QuantumChannel(loss=0.08, noise_model="depolarizing", noise_level=0.02)

mdi = MDIQKD(
    num_qubits=1000,
    channel_alice=ch_alice,
    channel_bob=ch_bob,
    bsm_success_probability=0.5,
    misalignment_error=0.01,
    random_basis=True,
)
result = mdi.execute()

print(f"Final key:           {result['final_key'][:32]}")
print(f"QBER:                {result['qber']:.2%}")
print(f"Key rate:            {result['key_rate']:.4f}")
print(f"BSM successes:       {result['bsm_success_count']}")
print(f"Sifted length:       {result['sifted_length']}")
```

MDI-QKD removes all detector-side-channel attacks by placing an
untrusted Charlie (relay) between Alice and Bob. Each has their
own independent channel.

### DI-QKD — Device-Independent (Self-Testing)

```python
from qkdpy.protocols import DIQKD

di = DIQKD(channel, key_length=128, security_threshold=2.0)
result = di.execute()

bell = result["bell_test"]
print(f"CHSH S-value:       {bell['s_value']:.3f}")
print(f"Secure:             {result['is_secure']}")
print(f"Final key:          {result['final_key'][:32]}")
```

DI-QKD does not trust the internal workings of the devices — it
relies on CHSH inequality violation to certify security. The
security threshold is on the CHSH S-value (≥2 means no violation).

### Twisted Pair QKD — Three-Basis Protocol

```python
from qkdpy.protocols import TwistedPairQKD

tp = TwistedPairQKD(channel, key_length=128)
result = tp.execute()

print(f"Twist efficiency: {tp.get_twist_efficiency():.2f}")
print(f"Basis distribution: {tp.get_basis_distribution()}")
print(f"QBER: {result['qber']:.2%}")
```

Uses three bases (computational, Hadamard, circular) with a twist
factor of 2 for enhanced noise tolerance.

---

## Core Quantum Stack

The `qkdpy.core` module provides the simulation primitives. These
are used internally by protocols but also available for
experimentation and custom protocol development.

### Qubit

```python
from qkdpy import Qubit

# Standard basis states
q0 = Qubit.zero()
q1 = Qubit.one()
q_plus  = Qubit.plus()
q_minus = Qubit.minus()

# Arbitrary state: α|0⟩ + β|1⟩
q = Qubit(alpha=0.707 + 0j, beta=0.707 + 0j)
print(f"State vector:   {q.state}")
print(f"Probabilities:  {q.probabilities}")      # (|α|², |β|²)
print(f"Density matrix: {q.density_matrix()}")
print(f"Bloch vector:   {q.bloch_vector()}")

# Apply gates
from qkdpy import Hadamard, PauliX, PauliZ

q.apply_gate(Hadamard())
q.apply_gate(PauliX())
print(f"After X·H: {q.state}")

# Measure (collapses state)
result = q.measure(basis="computational")
print(f"Measurement outcome: {result}")

# Clone (simulated, not a true quantum copy)
q2 = q.clone()
```

### Qudit — Higher-Dimensional States

```python
import numpy as np
from qkdpy import Qudit

# Computational basis state |3⟩ in dimension 5
qd = Qudit.computational_basis(level=3, dim=5)
print(f"State: {qd.state}")  # [0, 0, 0, 1, 0]

# Uniform superposition over d levels
qs = Qudit.uniform_superposition(dim=4)
print(f"State:   {qs.state}")
print(f"Fidelity with self: {qs.fidelity(qs):.2f}")

# Partial trace over a subsystem
tensor = qd.tensor_product(qs)
reduced = tensor.partial_trace(subsystem=0, sub_dim=5)
print(f"Reduced state dim: {reduced.shape}")
```

### QuantumGate

```python
from qkdpy import (
    Hadamard, PauliX, PauliY, PauliZ, S, T, SDag, TDag,
    Rx, Ry, Rz, CNOT, CZ, SWAP,
)

# Single-qubit gates
h, x, y, z = Hadamard(), PauliX(), PauliY(), PauliZ()

# Rotation gates (angle in radians)
rx = Rx(theta=0.5)
ry = Ry(theta=np.pi / 4)
rz = Rz(theta=np.pi)

# Two-qubit gates
cnot = CNOT()
cz   = CZ()
swap = SWAP()
```

### MultiQubitState — Entanglement

```python
from qkdpy import MultiQubitState

# Bell state (|00⟩ + |11⟩) / √2
ghz2 = MultiQubitState.ghz(num_qubits=2)

# GHZ state for 3 qubits
ghz3 = MultiQubitState.ghz(num_qubits=3)

# W-state: (|100⟩ + |010⟩ + |001⟩) / √3
w3 = MultiQubitState.w_state(num_qubits=3)

# Measure entanglement
entropy = ghz3.entanglement_entropy(subsystem_qubits=[0])
print(f"Entanglement entropy: {entropy:.3f}")

# Apply a CNOT on qubits 0 and 1
ghz3.apply_gate(CNOT(), target_qubits=[0, 1])
print(f"After CNOT: {ghz3.state}")
```

### Measurement Utilities

```python
from qkdpy import Measurement

q = Qubit.plus()

# Single-qubit measurements
result = Measurement.measure_in_basis(q, "hadamard")

# Batch measurements
qubits = [Qubit.zero(), Qubit.plus(), Qubit.one()]
results = Measurement.measure_batch_in_random_bases(
    qubits, bases=["computational", "hadamard", "computational"]
)

# State characterization
fidelity = Measurement.measure_state_fidelity(Qubit.zero(), Qubit.zero())
bloch    = Measurement.measure_bloch_coordinates(Qubit.plus())
purity   = Measurement.measure_purity(q)

print(f"Fidelity: {fidelity:.2f}")
print(f"Bloch:    {bloch}")
print(f"Purity:   {purity:.3f}")

# Bell-state measurement
q1, q2 = Qubit.zero(), Qubit.zero()
bell_result = Measurement.measure_bell_state(q1, q2)

# Quantum state tomography
tomography = Measurement.quantum_state_tomography(Qubit.plus(), num_measurements=1000)
```

### Channel Statistics & Eavesdropping

```python
# After running a protocol, inspect channel-level statistics
stats = channel.get_statistics()
print(f"Pulses sent:      {stats['transmitted']}")
print(f"Pulses lost:      {stats['lost']} ({stats['loss_rate']:.1%})")
print(f"Pulses received:  {stats['received']}")
print(f"Errors:           {stats['errors']} ({stats['error_rate']:.1%})")
print(f"Eve interactions: {stats['eavesdropped']}")
print(f"Eve detected:     {stats['eavesdropper_detected']}")

# Reset counters for a fresh experiment
channel.reset_statistics()
```

---

## Key Management

`qkdpy.key_management` turns sifted key material into a
shared secret through error correction and privacy amplification.

### Error Correction

```python
from qkdpy import ErrorCorrection

# Simulate mismatched keys
alice_key = [1, 0, 1, 1, 0, 0, 1, 0, 1, 1]
bob_key   = [1, 0, 1, 0, 0, 0, 1, 0, 1, 0]  # 2 bit errors

# Cascade protocol (interactive, low-overhead)
corrected_alice, corrected_bob = ErrorCorrection.cascade(
    alice_key, bob_key, iterations=4, random_permute=True
)
print(f"Key errors after cascade: {ErrorCorrection.error_rate(corrected_alice, corrected_bob):.2%}")

# Winnow protocol (faster, uses parity checks)
ca, cb = ErrorCorrection.winnow(alice_key, bob_key, block_size=4, iterations=4)

# LDPC codes (high-efficiency for large keys)
ca, cb, iters = ErrorCorrection.low_density_parity_check(
    alice_key * 100, bob_key * 100,
    code_rate=0.5, max_iterations=50
)
print(f"LDPC converged in {iters} iterations")

# Reed-Solomon (good for burst errors)
ca, cb, success = ErrorCorrection.reed_solomon(
    alice_key, bob_key, n=15, k=9, error_probability=0.1
)
print(f"Reed-Solomon success: {success}")

# BCH codes
ca, cb, success = ErrorCorrection.bch(
    alice_key, bob_key, n=15, k=11, t=1, error_probability=0.1
)

# Helpers
dist = ErrorCorrection.hamming_distance(alice_key, bob_key)
rate = ErrorCorrection.error_rate(alice_key, bob_key)
print(f"Hamming distance: {dist}  Error rate: {rate:.2%}")
```

### Privacy Amplification

```python
from qkdpy import PrivacyAmplification

key = list(range(256))  # example sifted key

# Universal hashing (random binary matrix)
shortened = PrivacyAmplification.universal_hashing(key, output_length=128, seed=42)

# Toeplitz hashing (efficient for hardware)
toeplitz = PrivacyAmplification.toeplitz_hashing(key, output_length=128)

# Cryptographic hash
sha = PrivacyAmplification.cryptographic_hash(key, output_length=256, hash_algorithm="sha256")

# Bennett-Brassard 1992 (BB) two-universal hashing
bb = PrivacyAmplification.bennett_brassard_hashing(key, output_length=128, error_rate=0.02)

# Leftover-hash lemma with explicit min-entropy
leftover = PrivacyAmplification.leftover_hash_lemma(
    key, min_entropy=0.8, security_parameter=1e-9
)
```

### Key Distillation Pipeline

```python
from qkdpy import KeyDistillation

distiller = KeyDistillation(
    error_correction_method="cascade",
    privacy_amplification_method="universal_hashing",
)

# Simulate a key exchange with bit errors
import random
alice = [random.randint(0, 1) for _ in range(256)]
bob = alice.copy()
for i in random.sample(range(256), 10):  # 10 random errors
    bob[i] ^= 1

distilled = distiller.distill(alice, bob, qber=10/256, final_key_length=128)
print(f"Initial length:  {distilled['initial_length']}")
print(f"Corrected:       {distilled['corrected_length']}")
print(f"Final length:    {distilled['final_length']}")
print(f"Error rate:      {distilled['error_rate']:.2%}")
print(f"Eve information: {distilled['eve_information']:.4f}")
print(f"Key rate:        {distilled['key_rate']:.4f}")

stats = distiller.get_statistics()
distiller.reset_statistics()
```

### QuantumKeyManager — Full Lifecycle

```python
from qkdpy import QuantumKeyManager, QuantumChannel

qkm = QuantumKeyManager(channel)

# Generate a key via the manager
key_id, key_data = qkm.generate_key(
    session_id="session-001",
    key_length=256,
    protocol="BB84",
)
print(f"Key ID: {key_id}")
print(f"Key hex: {key_data[:32]}")

# Retrieve a key (with optional hash verification)
retrieved, hash_val = qkm.get_key(key_id, return_hash=True)
print(f"Retrieved: {retrieved[:32]}")
print(f"Hash:      {hash_val}")

# Session management
keys = qkm.get_session_keys("session-001")
print(f"Keys in session: {len(keys)}")

# Rotate (generate a fresh key for an existing session)
new_key_id, new_key = qkm.rotate_session_key("session-001", key_length=256)

# Export / import key store
qkm.export_key_store("key_store.json")
qkm.import_key_store("key_store.json")

# Statistics
stats = qkm.get_key_statistics()
print(f"Total keys: {stats['total_keys']}")

# Clean up expired sessions
qkm.cleanup_expired_sessions(max_age=3600.0)

# Delete a specific key
qkm.delete_key(key_id)
```

### Quantum Error Correction (QEC)

```python
from qkdpy.key_management import (
    ShorCode, SteaneCode, FiveQubitCode,
    detect_and_correct_error,
    simulate_error_correction_performance,
)

# Encode a qubit with the Shor 9-qubit code
encoded = ShorCode.encode(Qubit.zero())
print(f"Encoded state shape: {encoded.shape}")

# Encode with Steane 7-qubit code
encoded_steane = SteaneCode.encode(Qubit.plus())

# Simulate error correction performance
results = simulate_error_correction_performance(
    num_trials=1000,
    code_type="steane",
    error_probability=0.05,
)
print(f"Logical error rate: {results['logical_error_rate']:.4f}")
```

---

## Network & Satellite QKD

### SatelliteQKD — LEO/MEO/GEO Pass Simulation

```python
from qkdpy.network import SatelliteQKD, OrbitType, AtmosphericProfile

# Low-Earth Orbit (500 km) satellite over the equator
sat = SatelliteQKD(
    orbit_type=OrbitType.LEO,
    altitude_km=500.0,
    ground_station_lat=0.0,
    ground_station_lon=0.0,
    protocol="BB84",
)

# Define atmospheric conditions
atmosphere = AtmosphericProfile(
    visibility_km=23.0,        # Clear visibility
    turbulence_cn2=1e-14,      # Refractive-index structure constant
    aerosol_optical_depth=0.1,
    water_vapor_mm=10.0,
    cloud_optical_depth=0.0,   # Cloudless
    temperature_k=288.0,
    pressure_hpa=1013.25,
)

# Simulate a satellite pass
report = sat.simulate_pass(
    duration_seconds=300.0,
    time_steps=60,
    atmosphere=atmosphere,
)

print(f"Key yield:  {report.get('key_yield', 'N/A')}")
print(f"QBER range: {report.get('qber_range', 'N/A')}")
print(f"Pass duration: {report.get('pass_duration_s', 'N/A')} s")

# Predict key yield for a given peak elevation
yield_pred = sat.predict_key_yield(atmosphere, peak_elevation=80.0)
print(f"Predicted yield: {yield_pred}")

# Train a ML predictor for channel conditions
sat.train_channel_predictor()
print(sat.get_mission_summary())
```

### Different Orbit Types

```python
from qkdpy.network import OrbitType

# LEO — Low Earth Orbit (300–2000 km), short passes, high attenuation
leo = SatelliteQKD(orbit_type=OrbitType.LEO, altitude_km=500)

# MEO — Medium Earth Orbit (2000–35786 km), longer visibility
meo = SatelliteQKD(orbit_type=OrbitType.MEO, altitude_km=10000)

# GEO — Geostationary (35786 km), continuous link but extreme loss
geo = SatelliteQKD(orbit_type=OrbitType.GEO, altitude_km=35786)

for s in [leo, meo, geo]:
    r = s.simulate_pass(duration_seconds=300)
    print(f"{s.orbit_type.value}: key_yield={r.get('key_yield', 'N/A')}")
```

### FreeSpaceOpticalChannel — Satellite-Ground Link

```python
from qkdpy.network import FreeSpaceOpticalChannel, SatellitePosition

# Create a satellite position at a point in the pass
pos = SatellitePosition.from_orbit(
    altitude_km=500,
    ground_lat=0.0, ground_lon=0.0,
    sat_lat=10.0, sat_lon=15.0,
)

# Build the optical channel
fso = FreeSpaceOpticalChannel(
    satellite_position=pos,
    atmosphere=atmosphere,
    wavelength_nm=850.0,
    telescope_diameter_m=0.3,
    pointing_error_urad=1.0,
    is_night=True,
    link_direction="downlink",
    noise_model="depolarizing",
    noise_level=0.02,
)

metrics = fso.get_channel_metrics()
print(f"Slant range:            {metrics['slant_range_km']:.1f} km")
print(f"Elevation angle:        {metrics['elevation_angle_deg']:.1f}°")
print(f"Total loss:             {metrics['total_loss_db']:.1f} dB")
print(f"Fried parameter:        {metrics['fried_parameter_cm']:.2f} cm")
print(f"Atmospheric seeing:     {metrics['atmospheric_seeing_arcsec']:.2f} arcsec")
print(f"MODTRAN transmittance:  {metrics['modtran_transmittance']:.3f}")
print(f"Stray count rate:       {metrics['stray_count_rate']:.1f} /s")
```

### Atmospheric Physics Helpers

```python
from qkdpy.network import (
    modtran_band_transmittance,
    background_stray_count_rate,
    hufnagel_valley_cn2,
    von_karman_spectrum,
    fried_parameter,
    rytov_variance,
    scintillation_index,
)

# MODTRAN band transmittance at 850 nm
trans = modtran_band_transmittance(wavelength_nm=850.0)
print(f"Atmospheric transmittance at 850 nm: {trans:.3f}")

# Background stray counts (night vs day)
night = background_stray_count_rate(850.0, is_night=True)
day   = background_stray_count_rate(850.0, is_night=False)
print(f"Night stray rate: {night:.1f} /s")
print(f"Day stray rate:   {day:.1f} /s")

# Turbulence profiling
cn2 = hufnagel_valley_cn2(altitude_m=1000, wind_speed_ms=21.0)
print(f"CN² at 1 km: {cn2:.2e}")

r0 = fried_parameter(wavelength_nm=850.0, cn2=1e-14)
print(f"Fried parameter: {r0:.2f} cm")
```

### QuantumNetwork — Multi-Node Topologies

```python
from qkdpy.network import QuantumNetwork
from qkdpy import QuantumChannel

net = QuantumNetwork(name="City-scale QKD", topology_type="custom")

# Add nodes
net.add_node(node_id="alice", protocol="BB84")
net.add_node(node_id="bob", protocol="BB84")
net.add_node(node_id="charlie", protocol="BB84")

# Add connections (channels between nodes)
net.add_connection("alice", "bob", channel=QuantumChannel(distance=10.0), distance=10.0)
net.add_connection("bob", "charlie", channel=QuantumChannel(distance=15.0), distance=15.0)
net.add_connection("alice", "charlie", channel=QuantumChannel(distance=30.0), distance=30.0)

# Route finding
path = net.get_shortest_path("alice", "charlie", weight="distance")
print(f"Shortest path: {path}")  # ['alice', 'bob', 'charlie']

# Key establishment across a path
key_result = net.establish_key_between_nodes(
    "alice", "charlie",
    key_length=128,
    path_type="shortest",
    security_threshold=0.11,
)
print(f"Key established: {key_result.get('final_key', 'N/A')[:32]}")

# Entanglement swapping
swap_result = net.perform_entanglement_swapping("alice", "charlie")

# Network statistics
net_stats = net.get_network_statistics()
print(f"Nodes: {net_stats['num_nodes']}, Links: {net_stats['num_connections']}")

# Full performance simulation
perf = net.simulate_network_performance(
    num_trials=50,
    path_selection="random",
)
```

### Multi-Party QKD

```python
from qkdpy.network import conference_key_agreement, quantum_secret_sharing, reconstruct_secret

# Three-party conference key
ck = conference_key_agreement(net, participants=["alice", "bob", "charlie"], key_length=128)
print(f"Conference key: {ck[:32]}")

# Quantum secret sharing
secret = 0b10110101
shares = quantum_secret_sharing(secret, num_shares=5, threshold=3)
print(f"Shares: {shares}")

# Reconstruct from threshold subset
reconstructed = reconstruct_secret(shares[:3])
print(f"Reconstructed: {bin(reconstructed)}")
assert reconstructed == secret
```

---

## ML Optimization

### QKDOptimizer — Bayesian, Genetic & Neural Methods

```python
from qkdpy import QKDOptimizer

optimizer = QKDOptimizer(protocol_name="BB84")

# Define the parameter space
param_space = {
    "loss": (0.0, 0.5),
    "noise_level": (0.0, 0.1),
    "dark_count_rate": (1e-8, 1e-5),
}

def objective_fn(params):
    """Return the secure key rate (higher = better)."""
    ch = QuantumChannel(
        loss=params["loss"],
        noise_model="depolarizing",
        noise_level=params["noise_level"],
        dark_count_rate=params["dark_count_rate"],
    )
    result = BB84(ch, key_length=128).execute()
    return result["qber"] if not result["is_secure"] else result.get("key_rate", 0)

# Bayesian optimization (Gaussian Process)
best_bayesian = optimizer.optimize_channel_parameters(
    param_space,
    objective_fn,
    num_iterations=100,
    method="bayesian",
)
print(f"Bayesian best params: {best_bayesian}")

# Genetic algorithm
best_genetic = optimizer.optimize_channel_parameters(
    param_space,
    objective_fn,
    num_iterations=200,
    method="genetic",
)
print(f"Genetic best params: {best_genetic}")

# Neural-network surrogate
best_neural = optimizer.optimize_channel_parameters(
    param_space,
    objective_fn,
    num_iterations=150,
    method="neural",
)

# Inspect optimization history
history = optimizer.get_optimization_history()
print(f"History entries: {len(history)}")

# Predict performance for a set of parameters
pred = optimizer.predict_performance({"loss": 0.1, "noise_level": 0.02, "dark_count_rate": 1e-6})
print(f"Predicted score: {pred}")
```

### EfficientQKDPredictor — Lightweight Edge Deployment

```python
import numpy as np
from qkdpy import EfficientQKDPredictor

# Train a small predictor for edge devices
predictor = EfficientQKDPredictor(
    input_dim=5,
    max_memory_mb=64,           # constraint to 64 MB
    enable_quantization=True,    # int8 quantization
    enable_pruning=True,         # weight pruning
    pruning_threshold=0.01,
)

# Generate synthetic training data
X = np.random.rand(1000, 5)
y = np.random.rand(1000)

# Train with early stopping
history = predictor.fit(
    X, y,
    epochs=50,
    learning_rate=0.01,
    batch_size=32,
    early_stopping_patience=10,
    validation_split=0.1,
)
print(f"Training history: {history['loss'][-1]:.4f} final loss")

# Predict
X_test = np.random.rand(10, 5)
preds = predictor.predict(X_test)
print(f"Predictions: {preds[:3]}")

# Model efficiency metrics
print(f"Model size: {predictor.get_model_size_bytes()} bytes")
print(f"Sparsity:   {predictor.get_sparsity():.2%}")
```

### QKDAnomalyDetector

```python
from qkdpy import QKDAnomalyDetector

detector = QKDAnomalyDetector()

# Establish baseline from historical metrics
baseline_metrics = [
    {"qber": 0.03, "key_rate": 0.45, "snr": 12.0, "loss_rate": 0.1},
    {"qber": 0.04, "key_rate": 0.42, "snr": 11.5, "loss_rate": 0.12},
    {"qber": 0.035, "key_rate": 0.44, "snr": 11.8, "loss_rate": 0.11},
]
detector.establish_baseline(baseline_metrics)

# Detect anomalies in current metrics
current = {"qber": 0.15, "key_rate": 0.10, "snr": 4.0, "loss_rate": 0.5}
anomalies = detector.detect_anomalies(current)
print(f"Anomalies detected: {anomalies}")

# Adjust detection sensitivity
detector.update_anomaly_threshold(0.05)

# Full detection report
report = detector.get_detection_report()
```

---

## Enterprise Features

Enterprise features are gated by product tier. The free tier
includes all protocols, satellite QKD, and ML optimization.
Additional capabilities unlock with a valid license key.

### Tier Activation

```python
from qkdpy.enterprise import (
    ProductTier, Feature,
    get_active_tier, set_active_tier,
    feature_available, require_feature,
)

# Check current tier
print(f"Active tier: {get_active_tier()}")  # ProductTier.FREE

# Activate ENTERPRISE (requires license key)
set_active_tier(ProductTier.ENTERPRISE, license_key="your-license-key")

# Check specific feature access
if feature_available(Feature.HSM_INTEGRATION):
    print("HSM integration is available")

# The @require_feature decorator gates individual functions
```

### HSM Interface

```python
from qkdpy.enterprise import get_hsm, HSMProvider

# Get the software HSM (simulated — not for production)
hsm = get_hsm(provider=HSMProvider.SOFTWARE)

# Initialize
hsm.initialize()

# Generate a key
key_handle = hsm.generate_key(key_type="AES-256", label="qkd-key-001")
print(f"Key ID: {key_handle.key_id}")

# Encrypt/decrypt
plaintext = b"secret quantum key material"
ciphertext = hsm.encrypt(key_handle.key_id, plaintext)
decrypted = hsm.decrypt(key_handle.key_id, ciphertext)
assert decrypted == plaintext

# Wrap (export) and unwrap (import) keys
wrapped = hsm.wrap_key(key_handle.key_id, target_key_id="transport-key")
new_handle = hsm.unwrap_key(wrapped, key_type="AES-256")
print(f"Unwrapped key ID: {new_handle.key_id}")

# List all keys
keys = hsm.list_keys()
print(f"HSM keys: {keys}")

hsm.close()
```

### Audit Logger

```python
from qkdpy.enterprise import AuditLogger, AuditEventType

logger = AuditLogger(storage_path="audit.json", enable_chain_verification=True)

# Log various event types
logger.log_event(
    event_type=AuditEventType.KEY_GENERATED,
    actor="alice",
    resource="session-001",
    result="success",
    details={"key_length": 256, "protocol": "BB84"},
)

logger.log_security_event(
    actor="system",
    resource="channel-1",
    result="blocked",
    details={"threat": "high_qber", "qber": 0.15},
    severity="high",
)

# Chain integrity verification
is_valid, errors = logger.verify_chain_integrity()
print(f"Chain valid: {is_valid}")
if errors:
    for err in errors:
        print(f"  Chain error: {err}")

# Query events
events = logger.get_events(
    event_type=AuditEventType.KEY_GENERATED,
    actor="alice",
    limit=50,
)

# Export to various formats
json_export = logger.export_events(format="json")
cef_export  = logger.export_events(format="cef")   # Common Event Format
leef_export = logger.export_events(format="leef")   # Log Event Extended Format

stats = logger.get_statistics()
print(f"Total events: {stats['total_events']}")
```

### Compliance Checking

```python
from qkdpy.enterprise import ComplianceChecker

# Check against specific standards
checker = ComplianceChecker(
    standards=["ETSI_GS_QKD_014", "NIST_SP_800_57", "FIPS_140_2"],
)

report = checker.check_compliance()
print(f"Overall compliant: {report.overall_compliant}")
print(f"Passed: {report.passed_checks} / {report.total_checks}")

# Summary and export
summary = report.get_summary()
for check in report.get_failed_checks():
    print(f"  FAIL: {check.standard} — {check.requirement}")
    print(f"    {check.recommendation}")

# Export as Markdown or HTML
markdown_report = report.export_markdown()
html_report = report.export_html()
```

### Quantum-Safe Migration Toolkit

```python
from qkdpy.enterprise import (
    classic_enterprise_profile,
    generate_roadmap,
    QuantumSafeAssessment,
)

# Assess current crypto inventory
inventory = classic_enterprise_profile()
summary = inventory.get_summary()
print(f"Total assets:     {summary['total_assets']}")
print(f"Vulnerable count: {summary['vulnerable_count']}")
print(f"Risk score:       {summary['risk_score']:.2f}")

# Generate phased migration roadmap
roadmap = generate_roadmap(inventory=inventory)
for step in roadmap.steps:
    print(f"Phase {step.phase}: {step.description} (by {step.target_date})")

# Create an assessment from the inventory
assessment = QuantumSafeAssessment(inventory=inventory)
assessment_dict = assessment.to_dict()
```

---

## Observability

### OperationSpan — Timed Context Manager

```python
from qkdpy.utils import OperationSpan
import time

with OperationSpan("protocol.execute", protocol="BB84") as span:
    time.sleep(0.1)
    span.set_metadata(qber=0.035, key_length=256, is_secure=True)
    # On exit: automatically logs duration + metadata
```

### @instrument Decorator

```python
from qkdpy.utils import instrument

@instrument(span_name="key_distillation")
def distill(sifted_key, qber):
    # Function call is automatically timed and logged
    return manager.distill(sifted_key, qber)
```

### Domain-Specific Recording Helpers

```python
from qkdpy.utils import (
    record_protocol_execution,
    record_ml_training,
    record_qber_diagnostic,
)

# Protocol execution event
record_protocol_execution(
    protocol_name="BB84",
    key_length=256,
    qber=0.035,
    final_key_size=128,
    is_secure=True,
    duration_ms=45.2,
    channel_stats={"loss": 0.1, "noise": 0.02},
)

# ML training event
record_ml_training(
    model_name="EfficientQKDPredictor",
    epochs=50,
    final_loss=0.012,
    accuracy=0.98,
    learning_rate=0.01,
    dataset_size=1000,
    features=5,
)

# QBER diagnostic
record_qber_diagnostic(
    protocol="BB84",
    qber=0.035,
    threshold=0.11,
    key_size=256,
    distance_km=10.0,
)
```

### Logging Configuration

```python
from qkdpy.utils import configure_logging, get_logger, QKDLogger

# Enable JSON-structured output for log aggregation
configure_logging(
    level="INFO",
    json_output=True,
    redact_secrets=True,
)

# Get a domain-specific logger
logger = get_logger("qkdpy.protocols")
logger.info("Protocol starting", protocol="BB84", key_length=256)

# QKDLogger adds .audit() and .security() methods
qkd_logger = QKDLogger("qkdpy.enterprise")
qkd_logger.audit("Key generated", key_id="k-001")
qkd_logger.security("Unauthorized access attempt", source="unknown")
```

### Validation Helpers

```python
from qkdpy.utils import (
    validate_qber, validate_key_length,
    validate_density_matrix, validate_normalized_state,
)

validate_qber(0.03)            # OK
validate_qber(1.5)             # raises ValueError

validate_key_length(256)       # OK
validate_key_length(-1)        # raises ValueError

validate_density_matrix(np.eye(2) / 2)  # OK

import numpy as np
validate_normalized_state(np.array([0.707, 0.707]))  # OK
```

### Utility Helpers

```python
from qkdpy.utils import (
    random_bit_string, bits_to_bytes, bytes_to_bits,
    hamming_distance, binary_entropy, calculate_qber,
    mutual_information, generate_random_permutation,
)

# Random key generation
bits = random_bit_string(length=256)
print(f"Random bits: {bits[:32]}...")

# Conversion
byte_data = bits_to_bytes(bits)
bit_data = bytes_to_bits(byte_data)
print(f"Round-trip: {bits[:16] == bit_data[:16]}")

# Information-theoretic metrics
entropy = binary_entropy(0.11)
print(f"H₂(0.11) = {entropy:.4f}")

mutual = mutual_information(0.03, 0.05)
print(f"Mutual information: {mutual:.4f}")

qber = calculate_qber("10110", "10010")
print(f"QBER: {qber:.2%}")

# Permutation
perm = generate_random_permutation(10)
print(f"Permutation: {perm}")
```

---

## Framework Integrations

QKDpy can bridge its types to/from external quantum computing
frameworks. Each integration is lazy-loaded — it only imports the
third-party library when used and gracefully falls back if the
library is not installed.

### Integration Detection

```python
from qkdpy import (
    QISKIT_AVAILABLE, CIRQ_AVAILABLE,
    PENNYLANE_AVAILABLE, QPIAI_AVAILABLE,
)

print(f"Qiskit:    {QISKIT_AVAILABLE}")
print(f"Cirq:      {CIRQ_AVAILABLE}")
print(f"PennyLane: {PENNYLANE_AVAILABLE}")
print(f"QpiAI:     {QPIAI_AVAILABLE}")
```

### Qiskit Integration

```python
from qkdpy.integrations import QiskitIntegration

if QISKIT_AVAILABLE:
    # Convert a QKDpy Qubit to a Qiskit QuantumCircuit
    qk_qubit = Qubit.plus()
    circuit = QiskitIntegration.to_qiskit_circuit(qk_qubit)

    # Convert a QKDpy channel to Qiskit noise model
    qk_channel = QuantumChannel(noise_model="depolarizing", noise_level=0.02)
    noise_model = QiskitIntegration.to_qiskit_noise(qk_channel)

    # Execute a Qiskit circuit and convert result back
    counts = QiskitIntegration.execute(circuit, backend="qasm_simulator", shots=1024)
    qk_result = QiskitIntegration.from_qiskit_result(counts)
```

### Cirq Integration

```python
from qkdpy.integrations import CirqIntegration

if CIRQ_AVAILABLE:
    qubit = Qubit.zero()
    cirq_qubit = CirqIntegration.to_cirq(qubit)
    # Run on Cirq simulator
    result = CirqIntegration.simulate(cirq_qubit)
```

### PennyLane Integration

```python
from qkdpy.integrations import PennyLaneIntegration

if PENNYLANE_AVAILABLE:
    # Use within a PennyLane QNode
    dev = PennyLaneIntegration.get_device(wires=2, shots=1000)

    @PennyLaneIntegration.qnode(dev)
    def circuit(x):
        PennyLaneIntegration.apply_quantum_gate("RX", x, wires=[0])
        PennyLaneIntegration.apply_quantum_gate("CNOT", wires=[0, 1])
        return PennyLaneIntegration.measure(wires=[0, 1])

    result = circuit(0.5)
```

### QpiAI Integration

```python
from qkdpy.integrations import QpiAIIntegration

if QPIAI_AVAILABLE:
    # Convert and execute on QpiAI backends
    qubit = Qubit.plus()
    result = QpiAIIntegration.execute(qubit)
```

---

## Crypto

`qkdpy.crypto` provides the building blocks used internally by
protocols and key management.

```python
from qkdpy import (
    OneTimePad, QuantumRandomNumberGenerator,
    QuantumAuth, QuantumKeyExchange, QuantumSideChannelProtection,
)

# One-Time Pad encryption
otp = OneTimePad()
key = b"supersecretkey123"
plaintext = b"Quantum key material"
ciphertext = otp.encrypt(plaintext, key)
decrypted = otp.decrypt(ciphertext, key)
assert decrypted == plaintext

# Quantum-grade random number generation
qrng = QuantumRandomNumberGenerator()
random_bits = qrng.generate(256)
print(f"Random bits: {random_bits[:32]}")

# Side-channel protection (constant-time operations)
scp = QuantumSideChannelProtection()
safe_compare = scp.constant_time_compare("token_a", "token_b")
```

---

## Configuration

```python
from qkdpy import (
    QKDConfig, get_config, set_config,
    is_debug_mode, is_production_mode,
)

# Read current configuration
cfg = get_config()
print(f"Debug mode: {is_debug_mode()}")
print(f"Production: {is_production_mode()}")

# Modify configuration
cfg.security.default_key_length = 256
cfg.enterprise.enforcement = False
cfg.logging.level = "DEBUG"
set_config(cfg)

# Production mode enables enforcement, stricter logging
if is_production_mode():
    print("Running in production mode")
```
