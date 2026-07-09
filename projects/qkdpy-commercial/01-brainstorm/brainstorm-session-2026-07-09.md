# Brainstorm Session — QKDpy Commercialization

Date: 2026-07-09
Session: 1

## Ideas Generated

### 1. Open Core + Enterprise
| Field | Value |
|-------|-------|
| **One-liner** | Free open-source QKD simulation with paid enterprise compliance, ML, and support tiers |
| **Target user** | R&D teams in telecom, defense, and research who already use QKDpy and need production guarantees |
| **Problem** | Teams adopt open-source QKDpy for prototyping but can't use it in production without compliance reporting, SLA, priority support |
| **Why now** | Open-core is proven (GitLab, Redis, Grafana). First QKD networks being deployed — production need is emerging now |
| **Quick risk** | Will enterprises pay for a Python library? Need productized features beyond support (compliance dashboards, audit exports) |
| **Demand** | 4/5 |
| **Buildability** | 5/5 |
| **Moat** | 3/5 |

**Verdict: Top contender** — lowest risk, leverages 100% of existing codebase, proven business model.

---

### 2. Quantum-Safe Migration Toolkit
| Field | Value |
|-------|-------|
| **One-liner** | Combined QKD + PQC migration assessment and planning tool for enterprise security teams |
| **Target user** | CISO / enterprise security architecture teams planning post-quantum migration |
| **Problem** | Most enterprises don't know their crypto inventory, can't assess QKD vs PQC fit, have no migration roadmap |
| **Why now** | NSA/CISA "PQC timeline" publications, ETSI QKD standards finalizing, compliance pressure building |
| **Quick risk** | Crowded space — many PQC consulting firms, Cloudflare, big vendors moving in |
| **Demand** | 5/5 |
| **Buildability** | 4/5 |
| **Moat** | 3/5 |

**Verdict: Top contender** — best market timing, but need differentiation from PQC-only incumbents.

---

### 3. QKD Compliance Suite
| Field | Value |
|-------|-------|
| **One-liner** | Automated compliance verification for ETSI, ISO, NIST, and FIPS QKD standards |
| **Target user** | QKD hardware vendors, network operators, defense contractors who need certification |
| **Problem** | QKD standards (ETSI GS QKD 014/016, ISO 23837) are complex and evolving. Manual compliance checking is slow and error-prone |
| **Why now** | First ETSI standards finalized 2024-2025. EuroQCI, China national QKD network creating compliance demand |
| **Quick risk** | Market is small today (maybe 200-500 orgs globally). Need to be right on timing |
| **Demand** | 4/5 |
| **Buildability** | 4/5 |
| **Moat** | 3/5 |

**Verdict: Strong** — technical moat from existing compliance code, but market size risk.

---

### 4. QKD Security Auditor
| Field | Value |
|-------|-------|
| **One-liner** | ML-powered continuous security auditing for operational QKD networks |
| **Target user** | QKD network operations teams, managed security service providers |
| **Problem** | QKD networks need real-time attack detection (PNS, Trojan-horse, wavelength attacks). Most teams lack ML expertise |
| **Why now** | First commercial QKD networks going live in Europe and China. Security operations need tooling |
| **Quick risk** | Ongoing R&D cost to stay ahead of attack methods. Convincing ops teams to trust ML detection |
| **Demand** | 3/5 |
| **Buildability** | 3/5 |
| **Moat** | 4/5 |

**Verdict: Worth exploring** — high moat from ML + domain expertise, but niche market.

---

### 5. QKD Network Simulator (Managed)
| Field | Value |
|-------|-------|
| **One-liner** | Cloud-hosted QKD network simulation for planning ground and satellite QKD deployments |
| **Target user** | Telecom network planners, government agencies planning QKD infrastructure |
| **Problem** | Planning QKD deployments requires complex simulation of channel losses, satellite pass timing, key generation rates |
| **Why now** | EuroQCI, China QKD network, US quantum networking initiatives all creating planning needs |
| **Quick risk** | Long telco sales cycles (12-18 months). Need to compete with internal tools at Nokia/Ericsson/Huawei |
| **Demand** | 3/5 |
| **Buildability** | 3/5 |
| **Moat** | 3/5 |

**Verdict: Risky** — good product fit but brutal enterprise sales cycle for a small team.

---

### 6. QKD Training & Certification Platform
| Field | Value |
|-------|-------|
| **One-liner** | Structured online training and certification for QKD engineers and architects |
| **Target user** | New engineers entering quantum networking, telecom technicians retraining |
| **Problem** | Extreme shortage of QKD-literate engineers. No standardized training exists |
| **Why now** | First university quantum networking programs starting. Industry demand outpacing talent pipeline |
| **Quick risk** | Edtech is hard to monetize at small scale. Would need significant content investment |
| **Demand** | 4/5 |
| **Buildability** | 4/5 |
| **Moat** | 2/5 |

**Verdict: Complementary** — good add-on to another offering, weak standalone.

---

### 7. Hardware-in-the-Loop (HIL) Test Platform
| Field | Value |
|-------|-------|
| **One-liner** | Connect QKDpy simulation to real QKD hardware for automated regression and performance testing |
| **Target user** | QKD hardware manufacturers (ID Quantique, Toshiba, QuantumCTek, etc.) |
| **Problem** | Hardware teams lack repeatable test environments. Field testing is expensive and slow |
| **Why now** | Multiple QKD hardware vendors shipping commercial products — all need testing tooling |
| **Quick risk** | Partnership-dependent. Each vendor has proprietary APIs. Very niche |
| **Demand** | 2/5 |
| **Buildability** | 2/5 |
| **Moat** | 3/5 |

**Verdict: Too niche** — requires hardware partnerships, small total addressable market.

---

### 8. QKD Consulting + Software
| Field | Value |
|-------|-------|
| **One-liner** | Expert consulting on QKD deployment architecture with software tooling as the delivery vehicle |
| **Target user** | Enterprises and government agencies deploying QKD for the first time |
| **Problem** | QKD deployment requires expertise that doesn't exist inside most organizations |
| **Why now** | Early market means consulting is the wedge — sell expertise, keep the software as IP |
| **Quick risk** | Consulting doesn't scale. Need to productize to exit the services trap |
| **Demand** | 4/5 |
| **Buildability** | 3/5 |
| **Moat** | 2/5 |

**Verdict: Entry strategy** — good way to learn customer needs, dangerous as long-term model.

---

## Rankings

| Rank | Idea | Avg Score | Why |
|------|------|-----------|-----|
| 1 | Open Core + Enterprise | 4.0 | Lowest risk, leverages all existing code, proven model |
| 2 | Quantum-Safe Migration Toolkit | 4.0 | Best market timing, huge TAM, but more crowded |
| 3 | QKD Compliance Suite | 3.7 | Strong moat from existing compliance code, timing-dependent |
| 4 | QKD Training | 3.3 | Good add-on, weak standalone |
| 5 | QKD Security Auditor | 3.3 | High moat but small market |
| 6 | QKD Network Simulator | 3.0 | Good fit but brutal sales cycle |
| 7 | QKD Consulting | 3.0 | Entry strategy, doesn't scale |
| 8 | HIL Test Platform | 2.3 | Too niche, partnership-dependent |

## Top 3 Recommendations

1. **Open Core + Enterprise** — Start here. Lowest risk, and the enterprise compliance features already exist in the codebase. Ship enterprise tier with compliance reporting, ML detection, and priority support.
2. **Quantum-Safe Migration Toolkit** — Medium-term play. Leverage QKD expertise to build assessment tools, differentiate from PQC-only vendors.
3. **QKD Compliance Suite** — Adjacent to #1. Could be a feature of the enterprise tier or standalone product.
