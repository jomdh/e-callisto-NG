# SPDX-License-Identifier: AGPL-3.0-or-later
"""The record loop: drive an instrument and write a science product.

A thin synchronous orchestration that joins an
:class:`ecallisto_ng.core.InstrumentDriver` to an
:class:`ecallisto_ng.core.OutputWriter`. It owns no protocol knowledge -- it
speaks only the contracts, so the same loop records from the fake driver, a
Callisto over serial, or a future SDR. Async/threaded streaming for the live
web layer arrives in M2; this is the file-at-a-time baseline.
"""

from __future__ import annotations

import itertools
from collections.abc import Callable, Sequence
from pathlib import Path

from ecallisto_ng.core.calibration import Calibration
from ecallisto_ng.core.contracts import InstrumentDriver, OutputWriter
from ecallisto_ng.core.recording import Recording, RecordingMeta
from ecallisto_ng.core.spectra import Channel, SpectrumFrame
from ecallisto_ng.core.units import UnitLevel
from ecallisto_ng.services.lightcurve import write_light_curves
from ecallisto_ng.services.watchdog import DataLossError, Watchdog


def record(
    driver: InstrumentDriver,
    writer: OutputWriter,
    channels: Sequence[Channel],
    meta: RecordingMeta,
    out_dir: Path,
    *,
    sweeps_per_second: float,
    max_frames: int,
    unit: UnitLevel = UnitLevel.RAW,
    calibration: Calibration | None = None,
    on_frame: Callable[[SpectrumFrame], None] | None = None,
    watchdog: Watchdog | None = None,
    on_data_loss: Callable[[list[str]], None] | None = None,
) -> Path:
    """Record ``max_frames`` sweeps and write one product; return its path.

    ``on_frame`` is called for each frame as it arrives (e.g. to publish it
    live) -- it must not block. If ``watchdog`` flags a corrupt sweep,
    recording stops early, ``on_data_loss`` is invoked with the legacy alert
    lines, and the product is written from the good frames collected so far
    (degrade, don't die -- DESIGN 14a). The scheduler re-arms on its next tick.
    """
    if max_frames < 1:
        raise ValueError("max_frames must be >= 1")

    collected: list[SpectrumFrame] = []
    try:
        # Handshake inside the try so a mute-at-startup failure (now bounded,
        # ADR-0010) still releases the port via the finally -- otherwise the
        # leaked fd collides with the scheduler's next rebuild ("multiple
        # access on port").
        driver.connect()
        driver.identify()
        driver.configure(channels, sweeps_per_second)
        driver.start()
        for frame in itertools.islice(driver.stream(), max_frames):
            if watchdog is not None and watchdog.check(frame.values):
                if on_data_loss is not None:
                    on_data_loss(watchdog.alert_sequence())
                break
            if on_frame is not None:
                on_frame(frame)
            collected.append(frame)
    finally:
        driver.stop()
        driver.close()

    if not collected:
        raise DataLossError("no valid sweeps recorded")
    return _write_product(
        writer,
        channels,
        meta,
        out_dir,
        collected,
        sweeps_per_second,
        unit,
        calibration,
    )


def record_continuous(
    driver: InstrumentDriver,
    writer: OutputWriter,
    channels: Sequence[Channel],
    meta: RecordingMeta,
    out_dir: Path,
    *,
    sweeps_per_second: float,
    frames_per_file: int,
    unit: UnitLevel = UnitLevel.RAW,
    calibration: Calibration | None = None,
    on_frame: Callable[[SpectrumFrame], None] | None = None,
    watchdog: Watchdog | None = None,
    on_data_loss: Callable[[list[str]], None] | None = None,
    on_file: Callable[[Path], None] | None = None,
) -> list[Path]:
    """Record continuously, rolling a file every ``frames_per_file`` sweeps.

    Streams from a single ``start()`` and slices the stream into files (legacy
    15-min FITS rollover). Runs until ``driver.stop()`` ends the stream (an
    operator Stop or the scheduler closing the window), then flushes the
    partial final file (degrade, don't die -- DESIGN 14a). Returns the paths.

    Bounded liveness (ADR-0010): a stalled-but-enumerated device cannot hang
    here. ``stream()`` self-heals or raises ``FatalInstrumentError``, and the
    ``connect/identify/configure/start`` handshake times out (mute-at-startup)
    into a recoverable fault -- both inside the try, so the port is always
    released for the scheduler's next rebuild.
    """
    if frames_per_file < 1:
        raise ValueError("frames_per_file must be >= 1")

    paths: list[Path] = []
    try:
        # Handshake inside the try so a mute-at-startup failure (now bounded,
        # ADR-0010) still releases the port via the finally -- otherwise the
        # leaked fd collides with the scheduler's next rebuild ("multiple
        # access on port").
        driver.connect()
        driver.identify()
        driver.configure(channels, sweeps_per_second)
        driver.start()
        stream = driver.stream()
        while True:
            collected: list[SpectrumFrame] = []
            stopped = False
            try:
                for frame in itertools.islice(stream, frames_per_file):
                    if watchdog is not None and watchdog.check(frame.values):
                        if on_data_loss is not None:
                            on_data_loss(watchdog.alert_sequence())
                        stopped = True
                        break
                    if on_frame is not None:
                        on_frame(frame)
                    collected.append(frame)
            finally:
                # Always flush what we collected -- normal end, Stop, OR a
                # mid-batch exception (e.g. FatalInstrumentError after the
                # reset budget) -- so acquired sweeps are never lost (degrade,
                # don't die, DESIGN 14a).
                if collected:
                    path = _write_product(
                        writer,
                        channels,
                        meta,
                        out_dir,
                        collected,
                        sweeps_per_second,
                        unit,
                        calibration,
                    )
                    paths.append(path)
                    if on_file is not None:
                        on_file(path)
            # A short or empty batch means the stream ended (Stop / data loss).
            if stopped or len(collected) < frames_per_file:
                break
    finally:
        driver.stop()
        driver.close()
    return paths


def _write_product(
    writer: OutputWriter,
    channels: Sequence[Channel],
    meta: RecordingMeta,
    out_dir: Path,
    frames: Sequence[SpectrumFrame],
    sweeps_per_second: float,
    unit: UnitLevel,
    calibration: Calibration | None,
) -> Path:
    recording = Recording(
        meta=meta,
        channels=tuple(channels),
        frames=tuple(frames),
        sample_rate_hz=sweeps_per_second,
        unit=unit,
        calibration=calibration,
    )
    path = writer.write(recording, out_dir)
    write_light_curves(recording, out_dir)
    return path
