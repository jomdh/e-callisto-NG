"""System health endpoint + page."""

from __future__ import annotations

import shutil

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session as DbSession

from ecallisto_ng import __version__
from ecallisto_ng.api import auth
from ecallisto_ng.api.auth import require_role
from ecallisto_ng.api.db import get_session
from ecallisto_ng.api.models import Role, User
from ecallisto_ng.api.settings import get_settings
from ecallisto_ng.api.templating import templates
from ecallisto_ng.services import config_backup
from ecallisto_ng.services.clock import clock_synced
from ecallisto_ng.services.health import HealthReport
from ecallisto_ng.services.health_report import build_station_health

router = APIRouter(tags=["system"])

_viewer = require_role(Role.VIEWER)
_admin = require_role(Role.ADMIN)


def _report(db: DbSession) -> HealthReport:
    return build_station_health(db)


@router.get("/api/v1/system/health", dependencies=[Depends(_viewer)])
def health(db: DbSession = Depends(get_session)) -> HealthReport:
    return _report(db)


@router.get("/api/v1/system/info", dependencies=[Depends(_viewer)])
def system_info() -> dict[str, object]:
    """Version, storage, clock, and retention/archive policy."""
    settings = get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    usage = shutil.disk_usage(settings.data_dir)
    return {
        "version": __version__,
        "disk_total": usage.total,
        "disk_free": usage.free,
        "disk_pct_free": round(usage.free / usage.total * 100, 1),
        "clock_synced": clock_synced(),
        "retention_days": settings.retention_days,
        "archive_dir": settings.archive_dir,
        "data_dir": str(settings.data_dir),
    }


@router.get("/api/v1/config/export", dependencies=[Depends(_admin)])
def export_config(db: DbSession = Depends(get_session)) -> dict[str, object]:
    """Download the station's config (no accounts/secrets-in-clear)."""
    return config_backup.export_config(db)


@router.post("/api/v1/config/import", dependencies=[Depends(_admin)])
def import_config(
    body: dict[str, object], db: DbSession = Depends(get_session)
) -> dict[str, int]:
    """Restore config from a backup, replacing existing config tables."""
    return config_backup.import_config(db, body)


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
