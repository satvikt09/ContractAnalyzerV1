import time

from concurrent.futures import (
    ThreadPoolExecutor
)

from .risk_mapper import (
    get_rag
)

from .risk_generator import (
    generate_risk_entry
)

from .location_extractor import (
    extract_locations
)


HIGH_RISK_SIGNALS = [
    "except",
    "excluding",
    "unless",
    "subject to",
    "however",
    "notwithstanding",
    "carve-out",
    "carve out"
]

MEDIUM_RISK_SIGNALS = [
    "conditional",
    "approval",
    "deemed",
    "limited to",
    "only"
]


def has_risk_signals(result):

    text = (
        f"{result.get('evidence', '')} "
        f"{result.get('remarks', '')}"
    ).lower()

    score = 0

    for signal in HIGH_RISK_SIGNALS:

        if signal in text:
            score += 2

    for signal in MEDIUM_RISK_SIGNALS:

        if signal in text:
            score += 1

    return score >= 2


def generate_risk_table(
    compliance_results
):



    risk_table = []

    seen_clause_requirement = set()

    risky_results = []

    # --------------------------------
    # KEEP ONLY RISKY ITEMS
    # --------------------------------

    for result in compliance_results:

        key = (
            result["clause"],
            result["requirement"]
        )

        if key in seen_clause_requirement:
            continue

        seen_clause_requirement.add(key)

        status = str(
            result.get("status", "")
        ).lower()

        # Always keep actual compliance failures

        if (
            "partially" in status
            or "not met" in status
        ):

            risky_results.append(result)

        # For "Met" rows,
        # require strong evidence of carve-outs
        # and meaningful remarks

        elif (

            result["status"] == "Met"

            and has_risk_signals(result)

            and len(
                result.get(
                    "remarks",
                    ""
                )
            ) > 150

        ):

            risky_results.append(result)

    # --------------------------------
    # DEBUG
    # --------------------------------

    print("\nRISK CANDIDATES")

    for result in risky_results:

        print(
            f"{result['requirement']} "
            f"-> "
            f"{result['status']}"
        )

    print(
        f"\nTOTAL RISK CANDIDATES: "
        f"{len(risky_results)}"
    )

    # --------------------------------
    # GEMMA ANALYSIS
    # --------------------------------

    with ThreadPoolExecutor(
        max_workers=5
    ) as executor:

        futures = []

        for result in risky_results:

            futures.append(
                executor.submit(
                    generate_risk_entry,
                    result
                )
            )

        for result, future in zip(
            risky_results,
            futures
        ):

            generated = future.result()

            rag = get_rag(
                result["status"]
            )

            risk_table.append(
                {
                    "clause":
                        result["clause"],

                    "requirement":
                        result["requirement"],

                    "rag":
                        rag,

                    "risk":
                        generated.get(
                            "risk",
                            ""
                        ),

                    "rationale":
                        generated.get(
                            "rationale",
                            ""
                        ),

                    "mitigation":
                        generated.get(
                            "mitigation",
                            ""
                        ),

                    "evidence":
                        result.get(
                            "remarks",
                            ""
                        ),

                    "location":
                        extract_locations(
                            result.get(
                                "evidence",
                                ""
                            )
                            +
                            " "
                            +
                            result.get(
                                "remarks",
                                ""
                            )
                        )
                }
            )

    # --------------------------------
    # TIMING
    # --------------------------------

    print("\n")
    print("=" * 60)
    print("RISK AGENT SUMMARY")
    print("=" * 60)

    print(
        f"Rows: {len(compliance_results)}"
    )

    print(
        f"Gemma Calls: {len(risky_results)}"
    )



    print("=" * 60)

    return risk_table