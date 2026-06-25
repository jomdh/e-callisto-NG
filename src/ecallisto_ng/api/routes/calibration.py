# SPDX-License-Identifier: AGPL-3.0-or-later
"""Calibration-set CRUD."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session as DbSession
from sqlmodel import select

from ecallisto_ng.api.auth import require_role
from ecallisto_ng.api.db import get_session
from ecallisto_ng.api.models import CalibrationSet, Role

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


def _out(c: CalibrationSet) -> CalibrationOut:
    return CalibrationOut(
        id=c.id or 0,
        name=c.name,
        coefficients=json.loads(c.coefficients_json),
    )


@router.get("", dependencies=[Depends(_viewer)])
def list_sets(db: DbSession = Depends(get_session)) -> list[CalibrationOut]:
    return [_out(c) for c in db.exec(select(CalibrationSet)).all()]


@router.post("", status_code=201, dependencies=[Depends(_operator)])
def create_set(
    body: CalibrationIn, db: DbSession = Depends(get_session)
) -> CalibrationOut:
    obj = CalibrationSet(
        name=body.name, coefficients_json=json.dumps(body.coefficients)
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return _out(obj)


@router.delete("/{set_id}", status_code=204, dependencies=[Depends(_operator)])
def delete_set(set_id: int, db: DbSession = Depends(get_session)) -> None:
    obj = db.get(CalibrationSet, set_id)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no such set")
    db.delete(obj)
    db.commit()
