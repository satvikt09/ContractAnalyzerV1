from agents.contract_analyzer.services.document_extractor import extract_text


def get_extraction(file_path: str) -> dict:
    """Wrapper function to extract and analyze text metrics from document files."""
    try:
        result = extract_text(file_path)
    except Exception as e:
        raise ValueError(f"Extraction failed: {str(e)}")

    return {
        "raw_text": result["text"],
        "page_count": result["page_count"],
        "word_count": len(result["text"].split()),
        "char_count": len(result["text"]),
        "extraction_method": result["extraction_method"]
    }