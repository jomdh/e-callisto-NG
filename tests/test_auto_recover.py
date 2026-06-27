# SPDX-License-Identifier: AGPL-3.0-or-later
"""Opt-in auto-recover watchdog (ADR-0012 phase C): triggers the host hook on a
persistent stall, bounded by a budget, then alerts instead of looping."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlmodel import Session

from ecallisto_ng.api import db
from ecallisto_ng.api.models import Instrument, RecorderRuntime
from ecallisto_ng.api.settings import get_settings
from ecallisto_ng.services import host, recorder_state
from ecallisto_ng.services.auto_recover import AutoRecover

_NOW = datetime(2026, 6, 27, 12, 0, 0, tzinfo=UTC)


def _stalled(db_sess: Session, name: str = "AR") -> Instrument:
    inst = Instrument(name=name, channels=8, sweep_rate_hz=4.0)
    db_sess.add(inst)
    db_sess.commit()
    db_sess.refresh(inst)
    recorder_state.write(inst.id, "recording", None)
    row = db_sess.get(RecorderRuntime, inst.id)
    assert row is not None
    row.last_frame_at = _NOW - timedelta(seconds=600)  # long stale
    db_sess.add(row)
    db_sess.commit()
    return inst


def _capture_hook(calls: list[tuple[str, ...]]) -> None:
    def fake(verb: str, *args: str) -> tuple[bool, str]:
        calls.append((verb, *args))
        return True, "ok"

    host.run_hook = fake  # type: ignore[assignment]


def test_disabled_by_default_does_nothing(client: TestClient) -> None:
    get_settings.cache_clear()
    calls: list[tuple[str, ...]] = []
    orig = host.run_hook
    _capture_hook(calls)
    try:
        with Session(db.get_engine()) as s:
            inst = _stalled(s)
            AutoRecover().consider(s, inst, _NOW)
        assert calls == []  # auto_recover off -> no hook call
    finally:
        host.run_hook = orig  # type: ignore[assignment]


def test_stalled_triggers_recover_when_enabled(client: TestClient) -> None:
    os.environ["ECALLISTO_AUTO_RECOVER"] = "true"
    get_settings.cache_clear()
    calls: list[tuple[str, ...]] = []
    orig = host.run_hook
    _capture_hook(calls)
    try:
        with Session(db.get_engine()) as s:
            inst = _stalled(s)
            inst.address = "/dev/ttyUSB0"
            s.add(inst)
            s.commit()
            iid = inst.id
            AutoRecover().consider(s, inst, _NOW)
            assert calls == [("recover", str(iid), "/dev/ttyUSB0")]
    finally:
        del os.environ["ECALLISTO_AUTO_RECOVER"]
        get_settings.cache_clear()
        host.run_hook = orig  # type: ignore[assignment]


def test_fresh_heartbeat_is_not_recovered(client: TestClient) -> None:
    os.environ["ECALLISTO_AUTO_RECOVER"] = "true"
    get_settings.cache_clear()
    calls: list[tuple[str, ...]] = []
    orig = host.run_hook
    _capture_hook(calls)
    try:
        with Session(db.get_engine()) as s:
            inst = Instrument(name="OK", channels=8, sweep_rate_hz=4.0)
            s.add(inst)
            s.commit()
            s.refresh(inst)
            recorder_state.write(inst.id, "recording", None)
            recorder_state.touch_frame(inst.id)  # fresh
            AutoRecover().consider(s, inst, datetime.now(UTC))
        assert calls == []  # producing frames -> nothing to do
    finally:
        del os.environ["ECALLISTO_AUTO_RECOVER"]
        get_settings.cache_clear()
        host.run_hook = orig  # type: ignore[assignment]


def test_budget_bounds_then_alerts(client: TestClient) -> None:
    os.environ["ECALLISTO_AUTO_RECOVER"] = "true"
    os.environ["ECALLISTO_AUTO_RECOVER_BUDGET"] = "2"
    get_settings.cache_clear()
    calls: list[tuple[str, ...]] = []
    orig = host.run_hook
    _capture_hook(calls)
    sent: list[str] = []

    class _Chan:
        def send(self, subject: str, body: str) -> None:
            sent.append(subject)

    import ecallisto_ng.services.alerts as alerts_mod

    orig_enabled = alerts_mod.enabled_channels
    alerts_mod.enabled_channels = lambda rows: [_Chan()]  # type: ignore
    try:
        with Session(db.get_engine()) as s:
            inst = _stalled(s)
            ar = AutoRecover()
            # advance time slightly each tick so all land in the same window
            for i in range(5):
                ar.consider(s, inst, _NOW + timedelta(seconds=i))
        # budget=2 -> exactly 2 hook recoveries, then an alert (once)
        assert len(calls) == 2
        assert sent and "unrecoverable" in sent[0]
    finally:
        for k in ("ECALLISTO_AUTO_RECOVER", "ECALLISTO_AUTO_RECOVER_BUDGET"):
            os.environ.pop(k, None)
        get_settings.cache_clear()
        host.run_hook = orig  # type: ignore[assignment]
        alerts_mod.enabled_channels = orig_enabled  # type: ignore[assignment]


def test_scheduler_tick_invokes_auto_recover() -> None:
    # the watchdog is wired into the scheduler tick (acquire process)
    import inspect

    from ecallisto_ng.services import scheduler_service

    src = inspect.getsource(scheduler_service.SchedulerService.tick)
    assert "_auto_recover.consider" in src
