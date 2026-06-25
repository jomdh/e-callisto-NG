"""Core domain models and plugin contracts.

``core`` is the inward-most package: it depends on nothing concrete, and
every other package depends on it. See DESIGN section 5a.
"""

from __future__ import annotations

from ecallisto_ng.core.calibration import Calibration, ChannelCal
from ecallisto_ng.core.contracts import (
    CONTRACT_VERSION,
    BenchCapable,
    InstrumentDriver,
    OutputWriter,
    UploadTransport,
)
from ecallisto_ng.core.recording import Recording, RecordingMeta
from ecallisto_ng.core.spectra import (
    Capabilities,
    Channel,
    Housekeeping,
    InstrumentInfo,
    SpectrumFrame,
)
from ecallisto_ng.core.units import (
    InstrumentClass,
    LinkKind,
    ProcessingLocation,
    UnitLevel,
)

__all__ = [
    "CONTRACT_VERSION",
    "BenchCapable",
    "InstrumentDriver",
    "OutputWriter",
    "UploadTransport",
    "Calibration",
    "Capabilities",
    "Channel",
    "ChannelCal",
    "Housekeeping",
    "InstrumentInfo",
    "Recording",
    "RecordingMeta",
    "SpectrumFrame",
    "InstrumentClass",
    "LinkKind",
    "ProcessingLocation",
    "UnitLevel",
]
