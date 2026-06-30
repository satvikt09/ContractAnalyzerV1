# pyrefly: ignore [missing-import]
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from agents.contract_analyzer.services.config import (
    SHOW_EXECUTIVE_SUMMARY,
    SHOW_CLAUSE_SUMMARY_COLUMN,
    SHOW_STATUS_COLUMN,
    SHOW_HISTORICAL_ACTION_COLUMN
)

def _sort_compliance_results(results):
    try:
        from agents.contract_analyzer.services.checklist_requirements_benchmark import (
            CHECKLIST_REQUIREMENTS
        )
    except ImportError:
        return results
    
    order_map = {}
    for idx, item in enumerate(CHECKLIST_REQUIREMENTS):
        key = (item["clause"].strip().lower(), item["requirement"].strip().lower())
        if key not in order_map:
            order_map[key] = idx

    def get_order_key(res):
        clause = res.get("clause", "").strip().lower()
        req = res.get("requirement", "").strip().lower()
        key = (clause, req)
        if key in order_map:
            return order_map[key]
        for checklist_key, checklist_idx in order_map.items():
            if checklist_key[0] == clause and checklist_key[1] == req:
                return checklist_idx
        return 999999

    return sorted(results, key=get_order_key)

def get_pdf_styles():
    styles = getSampleStyleSheet()
    
    # Custom styles matching the purple/neutral palette
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=22,
        leading=26,
        textColor=colors.HexColor('#810055'),
        spaceAfter=15,
        keepWithNext=True
    )
    heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=15,
        leading=19,
        textColor=colors.HexColor('#810055'),
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )
    subheading_style = ParagraphStyle(
        'SubSectionHeading',
        parent=styles['Heading3'],
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#333333'),
        spaceBefore=8,
        spaceAfter=6,
        keepWithNext=True
    )
    body_style = ParagraphStyle(
        'ReportBody',
        parent=styles['Normal'],
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor('#333333'),
        spaceAfter=8
    )
    bullet_style = ParagraphStyle(
        'ReportBullet',
        parent=styles['Normal'],
        fontSize=9.5,
        leading=13.5,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )
    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontSize=8.5,
        leading=10.5,
        fontName='Helvetica-Bold',
        textColor=colors.white
    )
    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#333333')
    )
    
    return {
        'title': title_style,
        'heading': heading_style,
        'subheading': subheading_style,
        'body': body_style,
        'bullet': bullet_style,
        'table_header': table_header_style,
        'table_cell': table_cell_style
    }

def wrap_cell(text, style):
    return Paragraph(str(text or ""), style)

def make_table_style(num_rows):
    t_style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#810055')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D2D6DC')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ])
    for i in range(1, num_rows):
        bg = colors.HexColor('#F9FAFB') if i % 2 == 0 else colors.white
        t_style.add('BACKGROUND', (0, i), (-1, i), bg)
    return t_style

def export_contract_pdf(executive_summary, compliance_results, risk_results, mitigation_results, output_path_or_buffer):
    compliance_results = _sort_compliance_results(compliance_results)
    # Setup document: letter size is 612x792 pt. 36 pt margin on each side leaves 540 pt printable width.
    doc = SimpleDocTemplate(
        output_path_or_buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = get_pdf_styles()
    story = []
    
    # 1. Document Title
    story.append(Paragraph("Enterprise Contract Analysis Report", styles['title']))
    story.append(Spacer(1, 10))
    
    # 2. Executive Summary
    if SHOW_EXECUTIVE_SUMMARY and executive_summary:
        story.append(Paragraph("Executive Summary", styles['heading']))
        
        overall_rating = executive_summary.get('overall_rating', '')
        story.append(Paragraph(f"<b>Overall Risk Rating:</b> {overall_rating}", styles['body']))
        
        narrative = executive_summary.get('executive_narrative', '')
        if narrative:
            story.append(Paragraph(narrative, styles['body']))
            
        top_findings = executive_summary.get('top_findings', [])
        if top_findings:
            story.append(Paragraph("Key Findings", styles['subheading']))
            for finding in top_findings:
                story.append(Paragraph(f"&bull; {finding}", styles['bullet']))
            story.append(Spacer(1, 6))
                
        rec = executive_summary.get('recommendation', '')
        if rec:
            story.append(Paragraph("Recommendation", styles['subheading']))
            story.append(Paragraph(rec, styles['body']))
            
        story.append(PageBreak())
        
    # 3. Compliance Analysis Table
    story.append(Paragraph("Table 1 - Compliance Analysis", styles['heading']))
    
    comp_headers = ["Clause", "Requirement"]
    comp_weights = [1.0, 2.5]
    
    if SHOW_CLAUSE_SUMMARY_COLUMN:
        comp_headers.append("Summary of Key Details")
        comp_weights.append(2.2)
    if SHOW_STATUS_COLUMN:
        comp_headers.append("Status")
        comp_weights.append(1.2)
        
    comp_headers.extend(["Evidence", "Assessor Remarks"])
    comp_weights.extend([2.5, 2.5])
    
    if SHOW_HISTORICAL_ACTION_COLUMN:
        comp_headers.append("Historical Action Taken")
        comp_weights.append(1.8)
        
    # Calculate widths based on weights and 540 pt available width
    total_comp_weight = sum(comp_weights)
    comp_widths = [w * 540.0 / total_comp_weight for w in comp_weights]
    
    comp_table_data = [[wrap_cell(h, styles['table_header']) for h in comp_headers]]
    for row in compliance_results:
        row_cells = []
        row_cells.append(wrap_cell(row.get("clause", ""), styles['table_cell']))
        row_cells.append(wrap_cell(row.get("requirement", ""), styles['table_cell']))
        
        if SHOW_CLAUSE_SUMMARY_COLUMN:
            row_cells.append(wrap_cell(row.get("clause_summary", ""), styles['table_cell']))
        if SHOW_STATUS_COLUMN:
            row_cells.append(wrap_cell(row.get("status", ""), styles['table_cell']))
            
        row_cells.append(wrap_cell(row.get("evidence", ""), styles['table_cell']))
        row_cells.append(wrap_cell(row.get("remarks", ""), styles['table_cell']))
        
        if SHOW_HISTORICAL_ACTION_COLUMN:
            row_cells.append(wrap_cell(row.get("historical_action", ""), styles['table_cell']))
            
        comp_table_data.append(row_cells)
        
    comp_table = Table(comp_table_data, colWidths=comp_widths)
    comp_table.setStyle(make_table_style(len(comp_table_data)))
    story.append(comp_table)
    story.append(Spacer(1, 10))
    story.append(PageBreak())
    
    # 4. Risk Assessment Table
    story.append(Paragraph("Table 2 - Risk Assessment", styles['heading']))
    
    risk_headers = ["Clause", "Requirement", "RAG", "Risk", "Rationale", "Mitigation"]
    risk_weights = [1.0, 2.2, 1.0, 2.2, 2.6, 2.6]
    total_risk_weight = sum(risk_weights)
    risk_widths = [w * 540.0 / total_risk_weight for w in risk_weights]
    
    risk_table_data = [[wrap_cell(h, styles['table_header']) for h in risk_headers]]
    for row in risk_results:
        risk_table_data.append([
            wrap_cell(row.get("clause", ""), styles['table_cell']),
            wrap_cell(row.get("requirement", ""), styles['table_cell']),
            wrap_cell(row.get("rag", ""), styles['table_cell']),
            wrap_cell(row.get("risk", ""), styles['table_cell']),
            wrap_cell(row.get("rationale", ""), styles['table_cell']),
            wrap_cell(row.get("mitigation", ""), styles['table_cell'])
        ])
        
    risk_table = Table(risk_table_data, colWidths=risk_widths)
    risk_table.setStyle(make_table_style(len(risk_table_data)))
    story.append(risk_table)
    story.append(Spacer(1, 10))
    story.append(PageBreak())
    
    # 5. Mitigation Checklist Table
    story.append(Paragraph("Table 3 - Mitigation Checklist", styles['heading']))
    
    mit_headers = ["Clause", "Risk", "Mitigation Recommendation"]
    mit_weights = [1.2, 3.0, 4.8]
    total_mit_weight = sum(mit_weights)
    mit_widths = [w * 540.0 / total_mit_weight for w in mit_weights]
    
    mit_table_data = [[wrap_cell(h, styles['table_header']) for h in mit_headers]]
    for row in mitigation_results:
        mit_table_data.append([
            wrap_cell(row.get("clause", ""), styles['table_cell']),
            wrap_cell(row.get("risk", ""), styles['table_cell']),
            wrap_cell(row.get("mitigation", ""), styles['table_cell'])
        ])
        
    mit_table = Table(mit_table_data, colWidths=mit_widths)
    mit_table.setStyle(make_table_style(len(mit_table_data)))
    story.append(mit_table)
    
    doc.build(story)
    return output_path_or_buffer


def export_individual_compliance_pdf(compliance_results, output_path_or_buffer):
    compliance_results = _sort_compliance_results(compliance_results)
    doc = SimpleDocTemplate(
        output_path_or_buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = get_pdf_styles()
    story = []
    
    story.append(Paragraph("Compliance Evaluation Report", styles['title']))
    story.append(Spacer(1, 10))
    
    headers = ["Clause", "Requirement"]
    weights = [1.0, 2.5]
    
    if SHOW_CLAUSE_SUMMARY_COLUMN:
        headers.append("Key Details Summary")
        weights.append(2.2)
    if SHOW_STATUS_COLUMN:
        headers.append("Compliance Status")
        weights.append(1.2)
        
    headers.extend(["Evidence Reference", "Assessor Remarks"])
    weights.extend([2.5, 2.5])
    
    if SHOW_HISTORICAL_ACTION_COLUMN:
        headers.append("Historical Action Taken")
        weights.append(1.8)
        
    total_weight = sum(weights)
    widths = [w * 540.0 / total_weight for w in weights]
    
    table_data = [[wrap_cell(h, styles['table_header']) for h in headers]]
    for row in compliance_results:
        row_cells = []
        row_cells.append(wrap_cell(row.get("clause", ""), styles['table_cell']))
        row_cells.append(wrap_cell(row.get("requirement", ""), styles['table_cell']))
        
        if SHOW_CLAUSE_SUMMARY_COLUMN:
            row_cells.append(wrap_cell(row.get("clause_summary", ""), styles['table_cell']))
        if SHOW_STATUS_COLUMN:
            row_cells.append(wrap_cell(row.get("status", ""), styles['table_cell']))
            
        row_cells.append(wrap_cell(row.get("evidence", ""), styles['table_cell']))
        row_cells.append(wrap_cell(row.get("remarks", ""), styles['table_cell']))
        
        if SHOW_HISTORICAL_ACTION_COLUMN:
            row_cells.append(wrap_cell(row.get("historical_action", ""), styles['table_cell']))
            
        table_data.append(row_cells)
        
    table = Table(table_data, colWidths=widths)
    table.setStyle(make_table_style(len(table_data)))
    story.append(table)
    
    doc.build(story)
    return output_path_or_buffer


def export_individual_risk_pdf(risk_results, output_path_or_buffer):
    doc = SimpleDocTemplate(
        output_path_or_buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = get_pdf_styles()
    story = []
    
    story.append(Paragraph("Risk Assessment Report", styles['title']))
    story.append(Spacer(1, 10))
    
    headers = ["Clause", "Requirement", "RAG Priority", "Identified Risk", "Technical Rationale", "Suggested Mitigation", "Evidence Context"]
    weights = [1.0, 2.2, 1.0, 2.2, 2.4, 2.4, 2.2]
    total_weight = sum(weights)
    widths = [w * 540.0 / total_weight for w in weights]
    
    table_data = [[wrap_cell(h, styles['table_header']) for h in headers]]
    for row in risk_results:
        table_data.append([
            wrap_cell(row.get("clause", ""), styles['table_cell']),
            wrap_cell(row.get("requirement", ""), styles['table_cell']),
            wrap_cell(row.get("rag", ""), styles['table_cell']),
            wrap_cell(row.get("risk", ""), styles['table_cell']),
            wrap_cell(row.get("rationale", ""), styles['table_cell']),
            wrap_cell(row.get("mitigation", ""), styles['table_cell']),
            wrap_cell(row.get("evidence", ""), styles['table_cell'])
        ])
        
    table = Table(table_data, colWidths=widths)
    table.setStyle(make_table_style(len(table_data)))
    story.append(table)
    
    doc.build(story)
    return output_path_or_buffer


def export_individual_mitigation_pdf(mitigation_results, output_path_or_buffer):
    doc = SimpleDocTemplate(
        output_path_or_buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = get_pdf_styles()
    story = []
    
    story.append(Paragraph("Mitigation Strategy Guidelines", styles['title']))
    story.append(Spacer(1, 10))
    
    headers = ["Clause Reference", "Related Risk", "Mitigation Recommendation Guideline"]
    weights = [1.2, 3.0, 4.8]
    total_weight = sum(weights)
    widths = [w * 540.0 / total_weight for w in weights]
    
    table_data = [[wrap_cell(h, styles['table_header']) for h in headers]]
    for row in mitigation_results:
        table_data.append([
            wrap_cell(row.get("clause", ""), styles['table_cell']),
            wrap_cell(row.get("risk", ""), styles['table_cell']),
            wrap_cell(row.get("mitigation", ""), styles['table_cell'])
        ])
        
    table = Table(table_data, colWidths=widths)
    table.setStyle(make_table_style(len(table_data)))
    story.append(table)
    
    doc.build(story)
    return output_path_or_buffer
