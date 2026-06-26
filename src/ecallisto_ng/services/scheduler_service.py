# SPDX-License-Identifier: AGPL-3.0-or-later
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
from ecallisto_ng.services import recorder_state
from ecallisto_ng.services.calibration_build import resolve
from ecallisto_ng.services.channels import resolve_channels
from ecallisto_ng.services.overview import run_overview
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
from ecallisto_ng.services.timing import get_time_source
from ecallisto_ng.writers.fits import get_writer


def _system_boot_id() -> str:
    """A token that changes on every machine reboot (Linux ``/proc/stat``).

    Empty on non-Linux/dev hosts -- there a service restart and a reboot look
    alike, so intent persists (the safer, data-preserving default).
    """
    try:
        with open("/proc/stat", encoding="ascii") as fh:
            for line in fh:
                if line.startswith("btime"):
                    return line.split()[1]
    except OSError:  # pragma: no cover - non-Linux
        pass
    return ""


class SchedulerService:
    """Drives recordings from schedules. One per process."""

    def __init__(self) -> None:
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    def tick(self, db: Session, now: datetime) -> None:
        from ecallisto_ng.services.clock import (
            clock_offset_ms,
            clock_synced,
            may_record,
            within_drift,
        )

        station = db.exec(select(Station)).first() or Station()
        recorder = get_recorder()
        settings = get_settings()
        gate_ok = may_record(
            settings.require_clock_sync, clock_synced()
        ) and within_drift(clock_offset_ms(), settings.max_clock_offset_ms)
        instruments = db.exec(
            select(Instrument).where(Instrument.enabled)
        ).all()
        for inst in instruments:
            if inst.id is None:
                continue
            sched = self._active_schedule(db, inst.id)
            if sched is not None:  # fixed/sun: the window is the intent
                window = self._window(sched, station, now)
                desired = is_recording_desired(window, now)
            else:  # free-run (manual / no schedule): the operator flag is
                desired = recorder_state.get_desired(db, inst.id)
            state = recorder.status(inst.id).state
            if desired and gate_ok and state is not RecorderState.RECORDING:
                self._start(db, inst, station, sched)
            elif not desired and state is RecorderState.RECORDING:
                # Clock drift does NOT tear down a running recording (M34/D7,
                # ADR-0010): we trust the boot-synced clock and the file's
                # clock metadata flags the affected sweeps. Only loss of intent
                # (window close / operator Stop) stops it.
                recorder.stop(inst.id)
            else:
                self._maybe_overview(db, inst, sched, now)

    def _active_schedule(
        self, db: Session, instrument_id: int
    ) -> Schedule | None:
        """The instrument's windowed (fixed/sun) schedule, if any.

        A ``manual``-kind schedule -- or no enabled schedule -- means free-run
        (the window is always open; the operator's desired flag decides).
        """
        return db.exec(
            select(Schedule)
            .where(Schedule.instrument_id == instrument_id)
            .where(Schedule.enabled)
            .where(Schedule.kind != "manual")
        ).first()

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
            station.horizon_deg,
        )

    def _start(
        self,
        db: Session,
        inst: Instrument,
        st: Station,
        sched: Schedule | None,
    ) -> None:
        assert inst.id is not None
        iid = inst.id
        driver = build_driver(
            inst.instrument_class, inst.address, inst.focus_code, inst.channels
        )
        channels = self._channels(db, inst, sched)
        tsrc = get_time_source(get_settings().time_source)
        meta = RecordingMeta(
            instrument=inst.name,
            origin=st.observatory or "e-CALLISTO NG",
            latitude_deg=st.latitude_deg,
            longitude_deg=st.longitude_deg,
            altitude_m=st.altitude_m,
            pwm=inst.gain,
            focus_code=inst.focus_code,
            time_source=tsrc.name,
            clock_offset_ms=tsrc.offset_ms(),
        )
        # Record continuously, rolling a file every file_seconds; the scheduler
        # stops it at window close (scheduled) or on operator Stop (free-run).
        per_file = max(int(inst.file_seconds * inst.sweep_rate_hz), 1)
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
            max_frames=per_file,
            unit=unit,
            calibration=calibration,
            writer=get_writer(inst.output_mode),
            continuous=True,
            on_state=lambda st, lf: recorder_state.write(iid, st, lf),
        )

    def _channels(
        self, db: Session, inst: Instrument, sched: Schedule | None
    ) -> list[Channel]:
        """Channels for the run: the schedule's program overrides the
        instrument's own program, else a ramp (M32)."""
        program_id = sched.program_id if sched is not None else None
        return resolve_channels(db, inst, program_id)

    def _maybe_overview(
        self,
        db: Session,
        inst: Instrument,
        sched: Schedule | None,
        now: datetime,
    ) -> None:
        """Trigger a scheduled overview at ``overview_at``, once per day."""
        if sched is None or not sched.overview_at or inst.id is None:
            return
        today = now.strftime("%Y-%m-%d")
        if sched.last_overview_date == today:
            return
        if now.strftime("%H:%M") < sched.overview_at:
            return
        if get_recorder().status(inst.id).state is RecorderState.RECORDING:
            return
        driver = build_driver(
            inst.instrument_class, inst.address, inst.focus_code, inst.channels
        )
        data_dir = get_settings().data_dir
        data_dir.mkdir(parents=True, exist_ok=True)
        run_overview(driver, data_dir, inst.name, now)
        sched.last_overview_date = today
        db.add(sched)
        db.commit()

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

    def seed_desired_from_boot(
        self, db: Session, boot_id: str | None = None
    ) -> None:
        """Reconcile persisted state at startup; re-seed only on a real reboot.

        A fresh process owns no recordings, so any persisted ``recording``
        state is stale (left by the killed predecessor) -- always reset it to
        idle (the next tick resumes anything still desired).

        The operator's intent (``desired``) is only re-seeded from
        ``start_on_boot`` on an **actual machine reboot**, detected by a change
        in the system boot id. A mere service restart (crash auto-restart, a
        deploy) keeps the existing intent, so a manual or scheduled recording
        resumes -- maximize captured data, get back to plan. A manual run thus
        survives a hiccup but not a reboot; a human Stop is always respected.
        """
        for rt in recorder_state.read(db).values():
            if rt.state == RecorderState.RECORDING:
                recorder_state.write(
                    rt.instrument_id, RecorderState.IDLE, None
                )
        if boot_id is None:
            boot_id = _system_boot_id()
        marker = get_settings().data_dir / ".boot_epoch"
        last = marker.read_text().strip() if marker.exists() else None
        if last == boot_id:
            return  # service restart, not a reboot -- keep intent, resume
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(boot_id)
        for inst in db.exec(select(Instrument)).all():
            if inst.id is None:
                continue
            if self._active_schedule(db, inst.id) is not None:
                continue  # windowed schedule owns the intent
            recorder_state.set_desired(inst.id, bool(inst.start_on_boot))

    def start_loop(self) -> None:
        interval = get_settings().scheduler_tick_seconds
        if interval <= 0 or self._thread is not None:
            return
        try:
            with Session(get_engine()) as db:
                self.seed_desired_from_boot(db)
        except Exception:  # noqa: BLE001 - never block startup
            pass

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
