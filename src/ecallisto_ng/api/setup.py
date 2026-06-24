"""First-run configuration state."""

from __future__ import annotations

from sqlmodel import Session as DbSession
from sqlmodel import select

from ecallisto_ng.api.models import User


def is_configured(db: DbSession) -> bool:
    """A station is configured once it has at least one user (the admin)."""
    return db.exec(select(User)).first() is not None
