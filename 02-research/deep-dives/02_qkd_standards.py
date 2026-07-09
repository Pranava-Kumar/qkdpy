"""Deep research: QKD Standards landscape."""

import os

from exa_py import Exa

exa_api_key = os.environ.get("EXA_API_KEY")
if not exa_api_key:
    msg = "EXA_API_KEY not set in environment"
    raise RuntimeError(msg)

exa = Exa(api_key=exa_api_key)

QUERIES = [
    "ETSI GS QKD 014 015 016 implementation compliance open source 2025 2026",
    "ISO IEC 23837 quantum key distribution security requirements evaluation standard",
    "Common Criteria Protection Profile QKD BSI certification status",
    "QKD standardization landscape NIST ETSI ISO comparison update 2026",
    "open source quantum key distribution management system ETSI compliant implementation",
]

for i, q in enumerate(QUERIES):
    print(f"\n{'='*60}\n[{i+1}/{len(QUERIES)}] {q}\n{'='*60}")
    try:
        r = exa.search(
            q,
            type="deep",
            num_results=6,
            contents={"highlights": True, "text": {"max_characters": 2000}},
        )
        for res in r.results[:4]:
            title = getattr(res, "title", "") or ""
            url = getattr(res, "url", "") or ""
            print(f"\n--- {title[:80]} ---")
            print(f"  URL: {url}")
            if hasattr(res, "highlights") and res.highlights:
                for h in res.highlights[:3]:
                    print(f"  > {str(h)[:250]}")
    except Exception as e:
        print(f"ERROR: {e}")

print("\n=== STANDARDS RESEARCH DONE ===")
