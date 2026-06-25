"""SFTP transport registration + dated backup archive (M14)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from sqlmodel import Session

from ecallisto_ng.api import db
from ecallisto_ng.api.models import UploadJob, UploadTarget
from ecallisto_ng.core import UploadTransport
from ecallisto_ng.services import uploader
from ecallisto_ng.services.uploader_service import archive_done, archive_file
from ecallisto_ng.transports.sftp import SftpTransport


def test_sftp_transport_conforms_and_builds() -> None:
    assert isinstance(SftpTransport("h"), UploadTransport)
    target = UploadTarget(
        name="s", protocol="sftp", host="ftp.example", base_path="/in"
    )
    assert isinstance(uploader.build_transport(target), SftpTransport)


def test_archive_file_dated_tree(tmp_path: Path) -> None:
    src = tmp_path / "X_20260625_120000_01.fit"
    src.write_text("data")
    archive = tmp_path / "FITbackup"
    dest = archive_file(src, archive, datetime(2026, 6, 25, tzinfo=UTC))
    assert dest == archive / "2026" / "06" / "25" / src.name
    assert dest.exists() and not src.exists()  # moved


def test_archive_done_moves_uploaded_only(
    client: object, tmp_path: Path
) -> None:
    from ecallisto_ng.api.settings import get_settings

    data_dir = get_settings().data_dir
    data_dir.mkdir(parents=True, exist_ok=True)
    up = data_dir / "UP_20260625_010000_01.fit"
    up.write_text("x")
    pending = data_dir / "PEND_20260625_020000_01.fit"
    pending.write_text("y")

    archive = tmp_path / "arch"
    with Session(db.get_engine()) as s:
        t = UploadTarget(name="t", protocol="local", host=str(tmp_path))
        s.add(t)
        s.commit()
        s.refresh(t)
        s.add(UploadJob(filename=up.name, target_id=t.id, state="done"))
        s.commit()
        moved = archive_done(s, data_dir, archive)

    assert moved == 1
    assert not up.exists()  # uploaded -> archived
    assert (archive / "2026" / "06" / "25" / up.name).exists()
    assert pending.exists()  # not uploaded -> kept
