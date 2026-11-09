import json
from unittest.mock import MagicMock, patch

from indy_agent.models import Artifact, ArtifactDirection, ArtifactKind, RefactorError, Proposal
from indy_agent.proposer import DEBUG_CAPTURE_DIRECTORY_ENV, DEBUG_CAPTURE_LABEL_ENV, request_proposal, request_repair


def test_request_proposal_writes_opt_in_debug_capture(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv(DEBUG_CAPTURE_DIRECTORY_ENV, str(tmp_path))
    monkeypatch.setenv(DEBUG_CAPTURE_LABEL_ENV, "pytest")
    proposal = Proposal(edits=[], artifacts=[])

    with patch("indy_agent.proposer.ChatOllama") as chat_ollama:
        model = MagicMock()
        model._chat_params.return_value = {"messages": ["exact request"]}
        model.with_structured_output.return_value.invoke.return_value = proposal
        chat_ollama.return_value = model

        assert request_proposal("print('hello')") == proposal

    captures = list(tmp_path.glob("ollama-request-*.json"))
    assert len(captures) == 1
    capture = json.loads(captures[0].read_text())
    assert capture["label"] == "pytest"
    assert capture["ollama_request"] == {"messages": ["exact request"]}
    assert capture["parsed_response"] == proposal.model_dump(mode="json")
    assert "changes" not in capture["parsed_response"]
    assert capture["request_kind"] == "initial"


def test_request_repair_uses_the_same_proposal_schema_and_marks_capture(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv(DEBUG_CAPTURE_DIRECTORY_ENV, str(tmp_path))
    proposal = Proposal(edits=[], artifacts=[])
    with patch("indy_agent.proposer.ChatOllama") as chat_ollama:
        model = MagicMock()
        model._chat_params.return_value = {"messages": ["exact request"]}
        model.with_structured_output.return_value.invoke.return_value = proposal
        chat_ollama.return_value = model

        result = request_repair(
            source_script="x = './data'",
            working_script="x = args.dataset_path",
            artifacts=[Artifact(name="dataset", direction=ArtifactDirection.INPUT, kind=ArtifactKind.DATASET, cli_argument="--dataset-path")],
            error=RefactorError(stage="validate_result", message="missing flag"),
        )

    assert result is proposal
    captures = list(tmp_path.glob("ollama-request-*.json"))
    capture = json.loads(captures[0].read_text())
    assert capture["request_kind"] == "repair"
    messages = model.with_structured_output.return_value.invoke.call_args.args[0]
    repair_context = str(messages[1].content)
    assert "x = args.dataset_path" in repair_context
    assert "prior edit lists" in repair_context
