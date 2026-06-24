"""Live frame hub + WebSocket streaming."""

from __future__ import annotations

from datetime import UTC, datetime
from queue import Empty

from fastapi.testclient import TestClient
from sqlmodel import Session

from ecallisto_ng.api import auth, db
from ecallisto_ng.api.models import Role
from ecallisto_ng.core.spectra import SpectrumFrame
from ecallisto_ng.services.hub import FrameHub


def _frame(v: int) -> SpectrumFrame:
    return SpectrumFrame(
        timestamp_utc=datetime(2026, 6, 25, tzinfo=UTC),
        monotonic_ns=v,
        values=(v, v + 1, v + 2),
    )


def test_hub_pubsub_and_drop() -> None:
    hub = FrameHub()
    q = hub.subscribe(7)
    hub.publish(7, _frame(10))
    assert q.get_nowait().values == (10, 11, 12)
    hub.unsubscribe(7, q)
    # no subscribers -> publish is a no-op, no error
    hub.publish(7, _frame(0))


def test_hub_isolates_instruments() -> None:
    hub = FrameHub()
    q1 = hub.subscribe(1)
    q2 = hub.subscribe(2)
    hub.publish(1, _frame(5))
    assert q1.get_nowait().values[0] == 5
    try:
        q2.get_nowait()
    except Empty:
        return
    raise AssertionError("frame leaked across instruments")


def test_ws_streams_live_recording(client: TestClient) -> None:
    with Session(db.get_engine()) as s:
        auth.create_user(s, "op", "live-pass-1234", Role.OPERATOR)
    client.post(
        "/api/v1/auth/login",
        json={"username": "op", "password": "live-pass-1234"},
    )
    iid = client.post(
        "/api/v1/instruments", json={"name": "LIVE", "channels": 8}
    ).json()["id"]

    with client.websocket_connect(f"/ws/live/{iid}") as ws:
        client.post(f"/api/v1/instruments/{iid}/record?frames=15")
        msg = ws.receive_json()
        assert "values" in msg and len(msg["values"]) == 8
        assert "t" in msg
