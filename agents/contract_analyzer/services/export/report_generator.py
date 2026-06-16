from docx import Document


def export_contract_report(
    compliance_results,
    risk_results,
    mitigation_results,
    output_path
):

    doc = Document()

    doc.add_heading(
        'Enterprise Contract Analysis Report',
        level=1
    )

    # ==================================
    # TABLE 1
    # ==================================

    doc.add_heading(
        'Table 1 - Compliance Analysis',
        level=2
    )

    table = doc.add_table(
        rows=1,
        cols=4
    )

    table.style = 'Table Grid'

    hdr = table.rows[0].cells

    hdr[0].text = 'Clause'
    hdr[1].text = 'Requirement'
    hdr[2].text = 'Status'
    hdr[3].text = 'Evidence'

    for row in compliance_results:

        cells = table.add_row().cells

        cells[0].text = str(
            row.get("clause", "")
        )

        cells[1].text = str(
            row.get("requirement", "")
        )

        cells[2].text = str(
            row.get("status", "")
        )

        cells[3].text = str(
            row.get("evidence", "")
        )

    # ==================================
    # TABLE 2
    # ==================================

    doc.add_page_break()

    doc.add_heading(
        'Table 2 - Risk Assessment',
        level=2
    )

    table = doc.add_table(
        rows=1,
        cols=6
    )

    table.style = 'Table Grid'

    hdr = table.rows[0].cells

    hdr[0].text = 'Clause'
    hdr[1].text = 'Requirement'
    hdr[2].text = 'RAG'
    hdr[3].text = 'Risk'
    hdr[4].text = 'Rationale'
    hdr[5].text = 'Mitigation'

    for row in risk_results:

        cells = table.add_row().cells

        cells[0].text = str(
            row.get("clause", "")
        )

        cells[1].text = str(
            row.get("requirement", "")
        )

        cells[2].text = str(
            row.get("rag", "")
        )

        cells[3].text = str(
            row.get("risk", "")
        )

        cells[4].text = str(
            row.get("rationale", "")
        )

        cells[5].text = str(
            row.get("mitigation", "")
        )

    # ==================================
    # TABLE 3
    # ==================================

    doc.add_page_break()

    doc.add_heading(
        'Table 3 - Mitigation Checklist',
        level=2
    )

    table = doc.add_table(
        rows=1,
        cols=3
    )

    table.style = 'Table Grid'

    hdr = table.rows[0].cells

    hdr[0].text = 'Clause'
    hdr[1].text = 'Risk'
    hdr[2].text = 'Mitigation Recommendation'

    for row in mitigation_results:

        cells = table.add_row().cells

        cells[0].text = str(
            row.get("clause", "")
        )

        cells[1].text = str(
            row.get("risk", "")
        )

        cells[2].text = str(
            row.get("mitigation", "")
        )

    doc.save(output_path)

    return output_path