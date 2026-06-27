# SPDX-License-Identifier: AGPL-3.0-or-later
"""Remote instrument recovery (ADR-0012): the audited recover endpoint, the
host-hook USB ladder script, the opt-in settings, and the install wiring."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from ecallisto_ng.api import auth, db
from ecallisto_ng.api.models import AuditEvent, Role
from ecallisto_ng.api.settings import get_settings
from ecallisto_ng.services import host

_ROOT = Path(__file__).resolve().parents[1]
_HOOK = _ROOT / "packaging" / "hook" / "ecallisto-hook"


def _login(client: TestClient) -> None:
    with Session(db.get_engine()) as s:
        auth.create_user(s, "rec-op", "rec-pass-12345", Role.OPERATOR)
    client.post(
        "/api/v1/auth/login",
        json={"username": "rec-op", "password": "rec-pass-12345"},
    )


# --- the closed verb set + the audited endpoint --------------------------


def test_recover_is_in_closed_verb_set() -> None:
    assert "recover" in host._VERBS


def test_recover_endpoint_calls_hook_with_device_and_audits(
    client: TestClient, tmp_path: Path
) -> None:
    # a fake hook that records its argv; the endpoint must send the recover
    # verb + the instrument's device path, and audit host.recover.
    log = tmp_path / "argv.log"
    script = tmp_path / "hook.sh"
    script.write_text(f'#!/bin/sh\necho "$@" >> "{log}"\necho ok\n')
    script.chmod(0o755)
    os.environ["ECALLISTO_HOST_HOOK"] = str(script)
    get_settings.cache_clear()
    try:
        _login(client)
        iid = client.post(
            "/api/v1/instruments",
            json={
                "name": "RECCAL",
                "instrument_class": "heterodyne",
                "address": "/dev/ttyUSB0",
            },
        ).json()["id"]
        res = client.post(f"/api/v1/instruments/{iid}/reconnect").json()
        assert res["ok"] is True
        assert f"recover {iid} /dev/ttyUSB0" in log.read_text()
        with Session(db.get_engine()) as s:
            actions = [e.action for e in s.exec(select(AuditEvent)).all()]
            assert "host.recover" in actions
    finally:
        del os.environ["ECALLISTO_HOST_HOOK"]
        get_settings.cache_clear()


def test_recover_endpoint_omits_device_when_address_empty(
    client: TestClient, tmp_path: Path
) -> None:
    # no address -> the hook is asked to discover the Callisto itself.
    log = tmp_path / "argv.log"
    script = tmp_path / "hook.sh"
    script.write_text(f'#!/bin/sh\necho "$@" >> "{log}"\necho ok\n')
    script.chmod(0o755)
    os.environ["ECALLISTO_HOST_HOOK"] = str(script)
    get_settings.cache_clear()
    try:
        _login(client)
        iid = client.post(
            "/api/v1/instruments",
            json={"name": "NOADDR", "instrument_class": "heterodyne"},
        ).json()["id"]
        client.post(f"/api/v1/instruments/{iid}/reconnect")
        assert log.read_text().strip() == f"recover {iid}"
    finally:
        del os.environ["ECALLISTO_HOST_HOOK"]
        get_settings.cache_clear()


# --- the hook script: USB topology resolution ----------------------------


def _fixture_sysfs(tmp_path: Path, usbname: str, vid: str = "067b") -> Path:
    """A minimal sysfs tree: ttyUSB0 -> a USB device dir named `usbname`."""
    sysfs = tmp_path / "sys"
    devdir = sysfs / "bus" / "usb" / "devices" / usbname
    devdir.mkdir(parents=True)
    (devdir / "idVendor").write_text(vid + "\n")
    (devdir / "idProduct").write_text("2303\n")
    (devdir / "authorized").write_text("1\n")  # writable -> re-enumerate works
    tty = sysfs / "class" / "tty" / "ttyUSB0"
    tty.mkdir(parents=True)
    rel = os.path.relpath(devdir, tty)
    (tty / "device").symlink_to(rel)
    return sysfs


def _run_hook(
    args: list[str], sysfs: Path, dev: Path
) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "SYSFS_ROOT": str(sysfs), "DEV_ROOT": str(dev)}
    return subprocess.run(
        [str(_HOOK), *args], capture_output=True, text=True, env=env
    )


def test_hook_resolves_device_behind_a_hub(tmp_path: Path) -> None:
    sysfs = _fixture_sysfs(tmp_path, "2-1.1")
    out = _run_hook(["resolve", "/dev/ttyUSB0"], sysfs, tmp_path / "dev")
    assert out.stdout.strip() == "2-1 1"  # hub 2-1, port 1


def test_hook_resolves_device_on_root_hub_port(tmp_path: Path) -> None:
    sysfs = _fixture_sysfs(tmp_path, "2-1")
    out = _run_hook(["resolve", "/dev/ttyUSB0"], sysfs, tmp_path / "dev")
    assert out.stdout.strip() == "2 1"  # bus 2 (root hub), port 1


def test_hook_recover_reports_when_no_device(tmp_path: Path) -> None:
    empty = tmp_path / "sys"
    (empty / "class" / "tty").mkdir(parents=True)
    out = _run_hook(["recover", "7"], empty, tmp_path / "dev")
    assert out.returncode != 0
    assert "no Callisto device found" in out.stdout


def test_hook_recover_is_honest_when_vbus_unavailable(tmp_path: Path) -> None:
    # On a hub without per-port power switching (uhubctl absent here stands in
    # for that), the hook must NOT claim a power-cycle/"ok" -- it re-enumerates
    # and says VBUS cut was unavailable. The caller judges real recovery via
    # the heartbeat, not this exit code.
    sysfs = _fixture_sysfs(tmp_path, "2-1.1")
    out = subprocess.run(
        [str(_HOOK), "recover", "3", "/dev/ttyUSB0"],
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "SYSFS_ROOT": str(sysfs),
            "DEV_ROOT": str(tmp_path / "dev"),
            "REENUM_SETTLE_S": "0",
            "UHUBCTL": "/nonexistent/uhubctl",  # stand in for a no-PPPS hub
        },
    )
    assert "VBUS cut unavailable" in out.stdout
    assert "power-cycled" not in out.stdout  # no false success
    assert "re-enumerated via sysfs" in out.stdout


def test_hook_rejects_unknown_verb(tmp_path: Path) -> None:
    out = _run_hook(["frobnicate"], tmp_path, tmp_path)
    assert out.returncode == 64
    assert "unknown verb" in out.stdout


# --- opt-in defaults + install wiring ------------------------------------


def test_auto_recover_defaults_off() -> None:
    get_settings.cache_clear()
    s = get_settings()
    assert s.auto_recover is False  # automated power-cycles are opt-in
    assert s.auto_recover_budget >= 1  # but bounded when enabled


def test_hook_script_is_executable() -> None:
    assert _HOOK.exists()
    assert os.access(_HOOK, os.X_OK)


def test_installer_wires_hook_and_sudoers() -> None:
    install = (_ROOT / "scripts" / "install.sh").read_text()
    assert "/usr/local/sbin/ecallisto-hook" in install
    assert "/etc/sudoers.d/ecallisto-hook" in install
    assert "visudo -c" in install  # validated before install (no lockout)
    assert "NOPASSWD" in install
