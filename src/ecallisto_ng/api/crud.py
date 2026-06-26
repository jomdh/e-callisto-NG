# SPDX-License-Identifier: AGPL-3.0-or-later
"""Shared CRUD helpers for the API routes.

A unique-name or foreign-key violation on insert/update is operator-reachable
input, not a server fault -- it must be a clean 4xx, never a 500. Routes commit
through :func:`commit_or_conflict` so a duplicate name or dangling reference
becomes a 409 instead of an unhandled ``IntegrityError``.
"""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session


def commit_or_conflict(
    db: Session,
    detail: str = "a record with that name or reference already exists",
) -> None:
    """``db.commit()`` mapping an IntegrityError to a 409 (rolls back)."""
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail) from exc
