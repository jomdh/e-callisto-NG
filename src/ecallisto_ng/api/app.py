"""FastAPI application factory.

``create_app()`` builds the app so tests and the server share one construction
path. M1 grows this with auth, the portal, the wizard, and instrument routes;
S005 establishes the skeleton + a health probe.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from ecallisto_ng import __version__
from ecallisto_ng.api import models  # noqa: F401 -- register tables
from ecallisto_ng.api.db import get_engine, init_db
from ecallisto_ng.api.routes import access as access_routes
from ecallisto_ng.api.routes import auth as auth_routes
from ecallisto_ng.api.routes import calibration as calibration_routes
from ecallisto_ng.api.routes import data as data_routes
from ecallisto_ng.api.routes import fleet as fleet_routes
from ecallisto_ng.api.routes import instruments as instrument_routes
from ecallisto_ng.api.routes import live as live_routes
from ecallisto_ng.api.routes import migrate as migrate_routes
from ecallisto_ng.api.routes import portal as portal_routes
from ecallisto_ng.api.routes import programs as program_routes
from ecallisto_ng.api.routes import schedules as schedule_routes
from ecallisto_ng.api.routes import system as system_routes
from ecallisto_ng.api.routes import upload as upload_routes
from ecallisto_ng.api.routes import wizard as wizard_routes
from ecallisto_ng.api.templating import STATIC_DIR


@asynccontextmanager
async def _lifespan(_app: FastAPI) -> AsyncIterator[None]:
    from ecallisto_ng.services.scheduler_service import get_scheduler
    from ecallisto_ng.services.uploader_service import get_uploader

    init_db()
    get_scheduler().start_loop()
    get_uploader().start_loop()
    try:
        yield
    finally:
        get_scheduler().stop_loop()
        get_uploader().stop_loop()


_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'nonce-{nonce}'; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
    "font-src https://fonts.gstatic.com; "
    "img-src 'self' data:; "
    "connect-src 'self' ws: wss:"
)


def create_app() -> FastAPI:
    import secrets

    from starlette.requests import Request

    app = FastAPI(
        title="e-Callisto NG", version=__version__, lifespan=_lifespan
    )

    @app.middleware("http")
    async def _csp(request: Request, call_next: object) -> object:
        nonce = secrets.token_urlsafe(16)
        request.state.csp_nonce = nonce
        response = await call_next(request)  # type: ignore[operator]
        response.headers["Content-Security-Policy"] = _CSP.format(nonce=nonce)
        return response

    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    app.include_router(auth_routes.router)
    app.include_router(instrument_routes.router)
    app.include_router(portal_routes.router)
    app.include_router(wizard_routes.router)
    app.include_router(live_routes.router)
    app.include_router(data_routes.router)
    app.include_router(program_routes.router)
    app.include_router(schedule_routes.router)
    app.include_router(upload_routes.router)
    app.include_router(system_routes.router)
    app.include_router(calibration_routes.router)
    app.include_router(access_routes.router)
    app.include_router(migrate_routes.router)
    app.include_router(fleet_routes.router)

    @app.get("/api/v1/health")
    def health() -> dict[str, object]:
        db_ok = True
        try:
            with get_engine().connect() as conn:
                conn.execute(text("SELECT 1"))
        except Exception:  # pragma: no cover - defensive
            db_ok = False
        return {"status": "ok", "version": __version__, "db": db_ok}

    return app
