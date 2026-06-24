"""System health endpoint + page."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session as DbSession
from sqlmodel import func, select

from ecallisto_ng.api import auth
from ecallisto_ng.api.auth import require_role
from ecallisto_ng.api.db import get_session
from ecallisto_ng.api.models import Instrument, Role, UploadJob, User
from ecallisto_ng.api.settings import get_settings
from ecallisto_ng.api.templating import templates
from ecallisto_ng.services import catalog
from ecallisto_ng.services.health import HealthReport, build_report

router = APIRouter(tags=["system"])

_viewer = require_role(Role.VIEWER)


def _report(db: DbSession) -> HealthReport:
    data_dir = get_settings().data_dir
    instruments = db.exec(select(func.count()).select_from(Instrument)).one()
    recordings = catalog.list_recordings(data_dir)
    done = {
        j.filename
        for j in db.exec(
            select(UploadJob).where(UploadJob.state == "done")
        ).all()
    }
    pending = sum(1 for r in recordings if r.name not in done)
    return build_report(data_dir, int(instruments), len(recordings), pending)


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
