"""Process-isolation capability + drift-gating (M16)."""

from __future__ import annotations

from pathlib import Path

from ecallisto_ng.cli import build_parser
from ecallisto_ng.services.clock import within_drift

_ROOT = Path(__file__).resolve().parents[1]


def test_within_drift_gate() -> None:
    assert within_drift(None, 50.0) is True  # unknown -> allowed
    assert within_drift(10.0, 0.0) is True  # gate off (max 0)
    assert within_drift(10.0, 50.0) is True  # within tolerance
    assert within_drift(-10.0, 50.0) is True  # abs value
    assert within_drift(80.0, 50.0) is False  # exceeds -> blocked


def test_acquire_subcommand_registered() -> None:
    parser = build_parser()
    args = parser.parse_args(["acquire"])
    assert args.command == "acquire"
    assert callable(args.func)


def test_acquire_unit_packaged() -> None:
    unit = _ROOT / "packaging" / "systemd" / "ecallisto-acquire.service"
    assert unit.exists()
    text = unit.read_text()
    assert "ecallisto-ng acquire" in text
    assert "Restart=always" in text


def test_run_loops_in_web_setting_default() -> None:
    from ecallisto_ng.api.settings import Settings

    assert Settings().run_loops_in_web is True
