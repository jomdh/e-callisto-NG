# SPDX-License-Identifier: AGPL-3.0-or-later
"""Persist + read recorder run-state across processes (ADR-0007 / F14).

The recorder calls ``write`` on each state change (via a callback wired by the
API callers, so the recorder stays api-free). The web app reads ``state`` to
show acquisition status even when the separate ``acquire`` daemon owns the
recording loops.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlmodel import Session, select

from ecallisto_ng.api.db import get_engine
from ecallisto_ng.api.models import RecorderRuntime


def write(instrument_id: int, state: str, last_file: str | None) -> None:
    """Upsert the run-state for an instrument (best-effort)."""
    with Session(get_engine()) as db:
        row = db.get(RecorderRuntime, instrument_id)
        if row is None:
            row = RecorderRuntime(instrument_id=instrument_id)
        row.state = str(state)
        if last_file is not None:
            row.last_file = last_file
        row.updated_at = datetime.now(UTC)
        db.add(row)
        db.commit()


def read(db: Session) -> dict[int, RecorderRuntime]:
    """All persisted recorder run-states, keyed by instrument id."""
    return {r.instrument_id: r for r in db.exec(select(RecorderRuntime)).all()}


def set_desired(instrument_id: int, desired: bool) -> None:
    """Set the operator's record/idle intent for a free-run instrument.

    The scheduler keeps a free-run (manual / no-schedule) instrument recording
    while this is True. Record sets it True, Stop sets it False.
    """
    with Session(get_engine()) as db:
        row = db.get(RecorderRuntime, instrument_id)
        if row is None:
            row = RecorderRuntime(instrument_id=instrument_id)
        row.desired = desired
        row.updated_at = datetime.now(UTC)
        db.add(row)
        db.commit()


def get_desired(db: Session, instrument_id: int) -> bool:
    """The operator's current record/idle intent (False if never set)."""
    row = db.get(RecorderRuntime, instrument_id)
    return bool(row.desired) if row is not None else False
