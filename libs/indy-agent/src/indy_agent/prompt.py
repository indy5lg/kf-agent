"""Prompts for the bounded initial and repair model calls."""

SYSTEM_PROMPT = """You modify one Python ML script only at filesystem artifact boundaries.

Find hardcoded filesystem paths used to read inputs or write outputs. Classify each as a dataset, model, metrics, or generic artifact. Return only the structured response defined by the schema; do not return Markdown or a complete rewritten script.

For every artifact, declare a unique snake_case name, input/output direction, kind, --kebab-case CLI flag, and original path when known.

If one or more artifacts are declared, the proposed edits must collectively:
1. import argparse;
2. create an ArgumentParser;
3. add one CLI argument for every declared artifact;
4. assign args = parser.parse_args();
5. replace each declared hardcoded path with its matching args.<destination> value.

Every edit must use non-empty, non-overlapping old_text copied exactly from the supplied script, its exact expected match count, replacement new_text, and a concise purpose. All generated Python must appear only in edits[].new_text. For import insertion, replace one complete import line; include its trailing newline in old_text when possible.

Preserve all unrelated behavior. Do not repair bugs, alter ML logic or hyperparameters, or add directory creation.

If no supported artifact I/O is found, return empty edits and artifacts lists."""


def repair_prompt(
    *,
    source_script: str,
    working_script: str,
    artifacts: list[dict[str, object]],
    error: dict[str, object],
) -> str:
    """Build focused repair context without stale proposal edits or trace data."""
    import json

    return f"""You are repairing a previous transformation attempt. Return only the structured Proposal response.

ORIGINAL SOURCE (reference only; never use it as an edit target):
```python
{source_script}
```

CURRENT WORKING SCRIPT (every edits[].old_text value must match this script exactly):
```python
{working_script}
```

CURRENT ARTIFACT CONTRACT (return a complete corrected list; preserve it unless a correction requires changing it):
{json.dumps(artifacts, ensure_ascii=False)}

DETERMINISTIC FAILURE TO CORRECT:
{json.dumps(error, ensure_ascii=False)}

Make only the exact edits needed to correct the reported failure while preserving valid existing behavior. Artifact contract values and generated code must match exactly, character for character; for example, "_" and "-" are different characters. For every repair edit, old_text must be a meaningful, non-whitespace code or import block copied exactly from CURRENT WORKING SCRIPT. Never use an empty, whitespace-only, or newline-only anchor such as "\\n". For an insertion, replace one complete adjacent code or import line, including its trailing newline when possible, and set expected_matches to that anchor's exact count in CURRENT WORKING SCRIPT. Do not repeat already-applied edits, return Markdown, include prior edit lists, include prior diffs, or include stack traces."""
