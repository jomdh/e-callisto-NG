# SPDX-License-Identifier: AGPL-3.0-or-later
"""User management + audit log (admin only, DESIGN 8.4 / ADR-0006)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session as DbSession
from sqlmodel import col, select

from ecallisto_ng.api import auth
from ecallisto_ng.api.db import get_session
from ecallisto_ng.api.models import AuditEvent, Role, User
from ecallisto_ng.services import audit

router = APIRouter(prefix="/api/v1", tags=["users"])

_admin = auth.require_role(Role.ADMIN)


class UserIn(BaseModel):
    username: str
    password: str
    role: str = "viewer"


class UserPatch(BaseModel):
    role: str | None = None
    active: bool | None = None


class UserOut(BaseModel):
    id: int
    username: str
    role: str
    active: bool


def _out(u: User) -> UserOut:
    return UserOut(
        id=u.id or 0, username=u.username, role=u.role, active=u.active
    )


@router.get("/users", dependencies=[Depends(_admin)])
def list_users(db: DbSession = Depends(get_session)) -> list[UserOut]:
    return [_out(u) for u in db.exec(select(User)).all()]


@router.post("/users", status_code=201, dependencies=[Depends(_admin)])
def create_user(
    body: UserIn,
    db: DbSession = Depends(get_session),
    actor: User = Depends(_admin),
) -> UserOut:
    if db.exec(select(User).where(User.username == body.username)).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "username taken")
    user = auth.create_user(db, body.username, body.password, Role(body.role))
    audit.record(db, actor.username, "user.create", target=body.username)
    return _out(user)


@router.patch("/users/{user_id}", dependencies=[Depends(_admin)])
def update_user(
    user_id: int,
    body: UserPatch,
    db: DbSession = Depends(get_session),
    actor: User = Depends(_admin),
) -> UserOut:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no such user")
    if body.role is not None:
        user.role = Role(body.role)
        audit.record(
            db,
            actor.username,
            "user.role",
            target=user.username,
            detail=body.role,
        )
    if body.active is not None:
        user.active = body.active
        action = "user.enable" if body.active else "user.disable"
        audit.record(db, actor.username, action, target=user.username)
    db.add(user)
    db.commit()
    db.refresh(user)
    return _out(user)


@router.delete(
    "/users/{user_id}", status_code=204, dependencies=[Depends(_admin)]
)
def delete_user(
    user_id: int,
    db: DbSession = Depends(get_session),
    actor: User = Depends(_admin),
) -> None:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no such user")
    if user.id == actor.id:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "cannot delete yourself"
        )
    name = user.username
    db.delete(user)
    db.commit()
    audit.record(db, actor.username, "user.delete", target=name)


@router.get("/audit", dependencies=[Depends(_admin)])
def list_audit(
    limit: int = 200, db: DbSession = Depends(get_session)
) -> list[AuditEvent]:
    rows = db.exec(
        select(AuditEvent).order_by(col(AuditEvent.id).desc()).limit(limit)
    ).all()
    return list(rows)
