"""Live streaming: WebSocket frame feed + the live-viewer page."""

from __future__ import annotations

import asyncio
from queue import Empty

from fastapi import APIRouter, Depends, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session as DbSession

from ecallisto_ng.api import auth
from ecallisto_ng.api.db import get_session
from ecallisto_ng.api.models import Instrument, User
from ecallisto_ng.api.templating import templates
from ecallisto_ng.services.hub import get_hub

router = APIRouter(tags=["live"])

_POLL_SECONDS = 0.05


@router.get("/portal/live/{instrument_id}", response_class=HTMLResponse)
def live_page(
    instrument_id: int,
    request: Request,
    user: User | None = Depends(auth.optional_user),
    db: DbSession = Depends(get_session),
) -> object:
    if user is None:
        return RedirectResponse("/", status_code=303)
    inst = db.get(Instrument, instrument_id)
    if inst is None:
        return RedirectResponse("/portal", status_code=303)
    return templates.TemplateResponse(
        request, "portal/live.html", {"instrument": inst, "user": user}
    )


@router.websocket("/ws/live/{instrument_id}")
async def ws_live(websocket: WebSocket, instrument_id: int) -> None:
    await websocket.accept()
    hub = get_hub()
    queue = hub.subscribe(instrument_id)
    try:
        while True:
            try:
                frame = queue.get_nowait()
            except Empty:
                await asyncio.sleep(_POLL_SECONDS)
                continue
            await websocket.send_json(
                {
                    "t": frame.timestamp_utc.isoformat(),
                    "values": list(frame.values),
                }
            )
    except WebSocketDisconnect:
        pass
    finally:
        hub.unsubscribe(instrument_id, queue)
