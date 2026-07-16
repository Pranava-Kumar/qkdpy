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
"""Comprehensive blackbox test of qkdpy network/satellite QKD module.

Tests all modules in the network package:
  - SatelliteQKD, FreeSpaceOpticalChannel, AtmosphericProfile
  - QuantumNetwork, QuantumNode
  - MultiPartyQKDNetwork (multiparty_qkd.py)
  - MultiPartyQKD (quantum_network.py conference_key_agreement)
  - RealisticQuantumNetwork
  - ChannelPredictor protocol + EfficientQKDPredictor
  - Real TLE propagation with skyfield/sgp4
"""

import math
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from qkdpy.core import QuantumChannel
from qkdpy.ml import EfficientQKDPredictor
from qkdpy.network.multiparty_qkd import MultiPartyQKDNetwork, TrustedRelayNetwork
from qkdpy.network.protocols import ChannelPredictor
from qkdpy.network.quantum_network import (
    MultiPartyQKD,
    QuantumNetwork,
)
from qkdpy.network.realistic_quantum_network import RealisticQuantumNetwork

# Imports
from qkdpy.network.satellite_qkd import (
    AtmosphericProfile,
    FreeSpaceOpticalChannel,
    OrbitType,
    SatellitePosition,
    SatelliteQKD,
)
from qkdpy.protocols import BB84

SEP = "=" * 72
DASH = "-" * 72

print(SEP)
print("QKDPY v0.6.0 - NETWORK/SATELLITE QKD MODULE TEST")
print(SEP)

# ============================================================================
# 1.  SATELLITE QKD
# ============================================================================
print()
print(DASH)
print("SECTION 1: SATELLITE QKD")
print(DASH)

# 1a. Create SatelliteQKD - LEO, 500 km, Cape Canaveral ground station
print()
print(">>> 1a. Create SatelliteQKD instance")
sat = SatelliteQKD(
    orbit_type=OrbitType.LEO,
    altitude_km=500.0,
    ground_station_lat=28.5,
    ground_station_lon=-80.6,
    protocol="BB84",
)
summary = sat.get_mission_summary()
print(f"  orbit_type:            {summary['orbit_type']}")
print(f"  altitude_km:           {summary['altitude_km']}")
print(f"  ground_station_lat:    {summary['ground_station']['latitude']}")
print(f"  ground_station_lon:    {summary['ground_station']['longitude']}")
print(f"  protocol:              {summary['protocol']}")
print(f"  total_passes_simulated:{summary['total_passes_simulated']}")
print(f"  ml_predictor_trained:  {summary['ml_predictor_trained']}")
print(f"  estimated_daily_key_bits: {summary['estimated_daily_key_bits']}")

# 1b. Simulate a single pass over 600 seconds
print()
print(">>> 1b. Simulate one pass (600 s, 60 time-steps)")
pass_clear = sat.simulate_pass(
    duration_seconds=600.0,
    time_steps=60,
    atmosphere=AtmosphericProfile(visibility_km=23.0, turbulence_cn2=1e-14),
)

angles = pass_clear["elevation_angles"]
losses = pass_clear["channel_losses_db"]
rates = pass_clear["key_rates_bps"]
qbers = pass_clear["qber_values"]
total_bits = pass_clear["total_key_bits"]

print(
    f"  elevation_angles  - min: {min(angles):.4f} deg, "
    f"max: {max(angles):.4f} deg, "
    f"at_zenith: {angles[len(angles)//2]:.4f} deg"
)
print(f"  channel_losses_db - min: {min(losses):.2f} dB, " f"max: {max(losses):.2f} dB")
print(
    f"  key_rates_bps     - min: {min(rates):.2f}, "
    f"max: {max(rates):.2f}, "
    f"mean: {np.mean(rates):.2f}"
)
print(
    f"  qber_values       - min: {min(qbers):.6f}, "
    f"max: {max(qbers):.6f}, "
    f"mean: {np.mean(qbers):.6f}"
)
print(f"  total_key_bits:            {total_bits:.2f}")
print(f"  number of time-steps:      {len(angles)}")

# 1c. Slant range from SatellitePosition manual calculation
print()
print(">>> 1c. SatellitePosition.from_orbit() - geometry check")
pos = SatellitePosition.from_orbit(
    altitude_km=500.0,
    ground_lat=28.5,
    ground_lon=-80.6,
    sat_lat=30.0,
    sat_lon=-75.0,
)
print(f"  altitude_km:     {pos.altitude_km}")
print(f"  latitude:        {pos.latitude}")
print(f"  longitude:       {pos.longitude}")
print(f"  elevation_angle: {pos.elevation_angle:.4f} deg")
print(f"  slant_range_km:  {pos.slant_range_km:.2f} km")

# 1d. FreeSpaceOpticalChannel metrics
print()
print(">>> 1d. FreeSpaceOpticalChannel metrics")
fso = FreeSpaceOpticalChannel(
    satellite_position=pos,
    atmosphere=AtmosphericProfile(visibility_km=23.0, turbulence_cn2=1e-14),
    wavelength_nm=850.0,
    telescope_diameter_m=0.3,
    pointing_error_urad=1.0,
)
metrics = fso.get_channel_metrics()
print(f"  slant_range_km:        {metrics['slant_range_km']:.2f}")
print(f"  elevation_angle_deg:   {metrics['elevation_angle_deg']:.4f}")
print(f"  total_loss_db:         {metrics['total_loss_db']:.2f}")
print(f"  fried_parameter_cm:    {metrics['fried_parameter_cm']:.4f}")
print(f"  seeing_arcsec:         {metrics['atmospheric_seeing_arcsec']:.4f}")

# 1e. AtmosphericProfile - test different conditions
print()
print(">>> 1e. Atmospheric conditions comparison")
profiles = {
    "Clear (23 km, Cn2=1e-14)": AtmosphericProfile(
        visibility_km=23.0, turbulence_cn2=1e-14
    ),
    "Moderate (10 km, Cn2=1e-13)": AtmosphericProfile(
        visibility_km=10.0, turbulence_cn2=1e-13
    ),
    "Poor (3 km, Cn2=1e-12)": AtmosphericProfile(
        visibility_km=3.0, turbulence_cn2=1e-12
    ),
}

sat2 = SatelliteQKD(
    orbit_type=OrbitType.LEO,
    altitude_km=500.0,
    ground_station_lat=28.5,
    ground_station_lon=-80.6,
)

for label, prof in profiles.items():
    r = sat2.simulate_pass(duration_seconds=600.0, time_steps=60, atmosphere=prof)
    mean_rate = np.mean(r["key_rates_bps"])
    total = r["total_key_bits"]
    mean_loss = np.mean(r["channel_losses_db"])
    mean_qber = np.mean(r["qber_values"])
    print(
        f"  {label:45s}  key_rate_mean={mean_rate:10.2f} bps  "
        f"total={total:10.2f} bits  loss_mean={mean_loss:6.2f} dB  "
        f"qber_mean={mean_qber:.6f}"
    )

# 1f. ML channel prediction - train on 5 passes, then predict
print()
print(">>> 1f. ML channel prediction with EfficientQKDPredictor")
sat_ml = SatelliteQKD(
    orbit_type=OrbitType.LEO,
    altitude_km=500.0,
    ground_station_lat=28.5,
    ground_station_lon=-80.6,
)
# Simulate 5 passes with varying conditions
for i in range(5):
    v = 10 + 15 * np.random.random()
    cn = 1e-14 * (0.5 + np.random.random())
    prof = AtmosphericProfile(
        visibility_km=float(v),
        turbulence_cn2=float(cn),
        aerosol_optical_depth=float(0.05 + 0.1 * np.random.random()),
    )
    sat_ml.simulate_pass(duration_seconds=600.0, time_steps=60, atmosphere=prof)

train_result = sat_ml.train_channel_predictor()
print(f"  training epochs:   {train_result.get('epochs_trained', 'N/A')}")
print(f"  final_train_loss:  {train_result.get('final_train_loss', 'N/A')}")

# Predict for a given condition
pred = sat_ml.predict_key_yield(
    atmosphere=AtmosphericProfile(visibility_km=23.0, turbulence_cn2=1e-14),
    peak_elevation=80.0,
)
print(f"  predicted_key_yield (clear, peak 80 deg): {pred:.2f} bits")

pred2 = sat_ml.predict_key_yield(
    atmosphere=AtmosphericProfile(visibility_km=5.0, turbulence_cn2=1e-12),
    peak_elevation=40.0,
)
print(f"  predicted_key_yield (poor, peak 40 deg): {pred2:.2f} bits")

# 1g. Real TLE data - fetch ISS TLE from CelesTrak
print()
print(">>> 1g. Real TLE data - ISS pass computation")
import urllib.request

tle_line1 = None
tle_line2 = None
tle_text = None
try:
    print("  Fetching ISS TLE from CelesTrak (CATNR=25544) ...")
    req = urllib.request.Request(
        "https://celestrak.org/NORAD/elements/gp.php?CATNR=25544&FORMAT=TLE",
        headers={"User-Agent": "Mozilla/5.0"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        tle_text = resp.read().decode("utf-8").strip()
    print(f"  Response length: {len(tle_text)} chars")
    lines = [l.strip() for l in tle_text.split("\n") if l.strip()]
    for l in lines:
        if l.startswith("1 ") and tle_line1 is None:
            tle_line1 = l
        elif l.startswith("2 ") and tle_line2 is None:
            tle_line2 = l
    if tle_line1 and tle_line2:
        print(f"  TLE Line 1: {tle_line1}")
        print(f"  TLE Line 2: {tle_line2}")
    else:
        print("  Could not parse TLE from response, using simulated TLE")
        tle_line1 = tle_line2 = None
except Exception as e:
    print(f"  Web fetch failed: {e}")
    print("  Using simulated TLE (sgp4-based propagation)")
    tle_line1 = tle_line2 = None

from datetime import (
    UTC,
    datetime,
    timedelta,
)

from sgp4.api import Satrec

if tle_line1 and tle_line2:
    print("  Propagating with sgp4 ...")
    satellite = Satrec.twoline2rv(str(tle_line1), str(tle_line2))
else:
    print("  Using simulated ISS-like TLE for demonstration")
    # Simulated ISS-like orbit: 51.6 deg inclination, ~400 km altitude
    tle_line1 = "1 25544U 98067A   26197.50000000  .00016717  00000+0  10270-4 0  9001"
    tle_line2 = "2 25544  51.6429  98.5747 0007418  56.5432  55.7788 15.50119770350000"
    satellite = Satrec.twoline2rv(tle_line1, tle_line2)

# Ground station: Cape Canaveral
gs_lat_deg = 28.5
gs_lon_deg = -80.6
R_earth = 6371.0

print(f"  Ground station: {gs_lat_deg}N, {gs_lon_deg}W")


# ---------------------------------------------------------------------------
# sgp4 2.x removed EarthGravity.eci_to_geodetic(); reimplement inline.
# ---------------------------------------------------------------------------
def eci_to_geodetic(
    pos: tuple[float, float, float], jd: float
) -> tuple[float, float, float]:
    """Convert ECI (km) to geodetic (rad, rad, km) via ECEF rotation."""
    x, y, z = pos
    # GMST angle (radians)
    gmst = 2 * math.pi * (0.7790572732640 + 1.00273781191135448 * (jd - 2451545.0))
    # Rotate ECI->ECEF around Z
    xe = x * math.cos(gmst) + y * math.sin(gmst)
    ye = -x * math.sin(gmst) + y * math.cos(gmst)
    ze = z
    # ECEF -> geodetic (WGS84)
    a = 6378.137  # semi-major axis km
    f = 1.0 / 298.257223563  # flattening
    b = a * (1 - f)  # semi-minor axis
    e2 = 1 - (b / a) ** 2
    lon = math.atan2(ye, xe)
    p = math.sqrt(xe**2 + ye**2)
    lat = math.atan2(ze, p * (1 - e2))
    # Iterate to refine lat
    for _ in range(10):
        sin_lat = math.sin(lat)
        n = a / math.sqrt(1 - e2 * sin_lat * sin_lat)
        h = (
            p / math.cos(lat) - n
            if abs(lat) < math.pi / 3
            else ze / sin_lat - n * (1 - e2)
        )
        lat = math.atan2(ze, p * (1 - e2 * n / (n + h)))
    return lat, lon, max(0.0, h)


# Scan a 24-hour window for passes
from sgp4.conveniences import jday_datetime

start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
passes_found = []
dt_min = 1
scan_minutes = 24 * 60
prev_elev = -90.0
pass_data = None

for minute_offset in range(0, scan_minutes, dt_min):
    t = start + timedelta(minutes=minute_offset)
    jd, fr = jday_datetime(t)
    e_result = satellite.sgp4(jd, fr)
    if len(e_result) == 3:
        err_code, eci_pos, eci_vel = e_result
    else:
        eci_pos, eci_vel = e_result
        err_code = 0
    if eci_pos is None or err_code != 0:
        continue
    lat, lon, alt = eci_to_geodetic(eci_pos, jd)
    sat_lat_deg = math.degrees(lat)
    sat_lon_deg = math.degrees(lon)
    sat_alt_km = alt

    # Great-circle based elevation
    lat1 = math.radians(gs_lat_deg)
    lat2 = math.radians(sat_lat_deg)
    dlon = math.radians(sat_lon_deg - gs_lon_deg)
    cos_gamma = math.sin(lat1) * math.sin(lat2) + math.cos(lat1) * math.cos(
        lat2
    ) * math.cos(dlon)
    r_sat = R_earth + sat_alt_km
    slant_range = math.sqrt(R_earth**2 + r_sat**2 - 2 * R_earth * r_sat * cos_gamma)
    sin_elev = (r_sat * cos_gamma - R_earth) / slant_range
    elevation = math.degrees(math.asin(max(-1, min(1, sin_elev))))

    if elevation > 0 and prev_elev <= 0:
        pass_data = {"aos_time": t, "max_elev": -90.0, "los_time": None}
    if pass_data is not None and elevation > pass_data["max_elev"]:
        pass_data["max_elev"] = elevation
    if pass_data is not None and elevation <= 0 and prev_elev > 0:
        pass_data["los_time"] = t
        if pass_data["max_elev"] > 10:
            passes_found.append(pass_data)
        pass_data = None

    prev_elev = elevation

print(f"  Number of passes found (elev > 10 deg): {len(passes_found)}")
for i, p in enumerate(passes_found[:5]):
    aos_str = p["aos_time"].strftime("%H:%M:%S")
    los_str = p["los_time"].strftime("%H:%M:%S") if p["los_time"] else "N/A"
    dur_min = (
        (p["los_time"] - p["aos_time"]).total_seconds() / 60.0 if p["los_time"] else 0
    )
    print(
        f"    Pass {i+1}: AOS={aos_str}  LOS={los_str}  "
        f"duration={dur_min:.1f} min  max_elev={p['max_elev']:.1f} deg"
    )

if passes_found:
    best_pass = max(passes_found, key=lambda p: p["max_elev"])
    aos = best_pass["aos_time"]
    los = best_pass["los_time"]
    dur_s = (los - aos).total_seconds()
    n_steps = min(60, max(10, int(dur_s / 10)))

    elev_samples = []
    slant_samples = []
    t_total_bits = 0.0

    for i_step in range(n_steps):
        t_step = aos + timedelta(seconds=i_step * dur_s / n_steps)
        jd, fr = jday_datetime(t_step)
        eci_pos, _ = satellite.sgp4(jd, fr)
        if eci_pos is None:
            continue
        lat, lon, alt = eci_to_geodetic(eci_pos, jd)
        sat_lat = math.degrees(lat)
        sat_lon = math.degrees(lon)
        sat_alt = alt

        lat1 = math.radians(gs_lat_deg)
        lat2 = math.radians(sat_lat)
        dlon = math.radians(sat_lon - gs_lon_deg)
        cos_gamma = math.sin(lat1) * math.sin(lat2) + math.cos(lat1) * math.cos(
            lat2
        ) * math.cos(dlon)
        r_s = R_earth + sat_alt
        sr = math.sqrt(R_earth**2 + r_s**2 - 2 * R_earth * r_s * cos_gamma)
        sin_e = (r_s * cos_gamma - R_earth) / sr
        elev = math.degrees(math.asin(max(-1, min(1, sin_e))))

        if elev < 5:
            continue

        elev_samples.append(elev)
        slant_samples.append(sr)

        # Approximate key rate
        qber_val = 0.02 + 0.01 * (1.0 - math.sin(math.radians(elev)))
        L_m = sr * 1000.0
        diff_angle = 1.22 * 850e-9 / 0.3
        beam_r = L_m * diff_angle
        geom_eff = (0.3 / (2.0 * beam_r)) ** 2 if beam_r > 0 else 0
        geom_eff = min(1.0, geom_eff)
        elev_rad = math.radians(max(5, elev))
        air_mass = 1.0 / math.sin(elev_rad)
        rayleigh = 0.0116 * (550.0 / 850.0) ** 4
        atm_path = 8.0 * air_mass
        atm_trans = math.exp(-rayleigh * atm_path)
        total_eff = geom_eff * atm_trans
        loss_frac = 1.0 - max(0.0, min(1.0, total_eff))
        detector_rate = 1e6
        key_rate = detector_rate * (1.0 - loss_frac) * 0.5 * (1.0 - qber_val)
        key_rate = max(0.0, key_rate)

        t_total_bits += key_rate * (dur_s / n_steps)

    print(
        f"  Resampled with {len(elev_samples)} valid points (elev >= 5 deg, from {dur_s:.0f}s pass)"
    )
    if elev_samples:
        print(
            f"  TLE-pass elevation range: {min(elev_samples):.2f} - {max(elev_samples):.2f} deg"
        )
        print(
            f"  TLE-pass slant range:     {min(slant_samples):.2f} - {max(slant_samples):.2f} km"
        )
        print(f"  TLE-pass best elevation:  {best_pass['max_elev']:.2f} deg")
        print(f"  TLE-pass duration:        {dur_s:.0f} s")
    print(f"  TLE-pass estimated key bits: {t_total_bits:.2f}")
else:
    print("  No usable passes found in 24-hour window.")

# 1h. Convenience function simulate_satellite_qkd
print()
print(">>> 1h. simulate_satellite_qkd convenience function")
from qkdpy.network.satellite_qkd import simulate_satellite_qkd

sim_result = simulate_satellite_qkd(
    altitude_km=500.0, ground_lat=28.5, ground_lon=-80.6, num_passes=5
)
print(f"  total_key_bits (5 passes):    {sim_result['total_key_bits']:.2f}")
print(
    f"  ml_predictor_trained:         {sim_result['mission_summary']['ml_predictor_trained']}"
)
print(
    f"  total_passes_simulated:       {sim_result['mission_summary']['total_passes_simulated']}"
)
print(
    f"  estimated_daily_key_bits:     {sim_result['mission_summary']['estimated_daily_key_bits']:.2f}"
)

# ============================================================================
# 2.  QUANTUM NETWORK
# ============================================================================
print()
print(DASH)
print("SECTION 2: QUANTUM NETWORK")
print(DASH)

# 2a. Create network with 3 nodes
print()
print(">>> 2a. Create QuantumNetwork with 3 nodes")
qn = QuantumNetwork(name="TestNet-3", topology_type="star")
for i in range(3):
    protocol = BB84(QuantumChannel(distance=10.0, loss_coefficient=0.2), key_length=128)
    qn.add_node(f"Node{i}", protocol=protocol, position=(i * 10.0, i * 5.0))
print(f"  Nodes: {list(qn.nodes.keys())}")
stats = qn.get_network_statistics()
print(f"  num_nodes: {stats['num_nodes']}")
print(f"  num_connections: {stats['num_connections']}")
print(f"  average_degree: {stats['average_degree']:.2f}")
print(f"  network_diameter: {stats['network_diameter']}")

# 2b. Add connections
print()
print(">>> 2b. Add connections between nodes")
ch01 = QuantumChannel(distance=50.0, loss_coefficient=0.2, detector_efficiency=0.15)
qn.add_connection("Node0", "Node1", channel=ch01, distance=50.0, fiber_type="standard")

ch12 = QuantumChannel(distance=30.0, loss_coefficient=0.18, detector_efficiency=0.15)
qn.add_connection(
    "Node1", "Node2", channel=ch12, distance=30.0, fiber_type="dispersion-shifted"
)

path = qn.get_shortest_path("Node0", "Node2")
print(f"  Shortest path Node0 -> Node2: {path}")
print(f"  Number of connections: {len(qn.connections)}")

# 2c. Establish key between directly connected nodes
print()
print(">>> 2c. Key establishment - direct pair (Node0-Node1)")
key_result = qn.establish_key_between_nodes("Node0", "Node1", key_length=64)
if key_result and key_result.get("key"):
    key_bits = key_result["key"]
    print(f"  key (first 16 bits): {key_bits[:16]}")
    print(f"  key length:          {len(key_bits)}")
    print(f"  qber:                {key_result.get('qber', 'N/A')}")
    print(f"  key_rate:            {key_result.get('key_rate', 'N/A')}")
    print(f"  security:            {key_result.get('security', 'N/A')}")
    print(f"  path:                {key_result.get('path', 'N/A')}")
else:
    print("  Key establishment FAILED or returned unexpected format")
    print(f"  Raw result: {key_result}")

# 2d. Establish key via multi-hop (Node0 -> Node1 -> Node2)
print()
print(">>> 2d. Multi-hop key (Node0 -> Node2)")
key_mh = qn.establish_key_between_nodes("Node0", "Node2", key_length=64)
if key_mh and key_mh.get("key"):
    print(f"  key (first 16 bits): {key_mh['key'][:16]}")
    print(f"  key length:          {len(key_mh['key'])}")
    print(f"  qber:                {key_mh.get('qber', 'N/A')}")
    print(f"  path:                {key_mh.get('path', 'N/A')}")
else:
    print(f"  Multi-hop key result: {key_mh}")

# 2e. Entanglement swapping
print()
print(">>> 2e. Entanglement swapping (Node0-Relay-Node2)")
ch_relay_a = QuantumChannel(distance=20.0)
ch_relay_b = QuantumChannel(distance=20.0)
relay_prot = BB84(QuantumChannel(distance=20.0), key_length=128)
qn.add_node("Relay", protocol=relay_prot, position=(15.0, 5.0))
qn.add_connection("Node0", "Relay", channel=ch_relay_a, distance=20.0)
qn.add_connection("Relay", "Node2", channel=ch_relay_b, distance=20.0)

swap_ok = qn.perform_entanglement_swapping("Node0", "Node2")
print(f"  Entanglement swapping result: {swap_ok}")

# 2f. Network simulation
print()
print(">>> 2f. Network performance simulation")
perf = qn.simulate_network_performance(num_trials=10, path_selection="all_pairs")
print(f"  num_trials:                {perf['num_trials']}")
print(f"  successful_key_exchanges:  {perf['successful_key_exchanges']}")
print(f"  success_rate:              {perf['success_rate']:.4f}")
print(f"  average_key_length:        {perf['average_key_length']:.2f}")
print(f"  average_qber:              {perf['average_qber']:.6f}")
print(f"  average_key_rate:          {perf['average_key_rate']:.6f}")
print(f"  average_execution_time:    {perf['average_execution_time']:.6f} s")
print(f"  qber_std:                  {perf['qber_std']:.6f}")
print(f"  key_rate_std:              {perf['key_rate_std']:.6f}")

# ============================================================================
# 3.  MULTI-PARTY QKD
# ============================================================================
print()
print(DASH)
print("SECTION 3: MULTI-PARTY QKD")
print(DASH)

# 3a. MultiPartyQKD.conference_key_agreement (from quantum_network.py)
print()
print(">>> 3a. Conference key agreement - 3 parties (QuantumNetwork + MultiPartyQKD)")
conf_net = QuantumNetwork(name="ConfNet")
for i in range(3):
    prot = BB84(QuantumChannel(distance=10.0), key_length=64)
    conf_net.add_node(f"P{i}", protocol=prot)
for i in range(3):
    for j in range(i + 1, 3):
        ch = QuantumChannel(distance=10.0, loss_coefficient=0.2)
        conf_net.add_connection(f"P{i}", f"P{j}", channel=ch)

ck = MultiPartyQKD.conference_key_agreement(conf_net, ["P0", "P1", "P2"], key_length=32)
if ck:
    print(f"  Number of participants: {len(ck)}")
    for pid, key in ck.items():
        print(f"    {pid}: key={key[:8]}... (len={len(key)})")
    keys_list = list(ck.values())
    all_match = all(k == keys_list[0] for k in keys_list)
    print(f"  All keys match: {all_match}")
else:
    print("  Conference key agreement FAILED")

# 3b. MultiPartyQKDNetwork (from multiparty_qkd.py)
print()
print(">>> 3b. MultiPartyQKDNetwork - 5 parties")
mpnet = MultiPartyQKDNetwork(nodes=["Alice", "Bob", "Charlie", "Dave", "Eve"])
print(f"  Number of nodes: {len(mpnet.nodes)}")
print(f"  Nodes: {mpnet.nodes}")

for i in range(5):
    n1 = mpnet.nodes[i]
    n2 = mpnet.nodes[(i + 1) % 5]
    ch = QuantumChannel(distance=20.0, loss_coefficient=0.2)
    mpnet.add_channel(n1, n2, ch)

mpstats = mpnet.get_network_statistics()
print(f"  num_channels:            {mpstats['num_channels']}")
print(f"  connectivity:            {mpstats['connectivity']:.4f}")
print(f"  average_channel_loss:    {mpstats['average_channel_loss']:.6f}")
print(f"  num_established_keys:    {mpstats['num_established_keys']}")

# 3c. Pairwise key establishment in MultiPartyQKDNetwork
print()
print(">>> 3c. Pairwise key in MultiPartyQKDNetwork")
key = mpnet.establish_pairwise_key("Alice", "Bob", key_length=64)
if key:
    print(f"  Alice-Bob key (first 16): {key[:16]}")
    print(f"  key length:               {len(key)}")
else:
    print("  Pairwise key FAILED")

# 3d. Simulate eavesdropping attack
print()
print(">>> 3d. Network attack simulation")
attack_result = mpnet.simulate_network_attack("eavesdropping", ["Alice", "Bob"])
print(f"  attack_type:   {attack_result['attack_type']}")
print(f"  detection_status: {attack_result['detection_status']}")
print(f"  affected_channels: {len(attack_result['affected_channels'])}")

# 3e. TrustedRelayNetwork
print()
print(">>> 3e. TrustedRelayNetwork - multi-hop via relay")
trn = TrustedRelayNetwork(
    nodes=["Sender", "Relay1", "Relay2", "Receiver"],
    relay_nodes=["Relay1", "Relay2"],
)
trn.add_channel("Sender", "Relay1", QuantumChannel(distance=50.0))
trn.add_channel("Relay1", "Relay2", QuantumChannel(distance=50.0))
trn.add_channel("Relay2", "Receiver", QuantumChannel(distance=50.0))

mh_key = trn.establish_multihop_key("Sender", "Receiver", key_length=64)
if mh_key:
    print(f"  Multi-hop key (first 16): {mh_key[:16]}")
    print(f"  key length:               {len(mh_key)}")
else:
    print("  Multi-hop key FAILED")

relay_stats = trn.get_relay_statistics()
print(f"  relay_nodes:  {relay_stats['relay_nodes']}")
print(f"  num_relays:   {relay_stats['num_relays']}")
print(f"  total_nodes:  {relay_stats['total_nodes']}")

# ============================================================================
# 4.  NETWORK PROTOCOLS
# ============================================================================
print()
print(DASH)
print("SECTION 4: NETWORK PROTOCOLS (ChannelPredictor protocol)")
print(DASH)

print()
print(">>> 4a. Check EfficientQKDPredictor satisfies ChannelPredictor protocol")
predictor = EfficientQKDPredictor(input_dim=3, max_memory_mb=64)
check = isinstance(predictor, ChannelPredictor)
print(f"  EfficientQKDPredictor satisfies ChannelPredictor: {check}")
print(f"  is_trained (before): {predictor.is_trained}")

# Train with synthetic data
X_train = np.random.randn(20, 3).astype(np.float32)
y_train = np.random.randn(20).astype(np.float32) * 1e6 + 5e6
train_res = predictor.fit(X_train, y_train, epochs=20)
print(f"  epochs_trained:  {train_res['epochs_trained']}")
print(f"  final_train_loss:{train_res['final_train_loss']:.6f}")
print(f"  is_trained (after): {predictor.is_trained}")

# Predict
X_test = np.array([[23.0, 1.0, 0.1]], dtype=np.float32)
pred_val = predictor.predict(X_test)
print(f"  Prediction for [23, 1, 0.1]: {pred_val[0]:.2f} bits")

# ============================================================================
# 5.  REALISTIC QUANTUM NETWORK
# ============================================================================
print()
print(DASH)
print("SECTION 5: REALISTIC QUANTUM NETWORK")
print(DASH)

# 5a. Create network
print()
print(">>> 5a. Create RealisticQuantumNetwork with 3 nodes")
rqn = RealisticQuantumNetwork(name="RealisticNet")
for i in range(3):
    ch = QuantumChannel(distance=15.0, loss_coefficient=0.2)
    prot = BB84(ch, key_length=128)
    rqn.add_node(f"RNode{i}", protocol=prot)

# Add connections with realistic parameters
ch01 = QuantumChannel(
    distance=40.0,
    loss_coefficient=0.2,
    dark_count_rate=1e-6,
    detector_efficiency=0.15,
    misalignment_error=0.03,
)
ch12 = QuantumChannel(
    distance=25.0,
    loss_coefficient=0.18,
    dark_count_rate=8e-7,
    detector_efficiency=0.2,
    misalignment_error=0.02,
)
rqn.add_connection("RNode0", "RNode1", ch01)
rqn.add_connection("RNode1", "RNode2", ch12)

rn_stats = rqn.get_network_statistics()
print(f"  network_name:     {rn_stats['network_name']}")
print(f"  network_status:   {rn_stats['network_status']}")
print(f"  num_nodes:        {rn_stats['num_nodes']}")
print(f"  num_connections:  {rn_stats['num_connections']}")
print(f"  average_degree:   {rn_stats['average_degree']:.2f}")
print(f"  network_diameter: {rn_stats['network_diameter']}")
print(f"  average_node_health: {rn_stats['average_node_health']:.4f}")
print(f"  memory_usage:     {rn_stats['memory_usage']:.4f}")
print(f"  total_keys_generated: {rn_stats['total_keys_generated']}")

# 5b. Key establishment with realistic hardware constraints
print()
print(">>> 5b. Key establishment with realistic constraints")
key_r = rqn.establish_key_between_nodes("RNode0", "RNode1", key_length=64)
if key_r:
    print(f"  Direct key RNode0-RNode1: first 16 bits = {key_r[:16]}")
    print(f"  key length: {len(key_r)}")
    print(f"  total_keys_generated now: {rqn.total_keys_generated}")
else:
    print("  Direct key FAILED")

key_rh = rqn.establish_key_between_nodes("RNode0", "RNode2", key_length=64)
if key_rh:
    print(f"  Multi-hop key RNode0-RNode2: first 16 bits = {key_rh[:16]}")
    print(f"  key length: {len(key_rh)}")
    print(f"  total_keys_generated now: {rqn.total_keys_generated}")
else:
    print("  Multi-hop key FAILED")

# 5c. Node performance metrics
print()
print(">>> 5c. Node performance metrics")
for nid in ["RNode0", "RNode1", "RNode2"]:
    pm = rqn.nodes[nid].get_performance_metrics()
    print(f"  {nid}:")
    print(
        f"    health={pm['health']:.4f}  status={pm['hardware_status']}  "
        f"mem_usage={pm['memory_usage']:.4f}"
    )
    print(
        f"    det_eff={pm['detection_efficiency']:.4f}  "
        f"dark_count={pm['dark_count_rate']:.2e}  "
        f"jitter={pm['jitter']:.2e}"
    )

# 5d. Environmental effects + calibration
print()
print(">>> 5d. Environmental effects simulation and calibration")
rqn.simulate_environmental_effects(time_step=3600.0)  # 1 hour
print("  After environmental simulation:")
for nid in ["RNode0"]:
    pm = rqn.nodes[nid].get_performance_metrics()
    print(
        f"    {nid}: health={pm['health']:.4f}  det_eff={pm['detection_efficiency']:.4f}"
    )

cal_res = rqn.calibrate_network()
print(
    f"  Calibration: successful={cal_res['successful_calibrations']}  "
    f"failed={cal_res['failed_calibrations']}"
)

# 5e. Hardware degradation over multiple operations
print()
print(">>> 5e. Hardware degradation test")
rqn2 = RealisticQuantumNetwork(name="DegradationTest")
for i in range(3):
    ch = QuantumChannel(distance=10.0)
    prot = BB84(ch, key_length=64)
    rqn2.add_node(f"D{i}", protocol=prot)

rqn2.add_connection("D0", "D1", QuantumChannel(distance=20.0, loss_coefficient=0.2))
rqn2.add_connection("D1", "D2", QuantumChannel(distance=20.0, loss_coefficient=0.2))

success_count = 0
for trial in range(50):
    key_d = rqn2.establish_key_between_nodes("D0", "D2", key_length=64)
    if key_d:
        success_count += 1

deg_stats = rqn2.get_network_statistics()
print("  Key establishment attempts: 50")
print(f"  Successful:                 {success_count}")
print(f"  Success rate:               {success_count/50:.4f}")
print(f"  Total keys generated:       {deg_stats['total_keys_generated']}")
print(f"  Average node health:        {deg_stats['average_node_health']:.4f}")
print(f"  Network status:             {deg_stats['network_status']}")
print(f"  Memory usage:               {deg_stats['memory_usage']:.4f}")

# ============================================================================
# SUMMARY
# ============================================================================
print()
print(SEP)
print("TEST COMPLETE - ALL MODULES EXERCISED")
print(SEP)
print("""
Modules tested:
  - satellite_qkd.py:  SatelliteQKD, FreeSpaceOpticalChannel,
                       AtmosphericProfile, SatellitePosition,
                       OrbitType, simulate_satellite_qkd
  - quantum_network.py: QuantumNetwork, QuantumNode, MultiPartyQKD
  - multiparty_qkd.py:  MultiPartyQKDNetwork, TrustedRelayNetwork
  - protocols.py:       ChannelPredictor protocol
  - realistic_quantum_network.py: RealisticQuantumNetwork, RealisticQuantumNode
  - ml/efficient_models.py:       EfficientQKDPredictor

External:
  - CelesTrak TLE fetch (with graceful fallback to simulated TLE)
  - sgp4 satellite propagation
""")
