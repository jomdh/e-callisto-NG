"""Observation planning: source az/el track vs horizon (DESIGN 8 / F8)."""

from __future__ import annotations

from datetime import UTC, date, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session as DbSession
from sqlmodel import select

from ecallisto_ng.api.auth import require_role
from ecallisto_ng.api.db import get_session
from ecallisto_ng.api.models import Role, Station
from ecallisto_ng.services import astro_track

router = APIRouter(prefix="/api/v1/planning", tags=["planning"])

_viewer = require_role(Role.VIEWER)


@router.get("/track", dependencies=[Depends(_viewer)])
def track(
    source: str = "sun",
    day: str = "",
    db: DbSession = Depends(get_session),
) -> dict[str, object]:
    """Az/el track for a source over a day, with station + horizon."""
    station = db.exec(select(Station)).first() or Station()
    when = datetime.now(UTC).date()
    if day:
        try:
            when = date.fromisoformat(day)
        except ValueError as exc:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "bad date"
            ) from exc
    try:
        points = astro_track.source_track(
            station.latitude_deg,
            station.longitude_deg,
            station.altitude_m,
            when,
            source,
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    return {
        "source": source,
        "day": when.isoformat(),
        "sources": astro_track.SOURCES,
        "horizon_deg": station.horizon_deg,
        "track": [list(p) for p in points],
    }
