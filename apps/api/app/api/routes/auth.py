from __future__ import annotations

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from ...core.security import SESSION_COOKIE, SESSION_MAX_AGE, create_session, read_session
from ...db.session import get_db
from ...models.entities import User
from ...repositories.proofs import get_or_create_demo_user
from ...schemas.auth import AuthUser

router = APIRouter(prefix="/api/auth", tags=["auth"])


def serialize_user(user: User) -> AuthUser:
    return AuthUser(id=user.id, display_name=user.display_name, instagram_username=user.instagram_username, email=user.email)


def get_current_user(session: str | None = Cookie(default=None, alias=SESSION_COOKIE), db: Session = Depends(get_db)) -> User:
    from sqlalchemy import select

    user_id = read_session(session)
    user = db.scalar(select(User).where(User.id == user_id)) if user_id else None
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


@router.post("/demo", response_model=AuthUser)
def demo_login(response: Response, db: Session = Depends(get_db)) -> AuthUser:
    user = get_or_create_demo_user(db, "maya.creates")
    db.commit()
    response.set_cookie(SESSION_COOKIE, create_session(user.id), max_age=SESSION_MAX_AGE, httponly=True, samesite="lax", secure=False, path="/")
    return serialize_user(user)


@router.get("/me", response_model=AuthUser)
def current_user(user: User = Depends(get_current_user)) -> AuthUser:
    return serialize_user(user)


@router.post("/logout")
def logout(response: Response) -> dict[str, str]:
    response.delete_cookie(SESSION_COOKIE, path="/")
    return {"status": "signed_out"}
