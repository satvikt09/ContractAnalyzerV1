RISK_SIGNALS = [

    # exceptions
    "except",
    "excluding",
    "exclude",
    "unless",
    "however",
    "notwithstanding",

    # conditional language
    "subject to",
    "provided that",
    "conditional",
    "approval",
    "approval required",
    "prior approval",

    # scope limitations
    "limited to",
    "only",
    "restricted to",

    # legal narrowing
    "deemed",
    "at buyer discretion",
    "sole discretion",
    "may suspend",
    "may terminate",
    "may defer",

    # commercial offsets
    "less",
    "minus",
    "deduct",
    "offset",
    "credit",

    # liability carveouts
    "carve-out",
    "carve out",

    # exclusions
    "does not apply",
    "shall not apply",
    "not applicable",

    # partial coverage
    "undelivered balance",
    "remaining balance",

    # recovery reduction
    "salvage",
    "scrap value",
    "resale value"
]


def contains_risk_signal(text):

    text = text.lower()

    matches = []

    for signal in RISK_SIGNALS:

        if signal in text:
            matches.append(signal)

    return matches