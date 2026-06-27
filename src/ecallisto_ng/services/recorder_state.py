# SPDX-License-Identifier: AGPL-3.0-or-later
"""Persist + read recorder run-state across processes (ADR-0007 / F14).

The recorder calls ``write`` on each state change (via a callback wired by the
API callers, so the recorder stays api-free). The web app reads ``state`` to
show acquisition status even when the separate ``acquire`` daemon owns the
recording loops.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from ecallisto_ng.api.db import get_engine
from ecallisto_ng.api.models import RecorderRuntime


def _upsert(
    instrument_id: int, apply: Callable[[RecorderRuntime], None]
) -> None:
    """Get-or-create the row, apply a mutation, commit -- retrying once if a
    concurrent process inserted the row first (web + acquire both write)."""
    for attempt in (1, 2):
        with Session(get_engine()) as db:
            row = db.get(RecorderRuntime, instrument_id)
            created = row is None
            if row is None:
                row = RecorderRuntime(instrument_id=instrument_id)
            apply(row)
            row.updated_at = datetime.now(UTC)
            db.add(row)
            try:
                db.commit()
                return
            except IntegrityError:
                db.rollback()
                if created and attempt == 1:
                    continue  # another process won the insert -- retry update
                return  # best-effort; the other write is authoritative


def write(instrument_id: int, state: str, last_file: str | None) -> None:
    """Upsert the run-state for an instrument (best-effort)."""

    def apply(row: RecorderRuntime) -> None:
        row.state = str(state)
        if last_file is not None:
            row.last_file = last_file

    _upsert(instrument_id, apply)


def touch_frame(instrument_id: int) -> None:
    """Stamp ``last_frame_at`` = now: the recorder produced a frame (ADR-0012).

    The empirical liveness heartbeat. Called throttled (not every frame), and
    best-effort -- a missed heartbeat write is corrected by the next one.
    """

    def apply(row: RecorderRuntime) -> None:
        row.last_frame_at = datetime.now(UTC)

    _upsert(instrument_id, apply)


def read(db: Session) -> dict[int, RecorderRuntime]:
    """All persisted recorder run-states, keyed by instrument id."""
    return {r.instrument_id: r for r in db.exec(select(RecorderRuntime)).all()}


def set_desired(instrument_id: int, desired: bool) -> None:
    """Set the operator's record/idle intent for a free-run instrument.

    The scheduler keeps a free-run (manual / no-schedule) instrument recording
    while this is True. Record sets it True, Stop sets it False.
    """

    def apply(row: RecorderRuntime) -> None:
        row.desired = desired

    _upsert(instrument_id, apply)


def get_desired(db: Session, instrument_id: int) -> bool:
    """The operator's current record/idle intent (False if never set)."""
    row = db.get(RecorderRuntime, instrument_id)
    return bool(row.desired) if row is not None else False
