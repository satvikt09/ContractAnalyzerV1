from collections import Counter


def generate_executive_summary(
    compliance_results,
    risk_results
):

    total_requirements = len(
        compliance_results
    )

    status_counts = Counter(
        r["status"]
        for r in compliance_results
    )

    total_risks = len(
        risk_results
    )

    red_risks = sum(
        1
        for r in risk_results
        if r["rag"] == "Red"
    )

    amber_risks = sum(
        1
        for r in risk_results
        if r["rag"] == "Amber"
    )

    if red_risks >= 3:

        overall_rating = "High Risk"

    elif amber_risks >= 3:

        overall_rating = "Medium Risk"

    else:

        overall_rating = "Low Risk"

    top_findings = []

    seen = set()

    for risk in risk_results:

        finding = risk.get(
            "risk",
            ""
        ).strip()

        if (
            finding
            and finding not in seen
        ):

            seen.add(
                finding
            )

            top_findings.append(
                finding
            )

        if len(top_findings) >= 5:
            break

    if overall_rating == "High Risk":

        recommendation = (
            "Contract should undergo detailed legal "
            "and commercial review before execution."
        )

    elif overall_rating == "Medium Risk":

        recommendation = (
            "Review identified deviations and "
            "confirm business acceptance."
        )

    else:

        recommendation = (
            "No major contractual concerns identified. "
            "Proceed with standard review."
        )

    narrative_parts = []

    if red_risks:

        narrative_parts.append(
            f"{red_risks} high-risk contractual "
            f"deviations were identified."
        )

    if amber_risks:

        narrative_parts.append(
            f"{amber_risks} medium-risk findings "
            f"require attention."
        )

    not_met = status_counts.get(
        "Not Met",
        0
    )

    partially_met = status_counts.get(
        "Partially Met",
        0
    )

    if not_met:

        narrative_parts.append(
            f"{not_met} requirements were not met."
        )

    if partially_met:

        narrative_parts.append(
            f"{partially_met} requirements were "
            f"only partially satisfied."
        )

    narrative = " ".join(
        narrative_parts
    )

    return {

        "overall_rating":
            overall_rating,

        "requirements_checked":
            total_requirements,

        "met":
            status_counts.get(
                "Met",
                0
            ),

        "partially_met":
            partially_met,

        "not_met":
            not_met,

        "total_risks":
            total_risks,

        "red_risks":
            red_risks,

        "amber_risks":
            amber_risks,

        "executive_narrative":
            narrative,

        "recommendation":
            recommendation,

        "top_findings":
            top_findings
    }