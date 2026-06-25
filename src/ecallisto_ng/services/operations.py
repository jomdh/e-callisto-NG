"""Operations cockpit: per-instrument live state for the dashboard (DESIGN 8).

Aggregates, per instrument: recording state + last file (from the recorder),
the next scheduled action (from its schedule + sun/fixed window), and the last
upload. Read-only orchestration over recorder status + DB; the recorder remains
the source of run-state truth (cross-process persistence is M21/F14).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlmodel import Session, col, select

from ecallisto_ng.api.models import (
    FrequencyProgram,
    Instrument,
    Schedule,
    Station,
    UploadJob,
)
from ecallisto_ng.services.recorder import get_recorder
from ecallisto_ng.services.scheduler import (
    fixed_window,
    is_recording_desired,
    sun_window,
)


def _next_action(
    db: Session, inst: Instrument, station: Station, now: datetime
) -> str:
    sched = db.exec(
        select(Schedule).where(
            Schedule.instrument_id == inst.id, Schedule.enabled
        )
    ).first()
    if sched is None:
        return "no schedule"
    if sched.kind == "fixed":
        window = fixed_window(now.date(), sched.start_utc, sched.stop_utc)
    else:
        window = sun_window(
            station.latitude_deg,
            station.longitude_deg,
            now.date(),
            sched.margin_minutes,
        )
    if window is None:
        return "no window today"
    start, stop = window
    if is_recording_desired(window, now):
        return f"recording until {stop:%H:%M} UTC"
    if now < start:
        return f"next start {start:%H:%M} UTC"
    return "window passed today"


def instrument_cockpit(db: Session, now: datetime) -> list[dict[str, Any]]:
    """One status row per instrument for the dashboard.

    State/last-file come from the persisted runtime (cross-process, ADR-0007),
    falling back to this process's in-memory recorder view.
    """
    from ecallisto_ng.services import recorder_state

    station = db.exec(select(Station)).first() or Station()
    recorder = get_recorder()
    runtimes = recorder_state.read(db)
    rows: list[dict[str, Any]] = []
    for inst in db.exec(select(Instrument)).all():
        status = recorder.status(inst.id) if inst.id is not None else None
        runtime = runtimes.get(inst.id) if inst.id is not None else None
        state = (
            runtime.state if runtime else (status.state if status else "idle")
        )
        last_file = (
            runtime.last_file
            if runtime
            else (status.last_file if status else None)
        )
        last_upload = db.exec(
            select(UploadJob)
            .where(
                UploadJob.state == "done",
                col(UploadJob.filename).like(f"{inst.name}%"),
            )
            .order_by(col(UploadJob.id).desc())
        ).first()
        program = None
        sched = db.exec(
            select(Schedule).where(
                Schedule.instrument_id == inst.id, Schedule.enabled
            )
        ).first()
        if sched is not None and sched.program_id is not None:
            prog = db.get(FrequencyProgram, sched.program_id)
            program = prog.name if prog else None
        rows.append(
            {
                "id": inst.id,
                "name": inst.name,
                "instrument_class": inst.instrument_class,
                "channels": inst.channels,
                "enabled": inst.enabled,
                "state": state,
                "last_file": last_file,
                "next_action": _next_action(db, inst, station, now),
                "last_upload": (last_upload.filename if last_upload else None),
                "program": program,
            }
        )
    return rows
