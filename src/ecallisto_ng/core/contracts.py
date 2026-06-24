"""Plugin contracts -- the versioned seams the suite is built on.

Everything variable in the system is a plugin behind one of these
interfaces (DESIGN 5a). ``core`` defines the contracts; concrete drivers,
transports and writers implement them and are loaded from a registry. The
core never imports a concrete implementation.

Contracts are **semver-versioned**: changing one is an ADR + version bump,
never a silent break -- third parties (including closed SDR/FPGA drivers)
build against them (DESIGN 5b). ``CONTRACT_VERSION`` tracks this module.

They are ``Protocol`` types (structural typing): an implementation conforms
by shape, without importing or subclassing anything here -- which is what
keeps plugins independently developed and independently licensed.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Protocol, runtime_checkable

from ecallisto_ng.core.spectra import (
    Capabilities,
    Channel,
    InstrumentInfo,
    SpectrumFrame,
)
from ecallisto_ng.core.units import UnitLevel

CONTRACT_VERSION = "0.1.0"


@runtime_checkable
class InstrumentDriver(Protocol):
    """Drives one instrument and yields normalized spectra.

    Lifecycle: ``connect`` -> ``identify``/``configure`` -> ``start`` ->
    iterate ``stream`` -> ``stop`` -> ``close``. Class-specific mechanics
    (serial sweep + EEPROM, host DSP on IQ, FPGA ingest) live entirely behind
    this interface; callers only ever see ``capabilities`` and frames.
    """

    @property
    def capabilities(self) -> Capabilities:
        """What this instrument can do (read, do not assume)."""

    def connect(self) -> None:
        """Open the device connection (serial/USB/network)."""

    def identify(self) -> InstrumentInfo:
        """Confirm the device and report model/firmware/serial."""

    def configure(
        self, channels: Sequence[Channel], sample_rate_hz: float
    ) -> None:
        """Program the frequency plan and sweep/sample rate."""

    def start(self) -> None:
        """Begin acquisition."""

    def stop(self) -> None:
        """Halt acquisition (state preserved; ``stream`` ends)."""

    def stream(self) -> Iterator[SpectrumFrame]:
        """Yield spectra as they are acquired until stopped/closed."""

    def overview(self) -> Iterator[SpectrumFrame]:
        """Yield a one-shot wide spectral sweep (if supported)."""

    def close(self) -> None:
        """Release the device connection."""


@runtime_checkable
class OutputWriter(Protocol):
    """Writes accumulated spectra to a science product (e.g. FITS).

    The three output modes (legacy / standard / custom, DESIGN 6a) are three
    writers. Writers must honor the frame ``unit`` and bit depth -- never
    assume 8-bit, never silently rescale (DESIGN 6b).
    """

    def filename(self, frames: Sequence[SpectrumFrame]) -> str:
        """Compute the output filename for a block of frames."""

    def write(
        self, frames: Sequence[SpectrumFrame], unit: UnitLevel, out_dir: Path
    ) -> Path:
        """Write the product and return its path."""


@runtime_checkable
class UploadTransport(Protocol):
    """Ships a finished file to a destination (FTP/SFTP/...).

    Distinct from a driver's device connection: this is the outbound seam
    (DESIGN 5a). Implementations use a tmp-then-rename handshake upstream.
    """

    def connect(self) -> None:
        """Open the connection to the destination."""

    def put(self, local: Path, remote: str) -> None:
        """Upload one file to a remote path."""

    def verify(self, local: Path, remote: str) -> bool:
        """Confirm the remote copy matches the local file."""

    def close(self) -> None:
        """Close the connection."""
