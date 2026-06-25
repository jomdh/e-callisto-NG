# SPDX-License-Identifier: AGPL-3.0-or-later
"""Instrument CRUD + record control."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session as DbSession
from sqlmodel import select

from ecallisto_ng.api.auth import require_role
from ecallisto_ng.api.db import get_session
from ecallisto_ng.api.models import CalibrationSet, Instrument, Role, User
from ecallisto_ng.api.settings import get_settings
from ecallisto_ng.core.calibration import Calibration
from ecallisto_ng.core.contracts import BenchCapable
from ecallisto_ng.core.recording import RecordingMeta
from ecallisto_ng.core.units import UnitLevel
from ecallisto_ng.services import bench as bench_svc
from ecallisto_ng.services import noise_figure as nf_svc
from ecallisto_ng.services import port_lock, recorder_state
from ecallisto_ng.services.calibration_build import resolve
from ecallisto_ng.services.channels import resolve_channels
from ecallisto_ng.services.overview import run_overview
from ecallisto_ng.services.recorder import (
    RecorderState,
    build_driver,
    get_recorder,
)
from ecallisto_ng.services.timing import get_time_source
from ecallisto_ng.writers.fits import get_writer

router = APIRouter(prefix="/api/v1/instruments", tags=["instruments"])

_viewer = require_role(Role.VIEWER)
_operator = require_role(Role.OPERATOR)


class InstrumentIn(BaseModel):
    name: str
    instrument_class: str = "heterodyne"
    address: str = ""
    focus_code: int = 1
    gain: int = 120
    channels: int = 200
    sweep_rate_hz: float = 4.0
    file_seconds: int = 900
    unit: str = "raw"
    output_mode: str = "standard"
    program_id: int | None = None  # frequency plan (range/channels), M32
    calibration_set_id: int | None = None
    enabled: bool = True


def _instrument_calibration(
    db: DbSession, inst: Instrument
) -> tuple[UnitLevel, Calibration | None]:
    coeffs: str | None = None
    if inst.calibration_set_id is not None:
        cs = db.get(CalibrationSet, inst.calibration_set_id)
        if cs is not None:
            coeffs = cs.coefficients_json
    return resolve(inst.unit, coeffs, inst.channels)


def _get(db: DbSession, instrument_id: int) -> Instrument:
    obj = db.get(Instrument, instrument_id)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no such instrument")
    return obj


def _hw_error(exc: OSError) -> HTTPException:
    """Turn a hardware/serial open failure into a clear 503 (not a raw 500)."""
    msg = str(exc)
    hint = ""
    if "Permission denied" in msg:
        hint = (
            " -- add the user to the 'dialout' group "
            "(sudo usermod -aG dialout <user>) then log out and back in"
        )
    elif "could not open port" in msg or "No such file" in msg:
        hint = " -- check the address and that the device is plugged in"
    return HTTPException(
        status.HTTP_503_SERVICE_UNAVAILABLE, f"hardware error: {msg}{hint}"
    )


@router.get("", dependencies=[Depends(_viewer)])
def list_instruments(db: DbSession = Depends(get_session)) -> list[Instrument]:
    return list(db.exec(select(Instrument)).all())


@router.post("", status_code=201, dependencies=[Depends(_operator)])
def create_instrument(
    body: InstrumentIn, db: DbSession = Depends(get_session)
) -> Instrument:
    obj = Instrument(**body.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/{instrument_id}", dependencies=[Depends(_viewer)])
def get_instrument(
    instrument_id: int, db: DbSession = Depends(get_session)
) -> Instrument:
    return _get(db, instrument_id)


@router.patch("/{instrument_id}", dependencies=[Depends(_operator)])
def update_instrument(
    instrument_id: int,
    body: InstrumentIn,
    db: DbSession = Depends(get_session),
) -> Instrument:
    obj = _get(db, instrument_id)
    for key, value in body.model_dump().items():
        setattr(obj, key, value)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete(
    "/{instrument_id}", status_code=204, dependencies=[Depends(_operator)]
)
def delete_instrument(
    instrument_id: int, db: DbSession = Depends(get_session)
) -> None:
    db.delete(_get(db, instrument_id))
    db.commit()


@router.post("/{instrument_id}/record", dependencies=[Depends(_operator)])
def record_instrument(
    instrument_id: int,
    frames: int = 0,
    db: DbSession = Depends(get_session),
) -> dict[str, str]:
    """Start recording. ``frames=0`` (default) records **continuously** until
    Stop, rolling a file every ``file_seconds``; ``frames>0`` is a bounded
    test capture of that many sweeps."""
    inst = _get(db, instrument_id)
    if port_lock.is_busy(instrument_id):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "instrument is busy (a bench/overview op is using the port)",
        )
    driver = build_driver(
        inst.instrument_class, inst.address, inst.focus_code, inst.channels
    )
    channels = resolve_channels(db, inst)
    tsrc = get_time_source(get_settings().time_source)
    meta = RecordingMeta(
        instrument=inst.name,
        focus_code=inst.focus_code,
        time_source=tsrc.name,
        clock_offset_ms=tsrc.offset_ms(),
    )
    out_dir = get_settings().data_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    unit, calibration = _instrument_calibration(db, inst)
    continuous = frames <= 0
    # In continuous mode max_frames is the per-file rollover size.
    per_file = max(int(inst.file_seconds * inst.sweep_rate_hz), 1)
    try:
        get_recorder().start(
            instrument_id,
            driver,
            channels,
            meta,
            out_dir,
            sweep_rate_hz=inst.sweep_rate_hz,
            max_frames=per_file if continuous else frames,
            unit=unit,
            calibration=calibration,
            writer=get_writer(inst.output_mode),
            continuous=continuous,
            on_state=lambda st, lf: recorder_state.write(
                instrument_id, st, lf
            ),
        )
    except RuntimeError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    return {"state": RecorderState.RECORDING}


@router.post("/{instrument_id}/stop", dependencies=[Depends(_operator)])
def stop_instrument(instrument_id: int) -> dict[str, bool]:
    get_recorder().stop(instrument_id)
    return {"ok": True}


@router.post("/{instrument_id}/reconnect")
def reconnect_instrument(
    instrument_id: int,
    db: DbSession = Depends(get_session),
    actor: User = Depends(_operator),
) -> dict[str, object]:
    """Reconnect the receiver via the host hook (ADR-0008)."""
    from ecallisto_ng.services import audit, host

    _get(db, instrument_id)
    ok, message = host.run_hook("reconnect", str(instrument_id))
    audit.record(
        db,
        actor.username,
        "host.reconnect",
        target=str(instrument_id),
        detail="ok" if ok else message,
    )
    return {"ok": ok, "message": message}


@router.post("/{instrument_id}/overview", dependencies=[Depends(_operator)])
def overview_instrument(
    instrument_id: int, db: DbSession = Depends(get_session)
) -> dict[str, str]:
    """Run a 45-870 MHz spectral overview now; write the OVS .prn/.csv pair."""
    inst = _get(db, instrument_id)
    if get_recorder().status(instrument_id).state is RecorderState.RECORDING:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "instrument is recording"
        )
    driver = build_driver(
        inst.instrument_class, inst.address, inst.focus_code, inst.channels
    )
    out_dir = get_settings().data_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        with port_lock.hold(instrument_id):
            prn, csv = run_overview(
                driver,
                out_dir,
                inst.name,
                datetime.now(UTC),
                focus_code=inst.focus_code,
                pwm=inst.gain,
            )
    except port_lock.InstrumentBusy as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "instrument is busy (the port is in use by another operation)",
        ) from exc
    except OSError as exc:
        raise _hw_error(exc) from exc
    return {"prn": prn.name, "csv": csv.name}


class BenchSweepIn(BaseModel):
    f_min: float = 45.0
    f_max: float = 870.0
    n_points: int = 100
    gain: int = 120
    relay: int | None = None


def _bench_driver(db: DbSession, instrument_id: int) -> BenchCapable:
    inst = _get(db, instrument_id)
    if get_recorder().status(instrument_id).state is RecorderState.RECORDING:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "instrument is recording"
        )
    driver = build_driver(
        inst.instrument_class, inst.address, inst.focus_code, inst.channels
    )
    if not isinstance(driver, BenchCapable):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "instrument does not support bench mode",
        )
    return driver


@contextmanager
def _bench_session(
    db: DbSession, instrument_id: int
) -> Iterator[BenchCapable]:
    """Bench driver + exclusive port lock + connect/close + error mapping.

    Serializes serial access: a second bench/overview op while one is running
    gets a clean 409 instead of a pyserial "multiple access" collision.
    """
    driver = _bench_driver(db, instrument_id)
    try:
        with port_lock.hold(instrument_id):
            driver.connect()  # type: ignore[attr-defined]
            try:
                yield driver
            finally:
                driver.close()  # type: ignore[attr-defined]
    except port_lock.InstrumentBusy as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "instrument is busy (the port is in use by another operation)",
        ) from exc
    except OSError as exc:
        raise _hw_error(exc) from exc


@router.get(
    "/{instrument_id}/bench/detector", dependencies=[Depends(_operator)]
)
def bench_detector(
    instrument_id: int,
    freq: float = 150.0,
    gain: int = 120,
    db: DbSession = Depends(get_session),
) -> dict[str, float]:
    """Tune + read the detector voltage once (legacy 'simple' tool)."""
    with _bench_session(db, instrument_id) as driver:
        mv = bench_svc.read_detector(driver, freq, gain)
    return {"mv": mv, "freq": freq, "gain": float(gain)}


@router.post("/{instrument_id}/bench/sweep", dependencies=[Depends(_operator)])
def bench_sweep(
    instrument_id: int,
    body: BenchSweepIn,
    db: DbSession = Depends(get_session),
) -> dict[str, object]:
    """Sweep detector voltage vs frequency (underlies NF/bandpass, M12)."""
    with _bench_session(db, instrument_id) as driver:
        points = bench_svc.sweep(
            driver,
            body.f_min,
            body.f_max,
            body.n_points,
            body.gain,
            body.relay,
        )
    return {"points": points}


class NoiseFigureIn(BaseModel):
    f_min: float = 45.0
    f_max: float = 870.0
    n_points: int = 100
    gain: int = 250
    enr_db: float = 15.0
    att_db: float = 10.1
    cold_relay: int = 0
    warm_relay: int = 3
    hot_relay: int = 1
    integration: int = 1  # reads averaged per point (C3)
    settle_s: float = 0.0  # relay-settle delay (C7)
    # A fixed detector gradient (mV/dB) to use instead of the measured
    # per-point slope -- legacy single-constant NF (C4); None = per-point.
    gradient: float | None = None


@router.post(
    "/{instrument_id}/bench/noise_figure", dependencies=[Depends(_operator)]
)
def bench_noise_figure(
    instrument_id: int,
    body: NoiseFigureIn,
    db: DbSession = Depends(get_session),
) -> dict[str, object]:
    """Cold/warm/hot Y-factor noise figure + slope + bandpass (legacy NF)."""
    with _bench_session(db, instrument_id) as driver:

        def _sweep(relay: int) -> list[tuple[float, float]]:
            return bench_svc.sweep(
                driver,
                body.f_min,
                body.f_max,
                body.n_points,
                body.gain,
                relay=relay,
                integration=body.integration,
                settle_s=body.settle_s,
            )

        cold = _sweep(body.cold_relay)
        warm = _sweep(body.warm_relay)
        hot = _sweep(body.hot_relay)
    freqs = [f for f, _ in cold]
    cold_mv = [v for _, v in cold]
    warm_mv = [v for _, v in warm]
    hot_mv = [v for _, v in hot]
    slope = nf_svc.detector_slope(warm_mv, hot_mv, body.att_db)
    # C4: the configured scalar gradient if given, else the per-point slope.
    divisor: nf_svc.SlopeLike = (
        body.gradient if body.gradient is not None else slope
    )
    nf = nf_svc.noise_figure(cold_mv, hot_mv, divisor, body.enr_db)
    bandpass = nf_svc.bandpass(cold_mv, hot_mv, divisor)
    nf_stat = nf_svc.stats(nf)
    return {
        "freqs": freqs,
        "noise_figure": nf,
        "slope_mv_db": slope,
        "bandpass_db": bandpass,
        "nf_mean": nf_stat.mean,
        "nf_sigma": nf_stat.sigma,
    }


class AgcSweepIn(BaseModel):
    freq: float = 150.0
    pwm_min: int = 0
    pwm_max: int = 255
    pwm_step: int = 5


@router.post(
    "/{instrument_id}/bench/agc_sweep", dependencies=[Depends(_operator)]
)
def bench_agc_sweep(
    instrument_id: int,
    body: AgcSweepIn,
    db: DbSession = Depends(get_session),
) -> dict[str, object]:
    """AGC commissioning: detector voltage vs PWM gain (legacy AGC, C5)."""
    with _bench_session(db, instrument_id) as driver:
        points = bench_svc.agc_sweep(
            driver, body.freq, body.pwm_min, body.pwm_max, body.pwm_step
        )
    return {"points": points}


class ScopeIn(BaseModel):
    freq: float = 150.0
    gain: int = 120
    n_samples: int = 256
    threshold_mv: float | None = None


@router.post("/{instrument_id}/bench/scope", dependencies=[Depends(_operator)])
def bench_scope(
    instrument_id: int,
    body: ScopeIn,
    db: DbSession = Depends(get_session),
) -> dict[str, object]:
    """Time-domain detector capture + optional trigger (legacy scope, C6)."""
    with _bench_session(db, instrument_id) as driver:
        samples, triggered = bench_svc.scope(
            driver, body.freq, body.gain, body.n_samples, body.threshold_mv
        )
    return {"samples": samples, "triggered": triggered}


@router.get("/{instrument_id}/status", dependencies=[Depends(_viewer)])
def instrument_status(instrument_id: int) -> dict[str, object]:
    st = get_recorder().status(instrument_id)
    return {"state": st.state, "last_file": st.last_file, "error": st.error}


@router.get("/{instrument_id}/capabilities", dependencies=[Depends(_viewer)])
def instrument_capabilities(
    instrument_id: int, db: DbSession = Depends(get_session)
) -> dict[str, object]:
    """What device functions this instrument supports (class-gated, M25)."""
    inst = _get(db, instrument_id)
    driver = build_driver(
        inst.instrument_class, inst.address, inst.focus_code, inst.channels
    )
    caps = driver.capabilities
    return {
        "instrument_class": inst.instrument_class,
        "bench": isinstance(driver, BenchCapable),
        "overview": caps.supports_overview,
        "processing": caps.processing_location,
        "link": caps.link,
    }


@router.get("/{instrument_id}/diagnose", dependencies=[Depends(_operator)])
def diagnose_instrument(
    instrument_id: int, db: DbSession = Depends(get_session)
) -> dict[str, object]:
    """Probe the device: connect, identify, report info + capabilities."""
    inst = _get(db, instrument_id)
    driver = build_driver(
        inst.instrument_class, inst.address, inst.focus_code, inst.channels
    )
    try:
        driver.connect()
        info = driver.identify()
        caps = driver.capabilities
    except Exception as exc:  # noqa: BLE001 - report any probe failure
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, f"probe failed: {exc}"
        ) from exc
    finally:
        driver.close()
    return {
        "model": info.model,
        "firmware": info.firmware,
        "instrument_class": caps.instrument_class,
        "bit_depth": caps.bit_depth,
        "max_channels": caps.max_channels,
        "supports_overview": caps.supports_overview,
        "supports_calibration": caps.supports_calibration,
    }
