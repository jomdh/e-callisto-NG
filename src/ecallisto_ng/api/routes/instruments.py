"""Instrument CRUD + record control."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session as DbSession
from sqlmodel import select

from ecallisto_ng.api.auth import require_role
from ecallisto_ng.api.db import get_session
from ecallisto_ng.api.models import Instrument, Role
from ecallisto_ng.api.settings import get_settings
from ecallisto_ng.core.recording import RecordingMeta
from ecallisto_ng.core.spectra import Channel
from ecallisto_ng.services.recorder import (
    RecorderState,
    build_driver,
    get_recorder,
)

router = APIRouter(prefix="/api/v1/instruments", tags=["instruments"])

_viewer = require_role(Role.VIEWER)
_operator = require_role(Role.OPERATOR)


class InstrumentIn(BaseModel):
    name: str
    instrument_class: str = "heterodyne"
    address: str = ""
    focus_code: int = 1
    gain: int = 120
    channels: int = 200
    sweep_rate_hz: float = 4.0
    enabled: bool = True


def _get(db: DbSession, instrument_id: int) -> Instrument:
    obj = db.get(Instrument, instrument_id)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no such instrument")
    return obj


@router.get("", dependencies=[Depends(_viewer)])
def list_instruments(db: DbSession = Depends(get_session)) -> list[Instrument]:
    return list(db.exec(select(Instrument)).all())


@router.post("", status_code=201, dependencies=[Depends(_operator)])
def create_instrument(
    body: InstrumentIn, db: DbSession = Depends(get_session)
) -> Instrument:
    obj = Instrument(**body.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/{instrument_id}", dependencies=[Depends(_viewer)])
def get_instrument(
    instrument_id: int, db: DbSession = Depends(get_session)
) -> Instrument:
    return _get(db, instrument_id)


@router.patch("/{instrument_id}", dependencies=[Depends(_operator)])
def update_instrument(
    instrument_id: int,
    body: InstrumentIn,
    db: DbSession = Depends(get_session),
) -> Instrument:
    obj = _get(db, instrument_id)
    for key, value in body.model_dump().items():
        setattr(obj, key, value)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete(
    "/{instrument_id}", status_code=204, dependencies=[Depends(_operator)]
)
def delete_instrument(
    instrument_id: int, db: DbSession = Depends(get_session)
) -> None:
    db.delete(_get(db, instrument_id))
    db.commit()


@router.post("/{instrument_id}/record", dependencies=[Depends(_operator)])
def record_instrument(
    instrument_id: int,
    frames: int = 100,
    db: DbSession = Depends(get_session),
) -> dict[str, str]:
    inst = _get(db, instrument_id)
    driver = build_driver(
        inst.instrument_class, inst.address, inst.focus_code, inst.channels
    )
    channels = [Channel(frequency_mhz=45.0 + i) for i in range(inst.channels)]
    meta = RecordingMeta(instrument=inst.name, focus_code=inst.focus_code)
    out_dir = get_settings().data_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        get_recorder().start(
            instrument_id,
            driver,
            channels,
            meta,
            out_dir,
            sweep_rate_hz=inst.sweep_rate_hz,
            max_frames=frames,
        )
    except RuntimeError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    return {"state": RecorderState.RECORDING}


@router.post("/{instrument_id}/stop", dependencies=[Depends(_operator)])
def stop_instrument(instrument_id: int) -> dict[str, bool]:
    get_recorder().stop(instrument_id)
    return {"ok": True}


@router.get("/{instrument_id}/status", dependencies=[Depends(_viewer)])
def instrument_status(instrument_id: int) -> dict[str, object]:
    st = get_recorder().status(instrument_id)
    return {"state": st.state, "last_file": st.last_file, "error": st.error}
