"""Remote-access settings + generated Caddyfile (admin)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlmodel import Session as DbSession
from sqlmodel import select

from ecallisto_ng.api.auth import require_role
from ecallisto_ng.api.db import get_session
from ecallisto_ng.api.models import AccessSettings, Role
from ecallisto_ng.api.settings import get_settings
from ecallisto_ng.services.caddy import build_caddyfile

router = APIRouter(prefix="/api/v1/access", tags=["access"])

_viewer = require_role(Role.VIEWER)
_admin = require_role(Role.ADMIN)


class AccessIn(BaseModel):
    mode: str = "lan"
    hostname: str = ""
    tls_email: str = ""
    ddns_update_url: str = ""
    tunnel_relay: str = ""


def _get(db: DbSession) -> AccessSettings:
    obj = db.exec(select(AccessSettings)).first()
    if obj is None:
        obj = AccessSettings()
        db.add(obj)
        db.commit()
        db.refresh(obj)
    return obj


@router.get("", dependencies=[Depends(_viewer)])
def get_access(db: DbSession = Depends(get_session)) -> AccessSettings:
    return _get(db)


@router.put("", dependencies=[Depends(_admin)])
def put_access(
    body: AccessIn, db: DbSession = Depends(get_session)
) -> AccessSettings:
    obj = _get(db)
    for key, value in body.model_dump().items():
        setattr(obj, key, value)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get(
    "/caddyfile",
    dependencies=[Depends(_admin)],
    response_class=PlainTextResponse,
)
def caddyfile(db: DbSession = Depends(get_session)) -> str:
    access = _get(db)
    return build_caddyfile(
        access.mode,
        access.hostname,
        get_settings().port,
        access.tls_email,
    )
