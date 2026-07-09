# Strategic Research Synthesis: QKDpy's Next Moves

Date: 2026-07-09
Based on: 5 parallel deep dives (4-5 queries each) via Exa deep search, building on 48 prior queries
Topics: ML-for-QKD, QKD Standards, Network Simulators, PQC+QKD, Side-Channel Attacks

---

## TL;DR

Three clear actions for QKDpy emerge from all five deep dives. **ML integration** is the #1 differentiator — no competitor packages ML for QKD, and the research field is exploding (OptiQKD 2026, TCNs, RL, XGBoost). **ETSI GS QKD 014 compliance** is the highest-impact near-term fix — open-source reference implementations exist, and it unlocks enterprise credibility. **Side-channel analysis** is validated by active research and strengthens QKDpy's unique security position. Network simulators are complementary, not competitive. PQC+QKD hybrid is a future opportunity but not urgent now.

---

## 1. ML-for-QKD Research

### Key Findings

The ML-for-QKD field is accelerating rapidly with 2025-2026 seeing a surge of papers:

| Paper/Method | Year | Application | Key Result |
|-------------|------|-------------|------------|
| OptiQKD (arXiv:2603.04192) | 2026 | Real-time parameter tuning via ML | General-purpose ML optimization framework for QKD |
| Deep RL + VAE for QKD | 2025 | Quantum security modeling | Integrated RL + VAE model for enhanced security |
| ML-based CV-QKD optimization | 2026 | Mode mismatch mitigation | Optimizes transmitter pulse-shape to minimize mode mismatch |
| TCN phase compensation | 2024 | CV-QKD phase recovery | TCN outperforms traditional methods for phase estimation |
| Real-Time QBER Diagnostics | 2024 | QBER time-series analysis | ML diagnostics on QKD link via time series |
| Neural excess noise estimation | 2024 | CV-QKD noise estimation | NN for composable finite-size security |
| Final-XGBoost | 2025 | Bayesian parameter optimization | XGBoost with Bayesian tuning for QKD parameter selection |
| NN secret-key rate prediction | 2022 | Key rate prediction | **6 orders of magnitude speedup** vs numerical methods |
| Data-efficient QKD learning | 2026 | QBER estimation under noisy channels | Gaussian process regression for uncertainty-aware estimation |
| AutoML for CV-QKD SKR | 2022 | Automated secure key rate optimization | AutoML pipeline for discrete-modulated CV-QKD |
| Survey: ML-assisted CV-QKD | 2023 | Comprehensive survey | Systematic review of ML methods for CV-QKD |

### Research Themes

1. **Parameter optimization is the dominant use case** — OptiQKD, RL-based optimization, Bayesian XGBoost all target real-time parameter tuning. This is QKDpy's `predictor` and `optimizer` modules.
2. **QBER prediction is mature** — TCNs, Gaussian processes, and XGBoost hybrids all work. QKDpy's `anomaly detector` maps directly.
3. **Key rate prediction has proven speedup** — NNs achieve 6 orders of magnitude speedup. This validates QKDpy's ML approach.
4. **CV-QKD gets most ML attention** — excess noise estimation, phase compensation, mode mismatch. QKDpy's CVQKD + ML combo is well-positioned.

### What This Means for QKDpy

**The ML advantage is real and growing.** Every paper in 2025-2026 builds custom ML pipelines from scratch. No competitor packages ML into a library. QKDpy's 5 built-in ML components (predictor, optimizer, anomaly detector, knowledge distillation, adaptive model selector) are a genuine first-mover advantage.

**Risk**: This advantage erodes as the field matures. If NetSquid or SimQN adds ML within 12-18 months, QKDpy loses its key differentiator.

---

## 2. QKD Standards Landscape

### Key Findings

The standards ecosystem is clearer than the competitive teardown initially suggested:

| Standard | Status | What It Covers | Implementation Availability |
|----------|--------|---------------|---------------------------|
| **ETSI GS QKD 014** | Published, V2.x | KME-SA interface (key delivery API) | **Multiple open-source impls** (Python, Rust, C) |
| **ETSI GS QKD 016** | **V2.1.1 (2024-01), BSI-CERTIFIED** | Common Criteria Protection Profile | Certified by BSI (BSI-CC-PP-0120-2024) |
| **ISO/IEC 23837-1** | Published 2023 | Security requirements for QKD | Standard document only |
| **ISO/IEC 23837-2** | Published 2023 | Evaluation and testing methods | Standard document only |
| **ITU-T X.1711** | Published March 2026 | Framework of QKD protocols in QKDN | Within ITU framework |
| **NIST FIPS 203** | Finalized Aug 2024 | ML-KEM (PQC, not QKD) | Multiple implementations |

### Open-Source ETSI 014 Implementations

| Project | Language | Maturity | Features |
|---------|----------|----------|----------|
| qkdsec (pypi) | Python | Released v0.2.0 | Full ETSI GS QKD 014 client, conformance probe, BB84 sim |
| qkd-client (crates.io) | Rust | v0.1.0 (Feb 2026) | ETSI 014 + VRF zero-knowledge + PQ signatures + consensus |
| TUe-QTS/ETSI-QKD014-client | Rust/C | 5 stars | CLI program and library, ETSI 014 compliance |
| qursa-uc3m/qkd-etsi-api | C | 9 stars | C wrapper for ETSI GS QKD 004/014 APIs |
| qkd_kme_server | Python | Active | ETSI-compliant KME server |
| QKDLite (pQCee) | Middleware | Active | ETSI 014 business integration middleware |

### What This Means for QKDpy

**The compliance module should target ETSI GS QKD 014 first.** This is the most widely implemented standard with open-source reference code. Adding ETSI GS QKD 016 (Common Criteria) awareness as a secondary target makes sense.

**qkdsec already has an ETSI 014 client.** QKDpy should either integrate with qkdsec or implement its own ETSI 014 client. The Rust implementation (qkd-client) also has interesting features (VRF, PQ signatures) that QKDpy could learn from.

**ITU-T is actively standardizing QKDN** (Study Groups 11, 13, 17 — active 2026). QKDpy's network module should track ITU-T X.1711 for protocol framework alignment.

---

## 3. Quantum Network Simulators

### Key Findings

| Simulator | Stars | Approach | Best For | QKD Focus |
|-----------|-------|----------|----------|-----------|
| **SimQN** | 561 | Discrete-event, network-layer, Python/Cython | Large-scale quantum network investigation | QKD protocols as one use case |
| **NetSquid** | ~500 | Discrete-event, modular HW models, Python/C | Hardware-accurate network simulation | User-implemented QKD protocols |
| **SeQUeNCe** | ~200 | Modular discrete-event, Python | Photonic network modeling | Protocol components |
| **QuISP** | ~100 | OMNeT++/C++ | Quantum repeater networks | Repeater-focused |
| **Q2NS** | New (2026) | ns-3 based, modular | Classical-quantum co-simulation | Extensible |
| **SQUANCH** | ~30 | Python, parallelized | Distributed quantum sim | Protocol components |
| **QKDNetSim** | ~20 | NS-3 module | QKD network simulation | **KMS with key-relay** |
| **Quditto** | New (2025) | Digital twin platform | Orchestrated QKD deployments | Emulation platform |

### Critical Insight: SimQN at 561 stars

SimQN's 561 stars vs QKDpy's 6 is NOT because QKDpy is worse — it's because SimQN:
- Comes from a known university lab (USTC) with published papers
- Has a dedicated project page (qnlab-ustc.com)
- Targets "quantum network investigation" — a broader market
- Has documentation (Sphinx-based)

**SimQN is NOT a QKD library.** It does QKD as one use case among many (entanglement distribution, routing, resource allocation). QKDpy is more specialized and deeper in QKD.

### New Entrant: Q2NS (2026)

Q2NS on ns-3 is worth watching. It's very new (arXiv:2603.02857, 2026) but built on a mature simulation framework (ns-3). If it gains traction, it could become the simulation backend of choice for QKD network research — similar to how NetSquid dominates hardware-accurate simulation.

### Quditto: Digital Twin for QKD

Quditto (arXiv:2512.15408) is a digital twin platform for QKD networks. This is a different approach — emulation over real infrastructure rather than simulation. It suggests the field is maturing toward deployment.

### What This Means for QKDpy

**Don't compete with SimQN/NetSquid on network simulation fidelity.** Instead:
1. **Hardware backend adapter for SimQN/NetSquid** — Allow users to plug QKDpy protocols into SimQN or NetSquid for the physical layer. This neutralizes the "no hardware" criticism while keeping QKDpy's protocol library intact.
2. **Position as the QKD protocol library that simulators use** — "QKDpy protocols run on SimQN, NetSquid, or standalone." This is a leverage play, not a build-moat play.
3. **Monitor Q2NS** — If it gains traction, add an adapter.

---

## 4. PQC + QKD Hybrid Landscape

### Key Findings

**The consensus is clear: PQC and QKD are complementary, not competing.**

- "PQC-Enhanced QKD Networks: A Layered Approach" (IEEE QCNC 2026) — formal layered architecture for combining them
- "Hybrid Quantum Security: Integrating QKD and PQC in Brownfield Optical Networks" — practical brownfield deployment approach
- "PQC vs QKD: When to Use Software, Hardware, or Both" — decision framework exists

### Standards Status

NIST finalized 3 PQC standards in August 2024:
- **FIPS 203**: ML-KEM (Module-Lattice-Based Key-Encapsulation Mechanism)
- **FIPS 204**: ML-DSA (Module-Lattice-Based Digital Signature Algorithm)
- **FIPS 205**: SLH-DSA (Stateless Hash-Based Digital Signature Algorithm)

### PQC Libraries

| Library | Status | Features | Relevance to QKDpy |
|---------|--------|----------|-------------------|
| liboqs-python v0.15.0 | Active, well-maintained | All NIST-standardized PQC algorithms | Can be dependency for PQC integration |
| quantum-safe-py | Active | Hybrid KEM, signatures, audit scanner | Production-grade, good reference |
| liboqs-qkd | 0 stars, fork | QKD-enhanced liboqs | Prototype, early stage |

### Production Hybrid Deployments Already Exist

Chrome, Signal, iMessage, Cloudflare, and AWS already use hybrid PQC (classical + PQ). Enterprise migration frameworks are available (5-phase playbooks).

### What This Means for QKDpy

**PQC integration is a mid-term opportunity, not urgent.** The ecosystem is still maturing — NIST standards only finalized August 2024. Production deployments exist at tech giants but enterprise adoption is just beginning.

**QKDpy's role** could be:
1. **Hybrid key exchange simulation** — Simulate QKD + PQC hybrid protocols in one environment
2. **PQC-aware compliance checks** — Add PQC standards to compliance module
3. **Not a PQC library** — QKDpy should NOT build its own PQC implementation. Integrate with liboqs-python or quantum-safe-py instead.

---

## 5. Side-Channel Attacks on QKD

### Key Findings

Side-channel attacks on QKD are an active, growing research area with high-profile results:

| Attack Type | Target | Method | Effectiveness | Year |
|------------|--------|--------|---------------|------|
| **RF side-channel** | QKD electronics | Deep learning (CNN) on RF emissions | **Near-perfect key recovery** | 2023 |
| **TEMPEST attack** | QKD sender | Deep learning on electromagnetic emissions | Key extraction demonstrated | 2023 |
| **Trojan-horse** | QKD system | Bright pulse injection | Classic, well-characterized | 2015+ |
| **SPAD bright illumination** | Single-photon detectors | Bright light blinds SPADs | Hacks commercial systems | 2010 |
| **SPAD backflash** | Avalanche diodes | Secondary photon emission | Zero-error attack vector | 2016 |
| **Power analysis** | QKD electronics | Power consumption at 100MHz | 73.35% qubit prediction | 2025 |

### Research Validation

The side-channel field is producing comprehensive surveys:
- **"Cybersecurity of QKD Implementations"** (arXiv:2508.04669, 2025) — comprehensive survey of QKD implementation vulnerabilities
- **"From Provable to Practical"** (arXiv:2605.27497, 2026) — ML-based security analysis survey for QKD
- **"SQOUT"** (arXiv:2510.23462) — risk-based threat analysis framework for quantum communication
- **"Bridging the Gap"** (IEEE QCNC 2026) — systematic security assessment of commercial QKD
- **"The practical issues of side-channel-secure QKD"** (arXiv:2508.15197) — implementation challenges
- **"Side-Channel Attacks to QKD Systems and Mitigation Techniques"** (IEEE IMOC 2025)

### The Capability Gap

Despite the volume of research, there is **no integrated side-channel simulation tool** for QKD. Papers are theoretical or attack-specific. No existing library lets a QKD developer:
1. Model a side-channel (RF, EM, power, optical)
2. Simulate its impact on key rate/security
3. Evaluate countermeasures

**This is QKDpy's opportunity.**

### What This Means for QKDpy

**The side-channel analysis module is well-timed and unique.** The research validates that:
- Side-channel attacks are real and effective (near-perfect key recovery demonstrated)
- The field is producing surveys and frameworks (SQOUT, Bridging the Gap)
- **No competitor provides simulation-side security analysis**

QKDpy could position its side-channel module as the research-to-practice bridge — "use our module to simulate attacks and evaluate countermeasures before building hardware."

---

## Strategic Synthesis

### Decision Framework

| Dimension | QKDpy's Position | Competitive Pressure | Urgency |
|-----------|-----------------|---------------------|---------|
| **ML integration** | Unique, first-mover | Eroding (papers building their own) | **HIGH** — capitalize now |
| **Protocol breadth** | 3-5x any competitor | Low (no one building protocols) | Medium — maintain |
| **ETSI compliance** | Wrong standards | Multiple open-source ETSI 014 clients | **HIGH** — fix now |
| **Side-channel analysis** | Unique, validated | Zero competitors | Medium — grow |
| **Documentation** | Non-existent | All competitors weak here | **HIGH** — easy win |
| **Distribution** | 6 stars, 97 downloads/mo | Terrible | **CRITICAL** — block everything |
| **Network simulator adapter** | None | No one integrating either | Medium-long — build |

### Two Strategic Paths

**Path A: Become the ML-for-QKD library**
- Double down on ML components
- Publish ML benchmarks against brute-force simulation
- Target "protocol comparison + ML optimization" use case
- Risk: ML advantage is time-limited

**Path B: Become the QKD deployment validation tool**
- Fix ETSI compliance first
- Add hardware backend adapter (SimQN, NetSquid)
- Grow side-channel analysis into full security assessment
- Target "pre-deployment validation" use case
- Risk: Longer time-to-market, more dependencies

**Recommended: Both, sequenced. Path A for immediate differentiation (Q3 2026), Path B for moat-building (Q4 2026+).**

### Specific Next Steps (Prioritized)

1. **Fix compliance to ETSI GS QKD 014** — Reference implementations exist (qkdsec, TUe-QTS). This is the single highest-impact code change.
2. **Publish ML benchmarks** — Compare QKDpy's predictor/optimizer against brute-force simulation. Cite OptiQKD (2026), TCNs, XGBoost context. Attracts citations and credibility.
3. **Documentation overhaul** — Sphinx docs + API reference + "Protocol Comparison" tutorial. Low effort, high impact.
4. **Side-channel module expansion** — Add RF/EM attack models based on published research. SQOUT framework alignment.
5. **SimQN adapter** — Allow QKDpy protocols to run on SimQN's physical layer. Neutralizes "no hardware" criticism.
6. **PQC awareness** — Track liboqs-python for future hybrid simulation integration. Not urgent.

### Open Questions

- Should QKDpy integrate with qkdsec's ETSI 014 client or build its own?
- Is the SimQN API stable enough for an adapter, or wait for Q2NS?
- Should QKDpy's side-channel module align with the SQOUT threat framework?
- What's the right PyPI positioning: "ML-for-QKD" or "QKD deployment toolkit"?

---

## Sources

### ML-for-QKD
- OptiQKD (arXiv:2603.04192, 2026) — https://arxiv.org/abs/2603.04192
- Deep RL + VAE for QKD (MethodsX, 2025) — https://doi.org/10.1016/j.mex.2025.103445
- ML-based CV-QKD Optimization (arXiv:2606.31534, 2026) — https://arxiv.org/html/2606.31534v1
- Mode Mismatch Mitigation CV-QKD (arXiv:2505.07726, 2025) — https://arxiv.org/pdf/2505.07726
- Real-Time QBER Diagnostics (Entropy, 2024) — https://doi.org/10.3390/e26110922
- TCN Phase Compensation (JPA, 2024) — https://iopscience.iop.org/article/10.1088/1751-8121/ad31fe
- ML-assisted CV-QKD Survey (MDPI, 2023) — https://www.mdpi.com/2078-2489/14/10/553
- NN Excess Noise Estimation (Quantum Sci. Technol., 2024) — https://iopscience.iop.org/article/10.1088/2058-9565/ae4268
- Neural SKR Prediction (Sci. Reports, 2022) — https://preview-www.nature.com/articles/s41598-022-12647-x
- AutoML for CV-QKD SKR (arXiv:2201.09419, 2022) — https://ar5iv.labs.arxiv.org/html/2201.09419
- ML Optimal Parameter Prediction (Phys. Rev. A) — https://journals.aps.org/pra/abstract/10.1103/PhysRevA.100.062334
- Final-XGBoost QKD Optimization (Phys. Scripta, 2025) — https://doi.org/10.1088/1402-4896/addfb4
- Data-Efficient QKD Learning (IATMSI, 2026) — https://doi.org/10.1109/iatmsi68868.2026.11466042

### QKD Standards
- qkdsec v0.2.0 — https://pypi.org/project/qkdsec/
- TUe-QTS/ETSI-QKD014-client — https://github.com/TUe-QTS/ETSI-QKD014-client (Rust/C)
- qkd-client (crates.io) — https://crates.io/crates/qkd-client (Rust)
- qursa-uc3m/qkd-etsi-api — https://github.com/qursa-uc3m/qkd-etsi-api (C)
- ISO/IEC 23837-2:2023 — https://www.iso.org/obp/ui/en/#!iso:std:77097:en
- BSI-CC-PP-0120-2024 (ETSI GS QKD 016) — https://www.commoncriteriaportal.org/files/ppfiles/pp0120a_pdf.pdf
- ETSI GS QKD 016 V2.1.1 — https://www.etsi.org/deliver/etsi_gs/QKD/001_099/016/02.01.01_60/gs_QKD016v020101p.pdf
- ETSI ISG QKD — https://www.etsi.org/technical-groups/qkd/
- ITU-T QKDN Liaison (2026) — https://www.ietf.org/lib/dt/documents/LIAISON/liaison-2026-04-01-itu-t-sg-11
- ITU-T X.1711 (March 2026) — via NQSN standards tracker
- QKDNetSim — https://github.com/quantstellarlab/qkdnetsim
- Quditto — https://github.com/Networks-it-uc3m/QDTS

### Quantum Network Simulators
- SimQN — https://qnlab-ustc.com/projects/simqn/ (documentation), https://github.com/QNLab-USTC/SimQN (repo)
- Q2NS (arXiv:2603.02857, 2026) — https://www.arxiv.org/pdf/2603.02857
- NetSquid (Nature Comms Phys, 2021) — https://preview-www.nature.com/articles/s42005-021-00647-8
- Review: Software for Quantum Networks (Adv. Quantum Technol., 2025) — https://doi.org/10.1002/qute.202500808
- Quantum Network Sim: Roadmap (QCNC 2026) — https://arxiv.org/html/2603.01980v1
- Multipurpose Quantum Net Sim comparison — https://sol.sbc.org.br/index.php/wqunets/article/download/30010/29817/
- SQUANCH — https://doi.org/10.48550/arxiv.1808.07047
- SDN-enabled QKD networks (arXiv:2411.01970) — https://doi.org/10.48550/arxiv.2411.01970

### PQC + QKD Hybrid
- PQC-Enhanced QKD Networks (IEEE QCNC 2026) — https://doi.org/10.1109/qcnc69040.2026.00060
- Hybrid Quantum Security: QKD+PQC Brownfield (Quantum Insights, 2026) — https://doi.org/10.13052/qi2795-0492.116
- liboqs-python v0.15.0 — https://pypi.org/project/liboqs-python/
- quantum-safe-py — https://github.com/AnimeshShaw/quantum-safe
- liboqs-qkd — https://github.com/QuantumUPB/liboqs-qkd
- NIST PQC Standards (FIPS 203, 204, 205) — https://www.nist.gov/news-events/news/2024/08/nist-releases-first-3-finalized-post-quantum-encryption-standards
- Hybrid PQC Migration Playbook — https://quantumsequrity.com/blog/hybrid-migration-strategy-step-by-step
- Enterprise PQC Migration Roadmap — https://entangledfuture.com/quantum-safe-cryptography/migration-roadmap/
- PQC vs QKD Decision Guide — https://coqubit.com/pqc-vs-qkd-which-quantum-safe-approach-fits-your-network
- PQC vs Quantum Cryptography — https://quantumsecuritydefence.com/quantum-news/post-quantum-vs-quantum-cryptography-difference/

### Side-Channel Attacks
- DL-based RF side-channel on QKD (Phys. Rev. Applied 20, 054040) — https://doi.org/10.1103/physrevapplied.20.054040
- DL TEMPEST on QKD Sender (EQEC 2023) — https://opg.optica.org/abstract.cfm?uri=EQEC-2023-eb_p_1
- Trojan-horse on QKD (IEEE JSTQE, 2015) — http://www.vad1.com/publications/jain2015.IEEEJSelTopQuantumElectron-21-6600710.pdf
- Bright illumination hacking SPADs (Nature Photonics, 2010) — https://preview-www.nature.com/articles/nphoton.2010.214
- SPAD backflash radiation (Light: Science & Apps, 2016) — https://www.nature.com/articles/lsa2016261
- From Provable to Practical survey (arXiv:2605.27497, 2026) — https://arxiv.org/html/2605.27497v1
- Practical issues of SC-secure QKD (arXiv:2508.15197) — https://arxiv.org/html/2508.15197v1
- Cybersecurity of QKD Implementations (arXiv:2508.04669, 2025) — https://arxiv.org/pdf/2508.04669
- SQOUT Threat Framework (arXiv:2510.23462) — https://arxiv.org/html/2510.23462v1
- Bridging the Gap: QKD Security Assessment (IEEE QCNC 2026) — https://doi.org/10.1109/qcnc69040.2026.00022
- Side-Channel Attacks and Mitigation (IEEE IMOC, 2025) — https://doi.org/10.1109/imoc65414.2025.11365812
- Security vs side-channel leakage (Optics Express, 2024) — https://doi.org/10.1364/oe.560660
