"""Left-sidebar shell: present when authed, active highlight, none pre-auth."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlmodel import Session

from ecallisto_ng.api import auth, db
from ecallisto_ng.api.models import Role


def _login(client: TestClient) -> None:
    with Session(db.get_engine()) as s:
        auth.create_user(s, "op", "shell-pass-12", Role.OPERATOR)
    client.post(
        "/api/v1/auth/login",
        json={"username": "op", "password": "shell-pass-12"},
    )


def test_sidebar_present_when_authed(client: TestClient) -> None:
    _login(client)
    page = client.get("/portal")
    assert page.status_code == 200
    assert 'class="sidebar"' in page.text
    assert "nav-section-label" in page.text  # grouped sections
    assert "/static/js/sidebar.js" in page.text
    assert "material-design-system.css" in page.text
    # icons + section links
    assert '<span class="material-icons">dashboard</span>' in page.text
    assert 'href="/portal/manage/instruments"' in page.text


def test_active_highlight(client: TestClient) -> None:
    _login(client)
    tools = client.get("/portal/tools")
    assert 'class="nav-link active" href="/portal/tools"' in tools.text


def test_no_sidebar_pre_auth(client: TestClient) -> None:
    # login + wizard render without the sidebar (no user context)
    assert 'class="sidebar"' not in client.get("/", follow_redirects=True).text


def test_pages_render_in_shell(client: TestClient) -> None:
    _login(client)
    for path in (
        "/portal/manage/schedules",
        "/portal/data",
        "/portal/system",
        "/portal/tools",
        "/portal/viewer",
        "/portal/settings",
    ):
        r = client.get(path)
        assert r.status_code == 200, path
        assert 'class="sidebar"' in r.text, path
