"""First-run install wizard (MVP)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session as DbSession
from sqlmodel import select

from ecallisto_ng.api import auth
from ecallisto_ng.api.db import get_session
from ecallisto_ng.api.models import Instrument, Role, Station
from ecallisto_ng.api.setup import is_configured
from ecallisto_ng.api.templating import templates

router = APIRouter(tags=["wizard"])


@router.get("/wizard", response_class=HTMLResponse)
def wizard_page(
    request: Request, db: DbSession = Depends(get_session)
) -> object:
    if is_configured(db):
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(request, "portal/wizard.html", {})


@router.post("/wizard")
def wizard_submit(
    request: Request,
    admin_username: str = Form(...),
    admin_password: str = Form(...),
    station_name: str = Form("station"),
    observatory: str = Form(""),
    latitude_deg: float = Form(0.0),
    longitude_deg: float = Form(0.0),
    altitude_m: float = Form(0.0),
    instrument_name: str = Form(""),
    channels: int = Form(200),
    db: DbSession = Depends(get_session),
) -> object:
    if is_configured(db):
        return RedirectResponse("/", status_code=303)

    auth.create_user(db, admin_username, admin_password, Role.ADMIN)

    station = db.exec(select(Station)).first() or Station()
    station.name = station_name
    station.observatory = observatory
    station.latitude_deg = latitude_deg
    station.longitude_deg = longitude_deg
    station.altitude_m = altitude_m
    db.add(station)

    if instrument_name.strip():
        db.add(Instrument(name=instrument_name.strip(), channels=channels))
    db.commit()

    resp = RedirectResponse("/portal", status_code=303)
    auth.login(db, resp, admin_username, admin_password)
    return resp
