"""Upload targets (config) + run + queue."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session as DbSession
from sqlmodel import select

from ecallisto_ng.api.auth import require_role
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


@router.get("/targets", dependencies=[Depends(_viewer)])
def list_targets(db: DbSession = Depends(get_session)) -> list[UploadTarget]:
    return list(db.exec(select(UploadTarget)).all())


@router.post("/targets", status_code=201, dependencies=[Depends(_operator)])
def create_target(
    body: TargetIn, db: DbSession = Depends(get_session)
) -> UploadTarget:
    obj = UploadTarget(**body.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


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
