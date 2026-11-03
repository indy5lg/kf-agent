"""Typed contracts shared by the refactoring graph nodes."""

from __future__ import annotations

from enum import StrEnum
from typing import Any, TypedDict

from pydantic import BaseModel, Field, model_validator


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


class Edit(BaseModel):
    old_text: str = Field(min_length=1)
    new_text: str
    expected_matches: int = Field(ge=1)
    purpose: str = Field(min_length=1)


class Artifact(BaseModel):
    name: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    direction: ArtifactDirection
    kind: ArtifactKind
    cli_argument: str = Field(pattern=r"^--[a-z][a-z0-9-]*$")
    original_path: str | None = None


class Proposal(BaseModel):
    edits: list[Edit]
    artifacts: list[Artifact]
    changes: list[str]

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


class RefactorState(TypedDict, total=False):
    source_script: str
    proposal: Proposal | None
    refactored_script: str | None
    diff: str | None
    artifacts: list[Artifact]
    changes: list[str]
    status: RefactorStatus
    error: RefactorError | None
