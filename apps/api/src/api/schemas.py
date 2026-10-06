import uuid
from typing import Any, Literal

from pydantic import BaseModel, EmailStr


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


class UploadRequest(BaseModel):
    project: str


class UploadResponse(BaseModel):
    upload_url: str


class StartRunRequest(BaseModel):
    project: str
    preset_prompt: Literal[tuple(PRESET_PROMPTS)]  # type: ignore[valid-type]


class RunStatusResponse(BaseModel):
    stage: str
    result: Any | None = None
    error: str | None = None
