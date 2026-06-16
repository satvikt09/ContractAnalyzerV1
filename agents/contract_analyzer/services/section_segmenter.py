import re


INVALID_HEADINGS = {
    "NAME",
    "FIRM",
    "FUNCTION",
    "PROJECT MANAGER",
    "PROJECT ENGINEER",
    "DATE",
    "PAGE",
    "SIGNATURE",
    "TITLE",
    "ADDRESS",
    "PHONE",
    "EMAIL",
}


def is_document_title(title):

    title = title.strip()

    if not title:
        return False

    words = title.split()

    return (
        len(words) <= 8
        and "AGREEMENT" in title.upper()
        and not re.match(
            r'^\d+\.',
            title
        )
    )


def get_heading_type(line):

    line = line.strip()

    if not line:
        return None

    if line.upper() in INVALID_HEADINGS:
        return None

    # -------------------------
    # TOP LEVEL HEADINGS
    # -------------------------

    # 1. PAYMENT TERMS

    if re.match(
        r'^\d+\.\s+[A-Z]',
        line
    ):
        return "TOP"

    # ARTICLE IV

    if re.match(
        r'^ARTICLE\s+[IVXLC\d]+',
        line,
        re.IGNORECASE
    ):
        return "TOP"

    # SECTION 7

    if re.match(
        r'^SECTION\s+\d+',
        line,
        re.IGNORECASE
    ):
        return "TOP"

    # ALL CAPS HEADINGS

    if (
        line.isupper()
        and 1 <= len(line.split()) <= 10
        and len(line) > 5
        and not re.search(r'\d', line)
        and line.upper() not in INVALID_HEADINGS
    ):
        return "TOP"

    # -------------------------
    # SUBSECTIONS
    # -------------------------

    if re.match(
        r'^\d+\.\d+\s+',
        line
    ):
        return "SUB"

    if re.match(
        r'^[A-Z]\.\s+',
        line
    ):
        return "SUB"

    return None


def clean_content(lines):

    cleaned = []

    for line in lines:

        line = line.strip()

        if not line:
            continue

        # Page number removal

        if re.match(
            r'^Page\s+\d+$',
            line,
            re.IGNORECASE
        ):
            continue

        # Signature cleanup

        if (
            "SIGNATORY:" in line.upper()
            or "EMAIL OF SIGNATORY" in line.upper()
            or "TIMESTAMP:" in line.upper()
        ):
            continue

        cleaned.append(line)

    return "\n".join(cleaned)


def merge_multiline_headings(lines):

    merged = []

    i = 0

    while i < len(lines):

        current = lines[i].strip()

        # Example:
        #
        # 4.
        # EARLY TERMINATION

        if (
            re.match(r'^\d+\.$', current)
            and i + 1 < len(lines)
        ):

            next_line = lines[i + 1].strip()

            if (
                next_line
                and next_line.isupper()
            ):

                merged.append(
                    f"{current} {next_line}"
                )

                i += 2
                continue

        merged.append(current)

        i += 1

    return merged


def segment_contract(text):

    lines = text.splitlines()

    lines = merge_multiline_headings(
        lines
    )

    sections = []

    current_title = None

    current_content = []

    first_top_heading = True

    for line in lines:

        stripped = line.strip()

        if not stripped:
            continue

        heading_type = get_heading_type(
            stripped
        )

        # -------------------------
        # NEW TOP LEVEL SECTION
        # -------------------------

        if heading_type == "TOP":

            if current_title:

                sections.append(
                    {
                        "title": current_title,
                        "content": clean_content(
                            current_content
                        )
                    }
                )

            # -------------------------
            # DOCUMENT TITLE DETECTION
            # Example:
            #
            # SERVICE AGREEMENT
            # VENDOR AGREEMENT
            # MASTER SERVICE AGREEMENT
            #
            # Skip it because it's not a clause
            # -------------------------

            if (
                first_top_heading
                and is_document_title(
                    stripped
                )
            ):

                print(
                    f"[SEGMENTER] Skipping document title: {stripped}"
                )

                first_top_heading = False

                current_title = None

                current_content = []

                continue

            first_top_heading = False

            current_title = stripped

            current_content = []

            continue

        # -------------------------
        # SUBSECTION
        # Keep inside parent clause
        # -------------------------

        if heading_type == "SUB":

            current_content.append(
                f"\n{stripped}"
            )

            continue

        # -------------------------
        # NORMAL CONTENT
        # -------------------------

        current_content.append(
            stripped
        )

    # Final section

    if current_title:

        sections.append(
            {
                "title": current_title,
                "content": clean_content(
                    current_content
                )
            }
        )

    # -------------------------
    # FILTER EMPTY SECTIONS
    # -------------------------

    filtered = []

    for section in sections:

        if not section["content"].strip():
            continue

        filtered.append(section)

    # -------------------------
    # DEBUG
    # -------------------------

    print("\n========== SEGMENTER OUTPUT ==========")

    for section in filtered:

        print(
            f"TITLE: {section['title']}"
        )

    print("=====================================\n")

    # -------------------------
    # FALLBACK
    # -------------------------

    if not filtered:

        return [
            {
                "title": "FULL_DOCUMENT",
                "content": text
            }
        ]

    return filtered