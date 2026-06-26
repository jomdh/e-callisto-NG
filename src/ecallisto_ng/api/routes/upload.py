# SPDX-License-Identifier: AGPL-3.0-or-later
"""Upload targets (config) + run + queue."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session as DbSession
from sqlmodel import select

from ecallisto_ng.api.auth import require_role
from ecallisto_ng.api.crud import commit_or_conflict
from ecallisto_ng.api.crypto import encrypt
from ecallisto_ng.api.db import get_session
from ecallisto_ng.api.models import Role, UploadJob, UploadTarget
from ecallisto_ng.api.settings import get_settings
from ecallisto_ng.services import uploader

router = APIRouter(prefix="/api/v1/upload", tags=["upload"])

_viewer = require_role(Role.VIEWER)
_operator = require_role(Role.OPERATOR)


class TargetIn(BaseModel):
    name: str
    protocol: str = "local"
    host: str = ""
    base_path: str = "/"
    username: str = ""
    password: str = ""
    dispatch: str = "manual"
    window_start: str = "00:00"
    window_stop: str = "23:59"
    gzip: bool = True
    enabled: bool = True


class TargetOut(BaseModel):
    """Public view of a target -- never includes the secret (B2)."""

    id: int
    name: str
    protocol: str
    host: str
    base_path: str
    username: str
    dispatch: str
    window_start: str
    window_stop: str
    gzip: bool
    enabled: bool
    has_password: bool


def _out(t: UploadTarget) -> TargetOut:
    return TargetOut(
        id=t.id or 0,
        name=t.name,
        protocol=t.protocol,
        host=t.host,
        base_path=t.base_path,
        username=t.username,
        dispatch=t.dispatch,
        window_start=t.window_start,
        window_stop=t.window_stop,
        gzip=t.gzip,
        enabled=t.enabled,
        has_password=bool(t.password),
    )


@router.get("/targets", dependencies=[Depends(_viewer)])
def list_targets(db: DbSession = Depends(get_session)) -> list[TargetOut]:
    return [_out(t) for t in db.exec(select(UploadTarget)).all()]


@router.post("/targets", status_code=201, dependencies=[Depends(_operator)])
def create_target(
    body: TargetIn, db: DbSession = Depends(get_session)
) -> TargetOut:
    data = body.model_dump()
    data["password"] = encrypt(data["password"])  # B2: encrypt at rest
    obj = UploadTarget(**data)
    db.add(obj)
    commit_or_conflict(db, "an upload target with that name already exists")
    db.refresh(obj)
    return _out(obj)


@router.get("/queue", dependencies=[Depends(_viewer)])
def queue(db: DbSession = Depends(get_session)) -> list[UploadJob]:
    return list(db.exec(select(UploadJob)).all())


@router.post("/targets/{target_id}/run", dependencies=[Depends(_operator)])
def run_target(
    target_id: int, db: DbSession = Depends(get_session)
) -> dict[str, int]:
    target = db.get(UploadTarget, target_id)
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no such target")
    return uploader.upload_pending(db, target, get_settings().data_dir)


@router.post("/targets/{target_id}/test", dependencies=[Depends(_operator)])
def test_target(
    target_id: int, db: DbSession = Depends(get_session)
) -> dict[str, object]:
    """Test the connection to a target (reachability)."""
    target = db.get(UploadTarget, target_id)
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no such target")
    ok, message = uploader.test_target(target)
    return {"ok": ok, "message": message}
