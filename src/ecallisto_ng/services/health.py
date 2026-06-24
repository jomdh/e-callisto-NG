"""Station health: disk, instruments, recordings, upload backlog, alerts.

Distinguishes system health from data quality (DESIGN 14); this is the system
side. ``compute_alerts`` is pure and testable; ``gather_health`` reads the disk
and DB. Clock-sync detection is best-effort and platform-dependent, so it is
reported as a tri-state and only alerted when known-bad.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class HealthReport:
    disk_free_bytes: int
    disk_total_bytes: int
    disk_pct_free: float
    instruments: int
    recordings: int
    upload_pending: int
    clock_synced: bool | None
    alerts: list[str] = field(default_factory=list)


def compute_alerts(
    disk_pct_free: float,
    instruments: int,
    upload_pending: int,
    clock_synced: bool | None,
) -> list[str]:
    """Derive operator-facing alerts from the metrics."""
    alerts: list[str] = []
    if disk_pct_free < 10.0:
        alerts.append("Disk space low (under 10% free)")
    if instruments == 0:
        alerts.append("No instruments configured")
    if upload_pending > 50:
        alerts.append(f"{upload_pending} files pending upload")
    if clock_synced is False:
        alerts.append("System clock is not synchronized")
    return alerts


def disk_for(path: Path) -> tuple[int, int, float]:
    """Return (free, total, pct_free) for the filesystem holding ``path``."""
    probe = path if path.exists() else path.anchor or Path(".")
    usage = shutil.disk_usage(probe)
    pct = 100.0 * usage.free / usage.total if usage.total else 0.0
    return usage.free, usage.total, pct


def build_report(
    data_dir: Path,
    instruments: int,
    recordings: int,
    upload_pending: int,
    clock_synced: bool | None = None,
) -> HealthReport:
    free, total, pct = disk_for(data_dir)
    return HealthReport(
        disk_free_bytes=free,
        disk_total_bytes=total,
        disk_pct_free=round(pct, 1),
        instruments=instruments,
        recordings=recordings,
        upload_pending=upload_pending,
        clock_synced=clock_synced,
        alerts=compute_alerts(pct, instruments, upload_pending, clock_synced),
    )
