"""Host-action hook + log viewer + audited endpoints (M21 / ADR-0008)."""

from __future__ import annotations

import os
import stat
from pathlib import Path

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from ecallisto_ng.api import auth, db
from ecallisto_ng.api.models import AuditEvent, Role
from ecallisto_ng.api.settings import get_settings
from ecallisto_ng.services import host


def test_run_hook_disabled_by_default() -> None:
    get_settings.cache_clear()
    ok, msg = host.run_hook("reboot")
    assert ok is False
    assert "not configured" in msg


def test_run_hook_rejects_unknown_verb() -> None:
    ok, msg = host.run_hook("rm -rf")  # not in the closed verb set
    assert ok is False and "unknown host action" in msg


def _fake_hook(tmp_path: Path) -> Path:
    record = tmp_path / "hook.log"
    script = tmp_path / "hook.sh"
    script.write_text(
        "#!/bin/sh\n" f'echo "$@" >> "{record}"\n' 'echo "did $1"\n'
    )
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return script


def test_run_hook_invokes_with_verb(tmp_path: Path) -> None:
    script = _fake_hook(tmp_path)
    os.environ["ECALLISTO_HOST_HOOK"] = str(script)
    get_settings.cache_clear()
    try:
        ok, msg = host.run_hook("reconnect", "3")
        assert ok is True
        assert "did reconnect" in msg
        assert "reconnect 3" in (tmp_path / "hook.log").read_text()
    finally:
        del os.environ["ECALLISTO_HOST_HOOK"]
        get_settings.cache_clear()


def test_tail_log(tmp_path: Path) -> None:
    f = tmp_path / "app.log"
    f.write_text("".join(f"line {i}\n" for i in range(10)))
    os.environ["ECALLISTO_LOG_FILE"] = str(f)
    get_settings.cache_clear()
    try:
        lines = host.tail_log(3)
        assert lines == ["line 7\n", "line 8\n", "line 9\n"]
    finally:
        del os.environ["ECALLISTO_LOG_FILE"]
        get_settings.cache_clear()


def _admin(client: TestClient) -> None:
    with Session(db.get_engine()) as s:
        auth.create_user(s, "boss", "host-pass-12", Role.ADMIN)
    client.post(
        "/api/v1/auth/login",
        json={"username": "boss", "password": "host-pass-12"},
    )


def test_reboot_endpoint_disabled_but_audited(client: TestClient) -> None:
    _admin(client)
    res = client.post("/api/v1/system/reboot").json()
    assert res["ok"] is False  # no hook configured
    with Session(db.get_engine()) as s:
        actions = [e.action for e in s.exec(select(AuditEvent)).all()]
        assert "host.reboot" in actions


def test_reboot_admin_only(client: TestClient) -> None:
    with Session(db.get_engine()) as s:
        auth.create_user(s, "op", "op-pass-12345", Role.OPERATOR)
    client.post(
        "/api/v1/auth/login",
        json={"username": "op", "password": "op-pass-12345"},
    )
    assert client.post("/api/v1/system/reboot").status_code == 403


def test_log_endpoint(client: TestClient) -> None:
    _admin(client)
    body = client.get("/api/v1/system/log").json()
    assert "lines" in body  # not configured -> a hint line


def test_system_page_has_host_controls(client: TestClient) -> None:
    _admin(client)
    page = client.get("/portal/system")
    assert "host-reboot" in page.text
    assert "/static/js/system.js" in page.text
