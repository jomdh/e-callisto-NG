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

    driver.connect()
    driver.identify()
    driver.configure(channels, sweeps_per_second)
    driver.start()
    collected: list[SpectrumFrame] = []
    try:
        for frame in itertools.islice(driver.stream(), max_frames):
            if watchdog is not None and watchdog.check(frame.values):
                if on_data_loss is not None:
                    on_data_loss(watchdog.alert_sequence())
                break
            if on_frame is not None:
                on_frame(frame)
            collected.append(frame)
        frames = tuple(collected)
    finally:
        driver.stop()
        driver.close()

    if not frames:
        raise DataLossError("no valid sweeps recorded")

    recording = Recording(
        meta=meta,
        channels=tuple(channels),
        frames=frames,
        sample_rate_hz=sweeps_per_second,
        unit=unit,
        calibration=calibration,
    )
    path = writer.write(recording, out_dir)
    write_light_curves(recording, out_dir)
    return path
