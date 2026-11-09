"""Ollama-backed proposal generation."""

from __future__ import annotations

import os
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from pydantic import ValidationError

from indy_agent.models import Artifact, RefactorError, Proposal
from indy_agent.prompt import SYSTEM_PROMPT, repair_prompt

DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "gemma4:e4b"
DEBUG_CAPTURE_DIRECTORY_ENV = "OLLAMA_DEBUG_CAPTURE_DIR"
DEBUG_CAPTURE_LABEL_ENV = "OLLAMA_DEBUG_CAPTURE_LABEL"


def _write_debug_capture(payload: dict[str, object]) -> None:
    """Optionally persist one request/response pair for local diagnosis.

    This is intentionally disabled by default because a capture includes the
    complete user-provided script and prompt. It is only for comparing local
    development requests, never for production logging.
    """
    directory = os.getenv(DEBUG_CAPTURE_DIRECTORY_ENV)
    if not directory:
        return

    capture_directory = Path(directory)
    capture_directory.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
    capture_file = capture_directory / f"ollama-request-{timestamp}-{uuid4().hex}.json"
    capture_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str))


def _request_proposal(messages: list[SystemMessage | HumanMessage], *, request_kind: str) -> Proposal:
    """Make one structured model call and optionally capture its diagnostics."""
    base_url = os.getenv("OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE_URL)
    model_name = os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)
    model = ChatOllama(
        model=model_name,
        base_url=base_url,
        temperature=0,
    )
    # This is the request dictionary ChatOllama hands to its Ollama client. The
    # structured-output helper below binds this same Pydantic JSON schema as
    # the `format` request parameter.
    capture: dict[str, object] = {
        "captured_at": datetime.now(UTC).isoformat(),
        "label": os.getenv(DEBUG_CAPTURE_LABEL_ENV),
        "request_kind": request_kind,
        "base_url": base_url,
        "model": model_name,
        "ollama_request": model._chat_params(  # noqa: SLF001 - diagnostic capture of library request payload
            messages,
            format=Proposal.model_json_schema(),
        ),
    }
    structured_model = model.with_structured_output(Proposal)
    try:
        response = structured_model.invoke(messages)
    except Exception as error:
        capture["error"] = {"type": type(error).__name__, "message": str(error)}
        _write_debug_capture(capture)
        raise
    if isinstance(response, Proposal):
        capture["parsed_response"] = response.model_dump(mode="json")
        _write_debug_capture(capture)
        return response
    try:
        proposal = Proposal.model_validate(response)
    except ValidationError:
        capture["unparsed_response"] = response
        _write_debug_capture(capture)
        raise
    capture["parsed_response"] = proposal.model_dump(mode="json")
    _write_debug_capture(capture)
    return proposal


def request_proposal(source_script: str) -> Proposal:
    """Generate the initial proposal against the source-backed working script."""
    return _request_proposal(
        [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=source_script)],
        request_kind="initial",
    )


def request_repair(
    *,
    source_script: str,
    working_script: str,
    artifacts: list[Artifact],
    error: RefactorError,
) -> Proposal:
    """Generate a repair batch against the current working script."""
    return _request_proposal(
        [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(
                content=repair_prompt(
                    source_script=source_script,
                    working_script=working_script,
                    artifacts=[artifact.model_dump(mode="json") for artifact in artifacts],
                    error=error.model_dump(mode="json"),
                )
            ),
        ],
        request_kind="repair",
    )
