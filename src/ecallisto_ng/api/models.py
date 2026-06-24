"""Persistent models (SQLModel tables).

Importing this module registers the tables on ``SQLModel.metadata`` so
``init_db`` creates them.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Role(StrEnum):
    """Access roles, ordered viewer < operator < admin."""

    VIEWER = "viewer"
    OPERATOR = "operator"
    ADMIN = "admin"


_ORDER = {Role.VIEWER: 0, Role.OPERATOR: 1, Role.ADMIN: 2}


def role_satisfies(have: Role, need: Role) -> bool:
    """True if ``have`` meets or exceeds ``need``."""
    return _ORDER[have] >= _ORDER[need]


class User(SQLModel, table=True):
    """A login account."""

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    password_hash: str
    role: Role = Role.VIEWER
    active: bool = True
    created_at: datetime = Field(default_factory=_utcnow)


class Session(SQLModel, table=True):
    """A server-side session; the token lives in an HttpOnly cookie."""

    token: str = Field(primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=_utcnow)
    expires_at: datetime
