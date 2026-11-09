import json
from unittest.mock import MagicMock, patch

from indy_agent.models import Proposal
from indy_agent.proposer import DEBUG_CAPTURE_DIRECTORY_ENV, DEBUG_CAPTURE_LABEL_ENV, request_proposal


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
