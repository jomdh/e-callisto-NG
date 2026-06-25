"""System health endpoint + page."""

from __future__ import annotations

import shutil

from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from sqlmodel import Session as DbSession

from ecallisto_ng import __version__
from ecallisto_ng.api import auth
from ecallisto_ng.api.auth import require_role
from ecallisto_ng.api.db import get_session
from ecallisto_ng.api.models import Role, User
from ecallisto_ng.api.settings import get_settings
from ecallisto_ng.api.templating import templates
from ecallisto_ng.services import config_backup, support_bundle, updates
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


@router.get("/api/v1/operations", dependencies=[Depends(_viewer)])
def operations(db: DbSession = Depends(get_session)) -> dict[str, object]:
    """Per-instrument cockpit + station vitals (DESIGN 8.1)."""
    from datetime import UTC, datetime

    from ecallisto_ng.services.operations import instrument_cockpit

    report = build_station_health(db)
    return {
        "instruments": instrument_cockpit(db, datetime.now(UTC)),
        "disk_pct_free": report.disk_pct_free,
        "clock_synced": clock_synced(),
    }


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


@router.get("/api/v1/system/update", dependencies=[Depends(_viewer)])
def update_status() -> dict[str, str]:
    """Current version + the channel this station tracks (DESIGN 15)."""
    return updates.update_info(get_settings().update_channel)


@router.get("/api/v1/system/time", dependencies=[Depends(_viewer)])
def system_time() -> dict[str, object]:
    """Active time source: name, lock, offset (DESIGN 12a / ADR-0009)."""
    from ecallisto_ng.services.timing import get_time_source

    src = get_time_source(get_settings().time_source)
    return {
        "source": src.name,
        "locked": src.locked(),
        "offset_ms": src.offset_ms(),
        "now": src.now().isoformat(),
    }


@router.get("/api/v1/system/log", dependencies=[Depends(_admin)])
def system_log(lines: int = 200) -> dict[str, list[str]]:
    """Tail the configured log file (read-only, ADR-0008)."""
    from ecallisto_ng.services import host

    return {"lines": host.tail_log(lines)}


def _host_action(
    db: DbSession, actor: User, verb: str, *args: str
) -> dict[str, object]:
    from ecallisto_ng.services import audit, host

    ok, message = host.run_hook(verb, *args)
    audit.record(
        db, actor.username, f"host.{verb}", detail="ok" if ok else message
    )
    return {"ok": ok, "message": message}


@router.post("/api/v1/system/reboot")
def host_reboot(
    db: DbSession = Depends(get_session), actor: User = Depends(_admin)
) -> dict[str, object]:
    return _host_action(db, actor, "reboot")


@router.post("/api/v1/system/shutdown")
def host_shutdown(
    db: DbSession = Depends(get_session), actor: User = Depends(_admin)
) -> dict[str, object]:
    return _host_action(db, actor, "shutdown")


@router.post("/api/v1/system/update/apply")
def host_update_apply(
    db: DbSession = Depends(get_session), actor: User = Depends(_admin)
) -> dict[str, object]:
    return _host_action(db, actor, "update", get_settings().update_channel)


@router.post("/api/v1/system/update/rollback")
def host_update_rollback(
    db: DbSession = Depends(get_session), actor: User = Depends(_admin)
) -> dict[str, object]:
    return _host_action(db, actor, "rollback")


@router.get("/api/v1/system/support-bundle", dependencies=[Depends(_admin)])
def support_bundle_download(
    db: DbSession = Depends(get_session),
) -> FileResponse:
    """Download a redacted support bundle (no secrets)."""
    settings = get_settings()
    out_dir = settings.data_dir / "support"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = support_bundle.build_support_bundle(
        db,
        out_dir / "support-bundle.zip",
        __version__,
        system_info(),
    )
    return FileResponse(
        path, media_type="application/zip", filename="support-bundle.zip"
    )


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
