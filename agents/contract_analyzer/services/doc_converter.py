import os
import subprocess

SOFFICE_PATH = r"C:\Program Files\LibreOffice\program\soffice.exe"


def convert_doc_to_docx(doc_path: str) -> str:
    """Convert a legacy DOC file to DOCX using LibreOffice CLI."""
    output_dir = os.path.dirname(doc_path)
    command = [
        SOFFICE_PATH,
        "--headless",
        "--convert-to",
        "docx",
        doc_path,
        "--outdir",
        output_dir
    ]

    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise ValueError(f"DOC conversion failed: {result.stderr}")

    docx_path = os.path.splitext(doc_path)[0] + ".docx"
    if not os.path.exists(docx_path):
        raise ValueError("Converted DOCX file not found")

    return docx_path