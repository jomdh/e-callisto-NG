"""SDR instrument drivers (classes 2 and 3, DESIGN 5a).

- ``soft`` (class 2): host does the DSP -- raw IQ in, FFT to spectra here.
- ``fpga`` (class 3): the device does the DSP -- ready power spectra in.

Both implement the same ``InstrumentDriver`` contract and deliver normalized
spectra, so the recorder/writer/scheduler are unchanged.
"""

from __future__ import annotations

from ecallisto_ng.drivers.sdr.fpga import (
    FpgaSdrDriver,
    SimulatedFpga,
    build_fpga_driver,
)
from ecallisto_ng.drivers.sdr.soft import SoftSdrDriver

__all__ = [
    "SoftSdrDriver",
    "FpgaSdrDriver",
    "SimulatedFpga",
    "build_fpga_driver",
]
