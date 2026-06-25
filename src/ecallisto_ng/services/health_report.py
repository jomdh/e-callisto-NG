"""Build this station's health report (shared by system + fleet)."""

from __future__ import annotations

from sqlmodel import Session, func, select

from ecallisto_ng.api.models import Instrument, UploadJob
from ecallisto_ng.api.settings import get_settings
from ecallisto_ng.services import catalog
from ecallisto_ng.services.clock import clock_synced
from ecallisto_ng.services.health import HealthReport, build_report


def build_station_health(db: Session) -> HealthReport:
    data_dir = get_settings().data_dir
    instruments = db.exec(select(func.count()).select_from(Instrument)).one()
    recordings = catalog.list_recordings(data_dir)
    done = {
        j.filename
        for j in db.exec(
            select(UploadJob).where(UploadJob.state == "done")
        ).all()
    }
    pending = sum(1 for r in recordings if r.name not in done)
    return build_report(
        data_dir,
        int(instruments),
        len(recordings),
        pending,
        clock_synced=clock_synced(),
    )
