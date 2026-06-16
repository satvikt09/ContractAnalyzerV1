import os
import json

from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)


MODEL = genai.GenerativeModel(
    "gemini-2.5-flash"
)


def classify_clauses_batch(sections):

    if not sections:
        return []

    prompt = """
You are a legal contract clause classifier.

Possible clause types:

- parties
- scope_of_services
- payment
- confidentiality
- termination
- liability
- indemnification
- governing_law
- data_protection
- warranties
- dispute_resolution
- intellectual_property
- force_majeure
- assignment
- miscellaneous
- other

Return ONLY valid JSON.

Format:

[
  {
    "title": "...",
    "clause_type": "...",
    "confidence": 0.95,
    "reason": "..."
  }
]

Clauses:
"""

    for i, section in enumerate(sections, start=1):

        prompt += f"""

Clause {i}

TITLE:
{section["title"]}

CONTENT:
{section["content"][:3000]}
"""

    response = MODEL.generate_content(
        prompt
    )

    try:

        text = response.text.strip()

        if text.startswith("```json"):
            text = text.replace(
                "```json",
                ""
            ).replace(
                "```",
                ""
            )

        return json.loads(text)

    except Exception as e:

        print(
            "Batch classification failed:",
            str(e)
        )

        return []