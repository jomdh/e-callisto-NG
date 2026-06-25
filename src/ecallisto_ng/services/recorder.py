"""Background recorder: start/stop a recording per instrument.

A thin controller that runs the synchronous ``record()`` loop on a worker
thread so the API can return immediately. ``stop()`` ends the driver's stream,
which flushes the partial recording to a FITS file. True continuous +
live-streamed recording arrives in M2; this is the start/stop/status baseline.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

from ecallisto_ng.core.calibration import Calibration
from ecallisto_ng.core.contracts import InstrumentDriver, OutputWriter
from ecallisto_ng.core.recording import RecordingMeta
from ecallisto_ng.core.spectra import Channel
from ecallisto_ng.core.units import UnitLevel
from ecallisto_ng.drivers.callisto import CallistoConfig, CallistoDriver
from ecallisto_ng.drivers.fake import FakeDriver
from ecallisto_ng.services.acquisition import record
from ecallisto_ng.writers.fits import StandardFitsWriter


class RecorderState(StrEnum):
    IDLE = "idle"
    RECORDING = "recording"
    ERROR = "error"


@dataclass
class RecorderStatus:
    state: RecorderState = RecorderState.IDLE
    last_file: str | None = None
    error: str | None = None


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
        from ecallisto_ng.drivers.sdr.soft import SoftSdrDriver

        return SoftSdrDriver(channels=channels)
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
            return job.status if job else RecorderStatus()

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
    ) -> None:
        with self._lock:
            existing = self._jobs.get(instrument_id)
            if existing and existing.status.state is RecorderState.RECORDING:
                raise RuntimeError("already recording")

        from ecallisto_ng.core.spectra import SpectrumFrame
        from ecallisto_ng.services.hub import get_hub

        hub = get_hub()
        out_writer = writer or StandardFitsWriter()

        def _publish(frame: SpectrumFrame) -> None:
            hub.publish(instrument_id, frame)

        def _run() -> None:
            try:
                path = record(
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
                )
                self._finish(instrument_id, str(path), None)
            except Exception as exc:  # noqa: BLE001 - report any failure
                self._finish(instrument_id, None, str(exc))

        thread = threading.Thread(target=_run, daemon=True)
        status = RecorderStatus(state=RecorderState.RECORDING)
        with self._lock:
            self._jobs[instrument_id] = _Job(driver, thread, status)
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
