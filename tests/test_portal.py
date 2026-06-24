"""Portal: login page, form login -> dashboard, anonymous redirect."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlmodel import Session

from ecallisto_ng.api import auth, db
from ecallisto_ng.api.models import Role


def _make_operator() -> None:
    with Session(db.get_engine()) as session:
        auth.create_user(session, "op", "operator-pass-1", Role.OPERATOR)


def test_login_page_renders(client: TestClient) -> None:
    _make_operator()  # configured -> / shows login (not the wizard)
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Sign in" in resp.text
    assert "data-theme" in resp.text  # M3 theme bootstrap


def test_form_login_to_dashboard(client: TestClient) -> None:
    _make_operator()
    resp = client.post(
        "/login",
        data={"username": "op", "password": "operator-pass-1"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert "Instruments" in resp.text
    assert "op (operator)" in resp.text


def test_bad_login_shows_error(client: TestClient) -> None:
    _make_operator()
    resp = client.post(
        "/login",
        data={"username": "op", "password": "wrong"},
        follow_redirects=True,
    )
    assert resp.status_code == 401
    assert "Invalid username or password" in resp.text


def test_anonymous_dashboard_redirects(client: TestClient) -> None:
    resp = client.get("/portal", follow_redirects=False)
    assert resp.status_code == 303
    assert resp.headers["location"] == "/"


def test_static_css_served(client: TestClient) -> None:
    resp = client.get("/static/css/material-design-system.css")
    assert resp.status_code == 200
    assert "--nebula-accent" in resp.text
