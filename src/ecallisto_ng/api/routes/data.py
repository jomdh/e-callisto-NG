"""Data browsing: list / download / quicklook recorded FITS files."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from pydantic import BaseModel
from sqlmodel import Session as DbSession
from sqlmodel import select

from ecallisto_ng.api import auth
from ecallisto_ng.api.db import get_session
from ecallisto_ng.api.models import Role, UploadJob, User
from ecallisto_ng.api.settings import get_settings
from ecallisto_ng.api.templating import templates
from ecallisto_ng.services import catalog, spectrum
from ecallisto_ng.services.lightcurve_png import render_lightcurve_png

router = APIRouter(tags=["data"])

_viewer = auth.require_role(Role.VIEWER)
_operator = auth.require_role(Role.OPERATOR)


@router.get("/api/v1/files", dependencies=[Depends(_viewer)])
def list_files() -> list[catalog.FileInfo]:
    return catalog.list_recordings(get_settings().data_dir)


@router.get("/api/v1/files/calendar", dependencies=[Depends(_viewer)])
def files_calendar() -> dict[str, int]:
    """Recordings-per-day for the data-browser heatmap."""
    return catalog.recordings_by_day(get_settings().data_dir)


@router.get("/api/v1/files/{name}/header", dependencies=[Depends(_viewer)])
def file_header(name: str) -> dict[str, str]:
    path = catalog.resolve_in(get_settings().data_dir, name)
    if path is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no such file")
    return catalog.fits_header(path)


class BulkIn(BaseModel):
    names: list[str]


@router.post("/api/v1/files/bulk/delete", dependencies=[Depends(_operator)])
def bulk_delete(
    body: BulkIn, db: DbSession = Depends(get_session)
) -> dict[str, int]:
    """Delete selected recordings (and their upload jobs)."""
    data_dir = get_settings().data_dir
    deleted = 0
    for name in body.names:
        path = catalog.resolve_in(data_dir, name)
        if path is None:
            continue
        path.unlink(missing_ok=True)
        for job in db.exec(
            select(UploadJob).where(UploadJob.filename == name)
        ).all():
            db.delete(job)
        deleted += 1
    db.commit()
    return {"deleted": deleted}


@router.post("/api/v1/files/bulk/requeue", dependencies=[Depends(_operator)])
def bulk_requeue(
    body: BulkIn, db: DbSession = Depends(get_session)
) -> dict[str, int]:
    """Re-queue uploads: drop the 'done' jobs so the files upload again."""
    requeued = 0
    for name in body.names:
        for job in db.exec(
            select(UploadJob).where(
                UploadJob.filename == name, UploadJob.state == "done"
            )
        ).all():
            db.delete(job)
            requeued += 1
    db.commit()
    return {"requeued": requeued}


@router.get("/api/v1/spectra", dependencies=[Depends(_viewer)])
def list_spectra() -> list[str]:
    """Names of 2-column spectrum files (overviews etc.) for the viewer."""
    return spectrum.list_spectra(get_settings().data_dir)


@router.get("/api/v1/spectra/{name}", dependencies=[Depends(_viewer)])
def get_spectrum(name: str) -> dict[str, list[float]]:
    """Parsed (freqs, amps) of a 2-column spectrum file."""
    path = catalog.resolve_in(get_settings().data_dir, name)
    if path is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no such file")
    freqs, amps = spectrum.parse_two_column(path.read_text())
    return {"freqs": freqs, "amps": amps}


@router.get("/api/v1/lightcurves", dependencies=[Depends(_viewer)])
def list_lightcurves() -> list[str]:
    """Daily light-curve files (``LC*.txt``) available for rendering."""
    data_dir = get_settings().data_dir
    if not data_dir.is_dir():
        return []
    return sorted(
        p.name
        for p in data_dir.iterdir()
        if p.is_file() and p.name.startswith("LC") and p.suffix == ".txt"
    )


@router.get("/api/v1/lightcurves/{name}/png", dependencies=[Depends(_viewer)])
def lightcurve_png(name: str) -> FileResponse:
    """Render the public 24-h UT light-curve PNG (wwwgeni parity)."""
    settings = get_settings()
    path = catalog.resolve_in(settings.data_dir, name)
    if path is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no such file")
    out_dir = settings.data_dir / "lightcurves"
    out_dir.mkdir(parents=True, exist_ok=True)
    png = render_lightcurve_png(path, out_dir)
    return FileResponse(png, media_type="image/png")


@router.get("/api/v1/files/{name}/download", dependencies=[Depends(_viewer)])
def download_file(name: str) -> FileResponse:
    path = catalog.resolve_in(get_settings().data_dir, name)
    if path is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no such file")
    return FileResponse(
        path, media_type="application/fits", filename=path.name
    )


@router.get("/api/v1/files/{name}/quicklook", dependencies=[Depends(_viewer)])
def quicklook(name: str) -> FileResponse:
    settings = get_settings()
    path = catalog.resolve_in(settings.data_dir, name)
    if path is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no such file")
    png = catalog.quicklook_png(path, settings.data_dir / "quicklook")
    return FileResponse(png, media_type="image/png")


@router.get("/portal/data", response_class=HTMLResponse)
def data_page(
    request: Request, user: User | None = Depends(auth.optional_user)
) -> object:
    if user is None:
        return RedirectResponse("/", status_code=303)
    files = catalog.list_recordings(get_settings().data_dir)
    return templates.TemplateResponse(
        request, "portal/data.html", {"user": user, "files": files}
    )
