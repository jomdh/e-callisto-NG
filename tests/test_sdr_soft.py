"""Class-2 SDR (host DSP) driver against the contract + via the recorder."""

from __future__ import annotations

import itertools

from astropy.io import fits
from fastapi.testclient import TestClient
from sqlmodel import Session

from ecallisto_ng.api import auth, db
from ecallisto_ng.api.models import Role
from ecallisto_ng.core import InstrumentDriver, SpectrumFrame
from ecallisto_ng.core.units import InstrumentClass, ProcessingLocation
from ecallisto_ng.drivers.sdr import SoftSdrDriver
from ecallisto_ng.services.recorder import build_driver, get_recorder


def test_soft_sdr_conforms() -> None:
    assert isinstance(SoftSdrDriver(), InstrumentDriver)
    caps = SoftSdrDriver().capabilities
    assert caps.instrument_class is InstrumentClass.SDR_SOFT
    assert caps.processing_location is ProcessingLocation.HOST


def test_soft_sdr_streams_normalized_spectra() -> None:
    d = SoftSdrDriver(channels=64)
    d.connect()
    assert d.identify().model == "SDR-SOFT"
    d.start()
    frames = list(itertools.islice(d.stream(), 5))
    d.stop()
    d.close()
    assert len(frames) == 5
    for f in frames:
        assert isinstance(f, SpectrumFrame)
        assert len(f.values) == 64
        assert all(0 <= v <= 255 for v in f.values)
    # the DSP produces structure: not every frame is identical
    assert len({f.values for f in frames}) > 1


def test_build_driver_selects_sdr_soft() -> None:
    d = build_driver("sdr_soft", "", 1, 32)
    assert isinstance(d, SoftSdrDriver)


def test_record_sdr_soft_to_fits(client: TestClient) -> None:
    with Session(db.get_engine()) as s:
        auth.create_user(s, "op", "sdr-pass-1234", Role.OPERATOR)
    client.post(
        "/api/v1/auth/login",
        json={"username": "op", "password": "sdr-pass-1234"},
    )
    iid = client.post(
        "/api/v1/instruments",
        json={"name": "SDR1", "instrument_class": "sdr_soft", "channels": 32},
    ).json()["id"]
    client.post(f"/api/v1/instruments/{iid}/record?frames=6")
    get_recorder().join(iid, timeout=5.0)
    last = get_recorder().status(iid).last_file
    assert last is not None
    with fits.open(last) as hdul:
        assert hdul[0].data.shape == (32, 6)  # (freq, time)
