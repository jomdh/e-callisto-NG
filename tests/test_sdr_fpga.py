"""Class-3 SDR+FPGA driver (device DSP) against the contract + via recorder."""

from __future__ import annotations

import itertools

from astropy.io import fits
from fastapi.testclient import TestClient
from sqlmodel import Session

from ecallisto_ng.api import auth, db
from ecallisto_ng.api.models import Role
from ecallisto_ng.core import InstrumentDriver, SpectrumFrame
from ecallisto_ng.core.units import (
    InstrumentClass,
    LinkKind,
    ProcessingLocation,
)
from ecallisto_ng.drivers.sdr import (
    FpgaSdrDriver,
    SimulatedFpga,
    build_fpga_driver,
)
from ecallisto_ng.services.recorder import build_driver, get_recorder


def _driver(channels: int = 32) -> FpgaSdrDriver:
    return FpgaSdrDriver(SimulatedFpga(channels), channels=channels)


def test_fpga_conforms_and_caps() -> None:
    d = _driver()
    assert isinstance(d, InstrumentDriver)
    caps = d.capabilities
    assert caps.instrument_class is InstrumentClass.SDR_FPGA
    assert caps.processing_location is ProcessingLocation.DEVICE
    assert caps.link is LinkKind.NETWORK


def test_fpga_streams_device_spectra() -> None:
    d = _driver(32)
    d.connect()
    assert d.identify().model == "SDR-FPGA"
    d.start()
    frames = list(itertools.islice(d.stream(), 5))
    d.stop()
    d.close()
    assert len(frames) == 5
    for f in frames:
        assert isinstance(f, SpectrumFrame)
        assert len(f.values) == 32
        assert all(0 <= v <= 255 for v in f.values)
    assert len({f.values for f in frames}) > 1  # drifting peak


def test_build_fpga_selects_simulator_without_address() -> None:
    d = build_fpga_driver("", 16)
    assert isinstance(d, FpgaSdrDriver)
    d2 = build_driver("sdr_fpga", "", 1, 16)
    assert isinstance(d2, FpgaSdrDriver)


def test_record_sdr_fpga_to_fits(client: TestClient) -> None:
    with Session(db.get_engine()) as s:
        auth.create_user(s, "op", "fpga-pass-123", Role.OPERATOR)
    client.post(
        "/api/v1/auth/login",
        json={"username": "op", "password": "fpga-pass-123"},
    )
    iid = client.post(
        "/api/v1/instruments",
        json={"name": "FPGA1", "instrument_class": "sdr_fpga", "channels": 24},
    ).json()["id"]
    client.post(f"/api/v1/instruments/{iid}/record?frames=5")
    get_recorder().join(iid, timeout=5.0)
    last = get_recorder().status(iid).last_file
    assert last is not None
    with fits.open(last) as hdul:
        assert hdul[0].data.shape == (24, 5)
