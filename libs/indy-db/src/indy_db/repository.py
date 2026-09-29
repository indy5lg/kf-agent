import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as SQLAlchemySession

from indy_db.models import Session, User


class EmailAlreadyRegistered(Exception):
    pass


def create_user(db: SQLAlchemySession, email: str, password: str) -> User:
    user = User(email=email, password=password)
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise EmailAlreadyRegistered(email) from exc
    db.refresh(user)
    return user


def authenticate_user(db: SQLAlchemySession, email: str, password: str) -> User | None:
    user = db.scalar(select(User).where(User.email == email))
    if user is None or user.password != password:
        return None
    return user


def create_session(db: SQLAlchemySession, user_id: uuid.UUID, ttl_seconds: int) -> Session:
    session = Session(
        user_id=user_id,
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_valid_session(db: SQLAlchemySession, session_id: uuid.UUID) -> Session | None:
    session = db.get(Session, session_id)
    if session is None:
        return None
    if session.expires_at < datetime.now(timezone.utc):
        return None
    return session


def delete_session(db: SQLAlchemySession, session_id: uuid.UUID) -> None:
    session = db.get(Session, session_id)
    if session is not None:
        db.delete(session)
        db.commit()
