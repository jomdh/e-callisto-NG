"""Degrade-don't-die failure-mode policy matrix (DESIGN 14a).

A pure mapping from a fault condition to the station's response: keep running
where possible, isolate the fault, and always alert. The acquisition path is
independent of the web app, so a web fault never stops recording, and a
recording fault never takes down the web app.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Fault(StrEnum):
    DISK_FULL = "disk_full"
    DISK_LOW = "disk_low"
    RECEIVER_GONE = "receiver_gone"
    CLOCK_UNSYNCED = "clock_unsynced"
    UPLOAD_BACKLOG = "upload_backlog"
    DATA_LOSS = "data_loss"
    WEB_DOWN = "web_down"


class Response(StrEnum):
    CONTINUE = "continue"  # keep going, just alert
    PAUSE = "pause"  # stop recording until cleared
    RETRY = "retry"  # auto-recover (e.g. reconnect / restart)


@dataclass(frozen=True)
class Policy:
    response: Response
    alert: bool
    message: str


_MATRIX: dict[Fault, Policy] = {
    # No space left: stop recording (can't write), alert loudly.
    Fault.DISK_FULL: Policy(
        Response.PAUSE, True, "Disk full: recording paused"
    ),
    # Low but not full: keep recording, warn so the operator acts.
    Fault.DISK_LOW: Policy(Response.CONTINUE, True, "Disk space low"),
    # Receiver vanished: auto-reconnect/restart, alert.
    Fault.RECEIVER_GONE: Policy(
        Response.RETRY, True, "Receiver not responding: reconnecting"
    ),
    # Clock bad: pause if sync is required (timing gates science).
    Fault.CLOCK_UNSYNCED: Policy(
        Response.PAUSE, True, "Clock not synchronized"
    ),
    # Files piling up: keep recording (never lose data), alert.
    Fault.UPLOAD_BACKLOG: Policy(
        Response.CONTINUE, True, "Upload backlog growing"
    ),
    # Garbled stream: auto-stop + restart (the watchdog), alert.
    Fault.DATA_LOSS: Policy(
        Response.RETRY, True, "Data loss: auto-restarting"
    ),
    # Web app down: acquisition is independent -> keep recording, alert.
    Fault.WEB_DOWN: Policy(
        Response.CONTINUE, True, "Web app down (acquisition unaffected)"
    ),
}


def policy_for(fault: Fault) -> Policy:
    """The response policy for a fault (degrade-don't-die)."""
    return _MATRIX[fault]


def should_pause(faults: set[Fault]) -> bool:
    """True if any active fault requires pausing recording."""
    return any(_MATRIX[f].response is Response.PAUSE for f in faults)
