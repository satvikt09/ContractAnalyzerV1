from concurrent.futures import ThreadPoolExecutor
from .risk_mapper import get_rag
from .risk_generator import generate_risk_entry
from .location_extractor import extract_locations

HIGH_RISK_SIGNALS = [
    "except", "excluding", "unless", "subject to", "however", "notwithstanding",
    "carve-out", "carve out"
]

MEDIUM_RISK_SIGNALS = [
    "conditional", "approval", "deemed", "limited to", "only"
]


def has_risk_signals(result: dict) -> bool:
    """Detect if evidence/remarks contain keywords indicating hidden risks/carveouts."""
    text = f"{result.get('evidence', '')} {result.get('remarks', '')}".lower()
    score = 0
    for signal in HIGH_RISK_SIGNALS:
        if signal in text:
            score += 2
    for signal in MEDIUM_RISK_SIGNALS:
        if signal in text:
            score += 1
    return score >= 2


def generate_risk_table(compliance_results: list) -> list:
    """Process compliance results to identify potential risks and generate a risk register."""
    risk_table = []
    seen_clause_requirement = set()
    risky_results = []

    # Filter for non-compliant or high-risk "Met" rows
    for result in compliance_results:
        key = (result["clause"], result["requirement"])
        if key in seen_clause_requirement:
            continue
        seen_clause_requirement.add(key)

        status = str(result.get("status", "")).lower()
        if "partially" in status or "not met" in status:
            risky_results.append(result)
        elif (
            result["status"] == "Met"
            and has_risk_signals(result)
            and len(result.get("remarks", "")) > 150
        ):
            risky_results.append(result)

    print("\nRISK CANDIDATES")
    for result in risky_results:
        print(f"{result['requirement']} -> {result['status']}")
    print(f"\nTOTAL RISK CANDIDATES: {len(risky_results)}")

    # Run Ollama analysis in parallel for candidate risk entries
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(generate_risk_entry, res) for res in risky_results]

        for result, future in zip(risky_results, futures):
            generated = future.result()
            rag = get_rag(result["status"])

            risk_table.append({
                "clause": result["clause"],
                "requirement": result["requirement"],
                "rag": rag,
                "risk": generated.get("risk", ""),
                "rationale": generated.get("rationale", ""),
                "mitigation": generated.get("mitigation", ""),
                "evidence": result.get("remarks", ""),
                "location": extract_locations(
                    result.get("evidence", "") + " " + result.get("remarks", "")
                )
            })

    print("\n" + "=" * 60)
    print("RISK AGENT SUMMARY")
    print("=" * 60)
    print(f"Rows: {len(compliance_results)}")
    print(f"Gemma Calls: {len(risky_results)}")
    print("=" * 60)

    return risk_table