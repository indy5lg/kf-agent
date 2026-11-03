"""Static validation for refactored scripts; this module never executes source."""

from __future__ import annotations

import ast
from dataclasses import dataclass

from indy_agent.models import Artifact


@dataclass(frozen=True)
class SourceValidationError(Exception):
    message: str
    details: dict[str, object]
    invalid_code: bool = False


def _collect_argparse_evidence(tree: ast.AST) -> tuple[bool, set[str], set[str], bool]:
    has_import = any(
        isinstance(node, ast.Import) and any(alias.name == "argparse" for alias in node.names)
        for node in ast.walk(tree)
    )
    flags: set[str] = set()
    destinations: set[str] = set()
    parses_args = False

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "add_argument":
                for argument in node.args:
                    if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
                        if argument.value.startswith("--"):
                            flags.add(argument.value)
            if node.func.attr == "parse_args":
                parses_args = True
        if (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == "args"
        ):
            destinations.add(node.attr)
    return has_import, flags, destinations, parses_args


def validate_refactored_script(source_script: str, artifacts: list[Artifact]) -> None:
    """Raise a structured failure for invalid source or an invalid artifact contract."""
    try:
        tree = ast.parse(source_script, filename="<refactored-script>")
        compile(source_script, "<refactored-script>", "exec")
    except SyntaxError as error:
        raise SourceValidationError(
            "Generated script has invalid Python syntax.",
            {"line": error.lineno, "column": error.offset, "text": error.text},
            invalid_code=True,
        ) from error

    has_import, flags, destinations, parses_args = _collect_argparse_evidence(tree)
    if artifacts and not has_import:
        raise SourceValidationError("Generated script does not import argparse.", {})
    if artifacts and not parses_args:
        raise SourceValidationError("Generated script does not call parse_args().", {})

    for artifact in artifacts:
        destination = artifact.cli_argument.removeprefix("--").replace("-", "_")
        if artifact.cli_argument not in flags:
            raise SourceValidationError(
                "Declared artifact CLI argument is not defined by argparse.",
                {"artifact": artifact.name, "missing_cli_argument": artifact.cli_argument},
            )
        if destination not in destinations:
            raise SourceValidationError(
                "Declared artifact destination is not used through args.",
                {"artifact": artifact.name, "missing_destination": f"args.{destination}"},
            )
