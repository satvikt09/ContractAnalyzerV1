import os
import json
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
# pyrefly: ignore [missing-import]
import google.generativeai as genai

load_dotenv()

genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)


ALLOWED_CLAUSE_TYPES = [
    "payment",
    "termination",
    "confidentiality",
    "liability",
    "indemnity",
    "governing_law",
    "warranty",
    "force_majeure",
    "dispute_resolution",
    "intellectual_property",
    "scope_of_services",
    "parties",
    "definitions",
    "other"
]


def classify_clause(title, content):

    model = genai.GenerativeModel(
        "gemma4:31b-cloud"
    )

    prompt = f"""
You are a legal contract clause classifier.

Classify the clause into ONE of:

payment
termination
confidentiality
liability
indemnity
governing_law
warranty
force_majeure
dispute_resolution
intellectual_property
scope_of_services
parties
definitions
other

Return ONLY valid JSON.

Example:

{{
  "clause_type": "payment",
  "confidence": 0.95,
  "reason": "Contains payment obligations"
}}

Title:
{title}

Content:
{content}
"""

    try:

        response = model.generate_content(
            prompt
        )

        raw_text = (
            response.text
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )

        result = json.loads(raw_text)

        clause_type = (
            result.get(
                "clause_type",
                "other"
            )
            .lower()
            .strip()
        )

        if clause_type not in ALLOWED_CLAUSE_TYPES:
            clause_type = "other"

        confidence = float(
            result.get(
                "confidence",
                0.0
            )
        )

        reason = result.get(
            "reason",
            ""
        )

        return {
            "clause_type": clause_type,
            "confidence": confidence,
            "reason": reason
        }

    except Exception as e:

        return {
            "clause_type": "other",
            "confidence": 0.0,
            "reason": f"Classification failed: {str(e)}"
        }