# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fleet: token-gated health + peer registry + aggregate (DESIGN 8)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlmodel import Session as DbSession
from sqlmodel import select

from ecallisto_ng.api.auth import optional_user, require_role
from ecallisto_ng.api.crud import commit_or_conflict
from ecallisto_ng.api.db import get_session
from ecallisto_ng.api.models import PeerStation, Role, User
from ecallisto_ng.api.settings import get_settings
from ecallisto_ng.services import fleet
from ecallisto_ng.services.health import HealthReport
from ecallisto_ng.services.health_report import build_station_health

router = APIRouter(prefix="/api/v1/fleet", tags=["fleet"])

_admin = require_role(Role.ADMIN)


class PeerIn(BaseModel):
    name: str
    base_url: str
    token: str = ""
    enabled: bool = True


@router.get("/health")
def fleet_health(
    token: str = Query(default=""),
    db: DbSession = Depends(get_session),
) -> HealthReport:
    """This station's health, gated by the shared fleet token (no session)."""
    configured = get_settings().fleet_token
    if not configured or token != configured:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "invalid fleet token")
    return build_station_health(db)


@router.get("/peers", dependencies=[Depends(_admin)])
def list_peers(db: DbSession = Depends(get_session)) -> list[PeerStation]:
    return list(db.exec(select(PeerStation)).all())


@router.post("/peers", status_code=201, dependencies=[Depends(_admin)])
def add_peer(
    body: PeerIn, db: DbSession = Depends(get_session)
) -> PeerStation:
    obj = PeerStation(**body.model_dump())
    db.add(obj)
    commit_or_conflict(db, "a peer station with that name already exists")
    db.refresh(obj)
    return obj


@router.delete(
    "/peers/{peer_id}", status_code=204, dependencies=[Depends(_admin)]
)
def remove_peer(peer_id: int, db: DbSession = Depends(get_session)) -> None:
    obj = db.get(PeerStation, peer_id)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no such peer")
    db.delete(obj)
    db.commit()


@router.get("")
def aggregate(
    user: User | None = Depends(optional_user),
    db: DbSession = Depends(get_session),
) -> dict[str, object]:
    """Combined view: this station + every reachable peer."""
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "not authenticated")
    peers = list(db.exec(select(PeerStation)).all())
    return {
        "self": build_station_health(db),
        "peers": fleet.gather_fleet(peers),
    }
