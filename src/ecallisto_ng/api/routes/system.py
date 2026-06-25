"""System health endpoint + page."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session as DbSession

from ecallisto_ng.api import auth
from ecallisto_ng.api.auth import require_role
from ecallisto_ng.api.db import get_session
from ecallisto_ng.api.models import Role, User
from ecallisto_ng.api.templating import templates
from ecallisto_ng.services.health import HealthReport
from ecallisto_ng.services.health_report import build_station_health

router = APIRouter(tags=["system"])

_viewer = require_role(Role.VIEWER)


def _report(db: DbSession) -> HealthReport:
    return build_station_health(db)


@router.get("/api/v1/system/health", dependencies=[Depends(_viewer)])
def health(db: DbSession = Depends(get_session)) -> HealthReport:
    return _report(db)


@router.get("/portal/system", response_class=HTMLResponse)
def system_page(
    request: Request,
    user: User | None = Depends(auth.optional_user),
    db: DbSession = Depends(get_session),
) -> object:
    if user is None:
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(
        request, "portal/system.html", {"user": user, "h": _report(db)}
    )
