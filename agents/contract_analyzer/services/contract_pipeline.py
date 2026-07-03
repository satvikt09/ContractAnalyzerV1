"""Sequential execution pipeline for contract analysis processing."""

from agents.contract_analyzer.services.extraction_manager import get_extraction
from agents.contract_analyzer.services.section_segmenter import segment_contract
from agents.contract_analyzer.services.rule_classifier import classify_rule_based
from agents.contract_analyzer.services.batch_clause_classifier import classify_clauses_batch
from agents.contract_analyzer.services.compliance_checker import check_compliance
from agents.contract_analyzer.services.risk_assessment.risk_agent import generate_risk_table
from agents.contract_analyzer.services.mitigation_assessment.mitigation_agent import generate_mitigation_table
from agents.contract_analyzer.services.executive_summary import generate_executive_summary
from agents.contract_analyzer.services.export.report_generator import export_contract_report
from agents.contract_analyzer.services.config import SHOW_EXECUTIVE_SUMMARY


def process_contract(file_path: str, progress_callback=None) -> dict:
    """Execute the sequential stages of the contract analysis pipeline."""
    print("\n" + "=" * 60)
    print("PROCESSING CONTRACT PIPELINE")
    print("=" * 60)

    # 1. Text Extraction
    if progress_callback:
        progress_callback("Extracting text content from contract files...")

    extraction = get_extraction(file_path)
    print(f"Extraction Method: {extraction['extraction_method']}")

    # 2. Document Segmentation
    if progress_callback:
        progress_callback("Analyzing document structure & segments...")

    sections = segment_contract(extraction["raw_text"])
    print(f"Sections Found: {len(sections)}")

    # 3. Clause Classification
    if progress_callback:
        progress_callback("Identifying and classifying legal clauses...")

    classified_results = []
    unknown_sections = []

    for section in sections:
        rule_result = classify_rule_based(section["title"], section["content"])
        if rule_result:
            classified_results.append({
                "title": section["title"],
                "content": section["content"],
                **rule_result
            })
        else:
            unknown_sections.append(section)

    print(f"Rule Classified: {len(classified_results)}")
    print(f"Unknown Sections: {len(unknown_sections)}")

    # LLM fallback for unclassified clauses
    if unknown_sections:
        gemini_results = classify_clauses_batch(unknown_sections)
        for section, result in zip(unknown_sections, gemini_results):
            classified_results.append({
                "title": section["title"],
                "content": section["content"],
                "clause_type": result["clause_type"],
                "confidence": result["confidence"],
                "reason": result["reason"]
            })

    # Sort results to reflect original document order
    classified_results.sort(
        key=lambda x: next(
            (i for i, s in enumerate(sections) if s["title"] == x["title"]),
            999
        )
    )

    print(f"Total Classified: {len(classified_results)}")
    print("\n" + "=" * 60)
    print("CLASSIFIED CLAUSES")
    print("=" * 60)
    for item in classified_results:
        print(f"{item['title']}")
        print(f" -> {item['clause_type']}")
        print(f" -> {item['reason']}")
        print("-" * 40)

    # 4. Compliance Analysis
    if progress_callback:
        progress_callback("Checking clause compliance with legal guidelines...")

    compliance_results = check_compliance(classified_results)

    print("\n" + "=" * 60)
    print("COMPLIANCE CHECK")
    print("=" * 60)
    for item in compliance_results:
        print(f"{item['requirement']} -> {item['status']}")
    print("=" * 60)

    # 5. Risk Assessment
    if progress_callback:
        progress_callback("Assessing potential liabilities and risks...")

    print("\n" + "=" * 60)
    print("STARTING RISK ASSESSMENT")
    print("=" * 60)

    risk_results = generate_risk_table(compliance_results)
    print(f"Risk Rows Generated: {len(risk_results)}")
    print("\nSAMPLE RISK ENTRY\n")
    if risk_results:
        print(risk_results[0])

    # 6. Mitigation Assessment
    if progress_callback:
        progress_callback("Formulating mitigation strategies & recommendations...")

    print("\n" + "=" * 60)
    print("STARTING MITIGATION ASSESSMENT")
    print("=" * 60)

    mitigation_results = generate_mitigation_table(risk_results)

    if SHOW_EXECUTIVE_SUMMARY:
        executive_summary = generate_executive_summary(compliance_results, risk_results)
    else:
        executive_summary = {}

    print("\nEXECUTIVE SUMMARY")
    print(executive_summary)

    # 7. Document Export
    if progress_callback:
        progress_callback("Finalizing export documents and report...")

    report_path = "contract_analysis_report.docx"
    export_contract_report(
        executive_summary,
        compliance_results,
        risk_results,
        mitigation_results,
        report_path
    )

    print(f"Mitigation Rows Generated: {len(mitigation_results)}")
    if mitigation_results:
        print("\nSAMPLE MITIGATION ENTRY\n")
        print(mitigation_results[0])

    return {
        "extraction": extraction,
        "sections": sections,
        "classified_clauses": classified_results,
        "compliance_results": compliance_results,
        "risk_results": risk_results,
        "mitigation_results": mitigation_results,
        "executive_summary": executive_summary,
        "report_path": report_path
    }
