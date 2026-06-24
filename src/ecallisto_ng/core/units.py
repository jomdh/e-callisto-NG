"""Unit, processing-location, link and instrument-class enumerations.

These are the small, stable vocabularies the whole suite agrees on. They
live in ``core`` because every other package refers to them and ``core``
must depend on nothing concrete.

Design references: DESIGN sections 5a (instrument classes), 6b (units).
"""

from __future__ import annotations

from enum import StrEnum


class UnitLevel(StrEnum):
    """How values in a spectrum should be interpreted.

    ``RAW`` is always the default: persisted science data is raw ADC unless
    the instrument is explicitly calibrated. ``DB`` is an *optional* log
    estimate (never automatic); ``SFU``/``KELVIN`` require a calibration.
    Never silently transform between levels (DESIGN 6b).
    """

    RAW = "raw"  # native ADC / digits -- the default
    DB = "db"  # optional log-scaled estimate, not a physical calibration
    SFU = "sfu"  # calibrated solar flux units
    KELVIN = "kelvin"  # calibrated antenna temperature


class ProcessingLocation(StrEnum):
    """Where the signal processing that yields spectra happens."""

    HOST = "host"  # host-driven sweep or host DSP (class 1 / class 2)
    DEVICE = "device"  # on-instrument FFT/channelization (class 3)
    HYBRID = "hybrid"


class LinkKind(StrEnum):
    """The medium a driver uses to reach its instrument."""

    SERIAL = "serial"  # COM-over-USB (class 1 e-Callisto)
    USB = "usb"  # USB bulk (class 2 SDR dongle)
    NETWORK = "network"  # TCP/Ethernet (class 3 FPGA appliance)


class InstrumentClass(StrEnum):
    """The three instrument classes the driver seam must absorb."""

    HETERODYNE = "heterodyne"  # ADC + dumb MCU, host-driven (e-Callisto)
    SDR_SOFT = "sdr_soft"  # SDR, host does the DSP
    SDR_FPGA = "sdr_fpga"  # SDR, FPGA does the DSP
