import pytest
from pydantic import ValidationError

from indy_agent.models import AttemptKind, Artifact, DiffTraceEntry, Proposal, RefactorStatus


def test_proposal_rejects_duplicate_artifact_names() -> None:
    artifact = {"name": "dataset", "direction": "input", "kind": "dataset", "cli_argument": "--dataset-path"}
    with pytest.raises(ValidationError, match="artifact names must be unique"):
        Proposal.model_validate({"edits": [], "artifacts": [artifact, artifact]})


def test_proposal_rejects_duplicate_cli_arguments() -> None:
    first = {"name": "dataset", "direction": "input", "kind": "dataset", "cli_argument": "--path"}
    second = {"name": "model", "direction": "output", "kind": "model", "cli_argument": "--path"}
    with pytest.raises(ValidationError, match="artifact CLI arguments must be unique"):
        Proposal.model_validate({"edits": [], "artifacts": [first, second]})


def test_proposal_rejects_obsolete_changes_field() -> None:
    with pytest.raises(ValidationError, match="changes"):
        Proposal.model_validate({"edits": [], "artifacts": [], "changes": []})


def test_proposal_schema_does_not_advertise_changes() -> None:
    assert "changes" not in Proposal.model_json_schema()["properties"]


def test_proposal_schema_describes_working_script_batches() -> None:
    schema = Proposal.model_json_schema()["properties"]
    assert "working script" in schema["edits"]["description"]
    assert "complete current artifact contract" in schema["artifacts"]["description"]


def test_diff_trace_entry_accepts_a_valid_initial_attempt() -> None:
    entry = DiffTraceEntry(
        attempt_number=1,
        kind=AttemptKind.INITIAL,
        proposal=Proposal(edits=[], artifacts=[]),
        patch_diff="--- original.py\n+++ refactored.py\n",
        outcome=RefactorStatus.SUCCESS,
    )
    assert entry.attempt_number == 1
    assert entry.error is None


@pytest.mark.parametrize("field,value", [("direction", "sideways"), ("kind", "file"), ("cli_argument", "dataset-path")])
def test_artifact_rejects_invalid_contract_values(field: str, value: str) -> None:
    payload = {"name": "dataset", "direction": "input", "kind": "dataset", "cli_argument": "--dataset-path"}
    payload[field] = value
    with pytest.raises(ValidationError):
        Artifact.model_validate(payload)
