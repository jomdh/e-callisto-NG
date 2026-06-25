"""Health endpoint smoke test (uses the shared client fixture)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from ecallisto_ng import __version__


def test_health_ok(client: TestClient) -> None:
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["version"] == __version__
    assert body["db"] is True
