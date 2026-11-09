import hashlib
import json
import os
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import pytest

from indy_agent.graph import graph
from indy_agent.models import ArtifactDirection, ArtifactKind, RefactorStatus
from indy_agent.proposer import DEFAULT_OLLAMA_BASE_URL, DEFAULT_OLLAMA_MODEL


def _diagnostic_report(
    *,
    base_url: str,
    model: str,
    source: str,
    result: dict,
) -> str:
    """Make a failed live-model run inspectable from pytest's assertion output."""
    proposal = result.get("proposal")
    error = result.get("error")
    proposal_data = proposal.model_dump(mode="json") if proposal is not None else None
    error_data = error.model_dump(mode="json") if error is not None else None

    return "\n".join(
        (
            "Ollama integration diagnostic:",
            f"  endpoint: {base_url}",
            f"  model: {model}",
            f"  source_sha256: {hashlib.sha256(source.encode('utf-8')).hexdigest()}",
            f"  source_characters: {len(source)}",
            f"  terminal_status: {result.get('status')}",
            "  error:\n" + json.dumps(error_data, indent=2, sort_keys=True),
            "  proposal:\n" + json.dumps(proposal_data, indent=2, sort_keys=True),
            "  refactored_script:\n" + repr(result.get("refactored_script")),
            "  diff:\n" + repr(result.get("diff")),
        )
    )


@pytest.mark.integration
def test_sample_script_refactors_with_configured_ollama() -> None:
    if os.getenv("RUN_OLLAMA_INTEGRATION") != "1":
        pytest.skip("set RUN_OLLAMA_INTEGRATION=1 to run against Ollama")

    base_url = os.getenv("OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE_URL)
    model = os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)
    try:
        with urlopen(f"{base_url}/api/tags", timeout=2) as response:
            available_models = response.read().decode()
    except (OSError, URLError):
        pytest.skip("configured Ollama endpoint is unavailable")
    if model not in available_models:
        pytest.skip(f"configured model {model!r} is unavailable")

    source = (Path(__file__).resolve().parents[3] / "sample" / "sample_script.py").read_text()
    result = graph.invoke({"source_script": source})
    diagnostic = _diagnostic_report(
        base_url=base_url,
        model=model,
        source=source,
        result=result,
    )

    assert result["status"] == RefactorStatus.SUCCESS, diagnostic
    proposal = result["proposal"]
    assert proposal is not None, diagnostic
    assert any(
        artifact.direction == ArtifactDirection.INPUT and artifact.kind == ArtifactKind.DATASET
        for artifact in proposal.artifacts
    ), diagnostic
    assert any(
        artifact.direction == ArtifactDirection.OUTPUT and artifact.kind == ArtifactKind.MODEL
        for artifact in proposal.artifacts
    ), diagnostic
    for artifact in proposal.artifacts:
        destination = artifact.cli_argument.removeprefix("--").replace("-", "_")
        assert f"args.{destination}" in result["refactored_script"], diagnostic
    assert "artifacts" not in result, diagnostic
    assert "changes" not in result, diagnostic
    assert result["diff"], diagnostic
