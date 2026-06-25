# SPDX-License-Identifier: AGPL-3.0-or-later
"""Schedule CRUD + today's-window preview."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlmodel import Session as DbSession
from sqlmodel import select

from ecallisto_ng.api.auth import require_role
from ecallisto_ng.api.db import get_session
from ecallisto_ng.api.models import Instrument, Role, Schedule, Station
from ecallisto_ng.services.legacy_export import (
    ExportEntry,
    build_scheduler_cfg,
)
from ecallisto_ng.services.scheduler import (
    is_recording_desired,
    sun_window,
)

router = APIRouter(prefix="/api/v1/schedules", tags=["schedules"])

_viewer = require_role(Role.VIEWER)
_operator = require_role(Role.OPERATOR)


class ScheduleIn(BaseModel):
    instrument_id: int
    kind: str = "sun"
    margin_minutes: int = 0
    start_utc: str = "00:00"
    stop_utc: str = "23:59"
    program_id: int | None = None
    overview_at: str = ""
    enabled: bool = True


def _station(db: DbSession) -> Station:
    return db.exec(select(Station)).first() or Station()


@router.get("", dependencies=[Depends(_viewer)])
def list_schedules(db: DbSession = Depends(get_session)) -> list[Schedule]:
    return list(db.exec(select(Schedule)).all())


@router.post("", status_code=201, dependencies=[Depends(_operator)])
def create_schedule(
    body: ScheduleIn, db: DbSession = Depends(get_session)
) -> Schedule:
    obj = Schedule(**body.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete(
    "/{schedule_id}", status_code=204, dependencies=[Depends(_operator)]
)
def delete_schedule(
    schedule_id: int, db: DbSession = Depends(get_session)
) -> None:
    obj = db.get(Schedule, schedule_id)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no such schedule")
    db.delete(obj)
    db.commit()


@router.get(
    "/export/scheduler.cfg",
    dependencies=[Depends(_viewer)],
    response_class=PlainTextResponse,
)
def export_scheduler_cfg(db: DbSession = Depends(get_session)) -> str:
    """Export enabled fixed-mode schedules in the legacy format."""
    entries: list[ExportEntry] = []
    for sched in db.exec(select(Schedule).where(Schedule.enabled)).all():
        inst = db.get(Instrument, sched.instrument_id)
        fc = inst.focus_code if inst else 1
        if sched.kind == "fixed":
            entries.append(ExportEntry(sched.start_utc, fc, 3))
            entries.append(ExportEntry(sched.stop_utc, fc, 0))
    return build_scheduler_cfg(entries)


@router.get("/{schedule_id}/preview", dependencies=[Depends(_viewer)])
def preview(
    schedule_id: int, db: DbSession = Depends(get_session)
) -> dict[str, object]:
    sched = db.get(Schedule, schedule_id)
    if sched is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no such schedule")
    now = datetime.now(UTC)
    station = _station(db)
    window = sun_window(
        station.latitude_deg,
        station.longitude_deg,
        now.date(),
        sched.margin_minutes,
    )
    return {
        "kind": sched.kind,
        "window_start": window[0].isoformat() if window else None,
        "window_stop": window[1].isoformat() if window else None,
        "recording_now": is_recording_desired(window, now),
    }
