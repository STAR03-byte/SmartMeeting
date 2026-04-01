from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.schemas.auth import CurrentUserOut, TokenOut
from app.services.auth_service import authenticate_user, create_user_access_token
from app.services.audit_service import create_audit_log
from app.services.user_service import get_user

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Annotated[Session, Depends(get_db)]) -> CurrentUserOut:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError, TypeError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    user = get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


@router.post("/login", response_model=TokenOut)
def login(
    payload: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
) -> TokenOut:
    user = authenticate_user(db, payload.username, payload.password)
    if user is None:
        create_audit_log(
            db=db,
            actor_user_id=None,
            entity_type="auth",
            entity_id=0,
            action="LOGIN_FAILED",
            before_data=None,
            after_data={"username": payload.username},
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    create_audit_log(
        db=db,
        actor_user_id=user.id,
        entity_type="auth",
        entity_id=user.id,
        action="LOGIN_SUCCESS",
        before_data=None,
        after_data={"username": user.username},
    )
    return TokenOut(access_token=create_user_access_token(user))


@router.get("/me", response_model=CurrentUserOut)
def me(
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
) -> CurrentUserOut:
    return current_user
