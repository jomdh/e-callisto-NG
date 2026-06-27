# SPDX-License-Identifier: AGPL-3.0-or-later
"""Calibration-set CRUD."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session as DbSession
from sqlmodel import select

from ecallisto_ng.api.auth import require_role
from ecallisto_ng.api.crud import commit_or_conflict
from ecallisto_ng.api.db import get_session
from ecallisto_ng.api.models import CalibrationSet, Instrument, Role

router = APIRouter(prefix="/api/v1/calibration", tags=["calibration"])

_viewer = require_role(Role.VIEWER)
_operator = require_role(Role.OPERATOR)


class CalibrationIn(BaseModel):
    name: str
    coefficients: list[list[float]]  # rows of [a, b, cf, tb]


class CalibrationOut(BaseModel):
    id: int
    name: str
    coefficients: list[list[float]]
    used_by: list[int] = []  # ids of instruments referencing this set


def _out(
    c: CalibrationSet, used_by: list[int] | None = None
) -> CalibrationOut:
    return CalibrationOut(
        id=c.id or 0,
        name=c.name,
        coefficients=json.loads(c.coefficients_json),
        used_by=used_by or [],
    )


def _users_by_set(db: DbSession) -> dict[int, list[int]]:
    """Map calibration-set id -> ids of instruments referencing it."""
    out: dict[int, list[int]] = {}
    for inst in db.exec(select(Instrument)).all():
        if inst.calibration_set_id is not None and inst.id is not None:
            out.setdefault(inst.calibration_set_id, []).append(inst.id)
    return out


@router.get("", dependencies=[Depends(_viewer)])
def list_sets(db: DbSession = Depends(get_session)) -> list[CalibrationOut]:
    users = _users_by_set(db)
    return [
        _out(c, users.get(c.id or 0, []))
        for c in db.exec(select(CalibrationSet)).all()
    ]


@router.post("", status_code=201, dependencies=[Depends(_operator)])
def create_set(
    body: CalibrationIn, db: DbSession = Depends(get_session)
) -> CalibrationOut:
    obj = CalibrationSet(
        name=body.name, coefficients_json=json.dumps(body.coefficients)
    )
    db.add(obj)
    commit_or_conflict(db, "a calibration set with that name already exists")
    db.refresh(obj)
    return _out(obj)


@router.delete("/{set_id}", status_code=204, dependencies=[Depends(_operator)])
def delete_set(set_id: int, db: DbSession = Depends(get_session)) -> None:
    obj = db.get(CalibrationSet, set_id)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no such set")
    db.delete(obj)
    db.commit()
