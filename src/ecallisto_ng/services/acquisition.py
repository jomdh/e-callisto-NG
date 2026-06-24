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
from collections.abc import Sequence
from pathlib import Path

from ecallisto_ng.core.contracts import InstrumentDriver, OutputWriter
from ecallisto_ng.core.recording import Recording, RecordingMeta
from ecallisto_ng.core.spectra import Channel


def record(
    driver: InstrumentDriver,
    writer: OutputWriter,
    channels: Sequence[Channel],
    meta: RecordingMeta,
    out_dir: Path,
    *,
    sweeps_per_second: float,
    max_frames: int,
) -> Path:
    """Record ``max_frames`` sweeps and write one product; return its path."""
    if max_frames < 1:
        raise ValueError("max_frames must be >= 1")

    driver.connect()
    driver.identify()
    driver.configure(channels, sweeps_per_second)
    driver.start()
    try:
        frames = tuple(itertools.islice(driver.stream(), max_frames))
    finally:
        driver.stop()
        driver.close()

    recording = Recording(
        meta=meta,
        channels=tuple(channels),
        frames=frames,
        sample_rate_hz=sweeps_per_second,
    )
    return writer.write(recording, out_dir)
