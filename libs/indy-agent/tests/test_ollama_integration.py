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


SAMPLE_DIRECTORY = Path(__file__).resolve().parents[3] / "sample"
BASELINE_FIXTURE = "sample_script.py"
SPACING_VARIANT_FIXTURES = (
    "sample_script_compact_spacing.py",
    "sample_script_irregular_spacing.py",
)
ALL_SAMPLE_FIXTURES = (BASELINE_FIXTURE, *SPACING_VARIANT_FIXTURES)


def _read_sample_fixture(name: str) -> str:
    return (SAMPLE_DIRECTORY / name).read_text()


def _nonblank_lines(source: str) -> list[str]:
    return [line for line in source.splitlines() if line.strip()]


@pytest.mark.parametrize("fixture_name", SPACING_VARIANT_FIXTURES)
def test_spacing_variants_preserve_all_nonblank_source_lines(fixture_name: str) -> None:
    assert _nonblank_lines(_read_sample_fixture(fixture_name)) == _nonblank_lines(
        _read_sample_fixture(BASELINE_FIXTURE)
    )


def _configured_ollama() -> tuple[str, str]:
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
    return base_url, model


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
            "  working_script:\n" + repr(result.get("working_script")),
            "  diff:\n" + repr(result.get("diff")),
            "  diff_trace:\n" + repr([entry.model_dump(mode="json") for entry in result.get("diff_trace", [])]),
        )
    )


def _refactor_failure(
    *,
    base_url: str,
    model: str,
    source: str,
    result: dict,
) -> str | None:
    diagnostic = _diagnostic_report(
        base_url=base_url,
        model=model,
        source=source,
        result=result,
    )
    if result["status"] != RefactorStatus.SUCCESS:
        return diagnostic

    proposal = result["proposal"]
    if proposal is None:
        return diagnostic
    if not any(
        artifact.direction == ArtifactDirection.INPUT and artifact.kind == ArtifactKind.DATASET
        for artifact in proposal.artifacts
    ):
        return diagnostic
    if not any(
        artifact.direction == ArtifactDirection.OUTPUT and artifact.kind == ArtifactKind.MODEL
        for artifact in proposal.artifacts
    ):
        return diagnostic
    if any(
        f"args.{artifact.cli_argument.removeprefix('--').replace('-', '_')}"
        not in result["working_script"]
        for artifact in proposal.artifacts
    ):
        return diagnostic
    if "artifacts" in result or "changes" in result or "refactored_script" in result:
        return diagnostic
    if not result["diff"] or not result["diff_trace"]:
        return diagnostic
    analysis = result.get("dependency_analysis")
    if analysis is None:
        return diagnostic
    if analysis.requirements != ["torch", "torchvision"]:
        return diagnostic
    if analysis.unresolved_modules:
        return diagnostic
    return None


@pytest.mark.integration
def test_sample_script_refactors_with_configured_ollama() -> None:
    base_url, model = _configured_ollama()
    source = _read_sample_fixture(BASELINE_FIXTURE)
    result = graph.invoke({"source_script": source})
    failure = _refactor_failure(
        base_url=base_url,
        model=model,
        source=source,
        result=result,
    )
    assert failure is None, failure


@pytest.mark.comprehensive_integration
def test_spacing_variants_refactor_with_configured_ollama() -> None:
    base_url, model = _configured_ollama()
    failures: list[str] = []

    for fixture_name in ALL_SAMPLE_FIXTURES:
        source = _read_sample_fixture(fixture_name)
        try:
            result = graph.invoke({"source_script": source})
        except Exception as error:
            failures.append(f"{fixture_name}: graph invocation raised {error!r}")
            continue
        failure = _refactor_failure(
            base_url=base_url,
            model=model,
            source=source,
            result=result,
        )
        if failure is not None:
            failures.append(f"{fixture_name}:\n{failure}")

    assert not failures, "\n\n".join(failures)
