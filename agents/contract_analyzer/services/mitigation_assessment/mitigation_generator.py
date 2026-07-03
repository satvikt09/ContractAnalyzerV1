import requests
from .mitigation_prompt import MITIGATION_PROMPT

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "gemma4:31b-cloud"


def generate_mitigation(risk_row: dict) -> str:
    """Generate a single concise mitigation recommendation using Ollama."""
    prompt = MITIGATION_PROMPT.format(
        clause=risk_row["clause"],
        requirement=risk_row["requirement"],
        risk=risk_row["risk"],
        rationale=risk_row["rationale"]
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

    return response.json()["response"].strip()