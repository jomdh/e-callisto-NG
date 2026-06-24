"""Command-line entry point.

``ecallisto-ng record`` runs one recording end-to-end -- from a driver (the
hardware-free fake, or a Callisto over serial) to a standard FITS file -- and
prints the path. This is the M0 deliverable; the web app (M1+) is separate.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from ecallisto_ng.core.contracts import InstrumentDriver
from ecallisto_ng.core.recording import RecordingMeta
from ecallisto_ng.core.spectra import Channel
from ecallisto_ng.drivers.callisto import CallistoConfig, CallistoDriver
from ecallisto_ng.drivers.fake import FakeDriver
from ecallisto_ng.services.acquisition import record
from ecallisto_ng.writers.fits import StandardFitsWriter


def _build_driver(args: argparse.Namespace) -> InstrumentDriver:
    if args.driver == "fake":
        return FakeDriver(channels=args.channels)
    if args.driver == "callisto":
        if not args.port:
            raise SystemExit("--port is required for --driver callisto")
        from ecallisto_ng.connections.serial_link import SerialConnection

        conn = SerialConnection(args.port)
        return CallistoDriver(
            conn, config=CallistoConfig(focuscode=args.focus)
        )
    raise SystemExit(f"unknown driver: {args.driver}")


def _cmd_record(args: argparse.Namespace) -> int:
    driver = _build_driver(args)
    channels = tuple(
        Channel(frequency_mhz=45.0 + i) for i in range(args.channels)
    )
    meta = RecordingMeta(instrument=args.instrument, focus_code=args.focus)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = record(
        driver,
        StandardFitsWriter(),
        channels,
        meta,
        out_dir,
        sweeps_per_second=args.sweep_rate,
        max_frames=args.frames,
    )
    print(path)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ecallisto-ng")
    sub = parser.add_subparsers(dest="command", required=True)

    rec = sub.add_parser("record", help="record one FITS file")
    rec.add_argument("--driver", choices=["fake", "callisto"], default="fake")
    rec.add_argument("--port", help="serial port (callisto driver)")
    rec.add_argument("--instrument", default="STATION")
    rec.add_argument("--channels", type=int, default=200)
    rec.add_argument("--frames", type=int, default=100)
    rec.add_argument("--sweep-rate", type=float, default=4.0)
    rec.add_argument("--focus", type=int, default=1)
    rec.add_argument("--out", default=".")
    rec.set_defaults(func=_cmd_record)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
