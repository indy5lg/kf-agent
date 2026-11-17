import uuid
from typing import Any, Literal

from pydantic import BaseModel, EmailStr, Field


class Credentials(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(Credentials):
    pass


class LoginRequest(Credentials):
    pass


class UserPublic(BaseModel):
    id: uuid.UUID
    email: str


PRESET_PROMPTS = [
    "Explain this pipeline",
    "Suggest hyperparameter changes",
    "Convert to a Kubeflow pipeline",
]


# Project names become part of the SeaweedFS object key, so keep them to a
# safe character set (no slashes, no "..").
PROJECT_NAME_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$"


def storage_username(user) -> str:
    return user.email.split("@")[0]


class UploadRequest(BaseModel):
    project: str = Field(pattern=PROJECT_NAME_PATTERN)


class UploadResponse(BaseModel):
    upload_url: str


class StartRunRequest(BaseModel):
    project: str = Field(pattern=PROJECT_NAME_PATTERN)
    preset_prompt: Literal[tuple(PRESET_PROMPTS)]  # type: ignore[valid-type]


class RunStatusResponse(BaseModel):
    stage: str
    result: Any | None = None
    error: str | None = None
