# SPDX-License-Identifier: AGPL-3.0-or-later
"""Opt-in automated remote recovery (ADR-0012, phase C).

When a recording instrument goes STALLED past the driver's own self-heal, the
acquire daemon can invoke the host hook to recover it (USB re-enumerate +
power-cycle) -- closing the loop for an unattended remote station. This is
**off by default** (``auto_recover``): it needs a configured ``host_hook`` and
a deliberate operator choice, because a power-cycle is intrusive. It is also
**bounded** -- after ``auto_recover_budget`` attempts in a window it stops and
**alerts** instead of looping power-cycles forever, so a dead receiver
escalates to a human rather than thrashing.

Recovery is triggered by the frame heartbeat going stale (liveness), not by the
``recording``/``error`` state label, so it is robust to the recorder flapping
between rebuild attempts.
"""

from __future__ import annotations

import logging
from collections import deque
from datetime import datetime

from sqlmodel import Session, select

from ecallisto_ng.api.models import Instrument, RecorderRuntime
from ecallisto_ng.api.settings import get_settings
from ecallisto_ng.services import liveness

_log = logging.getLogger(__name__)


class AutoRecover:
    """Per-instrument stall watchdog with a bounded recovery budget."""

    def __init__(self) -> None:
        self._history: dict[int, deque[float]] = {}
        self._alerted: set[int] = set()

    def consider(self, db: Session, inst: Instrument, now: datetime) -> None:
        """Recover ``inst`` if it is meant to be recording but frames stopped.

        Call once per tick for each instrument that *should* be recording (the
        caller has already confirmed intent + clock gate). A no-op unless
        ``auto_recover`` is enabled.
        """
        settings = get_settings()
        if not settings.auto_recover or inst.id is None:
            return
        row = db.get(RecorderRuntime, inst.id)
        if row is None:
            return
        age = liveness.frame_age_seconds(row, now)
        if age is None:  # no frame yet -> measure from when it went recording
            age = (now - _aware(row.updated_at, now)).total_seconds()
        bound = liveness.stall_bound_seconds(inst.sweep_rate_hz)
        if age <= bound:
            self._alerted.discard(inst.id)  # healthy again
            return

        hist = self._history.setdefault(inst.id, deque())
        cutoff = now.timestamp() - settings.auto_recover_window_seconds
        while hist and hist[0] < cutoff:
            hist.popleft()
        if len(hist) >= settings.auto_recover_budget:
            self._alert(db, inst, len(hist))
            return
        hist.append(now.timestamp())
        self._recover(db, inst, age)

    def _recover(self, db: Session, inst: Instrument, age: float) -> None:
        from ecallisto_ng.services import audit, host

        args = [str(inst.id)]
        if inst.address:
            args.append(inst.address)
        ok, message = host.run_hook("recover", *args)
        _log.warning(
            "auto-recover #%s: stalled %.0fs -> recover: %s",
            inst.id,
            age,
            message,
        )
        audit.record(
            db,
            "auto-recover",
            "host.recover",
            target=str(inst.id),
            detail="ok" if ok else message,
        )

    def _alert(self, db: Session, inst: Instrument, attempts: int) -> None:
        iid = inst.id
        if iid is None or iid in self._alerted:
            return  # already alerted for this stall -- don't re-spam
        self._alerted.add(iid)
        _log.error(
            "auto-recover #%s (%s): %d recoveries in the window did not "
            "restore frames -- manual intervention needed",
            inst.id,
            inst.name,
            attempts,
        )
        from ecallisto_ng.api.models import AlertChannelConfig
        from ecallisto_ng.services import alerts

        rows = db.exec(select(AlertChannelConfig)).all()
        channels = alerts.enabled_channels(rows)
        if channels:
            alerts.dispatch(
                channels,
                "e-Callisto NG: instrument unrecoverable",
                f"Instrument #{inst.id} ({inst.name}) is stalled and "
                f"auto-recovery is exhausted ({attempts} attempts). The "
                "receiver likely needs a reboot or on-site attention.",
            )


def _aware(when: datetime, now: datetime) -> datetime:
    """Treat a naive (SQLite) timestamp as UTC so subtraction works."""
    return when if when.tzinfo else when.replace(tzinfo=now.tzinfo)
