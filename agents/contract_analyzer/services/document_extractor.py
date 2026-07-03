import re
import fitz
from docx import Document

from agents.contract_analyzer.services.doc_converter import convert_doc_to_docx


def extract_pdf_text(file_path: str) -> dict:
    """Extract text from PDF file using PyMuPDF."""
    try:
        document = fitz.open(file_path)
    except Exception as e:
        raise ValueError(f"Unable to open PDF: {str(e)}")

    if document.needs_pass:
        raise ValueError("Password protected PDF")

    text = ""
    for page in document:
        text += page.get_text()

    word_count = len(text.split())
    clean_words = re.findall(r"\b[A-Za-z]{3,}\b", text)
    quality_ratio = len(clean_words) / max(word_count, 1)

    print("\n========== PDF QUALITY CHECK ==========")
    print(f"Word Count: {word_count}")
    print(f"Quality Ratio: {quality_ratio}")
    print("=======================================\n")

    if not (word_count > 50 and quality_ratio > 0.60):
        print("Warning: Low quality text extraction detected, but continuing using PyMuPDF.")

    return {
        "text": text,
        "page_count": len(document),
        "extraction_method": "pymupdf"
    }


def extract_docx_text(file_path: str) -> dict:
    """Extract text content from a DOCX file."""
    try:
        document = Document(file_path)
    except Exception as e:
        raise ValueError(f"Unable to open DOCX: {str(e)}")

    paragraphs = [paragraph.text for paragraph in document.paragraphs]
    text = "\n".join(paragraphs)

    return {
        "text": text,
        "page_count": None,
        "extraction_method": "python-docx"
    }


def extract_doc_text(file_path: str) -> dict:
    """Convert and extract text from a legacy DOC file."""
    docx_path = convert_doc_to_docx(file_path)
    return extract_docx_text(docx_path)


def extract_text(file_path: str) -> dict:
    """Route document path to appropriate extractor based on file extension."""
    file_path = str(file_path)
    if file_path.lower().endswith(".pdf"):
        return extract_pdf_text(file_path)
    elif file_path.lower().endswith(".docx"):
        return extract_docx_text(file_path)
    elif file_path.lower().endswith(".doc"):
        return extract_doc_text(file_path)
    else:
        raise ValueError("Unsupported file type")