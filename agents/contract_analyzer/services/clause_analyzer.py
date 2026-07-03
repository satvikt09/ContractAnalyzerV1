import json
import os

from dotenv import load_dotenv

import google.generativeai as genai

load_dotenv()

genai.configure(
    api_key=os.getenv(
        "GEMINI_API_KEY"
    )
)

model = genai.GenerativeModel(
    "gemma4:31b-cloud"
)


def analyze_clauses_batch(
    classified_clauses
):

    if not classified_clauses:
        return []

    payload = []

    for clause in classified_clauses:

        payload.append(
            {
                "title":
                    clause["title"],

                "clause_type":
                    clause["clause_type"],

                "content":
                    clause["content"][:3000]
            }
        )

    prompt = f"""
You are an enterprise contract analyst.

For each clause return:

1. summary
2. key obligations
3. risk level

Return JSON only.

Example:

[
  {{
    "title":"PAYMENT TERMS",
    "summary":"...",
    "key_obligations":[
      "...",
      "..."
    ],
    "risk_level":"Medium"
  }}
]

Clauses:

{json.dumps(payload, indent=2)}
"""

    try:

        response = model.generate_content(
            prompt
        )

        text = (
            response.text
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )

        return json.loads(text)

    except Exception as e:

        print(
            f"Clause analysis failed: {e}"
        )

        return []