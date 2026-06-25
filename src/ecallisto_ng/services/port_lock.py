# SPDX-License-Identifier: AGPL-3.0-or-later
"""Cross-process, per-instrument serial-port lock.

One physical device, one operation at a time -- across processes. Record,
overview, diagnose, and bench all open the same serial port; two at once
collide (pyserial: "device reports readiness ... but returned no data ... multi
access on port"). On a station the **web** and the **acquire daemon** are
separate processes (ADR-0007), so a plain ``threading.Lock`` is not enough.

This uses ``flock`` on a per-instrument lock file under the data dir, which
serializes both threads (independent fds) and processes. A second holder gets a
clean ``InstrumentBusy`` instead of a corrupt read.
"""

from __future__ import annotations

import fcntl
import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from ecallisto_ng.api.settings import get_settings


class InstrumentBusy(Exception):
    """Raised when the instrument's port is already in use."""


def _lock_path(instrument_id: int) -> Path:
    locks = get_settings().data_dir / ".locks"
    locks.mkdir(parents=True, exist_ok=True)
    return locks / f"instrument-{instrument_id}.lock"


@contextmanager
def hold(instrument_id: int) -> Iterator[None]:
    """Hold the instrument's port for the duration, or raise InstrumentBusy."""
    fd = os.open(str(_lock_path(instrument_id)), os.O_CREAT | os.O_RDWR, 0o644)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise InstrumentBusy(instrument_id) from exc
        try:
            yield
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)


def is_busy(instrument_id: int) -> bool:
    """True if another thread/process currently holds the instrument's port."""
    fd = os.open(str(_lock_path(instrument_id)), os.O_CREAT | os.O_RDWR, 0o644)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            return True
        fcntl.flock(fd, fcntl.LOCK_UN)
        return False
    finally:
        os.close(fd)
