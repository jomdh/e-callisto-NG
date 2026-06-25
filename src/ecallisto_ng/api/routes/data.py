"""Data browsing: list / download / quicklook recorded FITS files."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse

from ecallisto_ng.api import auth
from ecallisto_ng.api.models import Role, User
from ecallisto_ng.api.settings import get_settings
from ecallisto_ng.api.templating import templates
from ecallisto_ng.services import catalog, spectrum

router = APIRouter(tags=["data"])

_viewer = auth.require_role(Role.VIEWER)


@router.get("/api/v1/files", dependencies=[Depends(_viewer)])
def list_files() -> list[catalog.FileInfo]:
    return catalog.list_recordings(get_settings().data_dir)


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
