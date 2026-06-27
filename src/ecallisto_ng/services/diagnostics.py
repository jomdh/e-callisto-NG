# SPDX-License-Identifier: AGPL-3.0-or-later
"""Station self-check: surface parasitic processes, wedged recordings, and the
operational state an operator (or the dev team) needs to troubleshoot.

Read-only and unprivileged -- process/port inspection via ``/proc``, service
state via ``systemctl show``. Every probe degrades to a ``warn`` rather than
raising, so the report is always produced.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime

from sqlmodel import Session, select

from ecallisto_ng.api.models import Instrument
from ecallisto_ng.api.settings import get_settings
from ecallisto_ng.services import recorder_state

OK, WARN, FAIL = "ok", "warn", "fail"
_RANK = {OK: 0, WARN: 1, FAIL: 2}


@dataclass
class Check:
    name: str
    status: str
    detail: str


def _procs() -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        try:
            with open(f"/proc/{pid}/cmdline", "rb") as fh:
                cmd = (
                    fh.read()
                    .replace(b"\0", b" ")
                    .decode("utf-8", "replace")
                    .strip()
                )
        except OSError:
            continue
        if cmd:
            out.append((int(pid), cmd))
    return out


def _check_processes() -> Check:
    """Exactly one web (+ one acquire in two-process mode); flag duplicates."""
    try:
        procs = _procs()
    except OSError:
        return Check(
            "processes", WARN, "process list unavailable on this host"
        )
    web = [p for p, c in procs if "uvicorn" in c and "ecallisto" in c]
    acq = [p for p, c in procs if "ecallisto-ng acquire" in c]
    want_acq = 0 if get_settings().run_loops_in_web else 1
    issues = []
    if len(web) > 1:
        issues.append(f"{len(web)} web processes (parasitic/orphan? expect 1)")
    if not web:
        issues.append("no web process found")
    if len(acq) > want_acq:
        issues.append(f"{len(acq)} acquire daemons (expect {want_acq})")
    if want_acq and not acq:
        issues.append("acquire daemon not running")
    status = WARN if issues else OK
    detail = "; ".join(issues) or f"{len(web)} web, {len(acq)} acquire -- ok"
    return Check("processes", status, detail)


def _device_holders(device: str) -> list[int]:
    holders: list[int] = []
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        fdd = f"/proc/{pid}/fd"
        try:
            for fd in os.listdir(fdd):
                try:
                    if os.readlink(f"{fdd}/{fd}") == device:
                        holders.append(int(pid))
                        break
                except OSError:
                    continue
        except OSError:
            continue
    return holders


def _check_serial_ports(db: Session) -> list[Check]:
    checks: list[Check] = []
    insts = db.exec(
        select(Instrument).where(Instrument.instrument_class == "heterodyne")
    ).all()
    for inst in insts:
        dev = inst.address
        if not dev or not dev.startswith("/dev/"):
            continue
        if not os.path.exists(dev):
            checks.append(Check(f"serial:{dev}", WARN, "device not present"))
            continue
        try:
            holders = _device_holders(dev)
        except OSError:
            checks.append(Check(f"serial:{dev}", WARN, "cannot inspect"))
            continue
        if len(holders) > 1:
            checks.append(
                Check(
                    f"serial:{dev}",
                    FAIL,
                    f"{len(holders)} processes hold the port (contention) "
                    f"pids {holders}",
                )
            )
        else:
            checks.append(
                Check(f"serial:{dev}", OK, "1 holder" if holders else "free")
            )
    return checks


def _newest_data_age_s(name: str) -> float | None:
    """Seconds since the newest ``{name}_*.fit`` was written, or None.

    The ground truth for 'is it actually producing data' -- unlike
    RecorderRuntime.updated_at, a wedged-but-cycling recording can't touch the
    filesystem, so a stale newest-file reliably reveals a wedge.
    """
    data = get_settings().data_dir
    newest = 0.0
    try:
        for p in data.glob(f"{name}_*.fit"):
            try:
                m = p.stat().st_mtime
            except OSError:
                continue
            newest = max(newest, m)
    except OSError:
        return None
    return (time.time() - newest) if newest else None


def _check_recorder_liveness(db: Session) -> list[Check]:
    """Is a 'recording' instrument actually producing frames?

    The frame heartbeat (last_frame_at, ADR-0012) is the primary, near-live
    signal -- unlike file age, which the in-RAM file buffer makes minutes-stale
    even when healthy. File age is kept only as a fallback for a run that has
    not stamped a heartbeat yet (just started, or an older deployment).
    """
    from ecallisto_ng.services import liveness

    checks: list[Check] = []
    for rt in recorder_state.read(db).values():
        key = f"recorder:{rt.instrument_id}"
        if rt.state == "error":
            checks.append(Check(key, WARN, "last run ended in error"))
            continue
        if rt.state != "recording":
            continue
        inst = db.get(Instrument, rt.instrument_id)
        rate = inst.sweep_rate_hz if inst else 4.0
        frame_age = liveness.frame_age_seconds(rt)
        if liveness.is_stalled(rt, rate):
            shown = int(frame_age) if frame_age is not None else "?"
            checks.append(
                Check(
                    key,
                    WARN,
                    f"recording but no frame for {shown}s (STALLED -- "
                    "recover the receiver)",
                )
            )
        elif frame_age is not None:
            checks.append(
                Check(key, OK, f"recording, last frame {int(frame_age)}s ago")
            )
        else:
            # No heartbeat yet -- fall back to the file-age proxy.
            period = inst.file_seconds if inst else 900
            age = _newest_data_age_s(inst.name) if inst else None
            if age is None:
                checks.append(
                    Check(key, OK, "recording, awaiting first frame")
                )
            elif age > period * 1.5 + 120:
                checks.append(
                    Check(
                        key,
                        WARN,
                        f"recording but newest file is {int(age // 60)} min "
                        "old (wedged -- recover the receiver?)",
                    )
                )
            else:
                checks.append(
                    Check(
                        key, OK, f"recording, newest file {int(age//60)}m ago"
                    )
                )
    return checks


def _service_show(unit: str) -> dict[str, str] | None:
    try:
        res = subprocess.run(
            [
                "systemctl",
                "show",
                "-p",
                "ActiveState,SubState,NRestarts",
                unit,
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if res.returncode != 0:
        return None
    return dict(
        line.split("=", 1) for line in res.stdout.splitlines() if "=" in line
    )


def _check_services() -> list[Check]:
    checks: list[Check] = []
    for unit in ("ecallisto-web", "ecallisto-acquire"):
        info = _service_show(unit)
        if info is None:
            checks.append(Check(f"service:{unit}", OK, "not managed here"))
            continue
        active = info.get("ActiveState", "?")
        restarts = int(info.get("NRestarts", "0") or 0)
        if active != "active":
            checks.append(Check(f"service:{unit}", FAIL, f"state {active}"))
        elif restarts > 5:
            checks.append(
                Check(
                    f"service:{unit}",
                    WARN,
                    f"active but {restarts} restarts (crash-looping?)",
                )
            )
        else:
            checks.append(
                Check(f"service:{unit}", OK, f"active, {restarts} restarts")
            )
    return checks


def _check_clock() -> Check:
    from ecallisto_ng.services.clock import clock_offset_ms, clock_synced

    synced = clock_synced()
    if synced is None:
        return Check("clock", OK, "no chrony probe (assumed ok)")
    if not synced:
        return Check("clock", WARN, "clock not NTP-synced")
    offset = clock_offset_ms()
    return Check(
        "clock",
        OK,
        f"synced{f', offset {offset:.0f} ms' if offset is not None else ''}",
    )


def _check_disk() -> Check:
    data = get_settings().data_dir
    try:
        data.mkdir(parents=True, exist_ok=True)
        usage = shutil.disk_usage(data)
    except OSError as exc:
        return Check("disk", FAIL, f"data dir unusable: {exc}")
    free_gb = usage.free / 1e9
    pct = usage.free / usage.total * 100 if usage.total else 0
    if free_gb < 1.0:
        return Check("disk", FAIL, f"only {free_gb:.1f} GB free")
    if pct < 10:
        return Check("disk", WARN, f"{free_gb:.1f} GB free ({pct:.0f}%)")
    return Check("disk", OK, f"{free_gb:.1f} GB free ({pct:.0f}%)")


def run_self_check(db: Session) -> dict[str, object]:
    """Run every probe; return an overall status + per-check results."""
    checks: list[Check] = [_check_processes()]
    checks += _check_serial_ports(db)
    checks += _check_recorder_liveness(db)
    checks += _check_services()
    checks.append(_check_clock())
    checks.append(_check_disk())
    overall = OK
    for c in checks:
        if _RANK[c.status] > _RANK[overall]:
            overall = c.status
    return {
        "status": overall,
        "generated_utc": datetime.now(UTC).isoformat(),
        "checks": [asdict(c) for c in checks],
    }
