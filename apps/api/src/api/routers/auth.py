import uuid

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from indy_db import User, config, repository
from indy_db.repository import EmailAlreadyRegistered
from sqlalchemy.orm import Session as SQLAlchemySession

from api.dependencies import SESSION_COOKIE_NAME, get_current_user, get_db
from api.schemas import LoginRequest, RegisterRequest, UserPublic

router = APIRouter(prefix="/auth")


def _set_session_cookie(response: Response, session_id: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_id,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=config.SESSION_TTL_SECONDS,
        path="/",
    )


@router.post("/register", response_model=UserPublic, status_code=201)
def register(body: RegisterRequest, db: SQLAlchemySession = Depends(get_db)) -> User:
    try:
        return repository.create_user(db, body.email, body.password)
    except EmailAlreadyRegistered as exc:
        raise HTTPException(status_code=409, detail="Email already registered") from exc


@router.post("/login", response_model=UserPublic)
def login(
    body: LoginRequest, response: Response, db: SQLAlchemySession = Depends(get_db)
) -> User:
    user = repository.authenticate_user(db, body.email, body.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    session = repository.create_session(db, user.id, config.SESSION_TTL_SECONDS)
    _set_session_cookie(response, str(session.id))
    return user


@router.post("/logout", status_code=204)
def logout(
    response: Response,
    session_id: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
    db: SQLAlchemySession = Depends(get_db),
) -> None:
    if session_id is not None:
        try:
            session_uuid = uuid.UUID(session_id)
        except ValueError:
            session_uuid = None
        if session_uuid is not None:
            repository.delete_session(db, session_uuid)
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")


@router.get("/me", response_model=UserPublic)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
