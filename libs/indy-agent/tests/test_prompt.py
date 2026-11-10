import json

from indy_agent.prompt import SYSTEM_PROMPT, repair_prompt


def test_prompt_limits_generated_python_to_edit_replacements() -> None:
    assert "all generated python must appear only in edits[].new_text" in SYSTEM_PROMPT.lower()
    assert "changes" not in SYSTEM_PROMPT


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
    assert "prior edit lists" in prompt
    assert "prior diffs" in prompt
    assert "stack traces" in prompt
    assert "Never use an empty, whitespace-only, or newline-only anchor" in prompt
    assert 'such as "\\n"' in prompt
    assert "match exactly, character for character" in prompt
    assert '"_" and "-" are different characters' in prompt
    assert "correct every reported violation" in prompt
    assert json.dumps(error, ensure_ascii=False) in prompt
