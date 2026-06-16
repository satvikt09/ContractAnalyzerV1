from unstructured.partition.pdf import partition_pdf
from unstructured.partition.docx import partition_docx
import re


def is_heading(text):

    text = text.strip()

    if not text:
        return False

    # ALL CAPS
    if (
        text.isupper()
        and len(text) > 5
        and len(text.split()) <= 10
    ):
        return True

    # 1. PAYMENT TERMS
    if re.match(
        r'^\d+\.\s+[A-Z]',
        text
    ):
        return True

    return False


def segment_with_unstructured(file_path):

    if file_path.lower().endswith(".pdf"):

        elements = partition_pdf(
            filename=file_path,
            strategy="fast"
        )

    elif file_path.lower().endswith(".docx"):

        elements = partition_docx(
            filename=file_path
        )

    else:

        raise ValueError(
            "Unsupported file type"
        )

    sections = []

    current_title = None
    current_content = []

    for element in elements:

        text = str(element).strip()

        if not text:
            continue

        if is_heading(text):

            if current_title:

                sections.append(
                    {
                        "title": current_title,
                        "content": "\n".join(
                            current_content
                        )
                    }
                )

            current_title = text
            current_content = []

        else:

            current_content.append(text)

    if current_title:

        sections.append(
            {
                "title": current_title,
                "content": "\n".join(
                    current_content
                )
            }
        )

    return sections