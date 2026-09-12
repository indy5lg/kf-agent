import uuid

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
