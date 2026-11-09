from indy_agent.prompt import SYSTEM_PROMPT


def test_prompt_limits_generated_python_to_edit_replacements() -> None:
    assert "all generated python must appear only in edits[].new_text" in SYSTEM_PROMPT.lower()
    assert "changes" not in SYSTEM_PROMPT
