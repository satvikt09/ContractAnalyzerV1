import json
import requests

from .risk_prompt import RISK_PROMPT


OLLAMA_URL = "http://localhost:11434/api/generate"

MODEL_NAME = "gemma3:4b"


def generate_risk_entry(result):

    prompt = RISK_PROMPT.format(
        clause=result["clause"],
        requirement=result["requirement"],
        status=result["status"],
        evidence=result["evidence"],
        remarks=result["remarks"],
        clause_content=result.get(
            "clause_content",
            ""
        ),
        location=result.get(
            "location",
            ""
        )
    )

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False
        },
        timeout=120
    )

    import re

    text = response.json()["response"]

    print("\nRAW GEMMA RESPONSE:")
    print(text)

    # --------------------------------
    # CLEAN RESPONSE
    # --------------------------------

    text = (
        text
        .replace("```json", "")
        .replace("```", "")
        .replace("\t", " ")
        .replace("\r", " ")
        .strip()
    )

    # --------------------------------
    # EXTRACT JSON OBJECT
    # --------------------------------

    match = re.search(
        r"\{.*\}",
        text,
        re.DOTALL
    )

    if match:
        text = match.group()

    # --------------------------------
    # PARSE JSON
    # --------------------------------

    try:
        text = (
            text
            .replace("“", '"')
            .replace("”", '"')
            .replace("’", "'")
            .replace("‘", "'")
        )        

        parsed = json.loads(text)

        return {
            "risk":
                parsed.get(
                    "risk",
                    "Unknown Risk"
                ),

            "rationale":
                parsed.get(
                    "rationale",
                    ""
                ),

            "mitigation":
                parsed.get(
                    "mitigation",
                    ""
                )
        }

    except Exception as e:

        print("\nJSON ERROR:")
        print(e)

        print("\nFAILED JSON:")
        print(text)

        return {
            "risk":
                "Manual Review Required",

            "rationale":
                text[:1000],

            "mitigation":
                "Manual review required"
        }