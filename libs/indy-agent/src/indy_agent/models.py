"""Typed contracts shared by the refactoring graph nodes."""

from __future__ import annotations

from enum import StrEnum
from typing import Any, TypedDict

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ArtifactDirection(StrEnum):
    INPUT = "input"
    OUTPUT = "output"


class ArtifactKind(StrEnum):
    DATASET = "dataset"
    MODEL = "model"
    METRICS = "metrics"
    ARTIFACT = "artifact"


class RefactorStatus(StrEnum):
    PENDING = "pending"
    SUCCESS = "success"
    NO_ARTIFACTS_FOUND = "no_artifacts_found"
    AGENT_FAILURE = "agent_failure"
    INVALID_AGENT_RESPONSE = "invalid_agent_response"
    EDIT_FAILURE = "edit_failure"
    INVALID_CODE = "invalid_code"
    INVALID_CONTRACT = "invalid_contract"


class AttemptKind(StrEnum):
    INITIAL = "initial"
    REPAIR = "repair"


class ValidationViolationCode(StrEnum):
    MISSING_ARGPARSE_IMPORT = "missing_argparse_import"
    MISSING_PARSE_ARGS = "missing_parse_args"
    MISSING_CLI_ARGUMENT = "missing_cli_argument"
    MISSING_ARGUMENT_DESTINATION = "missing_argument_destination"


class ValidationViolation(BaseModel):
    """One independently detectable mismatch in the generated argparse contract."""

    model_config = ConfigDict(extra="forbid")

    code: ValidationViolationCode
    artifact: str | None = None
    expected_cli_argument: str | None = None
    expected_destination: str | None = None


class Edit(BaseModel):
    old_text: str = Field(min_length=1, description="Exact non-empty text from the current working script to replace.")
    new_text: str = Field(description="Replacement source text; all generated Python belongs here.")
    expected_matches: int = Field(ge=1, description="Required count of exact matches in the current working script.")
    purpose: str = Field(min_length=1, description="Concise explanation of this concrete edit.")


class Artifact(BaseModel):
    name: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    direction: ArtifactDirection
    kind: ArtifactKind
    cli_argument: str = Field(pattern=r"^--[a-z][a-z0-9-]*$")
    original_path: str | None = None


class Proposal(BaseModel):
    """The next model-authored edit batch and complete artifact contract."""

    model_config = ConfigDict(extra="forbid")

    edits: list[Edit] = Field(description="Exact replacements targeting the current working script.")
    artifacts: list[Artifact] = Field(description="The complete current artifact contract for this edit batch.")

    @model_validator(mode="after")
    def validate_artifacts(self) -> Proposal:
        names = [artifact.name for artifact in self.artifacts]
        flags = [artifact.cli_argument for artifact in self.artifacts]
        if len(names) != len(set(names)):
            raise ValueError("artifact names must be unique")
        if len(flags) != len(set(flags)):
            raise ValueError("artifact CLI arguments must be unique")
        return self


class RefactorError(BaseModel):
    stage: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class DependencyAnalysis(BaseModel):
    """Deterministic requirements information derived from a working script."""

    model_config = ConfigDict(extra="forbid")

    imported_modules: list[str]
    standard_library_modules: list[str]
    requirements: list[str]
    requirements_text: str
    unresolved_modules: list[str]


class DiffTraceEntry(BaseModel):
    """One bounded proposal attempt and its deterministic outcome."""

    attempt_number: int = Field(ge=1)
    kind: AttemptKind
    proposal: Proposal | None = None
    feedback: RefactorError | None = None
    patch_diff: str | None = None
    outcome: RefactorStatus
    error: RefactorError | None = None


class RefactorState(TypedDict, total=False):
    source_script: str
    working_script: str
    proposal: Proposal | None
    diff: str | None
    diff_trace: list[DiffTraceEntry]
    attempt_count: int
    attempt_kind: AttemptKind
    repair_feedback: RefactorError | None
    dependency_analysis: DependencyAnalysis | None
    status: RefactorStatus
    error: RefactorError | None
