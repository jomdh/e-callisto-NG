# SPDX-License-Identifier: AGPL-3.0-or-later
"""First-run install wizard: multi-step, resumable (DESIGN 9).

Steps (admin -> station -> coordinates -> instrument -> review) accumulate into
a ``WizardState`` row, so a refresh or reboot resumes mid-flow. The admin
account is created only at the final step, so ``is_configured`` stays false
(the app keeps routing here) until setup is complete. An optional legacy
``callisto.cfg`` paste pre-fills the station/instrument (clone/import branch).
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session as DbSession
from sqlmodel import select

from ecallisto_ng.api import auth
from ecallisto_ng.api.db import get_session
from ecallisto_ng.api.models import Instrument, Role, Station, WizardState
from ecallisto_ng.api.setup import is_configured
from ecallisto_ng.api.templating import templates
from ecallisto_ng.services.legacy_import import parse_callisto_cfg

_STEPS = ["admin", "station", "coordinates", "instrument", "review"]
_FINAL = len(_STEPS) - 1


def _state(db: DbSession) -> WizardState:
    state = db.exec(select(WizardState)).first()
    if state is None:
        state = WizardState()
        db.add(state)
        db.commit()
        db.refresh(state)
    return state


router = APIRouter(tags=["wizard"])


@router.get("/wizard", response_class=HTMLResponse)
def wizard_page(
    request: Request, db: DbSession = Depends(get_session)
) -> object:
    if is_configured(db):
        return RedirectResponse("/", status_code=303)
    state = _state(db)
    return templates.TemplateResponse(
        request,
        "portal/wizard.html",
        {
            "step": state.step,
            "step_name": _STEPS[state.step],
            "data": json.loads(state.data_json),
            "total": len(_STEPS),
        },
    )


@router.post("/wizard")
async def wizard_submit(
    request: Request, db: DbSession = Depends(get_session)
) -> object:
    if is_configured(db):
        return RedirectResponse("/", status_code=303)
    state = _state(db)
    form = dict(await request.form())
    data = json.loads(state.data_json)

    # Legacy import branch: a pasted callisto.cfg pre-fills + jumps to review.
    cfg_text = str(form.pop("callisto_cfg", "") or "").strip()
    if cfg_text:
        cfg = parse_callisto_cfg(cfg_text)
        data.update(
            observatory=cfg.origin,
            station_name=cfg.origin or data.get("station_name", "station"),
            latitude_deg=cfg.latitude_deg,
            longitude_deg=cfg.longitude_deg,
            altitude_m=cfg.altitude_m,
            instrument_name=cfg.instrument,
        )
        state.step = _FINAL
        state.data_json = json.dumps(data)
        db.add(state)
        db.commit()
        return RedirectResponse("/wizard", status_code=303)

    data.update({k: str(v) for k, v in form.items()})

    if state.step < _FINAL:
        state.step += 1
        state.data_json = json.dumps(data)
        db.add(state)
        db.commit()
        return RedirectResponse("/wizard", status_code=303)

    return _finalize(db, data)


def _finalize(db: DbSession, data: dict[str, object]) -> object:
    username = str(data.get("admin_username", "admin"))
    password = str(data.get("admin_password", ""))
    auth.create_user(db, username, password, Role.ADMIN)

    station = db.exec(select(Station)).first() or Station()
    station.name = str(data.get("station_name", "station"))
    station.observatory = str(data.get("observatory", ""))
    station.latitude_deg = float(str(data.get("latitude_deg", 0.0) or 0.0))
    station.longitude_deg = float(str(data.get("longitude_deg", 0.0) or 0.0))
    station.altitude_m = float(str(data.get("altitude_m", 0.0) or 0.0))
    db.add(station)

    name = str(data.get("instrument_name", "")).strip()
    if name:
        db.add(
            Instrument(
                name=name,
                instrument_class=str(
                    data.get("instrument_class", "heterodyne")
                ),
                address=str(data.get("address", "")).strip(),
                channels=int(str(data.get("channels", 200) or 200)),
            )
        )

    for ws in db.exec(select(WizardState)).all():
        db.delete(ws)
    db.commit()

    resp = RedirectResponse("/portal", status_code=303)
    auth.login(db, resp, username, password)
    return resp
