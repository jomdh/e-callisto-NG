# SPDX-License-Identifier: AGPL-3.0-or-later
"""Alert-channel configuration + test (admin, DESIGN 14a)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session as DbSession
from sqlmodel import select

from ecallisto_ng.api.auth import require_role
from ecallisto_ng.api.crud import commit_or_conflict
from ecallisto_ng.api.db import get_session
from ecallisto_ng.api.models import AlertChannelConfig, Role
from ecallisto_ng.services import alerts

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])

_admin = require_role(Role.ADMIN)


class ChannelIn(BaseModel):
    name: str
    kind: str = "webhook"
    url: str = ""
    recipient: str = ""
    enabled: bool = True


@router.get("/channels", dependencies=[Depends(_admin)])
def list_channels(
    db: DbSession = Depends(get_session),
) -> list[AlertChannelConfig]:
    return list(db.exec(select(AlertChannelConfig)).all())


@router.post("/channels", status_code=201, dependencies=[Depends(_admin)])
def add_channel(
    body: ChannelIn, db: DbSession = Depends(get_session)
) -> AlertChannelConfig:
    obj = AlertChannelConfig(**body.model_dump())
    db.add(obj)
    commit_or_conflict(db, "an alert channel with that name already exists")
    db.refresh(obj)
    return obj


@router.delete(
    "/channels/{channel_id}", status_code=204, dependencies=[Depends(_admin)]
)
def delete_channel(
    channel_id: int, db: DbSession = Depends(get_session)
) -> None:
    obj = db.get(AlertChannelConfig, channel_id)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no such channel")
    db.delete(obj)
    db.commit()


@router.post("/channels/{channel_id}/test", dependencies=[Depends(_admin)])
def test_channel(
    channel_id: int, db: DbSession = Depends(get_session)
) -> dict[str, object]:
    """Send a test alert through one channel."""
    obj = db.get(AlertChannelConfig, channel_id)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no such channel")
    channel = alerts.build_channel(obj)
    if channel is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "channel not configured"
        )
    sent = alerts.dispatch(
        [channel], "e-Callisto NG test", "This is a test alert."
    )
    return {"sent": sent}
