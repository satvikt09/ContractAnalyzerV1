import re


def extract_locations(text: str) -> list[str]:
    """Extract and sort reference numbers found in the text."""
    return sorted(
        set(
            re.findall(
                r'\b\d{5}\.\d+(?:\.\d+)?\b',
                text
            )
        )
    )