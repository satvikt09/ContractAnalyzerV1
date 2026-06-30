import os
import logging
# pyrefly: ignore [missing-import]
from docx import Document

logger = logging.getLogger(__name__)

def parse_historical_docx(file_path):
    """
    Parses a historical docx report and extracts the rows of the compliance table.
    Looks for a table with both 'clause' and 'requirement' header fields.
    """
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return []

    try:
        doc = Document(file_path)
    except Exception as e:
        logger.error(f"Error opening docx {file_path}: {e}")
        return []

    extracted_rows = []
    
    for table_idx, table in enumerate(doc.tables):
        if not table.rows:
            continue
            
        # Extract headers from the first row
        headers = [cell.text.strip().lower() for cell in table.rows[0].cells]
        
        # Check if this table has both 'clause' and 'requirement'
        if "clause" in headers and "requirement" in headers:
            # Map header fields to column index
            col_map = {}
            for col_idx, header_text in enumerate(headers):
                if "clause" in header_text:
                    col_map["clause"] = col_idx
                elif "requirement" in header_text:
                    col_map["requirement"] = col_idx
                elif "status" in header_text:
                    col_map["status"] = col_idx
                elif "evidence" in header_text:
                    col_map["evidence"] = col_idx
                elif "remark" in header_text or "assessor" in header_text:
                    col_map["remarks"] = col_idx
                elif "historical" in header_text or "action" in header_text:
                    col_map["historical_action"] = col_idx
                elif "resolution" in header_text:
                    col_map["resolution"] = col_idx

            # Extract data rows
            for row_idx in range(1, len(table.rows)):
                row = table.rows[row_idx]
                cells = row.cells
                
                # Check that we have enough cells
                max_required_idx = max(col_map.values(), default=-1)
                if len(cells) <= max_required_idx:
                    continue
                    
                # Extract text for mapped fields
                clause_val = cells[col_map["clause"]].text.strip() if "clause" in col_map else ""
                req_val = cells[col_map["requirement"]].text.strip() if "requirement" in col_map else ""
                status_val = cells[col_map["status"]].text.strip() if "status" in col_map else ""
                evidence_val = cells[col_map["evidence"]].text.strip() if "evidence" in col_map else ""
                remarks_val = cells[col_map["remarks"]].text.strip() if "remarks" in col_map else ""
                historical_action_val = cells[col_map["historical_action"]].text.strip() if "historical_action" in col_map else ""
                resolution_val = cells[col_map["resolution"]].text.strip() if "resolution" in col_map else ""
                
                # Skip completely blank rows
                if not clause_val and not req_val:
                    continue
                    
                extracted_rows.append({
                    "clause": clause_val,
                    "requirement": req_val,
                    "status": status_val,
                    "evidence": evidence_val,
                    "remarks": remarks_val,
                    "historical_action": historical_action_val,
                    "resolution": resolution_val,
                    "file_source": os.path.basename(file_path)
                })
                
    return extracted_rows
