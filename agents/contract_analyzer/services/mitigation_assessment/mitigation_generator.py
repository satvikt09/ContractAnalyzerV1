import requests

from .mitigation_prompt import (
    MITIGATION_PROMPT
)

OLLAMA_URL = "http://localhost:11434/api/generate"

MODEL_NAME = "qwen3:8b"


def generate_mitigation(risk_row):

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

    return (
        response.json()["response"]
        .strip()
    )