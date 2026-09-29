import uuid
from collections.abc import Generator

from fastapi import Cookie, Depends, HTTPException
from indy_db import User, get_db_session, repository
from sqlalchemy.orm import Session as SQLAlchemySession

SESSION_COOKIE_NAME = "session_id"


def get_db() -> Generator[SQLAlchemySession, None, None]:
    yield from get_db_session()


def _unauthenticated() -> HTTPException:
    return HTTPException(status_code=401, detail="Not authenticated")


def get_current_user(
    session_id: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
    db: SQLAlchemySession = Depends(get_db),
) -> User:
    if session_id is None:
        raise _unauthenticated()
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError as exc:
        raise _unauthenticated() from exc
    session = repository.get_valid_session(db, session_uuid)
    if session is None:
        raise _unauthenticated()
    user = db.get(User, session.user_id)
    if user is None:
        raise _unauthenticated()
    return user
