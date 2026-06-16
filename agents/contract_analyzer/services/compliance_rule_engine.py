import re

RESIDUAL_RISK_SIGNALS = {

    # Strong signals
    "except": 3,
    "excluding": 3,
    "excluded": 3,
    "unless": 3,
    "subject to": 3,
    "notwithstanding": 3,
    "however": 3,

    # Medium signals
    "limited to": 2,
    "only": 2,
    "approval": 2,
    "deemed": 2,
    "provided that": 2,
    "tier-1": 2,
    "critical supplier": 2,

    # Commercial limitation signals
    "salvage": 2,
    "undelivered balance": 2,
    "bridge guarantee": 2,
    "expert determination": 2,

    # Scope restrictions
    "at buyer discretion": 2,
    "sole discretion": 2,
    "may terminate": 1,
    "may suspend": 1
}

def residual_risk_score(text):
    text = text.lower()
    score = 0
    for signal, weight in RESIDUAL_RISK_SIGNALS.items():
        if signal in text:
            score += weight
    return score

RESIDUAL_RISK_REQUIREMENTS = {
    "Applies to subcontractors","Equipment damage covered while at buyer premises",
    "Liability carve-outs defined","Consequential damages excluded",
    "Exceptions to exclusion defined","Seat of arbitration specified",
    "Arbitration mechanism defined","All payments Net 30 days from invoice",
    "Guarantee period defined","Coverage scope specified"
}

def extract_percentages(text):
    matches = re.findall(
        r'(\d+(?:\.\d+)?)\s*%',
        text
    )

    return [
        float(x)
        for x in matches
    ]
def extract_days(text):
    matches = re.findall(
        r'(\d+)\s*(?:day|days)',
        text.lower()
    )
    return [
        int(x)
        for x in matches
    ]

def extract_months(text):
    matches = re.findall(
        r'(\d+)\s*(?:month|months)',
        text.lower()
    )
    return [
        int(x)
        for x in matches
    ]

def extract_sentences(text):
    sentences = re.split(
        r"(?<=[.!?])\s+",
        text
    )
    cleaned = []
    for s in sentences:
        s = s.strip()
        if len(s) < 20:
            continue
        cleaned.append(s)
    return cleaned

def find_best_evidence(
    content,
    keywords
):
    sentences = extract_sentences(content)
    best_sentence = ""
    best_score = -999
    for sentence in sentences:
        sentence_lower = sentence.lower()
        score = 0
        # keyword matches
        for keyword in keywords:
            if keyword.lower() in sentence_lower:
                score += 3
        # prefer detailed sentences
        score += min(
            len(sentence) / 100,
            5
        )
        # punish headings
        if re.match(
            r"^\d+(\.\d+)*",
            sentence.strip()
        ):
            score -= 5
        # prefer sentences with numbers
        if re.search(
            r"\d+",
            sentence
        ):
            score += 2
        if score > best_score:
            best_score = score
            best_sentence = sentence
    return best_sentence, best_score
REQUIREMENT_KEYWORDS = {
    "Payment Terms": [
        "payment",
        "invoice",
        "billing"
    ],
    "Bank Guarantees": [
        "guarantee",
        "security",
        "bond"
    ],
    "Liquidated Damages": [
        "liquidated",
        "delay",
        "damages"
    ],
    "Guarantee": [
        "warranty",
        "repair",
        "replacement"
    ],
    "Force Majeure": [
        "force majeure",
        "event",
        "notice"
    ],
    "Termination": [
        "termination",
        "cancel"
    ],
    "Suspension": [
        "suspend",
        "suspension"
    ],
    "Change Orders": [
        "change",
        "amendment"
    ],
    "Governing Law": [
        "law",
        "jurisdiction"
    ],
    "Dispute Resolution": [
        "arbitration",
        "dispute"
    ],
    "Insurance": [
        "insurance",
        "coverage"
    ],
    "Liability": [
        "liability",
        "cap"
    ],
    "Consequential Damages": [
        "consequential",
        "indirect"
    ],
    "Critical Sub-Suppliers": [
        "vendor",
        "supplier",
        "sub-supplier"
    ]
}
def build_evidence(
    clause_obj,
    keywords
):
    evidence, score = find_best_evidence(
        clause_obj["content"],
        keywords
    )
    if evidence:
        return evidence
    return clause_obj["content"][:500]

def find_clause(
    clause_type,
    classified_clauses
):
    return next(
        (
            c
            for c in classified_clauses
            if c["clause_type"]
            == clause_type
        ),
        None
    )


def build_result(
    clause,
    requirement,
    evidence,
    remarks=None,
    confidence=0.90,
    clause_content="",
    location=""
):

    return {
        "clause": clause,
        "requirement": requirement,
        "status": "Met",
        "evidence": evidence,
        "remarks": remarks or evidence,
        "confidence": confidence,
        "clause_content": clause_content,
        "location": location
    }

def evaluate_requirement(
    requirement,
    classified_clauses
):

    clause = requirement["clause"]

    req = requirement["requirement"]

    clause_type_map = {

        "Payment Terms": "payment",

        "Bank Guarantees": "bank_guarantees",

        "Liquidated Damages": "liquidated_damages",

        "Guarantee": "warranties",

        "Force Majeure": "force_majeure",

        "Termination": "termination",

        "Suspension": "suspension",

        "Change Orders": "change_orders",

        "Governing Law": "governing_law",

        "Insurance": "insurance",

        "Liability": "liability",

        "Consequential Damages":
            "consequential_damages"
    }

    # ----------------------------------
    # CRITICAL SUB-SUPPLIERS
    # ----------------------------------

    if clause == "Critical Sub-Suppliers":

        annex = next(
            (
                c
                for c in classified_clauses
                if "annex"
                in c["title"].lower()
            ),
            None
        )

        if not annex:

            return None

        evidence, score = (
            find_best_evidence(
                annex["content"],
                REQUIREMENT_KEYWORDS.get(
                    clause,
                    []
                )
            )
        )

        print(
            f"{clause} | {req} | score={score}"
        )

        if score < 2:

            return None

        return build_result(
            clause,
            req,
            evidence,
            confidence=min(
                0.80 + (score * 0.05),
                0.99
            )
        )

    # ----------------------------------
    # DISPUTE RESOLUTION
    # ----------------------------------

    if clause == "Dispute Resolution":

        dispute = find_clause(
            "governing_law",
            classified_clauses
        )

        if not dispute:

            return None

        evidence, score = (
            find_best_evidence(
                dispute["content"],
                REQUIREMENT_KEYWORDS.get(
                    clause,
                    []
                )
            )
        )

        print(
            f"{clause} | {req} | score={score}"
        )

        if score < 2:

            return None

        return build_result(
            clause,
            req,
            evidence,
            confidence=min(
                0.80 + (score * 0.05),
                0.99
            )
        )
    # ----------------------------------
    # BANK GUARANTEES
    # ----------------------------------

    if clause == "Bank Guarantees":

        bg_clause = find_clause(
            "bank_guarantees",
            classified_clauses
        )

        if not bg_clause:
            return None

        content = bg_clause["content"].lower()

        if req == "Bank Guarantee validity period defined":

            if (
                "valid until" in content
                or "validity" in content
                or "expiry" in content
            ):
                evidence, _ = find_best_evidence(
                    bg_clause["content"],
                    [
                        "valid",
                        "validity",
                        "expiry",
                        "guarantee"
                    ]
                )

                return build_result(
                    clause,
                    req,
                    evidence,
                    clause_content=bg_clause["content"],
                    location=bg_clause["title"]
                )

        percentages = extract_percentages(
            content
        )

        total_security = sum(
            percentages
        )

        if (
            req == "Performance Guarantee not exceeding 10%"
            and total_security > 10
        ):

            return {
                "clause": clause,
                "requirement": req,
                "status": "Not Met",
                "evidence": build_evidence(bg_clause,
                    ["guarantee", "security", "bond"]
                ),
                "remarks": f"Total security obligations found: {total_security}%",
                "confidence": 0.98,
                "clause_content": bg_clause["content"],
                "location": bg_clause["title"]
            }

        return None

    # ----------------------------------
    # PAYMENT TERMS
    # ----------------------------------

    if clause == "Payment Terms":

        payment_clause = find_clause(
            "payment",
            classified_clauses
        )

        if not payment_clause:
            return None

        content = payment_clause["content"]

        percentages = extract_percentages(
            content
        )

        days = extract_days(
            content
        )

        # Advance payment requirements
        if req == "45% Minimum Advance":

            content_lower = content.lower()

            if (
                "45%" in content
                or "45 percent" in content_lower
            ):

                if any(
                    x in content_lower
                    for x in [
                        "after",
                        "approval",
                        "kick-off",
                        "pbg",
                        "document register",
                        "subject to"
                    ]
                ):

                    return {
                        "clause": clause,
                        "requirement": req,
                        "status": "Partially Met",
                        "evidence": build_evidence(
                            payment_clause,
                            ["payment", "advance", "invoice"]
                        ),
                        "remarks": "Advance payment split across conditions",
                        "confidence": 0.95,
                        "clause_content": payment_clause["content"],
                        "location": payment_clause["title"]
}

                return build_result(
                    clause,
                    req,
                    payment_clause["title"],
                    clause_content=payment_clause["content"],
                    location=payment_clause["title"]
                )
        # Net day requirements
        if "day" in req.lower():

            required_days = extract_days(
                req
            )

            if required_days and days:

                if required_days[0] in days:

                    content_lower = content.lower()

                    if any(
                        x in content_lower
                        for x in [
                            "grn",
                            "inspection",
                            "acceptance",
                            "approval",
                            "reconciliation"
                        ]
                    ):

                        return {
                            "clause": clause,
                            "requirement": req,
                            "status": "Partially Met",
                            "evidence": f"Found days: {days}",
                            "remarks": "Payment subject to additional conditions",
                            "confidence": 0.95,
                            "clause_content": payment_clause["content"],
                            "location": payment_clause["title"]
                        }

                    return build_result(
                        clause,
                        req,
                        f"Found days: {days}"
                    )

        return None  
    # ----------------------------------
    # LIABILITY
    # ----------------------------------

    if clause == "Liability":

        liability_clause = find_clause(
            "liability",
            classified_clauses
        )

        if liability_clause:

            content = liability_clause["content"].lower()

            if req == "Aggregate liability cap defined":

                percentages = extract_percentages(content)

                if percentages:

                    cap = max(percentages)

                    if cap > 100:

                        return {
                            "clause": clause,
                            "requirement": req,
                            "status": "Not Met",
                            "evidence": liability_clause["title"],
                            "remarks": f"Liability cap is {cap}%",
                            "confidence": 0.98,
                            "clause_content": liability_clause["content"],
                            "location": liability_clause["title"]
                        }

                    evidence, _ = find_best_evidence(
                        liability_clause["content"],
                        ["liability", "cap", "%"]
                    )

                    return build_result(
                        clause,
                        req,
                        evidence,
                        clause_content=liability_clause["content"],
                        location=liability_clause["title"]
                    )
    # ----------------------------------
    # INSURANCE
    # ----------------------------------

    if clause == "Insurance":

        insurance_clause = find_clause(
            "insurance",
            classified_clauses
        )

        if insurance_clause:

            content = insurance_clause["content"].lower()

            if req == "Insurance responsibilities defined":

                if "insurance" in content:

                    evidence, _ = find_best_evidence(
                        insurance_clause["content"],
                        [
                            "insurance",
                            "cover",
                            "coverage",
                            "insured"
                        ]
                    )
                    if req == "Coverage scope specified":

                        if (
                            "coverage" in content
                            or "cover" in content
                            or "insured" in content
                        ):

                            if any(
                                x in content
                                for x in [
                                    "exclude",
                                    "excluded",
                                    "excluding",
                                    "except",
                                    "not covered"
                                ]
                            ):

                                return {
                                    "clause": clause,
                                    "requirement": req,
                                    "status": "Partially Met",
                                    "evidence": insurance_clause["title"],
                                    "remarks": "Coverage exists but exclusions are present",
                                    "confidence": 0.95,
                                    "clause_content": insurance_clause["content"],
                                    "location": insurance_clause["title"]
                                }

                            return build_result(
                                clause,
                                req,
                                insurance_clause["title"],
                                clause_content=insurance_clause["content"],
                                location=insurance_clause["title"]
                            )
                if any(
                    x in content
                    for x in [
                        "exclude",
                        "excluded",
                        "excluding",
                        "except",
                        "not covered"
                    ]
                ):

                    return {
                        "clause": clause,
                        "requirement": req,
                        "status": "Partially Met",
                        "evidence": insurance_clause["title"],
                        "remarks": "Coverage exists but exclusions are present",
                        "confidence": 0.95,
                        "clause_content": insurance_clause["content"],
                        "location": insurance_clause["title"]
                    }

                return build_result(
                    clause,
                    req,
                    insurance_clause["title"],
                    clause_content=insurance_clause["content"],
                    location=insurance_clause["title"]
                )
    if clause == "Termination":

        termination_clause = find_clause(
            "termination",
            classified_clauses
        )

        if not termination_clause:
            return None

        content = termination_clause["content"].lower()

        # --------------------------------
        # Termination rights defined
        # --------------------------------

        if req == "Termination rights defined":

            if any(
                x in content
                for x in [
                    "terminate",
                    "termination",
                    "cancel",
                    "cancellation",
                    "early termination"
                ]
            ):

                evidence, _ = find_best_evidence(
                    termination_clause["content"],
                    [
                        "terminate",
                        "termination",
                        "cancel",
                        "cancellation"
                    ]
                )

                return build_result(
                    clause,
                    req,
                    evidence,
                    clause_content=termination_clause["content"],
                    location=termination_clause["title"]
                )

        # --------------------------------
        # Cancellation fee structure defined
        # --------------------------------

        if req == "Cancellation fee structure defined":

            percentages = extract_percentages(
                content
            )

            if len(percentages) >= 3:

                evidence, _ = find_best_evidence(
                    termination_clause["content"],
                    [
                        "%",
                        "day",
                        "cancellation"
                    ]
                )

                return build_result(
                    clause,
                    req,
                    evidence,
                    clause_content=termination_clause["content"],
                    location=termination_clause["title"]
                )

        # --------------------------------
        # Exact percentage requirements
        # --------------------------------

        percentages = extract_percentages(
            content
        )

        required_percentages = extract_percentages(
            req
        )

        if required_percentages:

            required = required_percentages[0]

            if required in percentages:

                return build_result(
                    clause,
                    req,
                    termination_clause["title"],
                    clause_content=termination_clause["content"],
                    location=termination_clause["title"]
                )

            return {
                "clause": clause,
                "requirement": req,
                "status": "Not Met",
                "evidence": termination_clause["title"],
                "remarks": f"Required {required}% not found",
                "confidence": 0.95,
                "clause_content": termination_clause["content"],
                "location": termination_clause["title"]
            }

        return None  

    if clause == "Liquidated Damages":

        ld_clause = find_clause(
            "liquidated_damages",
            classified_clauses
        )

        if not ld_clause:
            return None

        content = ld_clause["content"]

        if req == "Aggregate LD capped at 5% PO value":

            required = extract_percentages(req)

            found = extract_percentages(content)

            if required and found:

                actual = max(found)

                if actual == required[0]:

                    return build_result(
                        clause,
                        req,
                        build_evidence(
                            ld_clause,
                            ["liquidated", "delay", "damages"]
                        ),
                        clause_content=ld_clause["content"],
                        location=ld_clause["title"]
                    )

                elif actual > required[0]:

                    return {
                        "clause": clause,
                        "requirement": req,
                        "status": "Not Met",
                        "evidence": build_evidence(ld_clause,
                            ["liquidated", "delay", "damages"]
                        ),
                        "remarks": f"Found {actual}% cap",
                        "confidence": 0.98,
                        "clause_content": ld_clause["content"],
                        "location": ld_clause["title"]
                    }
    # ----------------------------------
    # SUSPENSION
    # ----------------------------------

    if clause == "Suspension":

        suspension_clause = find_clause(
            "suspension",
            classified_clauses
        )

        if not suspension_clause:
            return None

        content = suspension_clause["content"].lower()

        # -----------------------------
        # Maximum suspension limit
        # -----------------------------

        if req == "Maximum 2 suspensions and 30 days aggregate":

            if any(
                x in content
                for x in [
                    "regulatory",
                    "government",
                    "legal",
                    "safety"
                ]
            ):
                return {
                    "clause": clause,
                    "requirement": req,
                    "status": "Partially Met",
                    "evidence": "Suspension limits exclude regulatory, government, legal, and safety stoppages",
                    "remarks": "Certain suspension categories excluded from limit",
                    "confidence": 0.95,
                    "clause_content": suspension_clause["content"],
                    "location": suspension_clause["title"]
                }
            return build_result(
                clause,
                req,
                suspension_clause["title"],
                clause_content=suspension_clause["content"],
                location=suspension_clause["title"]
            )

        # -----------------------------
        # Supplier obligations
        # -----------------------------

        if req == "Supplier obligations during suspension defined":

            if any(
                x in content
                for x in [
                    "supplier shall",
                    "supplier must",
                    "contractor shall",
                    "contractor must",
                    "continue",
                    "obligation"
                ]
            ):

                evidence, _ = find_best_evidence(
                    suspension_clause["content"],
                    [
                        "supplier",
                        "shall",
                        "must",
                        "continue",
                        "obligation"
                    ]
                )

                return build_result(
                    clause,
                    req,
                    evidence,
                    clause_content=suspension_clause["content"],
                    location=suspension_clause["title"]
                )

        return None  
    
    if clause == "Force Majeure":

        fm_clause = find_clause(
            "force_majeure",
            classified_clauses
        )

        if not fm_clause:
            return None

        content = fm_clause["content"].lower()

        if req == "Applies to subcontractors":

            if (
                "tier-1" in content
                or "critical supplier" in content
                or "approved supplier" in content
            ):
                return {
                    "clause": clause,
                    "requirement": req,
                    "status": "Partially Met",
                    "evidence": "Force majeure applies only to named Tier-1 / approved suppliers",
                    "remarks": "Applies only to specific suppliers",
                    "confidence": 0.95,
                    "clause_content": fm_clause["content"],
                    "location": fm_clause["title"]
                }                                                      
    # ----------------------------------
    # STANDARD CLAUSES
    # ----------------------------------

    clause_type = clause_type_map.get(
        clause
    )

    if not clause_type:

        return None

    clause_obj = find_clause(
        clause_type,
        classified_clauses
    )

    if not clause_obj:

        return None

    evidence, score = (
        find_best_evidence(
            clause_obj["content"],
            REQUIREMENT_KEYWORDS.get(
                clause,
                []
            )
        )
    )

    print(
        f"{clause} | {req} | score={score}"
    )

    # IMPORTANT:
    # Weak evidence -> send to Ollama

    if clause in [
        "Governing Law",
        "Insurance",
        "Change Orders"
    ]:

        if score < 1:

            return None

    else:

        if score < 2:

            return None

    if clause in [
        "Termination",
        "Suspension"
    ]:
        return None
    
    risk_score = residual_risk_score(
        clause_obj["content"]
    )

    if risk_score >= 3:

        return {
            "clause": clause,
            "requirement": req,
            "status": "Partially Met",
            "evidence": evidence,
            "remarks": (
                "Clause contains material limitations, "
                "exceptions, carve-outs, conditions, "
                "or restricted applicability"
            ),
            "confidence": 0.90,
            "clause_content": clause_obj["content"],
            "location": clause_obj["title"]
        }

    risk_score = residual_risk_score(
        clause_obj["content"]
    )

    if (
        req in RESIDUAL_RISK_REQUIREMENTS
        and risk_score >= 4
    ):

        return {
            "clause": clause,
            "requirement": req,
            "status": "Partially Met",
            "evidence": evidence,
            "remarks":
                "Requirement exists but contains "
                "material limitations, exceptions, "
                "carve-outs, conditions, or reduced scope.",
            "confidence": 0.90,
            "clause_content": clause_obj["content"],
            "location": clause_obj["title"]
        }

    return build_result(
        clause,
        req,
        evidence,
        confidence=min(
            0.80 + (score * 0.05),
            0.99
        ),
        clause_content=clause_obj["content"],
        location=clause_obj["title"]
    )

def evaluate_compliance_rules(
    checklist_requirements,
    classified_clauses
):

    results = []

    unresolved = []

    for requirement in checklist_requirements:

        result = evaluate_requirement(
            requirement,
            classified_clauses
        )

        if result:

            results.append(
                result
            )

        else:

            unresolved.append(
                requirement
            )

    return {
        "rule_results": results,
        "unresolved_requirements": unresolved
    }