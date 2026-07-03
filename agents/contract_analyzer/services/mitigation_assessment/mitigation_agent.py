def generate_mitigation_table(risk_results: list) -> list:
    """Consolidate mitigation recommendations into a summary table."""
    mitigation_table = []

    for risk in risk_results:
        mitigation_table.append({
            "clause": risk["clause"],
            "risk": risk["requirement"],
            "mitigation": risk["mitigation"]
        })

    print("\n" + "=" * 60)
    print("MITIGATION AGENT SUMMARY")
    print("=" * 60)
    print(f"Rows: {len(mitigation_table)}")
    print("=" * 60)

    return mitigation_table