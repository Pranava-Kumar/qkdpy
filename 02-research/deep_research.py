"""Deep research: QKD simulation landscape."""

import json
import os

from exa_py import Exa

exa_api_key = os.environ.get("EXA_API_KEY")
if not exa_api_key:
    msg = "EXA_API_KEY not set in environment"
    raise RuntimeError(msg)

exa = Exa(api_key=exa_api_key)

QUERIES = [
    # Competitor-specific searches
    "qiskit qkd quantum key distribution library github",
    "NetSquid quantum network simulator features pricing",
    "QuNetSim quantum network simulation Python",
    "SimulaQron quantum network simulator status",
    "quantum key distribution open source simulation comparison",
    # Feature-specific searches
    "satellite quantum key distribution simulation software",
    "machine learning quantum key distribution channel prediction",
    "CVQKD continuous variable quantum key distribution simulation",
    "high dimensional quantum key distribution simulation",
    "quantum key distribution enterprise compliance NIST standards",
]


def run_deep_search(query: str) -> dict:
    """Run a deep search with synthesis."""
    print(f"\n{'=' * 60}")
    print(f"Query: {query}")
    print(f"{'=' * 60}")

    result = exa.search(
        query,
        type="deep",
        num_results=10,
        contents={
            "highlights": True,
            "text": {"max_characters": 3000, "verbosity": "compact"},
        },
        output_schema={
            "type": "object",
            "description": "Research findings for this query",
            "required": ["findings", "sources"],
            "properties": {
                "findings": {
                    "type": "array",
                    "description": "Key findings about the product, project, or landscape",
                    "items": {
                        "type": "object",
                        "required": ["finding"],
                        "properties": {
                            "finding": {
                                "type": "string",
                                "description": "A key finding",
                            },
                            "detail": {
                                "type": "string",
                                "description": "Detail or evidence",
                            },
                        },
                    },
                },
                "sources": {
                    "type": "array",
                    "description": "Relevant URLs found",
                    "items": {
                        "type": "object",
                        "required": ["url", "title"],
                        "properties": {
                            "url": {"type": "string"},
                            "title": {"type": "string"},
                            "relevance": {"type": "string"},
                        },
                    },
                },
            },
        },
    )

    # Print structured output
    if result.output and result.output.content:
        content = result.output.content
        if isinstance(content, str):
            print(content)
        else:
            print(json.dumps(content, indent=2))

    # Print text highlights from raw results
    for r in result.results[:3]:
        if r.title:
            print(f"\n--- {r.title} ---")
            print(f"URL: {r.url}")
        if r.text:
            print(r.text[:500])
        if r.highlights:
            for h in r.highlights[:2]:
                print(f"  > {h[:200]}")

    return result


if __name__ == "__main__":
    all_results = {}
    for q in QUERIES:
        try:
            all_results[q] = run_deep_search(q)
        except Exception as e:
            print(f"ERROR on '{q}': {e}")
            all_results[q] = {"error": str(e)}

    # Save full results
    with open("02-research/exa-research-output.json", "w") as f:
        json.dump({k: str(v) for k, v in all_results.items()}, f, indent=2)
    print("\n\nDone. Results saved to 02-research/exa-research-output.json")
