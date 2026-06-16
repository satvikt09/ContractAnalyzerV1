import re


def extract_locations(text):

    return sorted(
        set(
            re.findall(
                r'\b\d{5}\.\d+(?:\.\d+)?\b',
                text
            )
        )
    )