import pytest

from indy_agent.graph import graph
from indy_agent.models import Proposal, RefactorStatus


SOURCE = "import torch\nroot = './data'\nexport_path = './model.pth'\n"


def successful_proposal() -> Proposal:
    return Proposal.model_validate(
        {
            "edits": [
                {
                    "old_text": "import torch\n",
                    "new_text": "import argparse\nimport torch\nparser = argparse.ArgumentParser()\nparser.add_argument('--dataset-path')\nparser.add_argument('--model-path')\nargs = parser.parse_args()\n",
                    "expected_matches": 1,
                    "purpose": "add CLI",
                },
                {"old_text": "'./data'", "new_text": "args.dataset_path", "expected_matches": 1, "purpose": "input"},
                {"old_text": "'./model.pth'", "new_text": "args.model_path", "expected_matches": 1, "purpose": "output"},
            ],
            "artifacts": [
                {"name": "dataset", "direction": "input", "kind": "dataset", "cli_argument": "--dataset-path"},
                {"name": "model", "direction": "output", "kind": "model", "cli_argument": "--model-path"},
            ],
            "changes": ["parameterized paths"],
        }
    )


def test_graph_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("indy_agent.graph.request_proposal", lambda _: successful_proposal())
    result = graph.invoke({"source_script": SOURCE})
    assert result["status"] == RefactorStatus.SUCCESS
    assert "args.dataset_path" in result["refactored_script"]


def test_graph_short_circuits_when_no_artifacts(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("indy_agent.graph.request_proposal", lambda _: Proposal(edits=[], artifacts=[], changes=[]))
    result = graph.invoke({"source_script": SOURCE})
    assert result["status"] == RefactorStatus.NO_ARTIFACTS_FOUND
    assert "refactored_script" not in result


@pytest.mark.parametrize(
    "proposal,status",
    [
        (Proposal.model_validate({"edits": [{"old_text": "missing", "new_text": "x", "expected_matches": 1, "purpose": "bad"}], "artifacts": [{"name": "dataset", "direction": "input", "kind": "dataset", "cli_argument": "--dataset-path"}], "changes": ["bad"]}), RefactorStatus.EDIT_FAILURE),
        (Proposal.model_validate({"edits": [{"old_text": "import torch\n", "new_text": "if True print('bad')\n", "expected_matches": 1, "purpose": "bad"}], "artifacts": [{"name": "dataset", "direction": "input", "kind": "dataset", "cli_argument": "--dataset-path"}], "changes": ["bad"]}), RefactorStatus.INVALID_CODE),
    ],
)
def test_graph_short_circuits_after_failure(monkeypatch: pytest.MonkeyPatch, proposal: Proposal, status: RefactorStatus) -> None:
    monkeypatch.setattr("indy_agent.graph.request_proposal", lambda _: proposal)
    assert graph.invoke({"source_script": SOURCE})["status"] == status


def test_graph_maps_agent_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("indy_agent.graph.request_proposal", lambda _: (_ for _ in ()).throw(RuntimeError("offline")))
    assert graph.invoke({"source_script": SOURCE})["status"] == RefactorStatus.AGENT_FAILURE


def test_graph_maps_malformed_agent_response(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("indy_agent.graph.request_proposal", lambda _: (_ for _ in ()).throw(ValueError("bad JSON")))
    assert graph.invoke({"source_script": SOURCE})["status"] == RefactorStatus.INVALID_AGENT_RESPONSE


def test_graph_reports_invalid_contract_after_successful_edit(monkeypatch: pytest.MonkeyPatch) -> None:
    proposal = Proposal.model_validate(
        {
            "edits": [
                {"old_text": "import torch\n", "new_text": "import argparse\nimport torch\nparser = argparse.ArgumentParser()\nargs = parser.parse_args()\n", "expected_matches": 1, "purpose": "add parser"},
                {"old_text": "'./data'", "new_text": "args.dataset_path", "expected_matches": 1, "purpose": "input"},
            ],
            "artifacts": [{"name": "dataset", "direction": "input", "kind": "dataset", "cli_argument": "--dataset-path"}],
            "changes": ["bad contract"],
        }
    )
    monkeypatch.setattr("indy_agent.graph.request_proposal", lambda _: proposal)
    result = graph.invoke({"source_script": SOURCE})
    assert result["status"] == RefactorStatus.INVALID_CONTRACT
    assert result["refactored_script"] is None
