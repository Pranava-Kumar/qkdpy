"""Phase 2: Exhaustive deep research — QKD simulation landscape.

Discovers competitors, features, gaps, and market reality.
Does NOT validate assumptions — explores blind spots.
"""

import json
import os

from exa_py import Exa

exa_api_key = os.environ.get("EXA_API_KEY")
if not exa_api_key:
    msg = "EXA_API_KEY not set in environment"
    raise RuntimeError(msg)

exa = Exa(api_key=exa_api_key)

QUERIES = [
    # === Discover unknown competitors ===
    "quantum key distribution simulation framework python library not Qiskit",
    "qkd simulation open source software 2025 2026",
    "quantum cryptography library python pip",
    "quantum network simulator comparison features protocols",
    # === Deep dive each known competitor ===
    "qkdsec quantum key distribution toolkit features protocols",
    "qosst quantum open software secure transmissions CVQKD features",
    "qunetsim quantum network simulation latest version 2025 2026",
    "simulaqron 4.0 features NetQASM architecture",
    # === Survey papers / comparisons ===
    "survey quantum key distribution simulation tools comparison 2024 2025 2026",
    "review quantum network simulators open source comparison",
    "comparative analysis BB84 E91 CVQKD HDQKD simulation performance"
    # === Feature-specific deep dives ===
    "quantum key distribution error correction privacy amplification implementation library",
    "quantum key distribution security analysis side channel attack simulation",
    "quantum key distribution entanglement based E91 BBM92 simulation",
    "decoy state BB84 simulation implementation open source",
    "SARG04 quantum key distribution protocol implementation",
    "twin field quantum key distribution simulation open source",
    "measurement device independent quantum key distribution simulation open source",
    # === Extended protocols ===
    "continuous variable quantum key distribution open source implementation comparison",
    "high dimensional quantum key distribution open source implementation",
    "device independent quantum key distribution open source simulation",
    "quantum key distribution satellite link simulation open source",
    "free space optical quantum communication simulation python",
    # === ML + QKD (broader than before) ===
    "machine learning quantum key distribution optimization 2025 2026",
    "quantum key distribution parameter optimization reinforcement learning",
    "neural network quantum bit error rate prediction QKD",
    "quantum key distribution key rate prediction machine learning",
    # === Enterprise / deployment ===
    "quantum key distribution enterprise deployment management software",
    "quantum key distribution network management open source",
    "quantum key distribution key management system open source",
    "quantum key distribution compliance ETSI ISO standards certification",
    # === Commercial landscape ===
    "ID Quantique quantum key distribution products software",
    "QuintessenceLabs quantum key distribution software features",
    "quantum key distribution startup companies software platform 2025 2026",
    # === Academic / research tools ===
    "quantum key distribution numerical security proof framework open source",
    "quantum key distribution simulation MATLAB Simulink toolbox",
    "quantum internet simulator experimental testbed software",
    # === Related libraries (might be competitors) ===
    "post quantum cryptography python library comparison",
    "quantum random number generation software python",
    "quantum communication simulation library C++ Python",
]


def run_search(query: str) -> dict:
    print(f"\n{'='*60}")
    print(f"Q: {query}")
    print(f"{'='*60}")
    try:
        result = exa.search(
            query,
            type="deep",
            num_results=8,
            contents={
                "highlights": True,
                "text": {"max_characters": 2000, "verbosity": "compact"},
            },
            output_schema={
                "type": "object",
                "description": "Research findings",
                "required": ["findings", "competitors_mentioned", "sources"],
                "properties": {
                    "findings": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["finding"],
                            "properties": {
                                "finding": {"type": "string"},
                                "detail": {"type": "string"},
                            },
                        },
                    },
                    "competitors_mentioned": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["name"],
                            "properties": {
                                "name": {"type": "string"},
                                "relevance": {"type": "string"},
                            },
                        },
                    },
                    "sources": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["url", "title"],
                            "properties": {
                                "url": {"type": "string"},
                                "title": {"type": "string"},
                                "type": {"type": "string"},
                            },
                        },
                    },
                },
            },
        )
        if result.output and result.output.content:
            content = result.output.content
            print(
                json.dumps(content, indent=2) if isinstance(content, dict) else content
            )
        for r in result.results[:3]:
            title = getattr(r, "title", "") or ""
            url = getattr(r, "url", "") or ""
            print(f"\n--- {title[:80]} ---")
            print(f"  URL: {url}")
            if hasattr(r, "highlights") and r.highlights:
                for h in r.highlights[:2]:
                    print(f"  > {str(h)[:200]}")
        return result
    except Exception as e:
        print(f"ERROR: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    results = {}
    for i, q in enumerate(QUERIES):
        print(f"\n[{i+1}/{len(QUERIES)}] ", end="")
        results[q] = run_search(q)

    # Save
    with open("02-research/exa-deep-research.json", "w") as f:
        json.dump({k: str(v) for k, v in results.items()}, f, indent=2)
    print(f"\n\nDone. {len(QUERIES)} queries. Saved to exa-deep-research.json")
