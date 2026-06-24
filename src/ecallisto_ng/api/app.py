"""FastAPI application factory.

``create_app()`` builds the app so tests and the server share one construction
path. M1 grows this with auth, the portal, the wizard, and instrument routes;
S005 establishes the skeleton + a health probe.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from ecallisto_ng import __version__
from ecallisto_ng.api.db import get_engine, init_db


@asynccontextmanager
async def _lifespan(_app: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="e-Callisto NG", version=__version__, lifespan=_lifespan
    )

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
