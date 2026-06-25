# SPDX-License-Identifier: AGPL-3.0-or-later
"""Authentication: login/logout, current-user and role dependencies."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from fastapi import Depends, HTTPException, Request, Response, status
from sqlmodel import Session as DbSession
from sqlmodel import select

from ecallisto_ng.api.db import get_session
from ecallisto_ng.api.models import Role, Session, User, role_satisfies
from ecallisto_ng.api.security import (
    SESSION_COOKIE,
    SESSION_TTL_SECONDS,
    hash_password,
    new_session_token,
    verify_password,
)


def create_user(
    db: DbSession, username: str, password: str, role: Role
) -> User:
    """Create and persist a user (used by the wizard/CLI)."""
    user = User(
        username=username,
        password_hash=hash_password(password),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login(
    db: DbSession, response: Response, username: str, password: str
) -> User:
    from ecallisto_ng.services import audit

    user = db.exec(select(User).where(User.username == username)).first()
    if user is None or not user.active:
        audit.record(db, username, "login.fail", detail="unknown/inactive")
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "invalid credentials"
        )
    if not verify_password(password, user.password_hash):
        audit.record(db, username, "login.fail", detail="bad password")
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "invalid credentials"
        )

    token = new_session_token()
    expires = datetime.now(UTC) + timedelta(seconds=SESSION_TTL_SECONDS)
    assert user.id is not None
    db.add(Session(token=token, user_id=user.id, expires_at=expires))
    db.commit()
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        samesite="lax",
    )
    audit.record(db, username, "login.ok")
    return user


def logout(db: DbSession, request: Request, response: Response) -> None:
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        row = db.get(Session, token)
        if row is not None:
            db.delete(row)
            db.commit()
    response.delete_cookie(SESSION_COOKIE)


def get_current_user(
    request: Request, db: DbSession = Depends(get_session)
) -> User:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "not authenticated")
    session = db.get(Session, token)
    if session is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid session")
    if _expired(session.expires_at):
        db.delete(session)
        db.commit()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "session expired")
    user = db.get(User, session.user_id)
    if user is None or not user.active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "no such user")
    return user


def optional_user(
    request: Request, db: DbSession = Depends(get_session)
) -> User | None:
    """Return the logged-in user or ``None`` -- for server-rendered pages."""
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    session = db.get(Session, token)
    if session is None or _expired(session.expires_at):
        return None
    user = db.get(User, session.user_id)
    return user if user and user.active else None


def require_role(minimum: Role) -> Callable[[User], User]:
    """Dependency factory: require at least ``minimum`` role."""

    def _dep(user: User = Depends(get_current_user)) -> User:
        if not role_satisfies(user.role, minimum):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "insufficient role")
        return user

    return _dep


def _expired(when: datetime) -> bool:
    if when.tzinfo is None:
        when = when.replace(tzinfo=UTC)
    return when < datetime.now(UTC)
