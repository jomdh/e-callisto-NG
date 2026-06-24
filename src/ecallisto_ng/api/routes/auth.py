"""Auth routes: login, logout, me."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel
from sqlmodel import Session as DbSession

from ecallisto_ng.api import auth
from ecallisto_ng.api.db import get_session
from ecallisto_ng.api.models import Role, User

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    username: str
    role: Role


@router.post("/login", response_model=UserOut)
def login(
    body: LoginRequest,
    response: Response,
    db: DbSession = Depends(get_session),
) -> User:
    return auth.login(db, response, body.username, body.password)


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    db: DbSession = Depends(get_session),
) -> dict[str, bool]:
    auth.logout(db, request, response)
    return {"ok": True}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(auth.get_current_user)) -> User:
    return user
