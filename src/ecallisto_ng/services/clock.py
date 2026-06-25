"""Best-effort NTP clock-sync probe (DESIGN 12a).

Queries ``timedatectl`` for the real sync state. Returns a tri-state:
True/False when known, None when undeterminable (e.g. ``timedatectl``
absent, as on non-systemd hosts). Timing is scientific data, so the probe
feeds health and an optional recording gate.
"""

from __future__ import annotations

import shutil
import subprocess


def clock_synced() -> bool | None:
    """True/False if NTP sync is known; None if undeterminable."""
    if shutil.which("timedatectl") is None:
        return None
    try:
        out = subprocess.run(
            ["timedatectl", "show", "-p", "NTPSynchronized", "--value"],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:  # noqa: BLE001 - any probe failure -> unknown
        return None
    value = out.stdout.strip().lower()
    if value == "yes":
        return True
    if value == "no":
        return False
    return None


def may_record(require_sync: bool, synced: bool | None) -> bool:
    """Recording gate: block only when sync is *required* and known-bad."""
    if require_sync and synced is False:
        return False
    return True
