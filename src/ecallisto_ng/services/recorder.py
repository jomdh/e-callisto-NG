# SPDX-License-Identifier: AGPL-3.0-or-later
"""Background recorder: start/stop a recording per instrument.

A thin controller that runs the synchronous ``record()`` loop on a worker
thread so the API can return immediately. ``stop()`` ends the driver's stream,
which flushes the partial recording to a FITS file. True continuous +
live-streamed recording arrives in M2; this is the start/stop/status baseline.
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

from ecallisto_ng.core.calibration import Calibration
from ecallisto_ng.core.contracts import InstrumentDriver, OutputWriter
from ecallisto_ng.core.errors import FatalInstrumentError
from ecallisto_ng.core.recording import RecordingMeta
from ecallisto_ng.core.spectra import Channel
from ecallisto_ng.core.units import UnitLevel
from ecallisto_ng.drivers.callisto import CallistoConfig, CallistoDriver
from ecallisto_ng.drivers.fake import FakeDriver
from ecallisto_ng.services.acquisition import record, record_continuous
from ecallisto_ng.services.watchdog import Watchdog
from ecallisto_ng.writers.fits import StandardFitsWriter

_log = logging.getLogger(__name__)

# Minimum seconds between liveness heartbeat writes (ADR-0012).
_HEARTBEAT_S = 5.0


class RecorderState(StrEnum):
    IDLE = "idle"
    RECORDING = "recording"
    ERROR = "error"


@dataclass
class RecorderStatus:
    state: RecorderState = RecorderState.IDLE
    last_file: str | None = None
    error: str | None = None
    messages: list[str] = field(default_factory=list)


@dataclass
class _Job:
    driver: InstrumentDriver
    thread: threading.Thread
    status: RecorderStatus = field(default_factory=RecorderStatus)


def build_driver(
    instrument_class: str, address: str, focus_code: int, channels: int
) -> InstrumentDriver:
    """Pick a driver by instrument class (DESIGN 5a).

    sdr_soft -> host-DSP SDR; sdr_fpga -> FPGA SDR (network);
    heterodyne+address -> Callisto serial; otherwise the hardware-free fake.
    """
    if instrument_class == "sdr_soft":
        from ecallisto_ng.drivers.sdr.rx888 import (
            build_rx888_driver,
            is_rx888_address,
        )

        if is_rx888_address(address):
            return build_rx888_driver(address, channels)
        from ecallisto_ng.drivers.sdr.soft import SoftSdrDriver

        return SoftSdrDriver(channels=channels)
    if instrument_class == "sdr_fpga":
        from ecallisto_ng.drivers.sdr.fpga import build_fpga_driver

        return build_fpga_driver(address, channels)
    if address and instrument_class == "heterodyne":
        from ecallisto_ng.connections.serial_link import SerialConnection

        conn = SerialConnection(address)
        return CallistoDriver(
            conn, config=CallistoConfig(focuscode=focus_code)
        )
    return FakeDriver(channels=channels)


class RecorderService:
    """Process-wide registry of running recordings, keyed by instrument id."""

    def __init__(self) -> None:
        self._jobs: dict[int, _Job] = {}
        self._lock = threading.Lock()

    def status(self, instrument_id: int) -> RecorderStatus:
        with self._lock:
            job = self._jobs.get(instrument_id)
            if job is None:
                return RecorderStatus()
            # Liveness reconciliation (M34/D5): a job that claims RECORDING but
            # whose thread has died is wedged -- surface it as ERROR so the
            # scheduler re-arms instead of believing it is still recording.
            if (
                job.status.state is RecorderState.RECORDING
                and not job.thread.is_alive()
            ):
                job.status.state = RecorderState.ERROR
                job.status.error = job.status.error or "recorder thread died"
            return job.status

    def start(
        self,
        instrument_id: int,
        driver: InstrumentDriver,
        channels: list[Channel],
        meta: RecordingMeta,
        out_dir: Path,
        *,
        sweep_rate_hz: float,
        max_frames: int,
        unit: UnitLevel = UnitLevel.RAW,
        calibration: Calibration | None = None,
        writer: OutputWriter | None = None,
        on_state: Callable[[str, str | None], None] | None = None,
        on_heartbeat: Callable[[], None] | None = None,
        continuous: bool = False,
    ) -> None:
        """Start a recording.

        Bounded (``continuous=False``): record ``max_frames`` sweeps into one
        file, then go idle. Continuous (``continuous=True``): record until
        ``stop()``, rolling a new file every ``max_frames`` sweeps (the
        per-file size) -- the legacy continuous-with-rollover behaviour.
        """
        with self._lock:
            existing = self._jobs.get(instrument_id)
            if existing and existing.status.state is RecorderState.RECORDING:
                raise RuntimeError("already recording")

        from ecallisto_ng.core.spectra import SpectrumFrame
        from ecallisto_ng.services.hub import get_hub

        hub = get_hub()
        out_writer = writer or StandardFitsWriter()

        # Throttle the liveness heartbeat: stamp at most every _HEARTBEAT_S,
        # not on every frame, so a 4 Hz sweep doesn't hammer the SQLite row.
        last_hb = [0.0]

        def _publish(frame: SpectrumFrame) -> None:
            hub.publish(instrument_id, frame)
            if on_heartbeat is not None:
                now = time.monotonic()
                if now - last_hb[0] >= _HEARTBEAT_S:
                    last_hb[0] = now
                    on_heartbeat()

        def _on_data_loss(lines: list[str]) -> None:
            for line in lines:
                _log.warning("instrument %s: %s", instrument_id, line)
            with self._lock:
                job = self._jobs.get(instrument_id)
                if job:
                    job.status.messages.extend(lines)

        def _on_file(path: Path) -> None:
            # A continuous recording rolled a new file -- update last_file but
            # stay RECORDING.
            with self._lock:
                job = self._jobs.get(instrument_id)
                if job:
                    job.status.last_file = str(path)
            if on_state is not None:
                on_state(RecorderState.RECORDING, str(path))

        def _run() -> None:
            from ecallisto_ng.services import port_lock

            try:
                # Hold the device for the whole recording so a bench/overview
                # op (possibly in the other process) gets a clean busy, not a
                # corrupt read (ADR-0007 two-process model).
                with port_lock.hold(instrument_id):
                    if continuous:
                        paths = record_continuous(
                            driver,
                            out_writer,
                            channels,
                            meta,
                            out_dir,
                            sweeps_per_second=sweep_rate_hz,
                            frames_per_file=max_frames,
                            unit=unit,
                            calibration=calibration,
                            on_frame=_publish,
                            watchdog=Watchdog(),
                            on_data_loss=_on_data_loss,
                            on_file=_on_file,
                        )
                        last = str(paths[-1]) if paths else None
                    else:
                        last = str(
                            record(
                                driver,
                                out_writer,
                                channels,
                                meta,
                                out_dir,
                                sweeps_per_second=sweep_rate_hz,
                                max_frames=max_frames,
                                unit=unit,
                                calibration=calibration,
                                on_frame=_publish,
                                watchdog=Watchdog(),
                                on_data_loss=_on_data_loss,
                            )
                        )
                self._finish(instrument_id, last, None)
                if on_state is not None:
                    on_state(RecorderState.IDLE, last)
            except port_lock.InstrumentBusy:
                self._finish(
                    instrument_id, None, "instrument busy (port in use)"
                )
                if on_state is not None:
                    on_state(RecorderState.ERROR, None)
            except FatalInstrumentError as exc:
                # The driver gave up self-healing -- finish ERROR; the
                # scheduler rebuilds a fresh driver + re-arms next tick (D6).
                self._finish(instrument_id, None, f"instrument fault: {exc}")
                if on_state is not None:
                    on_state(RecorderState.ERROR, None)
            except Exception as exc:  # noqa: BLE001 - report any failure
                self._finish(instrument_id, None, str(exc))
                if on_state is not None:
                    on_state(RecorderState.ERROR, None)

        thread = threading.Thread(target=_run, daemon=True)
        status = RecorderStatus(state=RecorderState.RECORDING)
        with self._lock:
            self._jobs[instrument_id] = _Job(driver, thread, status)
        if on_state is not None:
            on_state(RecorderState.RECORDING, None)
        thread.start()

    def stop(self, instrument_id: int) -> None:
        with self._lock:
            job = self._jobs.get(instrument_id)
        if job and job.status.state is RecorderState.RECORDING:
            job.driver.stop()

    def join(self, instrument_id: int, timeout: float = 5.0) -> None:
        """Wait for a recording to finish (used by tests)."""
        with self._lock:
            job = self._jobs.get(instrument_id)
        if job:
            job.thread.join(timeout)

    def _finish(
        self, instrument_id: int, path: str | None, error: str | None
    ) -> None:
        with self._lock:
            job = self._jobs.get(instrument_id)
            if not job:
                return
            job.status.state = (
                RecorderState.ERROR if error else RecorderState.IDLE
            )
            job.status.last_file = path
            job.status.error = error


_service = RecorderService()


def get_recorder() -> RecorderService:
    return _service
