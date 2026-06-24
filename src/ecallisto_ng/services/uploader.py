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

from ecallisto_ng.core.contracts import UploadTransport


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
