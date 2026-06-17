from agents.contract_analyzer.services.extraction_manager import (
    get_extraction
)

from agents.contract_analyzer.services.section_segmenter import (
    segment_contract
)

from agents.contract_analyzer.services.rule_classifier import (
    classify_rule_based
)

from agents.contract_analyzer.services.batch_clause_classifier import (
    classify_clauses_batch
)

from agents.contract_analyzer.services.compliance_checker import (
    check_compliance
)
#agent2
from agents.contract_analyzer.services.risk_assessment.risk_agent import (
    generate_risk_table
)
#agent3
from agents.contract_analyzer.services.mitigation_assessment.mitigation_agent import (
    generate_mitigation_table
)
from agents.contract_analyzer.services.executive_summary import (
    generate_executive_summary
)
#export
from agents.contract_analyzer.services.export.report_generator import (
    export_contract_report
)
from agents.contract_analyzer.services.config import (
    SHOW_EXECUTIVE_SUMMARY
)

def process_contract(file_path):

    print("\n" + "=" * 60)
    print("PROCESSING CONTRACT PIPELINE")
    print("=" * 60)

    # --------------------------------
    # EXTRACTION
    # --------------------------------

    extraction = get_extraction(
        file_path
    )

    print(
        f"Extraction Method: "
        f"{extraction['extraction_method']}"
    )

    # --------------------------------
    # SEGMENTATION
    # --------------------------------

    sections = segment_contract(
        extraction["raw_text"]
    )

    print(
        f"Sections Found: "
        f"{len(sections)}"
    )

    # --------------------------------
    # CLASSIFICATION
    # --------------------------------

    classified_results = []

    unknown_sections = []

    for section in sections:

        rule_result = classify_rule_based(
            section["title"],
            section["content"]
        )

        if rule_result:

            classified_results.append(
                {
                    "title": section["title"],
                    "content": section["content"],
                    **rule_result
                }
            )

        else:

            unknown_sections.append(
                section
            )

    print(
        f"Rule Classified: "
        f"{len(classified_results)}"
    )

    print(
        f"Unknown Sections: "
        f"{len(unknown_sections)}"
    )

    # --------------------------------
    # LLM FALLBACK
    # --------------------------------

    if unknown_sections:

        gemini_results = (
            classify_clauses_batch(
                unknown_sections
            )
        )

        for section, result in zip(
            unknown_sections,
            gemini_results
        ):

            classified_results.append(
                {
                    "title": section["title"],
                    "content": section["content"],
                    "clause_type":
                        result["clause_type"],
                    "confidence":
                        result["confidence"],
                    "reason":
                        result["reason"]
                }
            )

    # --------------------------------
    # SORT TO DOCUMENT ORDER
    # --------------------------------

    classified_results.sort(
        key=lambda x: next(
            (
                i
                for i, s in enumerate(
                    sections
                )
                if s["title"]
                == x["title"]
            ),
            999
        )
    )

    print(
        f"Total Classified: "
        f"{len(classified_results)}"
    )

    print("\n" + "=" * 60)
    print("CLASSIFIED CLAUSES")
    print("=" * 60)

    for item in classified_results:

        print(
            f"{item['title']}"
        )

        print(
            f" -> {item['clause_type']}"
        )

        print(
            f" -> {item['reason']}"
        )

        print("-" * 40)

    # --------------------------------
    # AGENT 1
    # COMPLIANCE ANALYSIS
    # --------------------------------

    compliance_results = (
        check_compliance(
            classified_results
        )
    )

    print("\n" + "=" * 60)
    print("COMPLIANCE CHECK")
    print("=" * 60)

    for item in compliance_results:

        print(
            f"{item['requirement']} "
            f"-> "
            f"{item['status']}"
        )

    print("=" * 60)
    # --------------------------------
    # AGENT 2
    # RISK ASSESSMENT
    # --------------------------------

    print("\n" + "=" * 60)
    print("STARTING RISK ASSESSMENT")
    print("=" * 60)

    risk_results = (
        generate_risk_table(
            compliance_results
        )
    )

    print(
        f"Risk Rows Generated: "
        f"{len(risk_results)}"
    )

    print("\nSAMPLE RISK ENTRY\n")

    if risk_results:

        print(
            risk_results[0]
        )

    # --------------------------------
    # AGENT 3
    # MITIGATION ASSESSMENT
    # --------------------------------

    print("\n" + "=" * 60)
    print("STARTING MITIGATION ASSESSMENT")
    print("=" * 60)

    mitigation_results = (
        generate_mitigation_table(
            risk_results
        )
    )
    if SHOW_EXECUTIVE_SUMMARY:

        executive_summary = (
            generate_executive_summary(
                compliance_results,
                risk_results
            )
        )

    else:

        executive_summary = {}
    print("\nEXECUTIVE SUMMARY")
    print(executive_summary)

    report_path = (
        "contract_analysis_report.docx"
    )

    export_contract_report(
        executive_summary,
        compliance_results,
        risk_results,
        mitigation_results,
        report_path
    )
    print(
        f"Mitigation Rows Generated: "
        f"{len(mitigation_results)}"
    )

    if mitigation_results:

        print("\nSAMPLE MITIGATION ENTRY\n")

        print(
            mitigation_results[0]
        )

    # --------------------------------
    # RETURN
    # --------------------------------

    return {

        "extraction":
            extraction,

        "sections":
            sections,

        "classified_clauses":
            classified_results,

        "compliance_results":
            compliance_results,

        "risk_results":
            risk_results,

        "mitigation_results":
            mitigation_results,

        "executive_summary":
            executive_summary,
        "report_path":
            report_path,            
    }

