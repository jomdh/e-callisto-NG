"""Health endpoint smoke test against a temp SQLite database."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from ecallisto_ng import __version__
from ecallisto_ng.api import db
from ecallisto_ng.api.settings import get_settings


def _client(tmp_path: Path) -> TestClient:
    get_settings.cache_clear()
    db.reset_engine_for_tests()
    import os

    os.environ["ECALLISTO_DB_URL"] = f"sqlite:///{tmp_path / 'test.db'}"
    from ecallisto_ng.api.app import create_app

    return TestClient(create_app())


def test_health_ok(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["version"] == __version__
        assert body["db"] is True
