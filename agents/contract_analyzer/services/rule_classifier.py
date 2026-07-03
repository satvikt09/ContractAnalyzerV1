import re

CLAUSE_RULES = {
    # --------------------------------------------------
    # GENERIC CONTRACT CLAUSES
    # --------------------------------------------------
    "parties": [
        "parties", "definitions", "customer", "client", "service provider"
    ],
    "scope_of_services": [
        "scope of services", "scope", "services", "statement of work", "deliverables", "work description"
    ],
    "payment": [
        "payment", "payment terms", "invoice", "invoicing", "billing", "advance payment", "payment and invoicing"
    ],
    "confidentiality": [
        "confidentiality", "confidential", "non-disclosure", "nda"
    ],
    "termination": [
        "termination", "terminate", "term and termination", "expiration", "duration", "cancellation", "early termination"
    ],
    "indemnification": [
        "indemnification", "indemnify", "hold harmless"
    ],
    "liability": [
        "liability", "liable", "limitation of liability", "limitation of remedies", "defect liability"
    ],
    "governing_law": [
        "governing law", "jurisdiction", "applicable law"
    ],
    "data_protection": [
        "data protection", "privacy", "personal data", "gdpr", "data processing"
    ],
    "warranties": [
        "warranty", "warranties", "guarantee and warranty", "represents and warrants"
    ],
    "intellectual_property": [
        "intellectual property", "ownership", "ownership of deliverables", "copyright", "patent", "trademark", "ip rights"
    ],
    "force_majeure": [
        "force majeure", "act of god", "unforeseeable events"
    ],
    "assignment": [
        "assignment", "assign", "transfer of rights"
    ],
    "dispute_resolution": [
        "dispute resolution", "arbitration", "mediation", "disputes"
    ],

    # --------------------------------------------------
    # BENCHMARK CONTRACT CLAUSES
    # --------------------------------------------------
    "bank_guarantees": [
        "bank guarantee", "bank guarantees", "performance security", "performance bond", "performance guarantee"
    ],
    "liquidated_damages": [
        "liquidated damages", "delay damages", "ld"
    ],
    "suspension": [
        "suspension", "suspend", "suspended"
    ],
    "change_orders": [
        "change order", "change orders", "purchase order amendment", "amendment"
    ],
    "insurance": [
        "insurance", "insured", "property insurance", "insurance at godrej premises"
    ],
    "consequential_damages": [
        "consequential damages", "indirect damages", "loss of revenue", "loss of profit"
    ],
    "critical_sub_suppliers": [
        "critical sub-suppliers", "critical suppliers", "sub-supplier", "sub-suppliers", "approved vendor", "approved critical vendor"
    ]
}


def classify_rule_based(title: str, content: str) -> dict | None:
    """Classify a clause based on rule keywords matched in the title or content."""
    title_lower = title.lower()
    content_lower = content.lower()

    skip_payment = any(
        word in title_lower
        for word in ["delivery", "storage", "shipment", "dispatch", "logistics"]
    )

    # PASS 1: Exact title match
    for clause_type, keywords in CLAUSE_RULES.items():
        for keyword in keywords:
            if keyword == title_lower:
                return {
                    "clause_type": clause_type,
                    "confidence": 0.99,
                    "reason": f"Exact title match: {keyword}",
                    "source": "rule"
                }

    # PASS 2: Title contains keyword
    for clause_type, keywords in CLAUSE_RULES.items():
        for keyword in keywords:
            if keyword in title_lower:
                return {
                    "clause_type": clause_type,
                    "confidence": 0.97,
                    "reason": f"Title matched keyword: {keyword}",
                    "source": "rule"
                }

    # PASS 3: Content contains keyword
    for clause_type, keywords in CLAUSE_RULES.items():
        if clause_type == "payment" and skip_payment:
            continue

        for keyword in keywords:
            if re.search(rf"\b{re.escape(keyword)}\b", content_lower):
                return {
                    "clause_type": clause_type,
                    "confidence": 0.93,
                    "reason": f"Content matched keyword: {keyword}",
                    "source": "rule"
                }

    return None