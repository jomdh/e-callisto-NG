# SPDX-License-Identifier: AGPL-3.0-or-later
"""Live streaming: WebSocket frame feed + the live-viewer page."""

from __future__ import annotations

import asyncio
import time
from queue import Empty

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import RedirectResponse

from ecallisto_ng.api import auth
from ecallisto_ng.api.models import User
from ecallisto_ng.api.settings import get_settings
from ecallisto_ng.services.hub import get_hub

router = APIRouter(tags=["live"])

_POLL_SECONDS = 0.05


@router.get("/portal/live/{instrument_id}")
def live_page(
    instrument_id: int,
    user: User | None = Depends(auth.optional_user),
) -> object:
    # The live viewer is now the workspace's Live tab (ADR-0011); keep this
    # path working for bookmarks/links by redirecting into the workspace.
    if user is None:
        return RedirectResponse("/", status_code=303)
    return RedirectResponse(
        f"/portal/instruments/{instrument_id}#live", status_code=303
    )


@router.websocket("/ws/live/{instrument_id}")
async def ws_live(websocket: WebSocket, instrument_id: int) -> None:
    await websocket.accept()
    hub = get_hub()
    queue = hub.subscribe(instrument_id)
    # Surface liveness to the browser: when no frame arrives for the stall
    # grace, emit a status message so the panel shows "not responding" instead
    # of a frozen/blank canvas (ADR-0012). Self-contained -- driven by how
    # recently this connection saw a frame, no DB read in the hot loop.
    grace = get_settings().stall_grace_seconds
    last_frame = time.monotonic()
    sent_state: str | None = None

    async def emit_status() -> None:
        nonlocal sent_state
        cur = "stalled" if (time.monotonic() - last_frame) > grace else "live"
        if cur != sent_state:
            sent_state = cur
            await websocket.send_json({"type": "status", "state": cur})

    try:
        while True:
            try:
                frame = queue.get_nowait()
            except Empty:
                await emit_status()
                await asyncio.sleep(_POLL_SECONDS)
                continue
            last_frame = time.monotonic()
            await emit_status()
            await websocket.send_json(
                {
                    "type": "frame",
                    "t": frame.timestamp_utc.isoformat(),
                    "values": list(frame.values),
                }
            )
    except (WebSocketDisconnect, asyncio.CancelledError):
        # normal: the browser left the live view (uvicorn cancels the task
        # mid-sleep/-send). Clean up quietly instead of dumping a traceback.
        pass
    finally:
        hub.unsubscribe(instrument_id, queue)
