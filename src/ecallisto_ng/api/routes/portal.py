"""Server-rendered portal pages (login, dashboard)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session as DbSession
from sqlmodel import select

from ecallisto_ng.api import auth
from ecallisto_ng.api.db import get_session
from ecallisto_ng.api.models import Instrument, Station, User
from ecallisto_ng.api.setup import is_configured
from ecallisto_ng.api.templating import templates

router = APIRouter(tags=["portal"])


def _station(db: DbSession) -> Station:
    station = db.exec(select(Station)).first()
    return station or Station()


@router.get("/", response_class=HTMLResponse)
def index(
    request: Request,
    user: User | None = Depends(auth.optional_user),
    db: DbSession = Depends(get_session),
) -> object:
    if not is_configured(db):
        return RedirectResponse("/wizard", status_code=303)
    if user is not None:
        return RedirectResponse("/portal", status_code=303)
    return templates.TemplateResponse(request, "portal/login.html", {})


@router.post("/login")
def login_form(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: DbSession = Depends(get_session),
) -> object:
    resp = RedirectResponse("/portal", status_code=303)
    try:
        auth.login(db, resp, username, password)
    except HTTPException:
        return templates.TemplateResponse(
            request,
            "portal/login.html",
            {"error": "Invalid username or password."},
            status_code=401,
        )
    return resp


@router.get("/logout")
def logout_page(
    request: Request, db: DbSession = Depends(get_session)
) -> RedirectResponse:
    resp = RedirectResponse("/", status_code=303)
    auth.logout(db, request, resp)
    return resp


@router.get("/portal", response_class=HTMLResponse)
def dashboard(
    request: Request,
    user: User | None = Depends(auth.optional_user),
    db: DbSession = Depends(get_session),
) -> object:
    if user is None:
        return RedirectResponse("/", status_code=303)
    instruments = list(db.exec(select(Instrument)).all())
    return templates.TemplateResponse(
        request,
        "portal/dashboard.html",
        {"user": user, "station": _station(db), "instruments": instruments},
    )


# Resources surfaced by the generic management console (must match console.js).
_MANAGE = {
    "instruments": "Instruments",
    "schedules": "Schedules",
    "programs": "Frequency programs",
    "calibration": "Calibration sets",
    "uploads": "Upload targets",
    "peers": "Fleet peers",
    "users": "Users",
}


@router.get("/portal/manage/{resource}", response_class=HTMLResponse)
def manage(
    request: Request,
    resource: str,
    user: User | None = Depends(auth.optional_user),
) -> object:
    if user is None:
        return RedirectResponse("/", status_code=303)
    if resource not in _MANAGE:
        raise HTTPException(404, "no such section")
    return templates.TemplateResponse(
        request,
        "portal/manage.html",
        {"user": user, "resource": resource, "title": _MANAGE[resource]},
    )


def _page(request: Request, name: str, user: User | None) -> object:
    if user is None:
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(
        request, f"portal/{name}.html", {"user": user}
    )


@router.get("/portal/access", response_class=HTMLResponse)
def access_page(
    request: Request, user: User | None = Depends(auth.optional_user)
) -> object:
    return _page(request, "access", user)


@router.get("/portal/import", response_class=HTMLResponse)
def import_page(
    request: Request, user: User | None = Depends(auth.optional_user)
) -> object:
    return _page(request, "import", user)


@router.get("/portal/fleet", response_class=HTMLResponse)
def fleet_page(
    request: Request, user: User | None = Depends(auth.optional_user)
) -> object:
    return _page(request, "fleet", user)


@router.get("/portal/tools", response_class=HTMLResponse)
def tools_page(
    request: Request, user: User | None = Depends(auth.optional_user)
) -> object:
    return _page(request, "tools", user)


@router.get("/portal/viewer", response_class=HTMLResponse)
def viewer_page(
    request: Request, user: User | None = Depends(auth.optional_user)
) -> object:
    return _page(request, "viewer", user)


@router.get("/portal/audit", response_class=HTMLResponse)
def audit_page(
    request: Request, user: User | None = Depends(auth.optional_user)
) -> object:
    return _page(request, "audit", user)
