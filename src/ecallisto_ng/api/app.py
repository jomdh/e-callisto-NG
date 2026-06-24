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
from ecallisto_ng.api.routes import auth as auth_routes
from ecallisto_ng.api.routes import instruments as instrument_routes
from ecallisto_ng.api.routes import portal as portal_routes
from ecallisto_ng.api.templating import STATIC_DIR


@asynccontextmanager
async def _lifespan(_app: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="e-Callisto NG", version=__version__, lifespan=_lifespan
    )
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    app.include_router(auth_routes.router)
    app.include_router(instrument_routes.router)
    app.include_router(portal_routes.router)

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
