"""Frequency-program CRUD + overview-based generation."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session as DbSession
from sqlmodel import select

from ecallisto_ng.api.auth import require_role
from ecallisto_ng.api.db import get_session
from ecallisto_ng.api.models import FrequencyProgram, Role
from ecallisto_ng.services.freqgen import generate_frequencies

router = APIRouter(prefix="/api/v1/programs", tags=["programs"])

_viewer = require_role(Role.VIEWER)
_operator = require_role(Role.OPERATOR)


class ProgramOut(BaseModel):
    id: int
    name: str
    frequencies: list[float]
    start_mhz: float
    stop_mhz: float
    source: str


class ProgramIn(BaseModel):
    name: str
    frequencies: list[float] = []
    light_curve_indices: list[int] = []
    start_mhz: float = 45.0
    stop_mhz: float = 870.0


class GenerateIn(BaseModel):
    name: str
    overview: list[tuple[float, float]]  # (freq_mhz, amplitude)
    start_mhz: float = 45.0
    stop_mhz: float = 870.0
    n_channels: int = 200
    mode: str = "quiet"


def _out(p: FrequencyProgram) -> ProgramOut:
    return ProgramOut(
        id=p.id or 0,
        name=p.name,
        frequencies=json.loads(p.frequencies_json),
        start_mhz=p.start_mhz,
        stop_mhz=p.stop_mhz,
        source=p.source,
    )


@router.get("", dependencies=[Depends(_viewer)])
def list_programs(db: DbSession = Depends(get_session)) -> list[ProgramOut]:
    return [_out(p) for p in db.exec(select(FrequencyProgram)).all()]


@router.post("", status_code=201, dependencies=[Depends(_operator)])
def create_program(
    body: ProgramIn, db: DbSession = Depends(get_session)
) -> ProgramOut:
    prog = FrequencyProgram(
        name=body.name,
        frequencies_json=json.dumps(body.frequencies),
        light_curve_indices_json=json.dumps(body.light_curve_indices),
        start_mhz=body.start_mhz,
        stop_mhz=body.stop_mhz,
        source="manual",
    )
    db.add(prog)
    db.commit()
    db.refresh(prog)
    return _out(prog)


@router.post("/generate", status_code=201, dependencies=[Depends(_operator)])
def generate_program(
    body: GenerateIn, db: DbSession = Depends(get_session)
) -> ProgramOut:
    try:
        freqs = generate_frequencies(
            body.overview,
            body.start_mhz,
            body.stop_mhz,
            body.n_channels,
            body.mode,
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    prog = FrequencyProgram(
        name=body.name,
        frequencies_json=json.dumps(freqs),
        start_mhz=body.start_mhz,
        stop_mhz=body.stop_mhz,
        source="generated",
    )
    db.add(prog)
    db.commit()
    db.refresh(prog)
    return _out(prog)


@router.delete(
    "/{program_id}", status_code=204, dependencies=[Depends(_operator)]
)
def delete_program(
    program_id: int, db: DbSession = Depends(get_session)
) -> None:
    prog = db.get(FrequencyProgram, program_id)
    if prog is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no such program")
    db.delete(prog)
    db.commit()
