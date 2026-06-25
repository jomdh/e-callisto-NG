"""Background scheduler: start/stop recordings on each instrument's window.

Ticks periodically; each tick computes today's recording window per enabled
schedule (sun-relative from station coordinates, or fixed times) and arms or
stops the recorder. File-period rollover is implicit: when a bounded recording
finishes while the window still holds, the next tick re-arms it. ``tick`` is
pure-ish and testable; the loop just calls it.
"""

from __future__ import annotations

import threading
from datetime import UTC, datetime

from sqlmodel import Session, select

from ecallisto_ng.api.db import get_engine
from ecallisto_ng.api.models import (
    CalibrationSet,
    Instrument,
    Schedule,
    Station,
)
from ecallisto_ng.api.settings import get_settings
from ecallisto_ng.core.calibration import Calibration
from ecallisto_ng.core.recording import RecordingMeta
from ecallisto_ng.core.spectra import Channel
from ecallisto_ng.core.units import UnitLevel
from ecallisto_ng.services.calibration_build import resolve
from ecallisto_ng.services.recorder import (
    RecorderState,
    build_driver,
    get_recorder,
)
from ecallisto_ng.services.scheduler import (
    fixed_window,
    is_recording_desired,
    sun_window,
)


class SchedulerService:
    """Drives recordings from schedules. One per process."""

    def __init__(self) -> None:
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    def tick(self, db: Session, now: datetime) -> None:
        station = db.exec(select(Station)).first() or Station()
        recorder = get_recorder()
        for sched in db.exec(select(Schedule).where(Schedule.enabled)).all():
            inst = db.get(Instrument, sched.instrument_id)
            if inst is None or not inst.enabled or inst.id is None:
                continue
            window = self._window(sched, station, now)
            desired = is_recording_desired(window, now)
            state = recorder.status(inst.id).state
            if desired and state is not RecorderState.RECORDING:
                self._start(db, inst, station)
            elif not desired and state is RecorderState.RECORDING:
                recorder.stop(inst.id)

    def _window(
        self, sched: Schedule, station: Station, now: datetime
    ) -> tuple[datetime, datetime] | None:
        if sched.kind == "fixed":
            return fixed_window(now.date(), sched.start_utc, sched.stop_utc)
        return sun_window(
            station.latitude_deg,
            station.longitude_deg,
            now.date(),
            sched.margin_minutes,
        )

    def _start(self, db: Session, inst: Instrument, st: Station) -> None:
        assert inst.id is not None
        driver = build_driver(
            inst.instrument_class, inst.address, inst.focus_code, inst.channels
        )
        channels = [
            Channel(frequency_mhz=45.0 + i) for i in range(inst.channels)
        ]
        meta = RecordingMeta(
            instrument=inst.name,
            origin=st.observatory or "e-CALLISTO NG",
            latitude_deg=st.latitude_deg,
            longitude_deg=st.longitude_deg,
            altitude_m=st.altitude_m,
            pwm=inst.gain,
            focus_code=inst.focus_code,
        )
        frames = max(int(inst.file_seconds * inst.sweep_rate_hz), 1)
        data_dir = get_settings().data_dir
        data_dir.mkdir(parents=True, exist_ok=True)
        unit, calibration = self._calibration(db, inst)
        get_recorder().start(
            inst.id,
            driver,
            channels,
            meta,
            data_dir,
            sweep_rate_hz=inst.sweep_rate_hz,
            max_frames=frames,
            unit=unit,
            calibration=calibration,
        )

    def _calibration(
        self, db: Session, inst: Instrument
    ) -> tuple[UnitLevel, Calibration | None]:
        coeffs = None
        if inst.calibration_set_id is not None:
            cs = db.get(CalibrationSet, inst.calibration_set_id)
            if cs is not None:
                coeffs = cs.coefficients_json
        return resolve(inst.unit, coeffs, inst.channels)

    # -- background loop ---------------------------------------------------

    def start_loop(self) -> None:
        interval = get_settings().scheduler_tick_seconds
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


_service = SchedulerService()


def get_scheduler() -> SchedulerService:
    return _service
