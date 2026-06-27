# SPDX-License-Identifier: AGPL-3.0-or-later
"""Host operations behind a least-privilege hook (ADR-0008, DESIGN 8.4/15).

The web process is unprivileged. Host actions shell out to the single
configured ``host_hook`` command with a **fixed verb** + validated args, never
an arbitrary command. Disabled (and clearly so) when no hook is configured. Log
viewing tails a configured file read-only, no hook needed.
"""

from __future__ import annotations

import shlex
import subprocess
from collections import deque
from pathlib import Path

from ecallisto_ng.api.settings import get_settings

# The closed set of host verbs the hook accepts. "recover" walks the USB
# recovery ladder for one instrument (ADR-0012); "reconnect" is its alias.
_VERBS = {"recover", "reconnect", "reboot", "shutdown", "update", "rollback"}


def tail_log(lines: int = 200) -> list[str]:
    """Last ``lines`` of the configured ``log_file`` (read-only)."""
    path_str = get_settings().log_file
    if not path_str:
        return ["(no log_file configured)"]
    path = Path(path_str)
    if not path.is_file():
        return [f"(log file not found: {path})"]
    with path.open("r", errors="replace") as fh:
        return list(deque(fh, maxlen=max(1, lines)))


def run_hook(verb: str, *args: str) -> tuple[bool, str]:
    """Invoke ``<host_hook> <verb> [args]``; return (ok, message).

    The verb must be in the closed set; the hook must be configured.
    """
    if verb not in _VERBS:
        return False, f"unknown host action: {verb}"
    hook = get_settings().host_hook
    if not hook:
        return False, "host actions not configured (set host_hook)"
    cmd = [*shlex.split(hook), verb, *[str(a) for a in args]]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except Exception as exc:  # noqa: BLE001 - report any hook failure
        return False, f"{type(exc).__name__}: {exc}"
    out = (proc.stdout or proc.stderr or "").strip()
    return proc.returncode == 0, out or f"exit {proc.returncode}"
