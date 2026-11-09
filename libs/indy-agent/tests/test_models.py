import pytest
from pydantic import ValidationError

from indy_agent.models import Artifact, Proposal


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


@pytest.mark.parametrize("field,value", [("direction", "sideways"), ("kind", "file"), ("cli_argument", "dataset-path")])
def test_artifact_rejects_invalid_contract_values(field: str, value: str) -> None:
    payload = {"name": "dataset", "direction": "input", "kind": "dataset", "cli_argument": "--dataset-path"}
    payload[field] = value
    with pytest.raises(ValidationError):
        Artifact.model_validate(payload)
