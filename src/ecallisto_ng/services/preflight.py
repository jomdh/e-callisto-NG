# SPDX-License-Identifier: AGPL-3.0-or-later
"""Station preflight checks surfaced in the UI (serial access, etc.).

A proactive check so an operator sees a permission problem *before* hitting it
at record time -- most commonly the serial port (/dev/ttyUSB*) not being
openable because the user isn't effectively in the ``dialout`` group.
"""

from __future__ import annotations


def _try_open(device: str) -> tuple[bool, str]:
    try:
        import serial
    except ImportError:  # pragma: no cover - pyserial is a dependency
        return False, "pyserial not installed"
    try:
        port = serial.Serial(device)
        port.close()
        return True, "ok"
    except Exception as exc:  # noqa: BLE001 - report any open failure
        return False, str(exc)


def serial_access() -> dict[str, object]:
    """Whether this process can open the detected serial ports.

    Returns ``status`` one of ``ok`` / ``denied`` / ``busy`` / ``none`` /
    ``error`` with a human message and per-port detail. ``denied`` means a
    permission error -- the dialout-group fix applies.
    """
    from ecallisto_ng.services.discovery import scan_serial_ports

    ports = scan_serial_ports(probe=False)
    if not ports:
        return {
            "status": "none",
            "message": "no serial ports detected",
            "ports": [],
        }

    results: list[dict[str, object]] = []
    denied = busy = ok_any = False
    for p in ports:
        ok, detail = _try_open(p.address)
        ok_any = ok_any or ok
        if not ok and "Permission denied" in detail:
            denied = True
        if not ok and ("busy" in detail or "in use" in detail):
            busy = True
        results.append({"port": p.address, "ok": ok, "detail": detail})

    if denied:
        status, message = (
            "denied",
            "serial access denied -- add the user to the 'dialout' group "
            "(sudo usermod -aG dialout <user>) then log out and back in",
        )
    elif ok_any:
        status, message = "ok", "serial ports are accessible"
    elif busy:
        status, message = "busy", "serial port is in use (recording?)"
    else:
        status, message = "error", "serial ports present but not openable"
    return {"status": status, "message": message, "ports": results}
