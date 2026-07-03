import re

INVALID_HEADINGS = {
    "NAME", "FIRM", "FUNCTION", "PROJECT MANAGER", "PROJECT ENGINEER",
    "DATE", "PAGE", "SIGNATURE", "TITLE", "ADDRESS", "PHONE", "EMAIL",
}


def is_document_title(title: str) -> bool:
    """Check if the title represents a general document title rather than a specific clause."""
    title = title.strip()
    if not title:
        return False
    words = title.split()
    return (
        len(words) <= 8
        and "AGREEMENT" in title.upper()
        and not re.match(r'^\d+\.', title)
    )


def get_heading_type(line: str) -> str | None:
    """Identify if a line is a top-level heading (TOP) or a sub-heading (SUB)."""
    line = line.strip()
    if not line or line.upper() in INVALID_HEADINGS:
        return None

    # Top level headings: '1. PAYMENT TERMS', 'ARTICLE IV', 'SECTION 7', ALL CAPS
    if re.match(r'^\d+\.\s+[A-Z]', line):
        return "TOP"
    if re.match(r'^ARTICLE\s+[IVXLC\d]+', line, re.IGNORECASE):
        return "TOP"
    if re.match(r'^SECTION\s+\d+', line, re.IGNORECASE):
        return "TOP"
    if (
        line.isupper()
        and 1 <= len(line.split()) <= 10
        and len(line) > 5
        and not re.search(r'\d', line)
        and line.upper() not in INVALID_HEADINGS
    ):
        return "TOP"

    # Subsections: '1.1 ', 'A. '
    if re.match(r'^\d+\.\d+\s+', line) or re.match(r'^[A-Z]\.\s+', line):
        return "SUB"

    return None


def clean_content(lines: list[str]) -> str:
    """Clean extra page markers, signature stamps, and join content lines."""
    cleaned = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if re.match(r'^Page\s+\d+$', line, re.IGNORECASE):
            continue
        if (
            "SIGNATORY:" in line.upper()
            or "EMAIL OF SIGNATORY" in line.upper()
            or "TIMESTAMP:" in line.upper()
        ):
            continue
        cleaned.append(line)
    return "\n".join(cleaned)


def merge_multiline_headings(lines: list[str]) -> list[str]:
    """Merge lines where heading labels are split from heading text."""
    merged = []
    i = 0
    while i < len(lines):
        current = lines[i].strip()
        # Handle case like '4.' followed by 'EARLY TERMINATION' on next line
        if re.match(r'^\d+\.$', current) and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if next_line and next_line.isupper():
                merged.append(f"{current} {next_line}")
                i += 2
                continue
        merged.append(current)
        i += 1
    return merged


def segment_contract(text: str) -> list[dict]:
    """Segment raw contract text into structured sections by parsing headings."""
    lines = text.splitlines()
    lines = merge_multiline_headings(lines)

    sections = []
    current_title = None
    current_content = []
    first_top_heading = True

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        heading_type = get_heading_type(stripped)

        if heading_type == "TOP":
            if current_title:
                sections.append({
                    "title": current_title,
                    "content": clean_content(current_content)
                })

            if first_top_heading and is_document_title(stripped):
                print(f"[SEGMENTER] Skipping document title: {stripped}")
                first_top_heading = False
                current_title = None
                current_content = []
                continue

            first_top_heading = False
            current_title = stripped
            current_content = []
            continue

        if heading_type == "SUB":
            current_content.append(f"\n{stripped}")
            continue

        current_content.append(stripped)

    # Add final section
    if current_title:
        sections.append({
            "title": current_title,
            "content": clean_content(current_content)
        })

    # Filter out empty sections
    filtered = [s for s in sections if s["content"].strip()]

    print("\n========== SEGMENTER OUTPUT ==========")
    for section in filtered:
        print(f"TITLE: {section['title']}")
    print("=====================================\n")

    if not filtered:
        return [{"title": "FULL_DOCUMENT", "content": text}]

    return filtered