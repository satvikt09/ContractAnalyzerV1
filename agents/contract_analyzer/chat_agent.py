"""Sample conversational agent scaffold (ped_c-inspired).

Fill the TODO sections to make this agent production-ready, then copy the
completed module into `geg_guru/agents/<agent_name>/chat_agent.py`.

Key expectations:
- Uses Claude 3.7 Sonnet on Bedrock (HTTPS by default) with optional image
  payloads when PDF text extraction fails.
- Reads AWS credentials from environment only (`AWS_REGION`, `AWS_ACCESS_KEY_ID`,
  `AWS_SECRET_ACCESS_KEY`, optional `BEDROCK_MODEL_ID` override).
- Keeps processing inside the Django app; adjust storage if you offload to S3.
"""

from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import boto3
from botocore.exceptions import ClientError

from agents.contract_analyzer.services.contract_pipeline import (
    process_contract
)

# Optional heavy deps: keep guarded so the scaffold can import even if missing.
try:
    import fitz  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    fitz = None  # type: ignore

try:
    import textract  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    textract = None  # type: ignore

# -------------------------------
# Basic configuration
# -------------------------------
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt"}
MAX_UPLOAD_FILES = 10
MAX_UPLOAD_BYTES = 50 * 1024 * 1024
HISTORY_LIMIT = 25

# Default to Claude 3.7 Sonnet; replace ARN if your deployment differs.
AWS_REGION = os.environ.get("AWS_REGION", "ap-south-1")
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
BEDROCK_MODEL_ID = os.environ.get(
    "BEDROCK_MODEL_ID",
    "arn:aws:bedrock:ap-south-1::foundation-model/anthropic.claude-3-7-sonnet-20250219-v1:0",
)
DEFAULT_TEMPERATURE = 0.2
DEFAULT_TOP_P = 0.9
DEFAULT_MAX_TOKENS = 2048

PROJECT_ROOT = Path(__file__).resolve().parents[2]
UPLOAD_ROOT = PROJECT_ROOT / "media" / "custom_dev_sample_agent"
UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)

_bedrock_client = None


@dataclass
class UploadedArtifact:
    name: str
    path: Path
    mime: Optional[str] = None
    size: Optional[int] = None
    text_preview: Optional[str] = None
    # Store anything else you need (e.g., embeddings, page ranges, metadata)
    extras: Dict[str, Any] = field(default_factory=dict)

#updated sessionState as follows:
# Replaced vector_index from the sample RAG agent with contract-processing state.
# The Contract Analyzer uses a sequential pipeline
# each stage's output must be stored in session memory for downstream agents.
@dataclass
class SessionState:
    files: List[UploadedArtifact] = field(default_factory=list)

    history: List[Dict[str, str]] = field(default_factory=list)

    extracted_text: str = ""

    sections: List[Dict[str, Any]] = field(
        default_factory=list
    )

    classified_clauses: List[
        Dict[str, Any]
    ] = field(
        default_factory=list
    )
    compliance_results: List[
        Dict[str, Any]
    ] = field(
        default_factory=list
    )

    clause_analysis: List[
        Dict[str, Any]
    ] = field(
        default_factory=list
    )

    risk_analysis: List[
        Dict[str, Any]
    ] = field(
        default_factory=list
    )

    mitigation_analysis: List[
        Dict[str, Any]
    ] = field(
        default_factory=list
    )

    executive_summary: Dict[
        str,
        Any
    ] = field(
        default_factory=dict
    )

    report_path: str = ""

_SESSION_DATA: Dict[str, SessionState] = {}


def _ensure_session(session_id: str) -> SessionState:
    state = _SESSION_DATA.setdefault(session_id, SessionState())
    # Keep chat history bounded.
    if len(state.history) > HISTORY_LIMIT:
        state.history = state.history[-HISTORY_LIMIT:]
    return state


def reset_session(session_id: str) -> None:
    """Clear uploads and chat state."""
    _SESSION_DATA[session_id] = SessionState()


def list_files(session_id: str) -> List[Dict[str, Any]]:
    state = _ensure_session(session_id)
    return [{"name": f.name, "size": f.size} for f in state.files]


def remove_uploaded_file(session_id: str, filename: str) -> Dict[str, Any]:
    """Remove a file from session and disk."""
    state = _ensure_session(session_id)
    keep: List[UploadedArtifact] = []
    removed = False
    for f in state.files:
        if f.name == filename:
            removed = True
            try:
                f.path.unlink(missing_ok=True)
            except Exception:
                pass
        else:
            keep.append(f)
    state.files = keep
    return {"removed": removed, "files": list_files(session_id)}


def _get_bedrock_client():
    global _bedrock_client
    if _bedrock_client is None:
        _bedrock_client = boto3.client(
            "bedrock-runtime",
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        )
    return _bedrock_client


def call_bedrock_chat(
    prompt: str,
    *,
    system_message: str | None = None,
    model_id: str | None = None,
    temperature: float | None = None,
    top_p: float | None = None,
    max_tokens: int | None = None,
    image_bytes: Optional[List[bytes]] = None,
) -> str:
    """Minimal Bedrock wrapper with image fallback support."""
    model = model_id or BEDROCK_MODEL_ID
    if not model:
        raise RuntimeError("BEDROCK_MODEL_ID must be set in environment.")

    temp = float(DEFAULT_TEMPERATURE if temperature is None else temperature)
    tp = float(DEFAULT_TOP_P if top_p is None else top_p)
    max_tok = int(DEFAULT_MAX_TOKENS if max_tokens is None else max_tokens)

    client = _get_bedrock_client()

    # Bedrock v2 (converse) path with optional image parts.
    images = []
    for blob in image_bytes or []:
        try:
            images.append({"image": {"format": "png", "source": {"bytes": blob}}})
        except Exception:
            continue

    try:
        messages = [{"role": "user", "content": [{"text": prompt}, *images]}]
        system_blocks = [{"text": system_message}] if system_message else []
        resp = client.converse(
            modelId=model,
            messages=messages,
            inferenceConfig={"temperature": temp, "topP": tp, "maxTokens": max_tok},
            system=system_blocks or None,
        )
        parts = resp.get("output", {}).get("message", {}).get("content", []) or []
        text = "".join(p.get("text", "") for p in parts if isinstance(p, dict))
        if text.strip():
            return text.strip()
    except Exception as err:
        last_error: Exception | None = err
    else:
        last_error = None

    # Fallback to legacy invoke_model.
    body = {
        "prompt": f"[System]\n{system_message}\n\n[User]\n{prompt}" if system_message else prompt,
        "max_tokens_to_sample": max_tok,
        "temperature": temp,
        "top_p": tp,
    }
    try:
        resp = client.invoke_model(
            modelId=model,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(body),
        )
        data = json.loads(resp["body"].read().decode("utf-8"))
        if isinstance(data, dict):
            if data.get("generation"):
                return str(data["generation"]).strip()
            if data.get("outputs"):
                return str(data["outputs"][0].get("text", "")).strip()
            if data.get("output_text"):
                return str(data["output_text"]).strip()
    except Exception as err:
        last_error = last_error or err

    raise last_error or RuntimeError("Bedrock returned an empty response.")


def _save_upload(session_id: str, upload) -> UploadedArtifact:
    """Persist an uploaded file to disk; customize to use S3 if needed."""
    suffix = Path(upload.name).suffix.lower()
    session_dir = UPLOAD_ROOT / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    target = session_dir / upload.name

    with target.open("wb") as fh:
        for chunk in upload.chunks() if hasattr(upload, "chunks") else [upload.read()]:
            fh.write(chunk)

    size = target.stat().st_size
    return UploadedArtifact(name=upload.name, path=target, size=size, mime=getattr(upload, "content_type", None))


def _extract_text(path: Path) -> str:
    """Extract text from a file. Replace with your own pipeline as needed."""
    # TODO: implement robust PDF/DOCX extraction. Example placeholders below.
    if textract and path.suffix.lower() in {".pdf", ".doc", ".docx"}:
        try:
            return textract.process(str(path)).decode("utf-8", errors="ignore")
        except Exception:
            pass
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def _extract_images_from_pdf(path: Path, limit: int = 3) -> List[bytes]:
    """Fallback: render first N pages to images if text extraction is weak."""
    if not fitz or path.suffix.lower() != ".pdf":
        return []
    images: List[bytes] = []
    try:
        doc = fitz.open(str(path))
        for i, page in enumerate(doc):
            if i >= limit:
                break
            pix = page.get_pixmap(dpi=120)
            images.append(pix.tobytes("png"))
    except Exception:
        return []
    return images

# Modified for Contract Analyzer:
# Processes uploaded contracts through extraction,segmentation, and clause classification 
# instead of storing only a text preview for chat.
def index_uploaded_files(
    session_id: str,
    uploads: Sequence[Any]
) -> Dict[str, Any]:

    state = _ensure_session(
        session_id
    )

    warnings = []

    if (
        len(state.files)
        + len(uploads)
        > MAX_UPLOAD_FILES
    ):
        raise ValueError(
            f"Too many files. Limit: {MAX_UPLOAD_FILES}"
        )

    for upload in uploads:

        suffix = (
            Path(upload.name)
            .suffix
            .lower()
        )

        if suffix not in ALLOWED_EXTENSIONS:

            warnings.append(
                f"Skipped {upload.name}: unsupported type."
            )

            continue

        artifact = _save_upload(
            session_id,
            upload
        )

        if (
            artifact.size
            and artifact.size
            > MAX_UPLOAD_BYTES
        ):

            warnings.append(
                f"Skipped {artifact.name}: exceeds size limit."
            )

            artifact.path.unlink(
                missing_ok=True
            )

            continue

        state.files.append(
            artifact
        )

        try:

            print("\n" + "=" * 60)
            print("PROCESSING FILE")
            print("=" * 60)
            print(f"File: {artifact.name}")
            print(f"Path: {artifact.path}")

            result = process_contract(
                str(artifact.path)
            )

            state.extracted_text = (
                result["extraction"]["raw_text"]
            )

            state.sections = (
                result["sections"]
            )

            state.classified_clauses = (
                result["classified_clauses"]
            )

            state.compliance_results = (
                result["compliance_results"]
            )
            state.risk_analysis = (
                result.get(
                    "risk_results",
                    []
                )
            )            
            state.mitigation_analysis = (
                result.get(
                    "mitigation_results",
                    []
                )
            )
            state.executive_summary = (
                result.get(
                    "executive_summary",
                    {}
                )
            )            
            state.report_path = (
                result.get(
                    "report_path",
                    ""
                )
            )
            print("\n" + "=" * 60)
            print("FINAL SUMMARY")
            print("=" * 60)

            print(
                f"Sections Found: {len(state.sections)}"
            )

            print(
                f"Clauses Classified: {len(state.classified_clauses)}"
            )

            print(
                f"Risk Rows: {len(state.risk_analysis)}"
            )
            print(
                f"Mitigation Rows: "
                f"{len(state.mitigation_analysis)}"
            )            
            print("=" * 60 + "\n")

        except Exception as e:

            print("\n" + "=" * 60)
            print("ERROR")
            print("=" * 60)
            print(str(e))
            print("=" * 60 + "\n")

            warnings.append(
                f"{artifact.name}: {str(e)}"
            )

    return {
        "files": list_files(session_id),

        "warnings": warnings,

        "sections":
            state.sections,

        "classified_clauses":
            state.classified_clauses,

        "compliance_results":
            state.compliance_results,

        "risk_results":
            state.risk_analysis,

        "mitigation_results":
            state.mitigation_analysis,

        "executive_summary":
            state.executive_summary,

        "report_path":
            state.report_path
    }


def answer_question(
    session_id: str,
    message: str,
    *,
    top_k: int = 3,
) -> Dict[str, Any]:
    """Route the user question through retrieval + Claude chat."""
    state = _ensure_session(session_id)
    message = (message or "").strip()
    if not message:
        raise ValueError("Message cannot be empty.")

    # TODO: replace with real retrieval from `state.vector_index` or similar.
    context_snippets: List[str] = []
    for f in state.files[:top_k]:
        if f.text_preview:
            context_snippets.append(f"File: {f.name}\n{f.text_preview}")

    # If no text context, fall back to the first available image bytes.
    image_payload: List[bytes] = []
    for f in state.files:
        image_payload = f.extras.get("image_bytes") or []
        if image_payload:
            break

    prompt_parts = [
        "Context:",
        "\n---\n".join(context_snippets) if context_snippets else "[No text context extracted yet.]",
        "\n\nUser question:",
        message,
    ]
    raw_prompt = "\n".join(prompt_parts)

    reply = call_bedrock_chat(
        raw_prompt,
        system_message=DEFAULT_SYSTEM_PROMPT,
        model_id=BEDROCK_MODEL_ID,
        image_bytes=image_payload or None,
    )

    # Track chat history (plaintext only).
    state.history.append({"role": "user", "content": message})
    state.history.append({"role": "assistant", "content": reply})
    if len(state.history) > HISTORY_LIMIT:
        state.history = state.history[-HISTORY_LIMIT:]

    return {
        "answer": reply,
        "copy_ready": True,
        "chat_history": list(state.history),
        "used_files": [f.name for f in state.files],
    }


def export_session_state(session_id: str) -> Dict[str, Any]:
    """Serialize session state to persist across requests (e.g., in cache)."""
    state = _ensure_session(session_id)
    return {
        "files": [
            {
                "name": f.name,
                "path": str(f.path),
                "size": f.size,
                "mime": f.mime,
                "text_preview": f.text_preview,
                "image_bytes": [_encode_bytes(b) for b in f.extras.get("image_bytes", [])],
            }
            for f in state.files
        ],
        "history": list(state.history),
    }


def restore_session_state(session_id: str, payload: Dict[str, Any]) -> None:
    """Rehydrate state that was produced by `export_session_state`."""
    files: List[UploadedArtifact] = []
    for entry in payload.get("files", []):
        path = Path(entry.get("path", ""))
        files.append(
            UploadedArtifact(
                name=entry.get("name", path.name),
                path=path,
                size=entry.get("size"),
                mime=entry.get("mime"),
                text_preview=entry.get("text_preview"),
                extras={
                    "image_bytes": [
                        b for b in (_decode_bytes(x) for x in entry.get("image_bytes") or []) if b
                    ]
                },
            )
        )

    state = SessionState(
        files=files,
        history=list(payload.get("history", [])),
    )
    _SESSION_DATA[session_id] = state


def _encode_bytes(blob: Optional[bytes]) -> Optional[str]:
    if not blob:
        return None
    try:
        return base64.b64encode(blob).decode("ascii")
    except Exception:
        return None


def _decode_bytes(value: Optional[str]) -> Optional[bytes]:
    if not value:
        return None
    try:
        return base64.b64decode(value.encode("ascii"))
    except Exception:
        return None

