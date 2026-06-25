# SPDX-License-Identifier: AGPL-3.0-or-later
"""Auto-dispatch uploads + retention, on a background loop.

Each tick: for every enabled target, upload pending files if its dispatch mode
says so now -- ``immediate`` always, ``scheduled`` only inside the target's
window, ``manual`` never. Then prune local files that have been uploaded to all
enabled targets and are older than the retention age (un-uploaded files are
never pruned). ``tick`` is the testable unit; the loop just calls it.
"""

from __future__ import annotations

import threading
import time
from datetime import UTC, datetime
from pathlib import Path

from sqlmodel import Session, select

from ecallisto_ng.api.db import get_engine
from ecallisto_ng.api.models import UploadJob, UploadTarget
from ecallisto_ng.api.settings import get_settings
from ecallisto_ng.services import catalog, uploader
from ecallisto_ng.services.scheduler import fixed_window, is_recording_desired


def _due(target: UploadTarget, now: datetime) -> bool:
    if not target.enabled or target.dispatch == "manual":
        return False
    if target.dispatch == "immediate":
        return True
    window = fixed_window(now.date(), target.window_start, target.window_stop)
    return is_recording_desired(window, now)


def prune(db: Session, data_dir: Path, retention_days: int) -> int:
    """Delete files uploaded to all enabled targets and older than retention.

    ``retention_days < 0`` disables pruning. Un-uploaded files are kept.
    """
    if retention_days < 0:
        return 0
    data = Path(data_dir)
    targets = db.exec(select(UploadTarget).where(UploadTarget.enabled)).all()
    if not targets:
        return 0
    target_ids = {t.id for t in targets}
    now = time.time()
    min_age = retention_days * 86400
    deleted = 0
    for info in catalog.list_recordings(data):
        done = {
            j.target_id
            for j in db.exec(
                select(UploadJob).where(
                    UploadJob.filename == info.name,
                    UploadJob.state == "done",
                )
            ).all()
        }
        if not target_ids.issubset(done):
            continue  # not yet uploaded everywhere
        path = data / info.name
        if now - path.stat().st_mtime < min_age:
            continue
        path.unlink(missing_ok=True)
        deleted += 1
    return deleted


def archive_file(src: Path, archive_root: Path, when: datetime) -> Path:
    """Move ``src`` into a dated ``YYYY/MM/DD`` tree (legacy FITbackup)."""
    dest_dir = archive_root / f"{when:%Y}" / f"{when:%m}" / f"{when:%d}"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    src.replace(dest)
    return dest


def archive_done(db: Session, data_dir: Path, archive_root: Path) -> int:
    """Move files uploaded to all enabled targets into the dated archive."""
    data = Path(data_dir)
    targets = db.exec(select(UploadTarget).where(UploadTarget.enabled)).all()
    if not targets:
        return 0
    target_ids = {t.id for t in targets}
    moved = 0
    for path in data.glob("*.fit"):
        done = {
            j.target_id
            for j in db.exec(
                select(UploadJob).where(
                    UploadJob.filename == path.name,
                    UploadJob.state == "done",
                )
            ).all()
        }
        if not target_ids.issubset(done):
            continue
        when = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
        archive_file(path, archive_root, when)
        moved += 1
    return moved


class UploaderService:
    """Auto-dispatch + retention/archive loop. One per process."""

    def __init__(self) -> None:
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._last_alert_sig = ""

    def tick(self, db: Session, now: datetime) -> None:
        settings = get_settings()
        for target in db.exec(select(UploadTarget)).all():
            if _due(target, now):
                uploader.upload_pending(db, target, settings.data_dir)
        if settings.archive_dir:
            archive_done(db, settings.data_dir, Path(settings.archive_dir))
        else:
            prune(db, settings.data_dir, settings.retention_days)
        self._notify(db)

    def _notify(self, db: Session) -> None:
        """Dispatch health alerts to enabled channels, deduped per change."""
        from ecallisto_ng.api.models import AlertChannelConfig
        from ecallisto_ng.services import alerts
        from ecallisto_ng.services.health_report import build_station_health

        report = build_station_health(db)
        active = list(getattr(report, "alerts", []) or [])
        sig = "\n".join(sorted(active))
        if sig == self._last_alert_sig:
            return  # nothing new -> don't re-spam
        self._last_alert_sig = sig
        if not active:
            return
        rows = db.exec(select(AlertChannelConfig)).all()
        channels = alerts.enabled_channels(rows)
        if channels:
            alerts.dispatch(channels, "e-Callisto NG alert", sig)

    def start_loop(self) -> None:
        interval = get_settings().uploader_tick_seconds
        if interval <= 0 or self._thread is not None:
            return

        def _run() -> None:
            while not self._stop.wait(interval):
                try:
                    with Session(get_engine()) as db:
                        self.tick(db, datetime.now(UTC))
                except Exception:  # noqa: BLE001 - keep the loop alive
                    pass

        self._stop.clear()
        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()

    def stop_loop(self) -> None:
        self._stop.set()
        self._thread = None


_service = UploaderService()


def get_uploader() -> UploaderService:
    return _service
