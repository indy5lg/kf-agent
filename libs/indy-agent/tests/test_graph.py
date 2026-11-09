import pytest
from langchain_core.exceptions import OutputParserException

from indy_agent.graph import graph
from indy_agent.models import AttemptKind, Proposal, RefactorStatus


SOURCE = "import torch\nroot = './data'\nexport_path = './model.pth'\n"


def proposal(*, include_flags: bool = True, artifact_name: str = "dataset") -> Proposal:
    parser = "parser.add_argument('--dataset-path')\nparser.add_argument('--model-path')\n" if include_flags else ""
    return Proposal.model_validate(
        {
            "edits": [
                {
                    "old_text": "import torch\n",
                    "new_text": f"import argparse\nimport torch\nparser = argparse.ArgumentParser()\n{parser}args = parser.parse_args()\n",
                    "expected_matches": 1,
                    "purpose": "add CLI",
                },
                {"old_text": "'./data'", "new_text": "args.dataset_path", "expected_matches": 1, "purpose": "input"},
                {"old_text": "'./model.pth'", "new_text": "args.model_path", "expected_matches": 1, "purpose": "output"},
            ],
            "artifacts": [
                {"name": artifact_name, "direction": "input", "kind": "dataset", "cli_argument": "--dataset-path"},
                {"name": "model", "direction": "output", "kind": "model", "cli_argument": "--model-path"},
            ],
        }
    )


def repair_parser_proposal() -> Proposal:
    return Proposal.model_validate(
        {
            "edits": [
                {
                    "old_text": "args = parser.parse_args()\n",
                    "new_text": "parser.add_argument('--dataset-path')\nparser.add_argument('--model-path')\nargs = parser.parse_args()\n",
                    "expected_matches": 1,
                    "purpose": "add missing flags",
                }
            ],
            "artifacts": [
                {"name": "dataset", "direction": "input", "kind": "dataset", "cli_argument": "--dataset-path"},
                {"name": "model", "direction": "output", "kind": "model", "cli_argument": "--model-path"},
            ],
        }
    )


def test_graph_success_initializes_working_script_and_trace(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("indy_agent.graph.request_proposal", lambda _: proposal())
    result = graph.invoke({"source_script": SOURCE})
    assert result["status"] == RefactorStatus.SUCCESS
    assert "args.dataset_path" in result["working_script"]
    assert "refactored_script" not in result
    assert result["attempt_count"] == 1
    assert len(result["diff_trace"]) == 1
    assert result["diff_trace"][0].kind == AttemptKind.INITIAL
    assert result["diff_trace"][0].outcome == RefactorStatus.SUCCESS
    assert result["diff_trace"][0].patch_diff
    assert result["diff"]


def test_graph_short_circuits_when_no_artifacts(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("indy_agent.graph.request_proposal", lambda _: Proposal(edits=[], artifacts=[]))
    result = graph.invoke({"source_script": SOURCE})
    assert result["status"] == RefactorStatus.NO_ARTIFACTS_FOUND
    assert result["working_script"] == SOURCE
    assert len(result["diff_trace"]) == 1


def test_graph_repairs_missing_argparse_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr("indy_agent.graph.request_proposal", lambda _: calls.append("initial") or proposal(include_flags=False))
    monkeypatch.setattr("indy_agent.graph.request_repair", lambda **_: calls.append("repair") or repair_parser_proposal())
    result = graph.invoke({"source_script": SOURCE})
    assert result["status"] == RefactorStatus.SUCCESS
    assert calls == ["initial", "repair"]
    assert result["attempt_count"] == 2
    assert [entry.kind for entry in result["diff_trace"]] == [AttemptKind.INITIAL, AttemptKind.REPAIR]
    assert [entry.outcome for entry in result["diff_trace"]] == [RefactorStatus.INVALID_CONTRACT, RefactorStatus.SUCCESS]
    assert "parser.add_argument('--dataset-path')" in result["working_script"]
    assert "-root = './data'" in result["diff"]


def test_graph_preserves_invalid_candidate_when_repair_budget_is_exhausted(monkeypatch: pytest.MonkeyPatch) -> None:
    initial = proposal(include_flags=False)
    bad_repair = Proposal.model_validate(
        {"edits": [{"old_text": "args = parser.parse_args()\n", "new_text": "args = parser.parse_args()\n", "expected_matches": 1, "purpose": "no-op"}], "artifacts": initial.model_dump(mode="json")["artifacts"]}
    )
    calls: list[str] = []
    monkeypatch.setattr("indy_agent.graph.request_proposal", lambda _: calls.append("initial") or initial)
    monkeypatch.setattr("indy_agent.graph.request_repair", lambda **_: calls.append("repair") or bad_repair)
    result = graph.invoke({"source_script": SOURCE})
    assert result["status"] == RefactorStatus.INVALID_CONTRACT
    assert result["attempt_count"] == 2
    assert "args.dataset_path" in result["working_script"]
    assert len(result["diff_trace"]) == 2
    assert result["diff_trace"][-1].outcome == RefactorStatus.INVALID_CONTRACT
    assert calls == ["initial", "repair"]


def test_invalid_python_candidate_is_repaired(monkeypatch: pytest.MonkeyPatch) -> None:
    invalid = Proposal.model_validate(
        {
            "edits": [{"old_text": "import torch\n", "new_text": "if True print('bad')\n", "expected_matches": 1, "purpose": "invalid source"}],
            "artifacts": [{"name": "dataset", "direction": "input", "kind": "dataset", "cli_argument": "--dataset-path"}],
        }
    )
    repaired = Proposal.model_validate(
        {
            "edits": [
                {"old_text": "if True print('bad')\n", "new_text": "import argparse\nimport torch\nparser = argparse.ArgumentParser()\nparser.add_argument('--dataset-path')\nargs = parser.parse_args()\n", "expected_matches": 1, "purpose": "restore valid parser"},
                {"old_text": "'./data'", "new_text": "args.dataset_path", "expected_matches": 1, "purpose": "input"},
            ],
            "artifacts": [{"name": "dataset", "direction": "input", "kind": "dataset", "cli_argument": "--dataset-path"}],
        }
    )
    monkeypatch.setattr("indy_agent.graph.request_proposal", lambda _: invalid)
    monkeypatch.setattr("indy_agent.graph.request_repair", lambda **_: repaired)
    result = graph.invoke({"source_script": SOURCE})
    assert result["status"] == RefactorStatus.SUCCESS
    assert result["diff_trace"][0].outcome == RefactorStatus.INVALID_CODE
    assert result["diff_trace"][1].outcome == RefactorStatus.SUCCESS


def test_repair_replaces_artifact_contract_and_patches_candidate(monkeypatch: pytest.MonkeyPatch) -> None:
    initial = Proposal.model_validate(
        {
            "edits": [
                {"old_text": "import torch\n", "new_text": "import argparse\nimport torch\nparser = argparse.ArgumentParser()\nparser.add_argument('--dataset-path')\nargs = parser.parse_args()\n", "expected_matches": 1, "purpose": "add partial CLI"},
                {"old_text": "'./data'", "new_text": "args.dataset_path", "expected_matches": 1, "purpose": "input"},
                {"old_text": "'./model.pth'", "new_text": "args.model_path", "expected_matches": 1, "purpose": "output"},
            ],
            "artifacts": [
                {"name": "dataset", "direction": "input", "kind": "dataset", "cli_argument": "--dataset-path"},
                {"name": "wrong_model", "direction": "output", "kind": "model", "cli_argument": "--wrong-model-path"},
            ],
        }
    )
    repaired = Proposal.model_validate(
        {
            "edits": [{"old_text": "args = parser.parse_args()\n", "new_text": "parser.add_argument('--model-path')\nargs = parser.parse_args()\n", "expected_matches": 1, "purpose": "add correct model flag"}],
            "artifacts": [
                {"name": "dataset", "direction": "input", "kind": "dataset", "cli_argument": "--dataset-path"},
                {"name": "model", "direction": "output", "kind": "model", "cli_argument": "--model-path"},
            ],
        }
    )
    monkeypatch.setattr("indy_agent.graph.request_proposal", lambda _: initial)
    monkeypatch.setattr("indy_agent.graph.request_repair", lambda **_: repaired)
    result = graph.invoke({"source_script": SOURCE})
    assert result["status"] == RefactorStatus.SUCCESS
    assert {artifact.name for artifact in result["proposal"].artifacts} == {"dataset", "model"}
    assert "parser.add_argument('--model-path')" in result["working_script"]
    assert result["diff_trace"][1].feedback is not None


def test_edit_failure_keeps_prior_working_script_and_repairs(monkeypatch: pytest.MonkeyPatch) -> None:
    invalid = Proposal.model_validate(
        {"edits": [{"old_text": "missing", "new_text": "x", "expected_matches": 1, "purpose": "bad"}], "artifacts": proposal().artifacts}
    )
    monkeypatch.setattr("indy_agent.graph.request_proposal", lambda _: invalid)
    monkeypatch.setattr("indy_agent.graph.request_repair", lambda **_: proposal())
    result = graph.invoke({"source_script": SOURCE})
    assert result["status"] == RefactorStatus.SUCCESS
    assert result["diff_trace"][0].outcome == RefactorStatus.EDIT_FAILURE
    assert result["diff_trace"][0].patch_diff is None
    assert result["working_script"] != SOURCE


def test_agent_failure_does_not_invoke_repair(monkeypatch: pytest.MonkeyPatch) -> None:
    repair_called = False
    monkeypatch.setattr("indy_agent.graph.request_proposal", lambda _: (_ for _ in ()).throw(RuntimeError("offline")))

    def repair(**_):
        nonlocal repair_called
        repair_called = True
        return proposal()

    monkeypatch.setattr("indy_agent.graph.request_repair", repair)
    result = graph.invoke({"source_script": SOURCE})
    assert result["status"] == RefactorStatus.AGENT_FAILURE
    assert not repair_called


def test_invalid_agent_response_can_use_single_repair(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("indy_agent.graph.request_proposal", lambda _: (_ for _ in ()).throw(ValueError("bad JSON")))
    monkeypatch.setattr("indy_agent.graph.request_repair", lambda **_: proposal())
    result = graph.invoke({"source_script": SOURCE})
    assert result["status"] == RefactorStatus.SUCCESS
    assert result["attempt_count"] == 2


def test_output_parser_failure_is_retryable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("indy_agent.graph.request_proposal", lambda _: (_ for _ in ()).throw(OutputParserException("invalid JSON")))
    monkeypatch.setattr("indy_agent.graph.request_repair", lambda **_: proposal())
    assert graph.invoke({"source_script": SOURCE})["status"] == RefactorStatus.SUCCESS
