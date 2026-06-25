"""Legacy-station import: config files -> NG records (DESIGN 9a)."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session as DbSession
from sqlmodel import select

from ecallisto_ng.api.auth import require_role
from ecallisto_ng.api.db import get_session
from ecallisto_ng.api.models import (
    CalibrationSet,
    FrequencyProgram,
    Instrument,
    Role,
    Schedule,
    Station,
)
from ecallisto_ng.services import legacy_import

router = APIRouter(prefix="/api/v1/import", tags=["migrate"])

_operator = require_role(Role.OPERATOR)


class ImportIn(BaseModel):
    callisto_cfg: str
    frq_cfg: str = ""
    scheduler_cfg: str = ""
    cal_prn: str = ""
    dry_run: bool = False


@router.post("", dependencies=[Depends(_operator)])
def import_legacy(
    body: ImportIn, db: DbSession = Depends(get_session)
) -> dict[str, object]:
    cfg = legacy_import.parse_callisto_cfg(body.callisto_cfg)
    summary: dict[str, object] = {
        "instrument": cfg.instrument,
        "latitude_deg": cfg.latitude_deg,
        "longitude_deg": cfg.longitude_deg,
        "program_channels": 0,
        "schedule_entries": 0,
        "calibration_rows": 0,
    }

    prog = (
        legacy_import.parse_frequency_program(body.frq_cfg)
        if body.frq_cfg
        else None
    )
    if prog:
        summary["program_channels"] = len(prog.frequencies)
    sched = legacy_import.parse_scheduler_cfg(body.scheduler_cfg)
    summary["schedule_entries"] = len(sched)
    cal_rows = (
        legacy_import.parse_calibration_prn(body.cal_prn)
        if body.cal_prn
        else []
    )
    summary["calibration_rows"] = len(cal_rows)

    if body.dry_run:
        summary["dry_run"] = True
        return summary

    # Station (single row): set identity + coordinates.
    station = db.exec(select(Station)).first() or Station()
    station.observatory = cfg.origin or station.observatory
    station.latitude_deg = cfg.latitude_deg
    station.longitude_deg = cfg.longitude_deg
    station.altitude_m = cfg.altitude_m
    db.add(station)

    cal_id = None
    if cal_rows:
        cset = CalibrationSet(
            name=f"{cfg.instrument or 'legacy'}-cal",
            coefficients_json=json.dumps(cal_rows),
        )
        db.add(cset)
        db.commit()
        db.refresh(cset)
        cal_id = cset.id

    inst = Instrument(
        name=cfg.instrument or "legacy",
        focus_code=cfg.focus_code,
        gain=cfg.gain,
        channels=len(prog.frequencies) if prog else 200,
        sweep_rate_hz=float(prog.sweeps_per_second) if prog else 4.0,
        calibration_set_id=cal_id,
    )
    db.add(inst)
    db.commit()
    db.refresh(inst)
    summary["instrument_id"] = inst.id

    if prog:
        fp = FrequencyProgram(
            name=f"{inst.name}-imported",
            frequencies_json=json.dumps(prog.frequencies),
            source="generated",
        )
        db.add(fp)

    # Legacy scheduler entries -> a fixed window (earliest start, latest stop).
    starts = [e for e in sched if e.mode not in (0,)]
    stops = [e for e in sched if e.mode == 0]
    if starts and inst.id is not None:
        start = min(e.time_utc for e in starts)[:5]
        stop = max(e.time_utc for e in stops)[:5] if stops else "23:59"
        db.add(
            Schedule(
                instrument_id=inst.id,
                kind="fixed",
                start_utc=start,
                stop_utc=stop,
            )
        )
    db.commit()
    return summary
