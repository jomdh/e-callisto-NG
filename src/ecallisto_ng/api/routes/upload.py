"""Upload targets (config) + run + queue."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session as DbSession
from sqlmodel import select

from ecallisto_ng.api.auth import require_role
from ecallisto_ng.api.db import get_session
from ecallisto_ng.api.models import Role, UploadJob, UploadTarget
from ecallisto_ng.api.settings import get_settings
from ecallisto_ng.core.contracts import UploadTransport
from ecallisto_ng.services import catalog, uploader

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
    gzip: bool = True
    enabled: bool = True


def _build_transport(target: UploadTarget) -> UploadTransport:
    if target.protocol == "local":
        from ecallisto_ng.transports.local import LocalTransport

        return LocalTransport(target.host)
    if target.protocol == "ftp":
        from ecallisto_ng.transports.ftp import FtpTransport

        return FtpTransport(
            target.host, target.username, target.password, target.base_path
        )
    raise HTTPException(
        status.HTTP_400_BAD_REQUEST, f"unknown protocol: {target.protocol}"
    )


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
    data_dir = get_settings().data_dir
    uploaded = 0
    failed = 0
    for info in catalog.list_recordings(data_dir):
        done = db.exec(
            select(UploadJob).where(
                UploadJob.target_id == target_id,
                UploadJob.filename == info.name,
                UploadJob.state == "done",
            )
        ).first()
        if done is not None:
            continue
        local = Path(data_dir) / info.name
        remote = uploader.remote_name_for(local, target.gzip)
        try:
            uploader.upload_file(
                _build_transport(target),
                local,
                remote,
                do_gzip=target.gzip,
            )
            db.add(
                UploadJob(
                    target_id=target_id, filename=info.name, state="done"
                )
            )
            uploaded += 1
        except Exception as exc:  # noqa: BLE001 - record per-file failure
            db.add(
                UploadJob(
                    target_id=target_id,
                    filename=info.name,
                    state="error",
                    error=str(exc),
                )
            )
            failed += 1
    db.commit()
    return {"uploaded": uploaded, "failed": failed}
