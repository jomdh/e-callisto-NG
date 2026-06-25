# SPDX-License-Identifier: AGPL-3.0-or-later
"""Station config backup / restore (DESIGN 8.4 Software).

Exports the DB-backed *configuration* (not science data, not user accounts) as
a plain dict, and restores it by replacing those tables. Insert order respects
FKs. User accounts, sessions, audit, and upload jobs are intentionally excluded
-- config backup is for reprovisioning, not for moving credentials or state.

Upload-target passwords travel as stored ciphertext, so a restore on the *same*
station (same secret_key) round-trips; moved elsewhere they won't decrypt.
"""

from __future__ import annotations

from typing import Any

from sqlmodel import Session, SQLModel, delete, select

from ecallisto_ng.api.models import (
    AccessSettings,
    CalibrationSet,
    FrequencyProgram,
    Instrument,
    PeerStation,
    Schedule,
    Station,
    UploadTarget,
)

# (key, model) in FK-safe insert order; export reverses for delete.
_TABLES: list[tuple[str, type[SQLModel]]] = [
    ("calibration_sets", CalibrationSet),
    ("programs", FrequencyProgram),
    ("stations", Station),
    ("instruments", Instrument),
    ("schedules", Schedule),
    ("upload_targets", UploadTarget),
    ("access", AccessSettings),
    ("peers", PeerStation),
]


def export_config(db: Session) -> dict[str, Any]:
    """Serialize all config tables to a dict."""
    out: dict[str, Any] = {"version": 1}
    for key, model in _TABLES:
        rows = db.exec(select(model)).all()
        out[key] = [r.model_dump(mode="json") for r in rows]
    return out


def import_config(db: Session, data: dict[str, Any]) -> dict[str, int]:
    """Replace config tables from a backup dict; return rows-per-table."""
    counts: dict[str, int] = {}
    # delete in reverse FK order
    for _key, model in reversed(_TABLES):
        db.exec(delete(model))
    db.commit()
    for key, model in _TABLES:
        rows = data.get(key, []) or []
        for row in rows:
            # model_validate coerces JSON types (e.g. ISO datetime strings)
            db.add(model.model_validate(row))
        counts[key] = len(rows)
    db.commit()
    return counts
