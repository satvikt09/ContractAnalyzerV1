def generate_clause_summary(text):

    if not text:
        return ""

    text = (
        text
        .replace("\n", " ")
        .replace("\t", " ")
        .strip()
    )

    sentences = [
        s.strip()
        for s in text.split(".")
        if len(s.strip()) > 20
    ]

    return ". ".join(
        sentences[:3]
    )