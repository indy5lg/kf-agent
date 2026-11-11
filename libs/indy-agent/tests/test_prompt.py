import json

from indy_agent.prompt import repair_prompt


def test_repair_prompt_labels_only_the_working_script_as_edit_target() -> None:
    error = {
        "stage": "validate_result",
        "message": "Generated script does not satisfy the artifact contract.",
        "details": {
            "violations": [
                {"code": "missing_cli_argument", "artifact": "dataset", "expected_cli_argument": "--dataset-path"},
                {"code": "missing_argument_destination", "artifact": "dataset", "expected_destination": "args.dataset_path"},
            ]
        },
    }
    prompt = repair_prompt(
        source_script="source = './data'",
        working_script="source = args.dataset_path",
        artifacts=[{"name": "dataset", "cli_argument": "--dataset-path"}],
        error=error,
    )
    assert "ORIGINAL SOURCE (reference only" in prompt
    assert "CURRENT WORKING SCRIPT (every edits[].old_text" in prompt
    assert "CURRENT ARTIFACT CONTRACT" in prompt
    assert "DETERMINISTIC FAILURE TO CORRECT" in prompt
    assert "source = './data'" in prompt
    assert "source = args.dataset_path" in prompt
    assert "--dataset-path" in prompt
    assert "Never use an empty, whitespace-only, or newline-only anchor" in prompt
    assert "match exactly, character for character" in prompt
    assert '"_" and "-" are different characters' in prompt
    assert "correct every reported violation" in prompt
    assert json.dumps(error, ensure_ascii=False) in prompt
