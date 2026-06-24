"""CLI smoke test: `record --driver fake` writes a FITS and prints it."""

from __future__ import annotations

from pathlib import Path

import pytest

from ecallisto_ng.cli import main


def test_cli_record_fake(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    rc = main(
        [
            "record",
            "--driver",
            "fake",
            "--instrument",
            "CLISTN",
            "--channels",
            "8",
            "--frames",
            "5",
            "--out",
            str(tmp_path),
        ]
    )
    assert rc == 0
    printed = capsys.readouterr().out.strip()
    out_path = Path(printed)
    assert out_path.exists()
    assert out_path.name.startswith("CLISTN_")
    assert out_path.suffix == ".fit"


def test_cli_callisto_requires_port(tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        main(
            [
                "record",
                "--driver",
                "callisto",
                "--out",
                str(tmp_path),
            ]
        )
