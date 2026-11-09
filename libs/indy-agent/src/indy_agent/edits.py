"""Deterministic, in-memory application of model-proposed exact edits."""

from __future__ import annotations

from dataclasses import dataclass
from difflib import unified_diff
import re

from indy_agent.models import Edit


@dataclass(frozen=True)
class EditApplicationError(Exception):
    message: str
    details: dict[str, object]


def _find_conflict(edits: list[Edit]) -> tuple[int, int] | None:
    for index, edit in enumerate(edits):
        for other_index, other in enumerate(edits[index + 1 :], start=index + 1):
            if edit.old_text in other.old_text or other.old_text in edit.old_text:
                return index, other_index
    return None


def _match_spans(source_script: str, old_text: str) -> list[tuple[int, int]]:
    """Return the exact regions an edit anchor is allowed to replace.

    Most anchors deliberately use normal literal-string matching: replacing a
    quoted path inside a larger expression is a valid edit.  Import anchors
    are different.  A proposal such as ``import torch`` is an instruction to
    edit that *entire import line*, not every longer import whose prefix happens
    to be ``import torch`` (for example ``import torch.nn as nn``).
    """
    if "\n" not in old_text and old_text.lstrip().startswith(("import ", "from ")):
        pattern = re.compile(rf"^{re.escape(old_text)}(?=\r?$)", re.MULTILINE)
        return [match.span() for match in pattern.finditer(source_script)]

    start = 0
    spans: list[tuple[int, int]] = []
    while True:
        index = source_script.find(old_text, start)
        if index == -1:
            return spans
        spans.append((index, index + len(old_text)))
        start = index + len(old_text)


def _replace_spans(
    source_script: str, replacements: list[tuple[int, int, str]]
) -> str:
    """Replace known regions right-to-left so earlier positions stay valid."""
    transformed = source_script
    for start, end, new_text in sorted(replacements, reverse=True):
        transformed = transformed[:start] + new_text + transformed[end:]
    return transformed


def create_diff(before_script: str, after_script: str) -> str:
    """Return a readable unified diff between two in-memory script versions."""
    return "".join(
        unified_diff(
            before_script.splitlines(keepends=True),
            after_script.splitlines(keepends=True),
            fromfile="original.py",
            tofile="refactored.py",
        )
    )


def apply_edits(working_script: str, edits: list[Edit]) -> tuple[str, str]:
    """Apply a batch to the current working script or raise without mutation."""
    conflict = _find_conflict(edits)
    if conflict is not None:
        raise EditApplicationError(
            "Proposed edits have overlapping anchors.",
            {"first_edit_index": conflict[0], "second_edit_index": conflict[1]},
        )

    edit_spans: list[list[tuple[int, int]]] = []
    for index, edit in enumerate(edits):
        spans = _match_spans(working_script, edit.old_text)
        actual_matches = len(spans)
        if actual_matches != edit.expected_matches:
            raise EditApplicationError(
                f"Edit {index} expected {edit.expected_matches} matches but found {actual_matches}.",
                {
                    "edit_index": index,
                    "expected_matches": edit.expected_matches,
                    "actual_matches": actual_matches,
                },
            )
        edit_spans.append(spans)

    replacements = [
        (start, end, edit.new_text)
        for edit, spans in zip(edits, edit_spans, strict=True)
        for start, end in spans
    ]
    transformed = _replace_spans(working_script, replacements)
    return transformed, create_diff(working_script, transformed)
