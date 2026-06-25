"""Uploader: ship recorded files to a transport, tracking what's done.

gzip (optional) -> transport.put (tmp-then-rename inside the transport) ->
record an UploadJob so the file is not re-sent. Offline/retry behavior is the
caller's loop; this processes one pass. The transport is the pluggable seam.
"""

from __future__ import annotations

import gzip
import shutil
import tempfile
from pathlib import Path

from sqlmodel import Session, select

from ecallisto_ng.api.models import UploadJob, UploadTarget
from ecallisto_ng.core.contracts import UploadTransport
from ecallisto_ng.services import catalog


def _gzip_to_temp(src: Path) -> Path:
    fd, tmp_name = tempfile.mkstemp(suffix=".gz")
    tmp = Path(tmp_name)
    import os

    os.close(fd)
    with src.open("rb") as f_in, gzip.open(tmp, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
    return tmp


def upload_file(
    transport: UploadTransport, local: Path, remote_name: str, *, do_gzip: bool
) -> None:
    """Upload one file (optionally gzipped) and verify it."""
    transport.connect()
    try:
        if do_gzip:
            tmp = _gzip_to_temp(local)
            try:
                transport.put(tmp, remote_name)
                if not transport.verify(tmp, remote_name):
                    raise RuntimeError("upload verification failed")
            finally:
                tmp.unlink(missing_ok=True)
        else:
            transport.put(local, remote_name)
            if not transport.verify(local, remote_name):
                raise RuntimeError("upload verification failed")
    finally:
        transport.close()


def remote_name_for(local: Path, do_gzip: bool) -> str:
    return local.name + ".gz" if do_gzip else local.name


def build_transport(target: UploadTarget) -> UploadTransport:
    """Construct the transport for an ``UploadTarget`` row."""
    if target.protocol == "local":
        from ecallisto_ng.transports.local import LocalTransport

        return LocalTransport(target.host)
    if target.protocol == "ftp":
        from ecallisto_ng.transports.ftp import FtpTransport

        return FtpTransport(
            target.host, target.username, target.password, target.base_path
        )
    raise ValueError(f"unknown protocol: {target.protocol}")


def upload_pending(
    db: Session, target: UploadTarget, data_dir: Path
) -> dict[str, int]:
    """Upload every recording not yet sent to ``target``; record jobs."""
    uploaded = 0
    failed = 0
    for info in catalog.list_recordings(data_dir):
        done = db.exec(
            select(UploadJob).where(
                UploadJob.target_id == target.id,
                UploadJob.filename == info.name,
                UploadJob.state == "done",
            )
        ).first()
        if done is not None:
            continue
        local = data_dir / info.name
        remote = remote_name_for(local, target.gzip)
        try:
            upload_file(
                build_transport(target), local, remote, do_gzip=target.gzip
            )
            db.add(
                UploadJob(
                    target_id=target.id, filename=info.name, state="done"
                )
            )
            uploaded += 1
        except Exception as exc:  # noqa: BLE001 - record per-file failure
            db.add(
                UploadJob(
                    target_id=target.id,
                    filename=info.name,
                    state="error",
                    error=str(exc),
                )
            )
            failed += 1
    db.commit()
    return {"uploaded": uploaded, "failed": failed}
