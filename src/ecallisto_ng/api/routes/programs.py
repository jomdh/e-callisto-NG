# SPDX-License-Identifier: AGPL-3.0-or-later
"""Frequency-program CRUD + overview-based generation."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlmodel import Session as DbSession
from sqlmodel import select

from ecallisto_ng.api.auth import require_role
from ecallisto_ng.api.db import get_session
from ecallisto_ng.api.models import FrequencyProgram, Role
from ecallisto_ng.services.freqgen import generate_frequencies, rf_to_if
from ecallisto_ng.services.legacy_export import build_frequency_program_cfg

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


class FrqImportIn(BaseModel):
    name: str
    text: str  # the pasted/uploaded legacy frqXXXXX.cfg content


class GenerateIn(BaseModel):
    name: str
    overview: list[tuple[float, float]]  # (freq_mhz, amplitude)
    start_mhz: float = 45.0
    stop_mhz: float = 870.0
    n_channels: int = 200
    mode: str = "quiet"
    exclude_from: float | None = None  # RFI-exclusion band start (MHz)
    exclude_to: float | None = None
    nonlinear_start: int = 0  # channels pinned to start_mhz (D2)
    # External up/down-converter (D3). The band above is the RF the user wants;
    # the receiver tunes the IF = converter(RF, LO). No RF range limit -- the
    # converter places the chosen band wherever the operator needs it.
    converter: str = "direct"  # direct | usb | lsb | up
    local_oscillator: float = 0.0  # converter LO (MHz)


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
    band = None
    if body.exclude_from is not None and body.exclude_to is not None:
        band = (body.exclude_from, body.exclude_to)
    try:
        freqs = generate_frequencies(
            body.overview,
            body.start_mhz,
            body.stop_mhz,
            body.n_channels,
            body.mode,
            exclude_band=band,
            nonlinear_start=body.nonlinear_start,
        )
        # D3: validate the chosen RF maps through the converter (no RF limit;
        # this just confirms the converter/LO is well-formed for each channel).
        for rf in freqs:
            rf_to_if(rf, body.local_oscillator, body.converter)
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


@router.post("/import/frq", status_code=201, dependencies=[Depends(_operator)])
def import_frq(
    body: FrqImportIn, db: DbSession = Depends(get_session)
) -> ProgramOut:
    """Create a program from a pasted/uploaded legacy frqXXXXX.cfg (M32)."""
    from ecallisto_ng.services.legacy_import import parse_frequency_program

    cfg = parse_frequency_program(body.text)
    if not cfg.frequencies:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "no channels found in the frq file"
        )
    prog = FrequencyProgram(
        name=body.name,
        frequencies_json=json.dumps(cfg.frequencies),
        start_mhz=min(cfg.frequencies),
        stop_mhz=max(cfg.frequencies),
        source="imported",
    )
    db.add(prog)
    db.commit()
    db.refresh(prog)
    return _out(prog)


@router.get(
    "/{program_id}/export/frq",
    dependencies=[Depends(_viewer)],
    response_class=PlainTextResponse,
)
def export_frq(
    program_id: int,
    external_lo: float = 0.0,
    db: DbSession = Depends(get_session),
) -> str:
    """Export a program as a legacy ``frqXXXXX.cfg`` file (audit D1)."""
    prog = db.get(FrequencyProgram, program_id)
    if prog is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no such program")
    return build_frequency_program_cfg(
        json.loads(prog.frequencies_json),
        json.loads(prog.light_curve_indices_json),
        external_lo=external_lo,
    )


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
