from typing import Annotated
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi import Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.limiter import limiter
from app.schemas.auth import CurrentUserOut, TokenOut
from app.services.auth_service import authenticate_user, create_user_access_token
from app.services.audit_service import create_audit_log
from app.services.user_service import get_user

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

logger = logging.getLogger(__name__)


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
@limiter.limit(settings.auth_login_rate_limit)
def login(
    request: Request,
    payload: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
) -> TokenOut:
    try:
        logger.info("Login attempt for user: %s", payload.username)
        user = authenticate_user(db, payload.username, payload.password)
        if user is None:
            logger.warning("Login failed for user: %s - invalid credentials", payload.username)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        token = create_user_access_token(user)
        logger.info("Login successful for user: %s", payload.username)
        return TokenOut(access_token=token)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Login error for user %s: %s", payload.username, exc)
        raise


@router.get("/me", response_model=CurrentUserOut)
def me(
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
) -> CurrentUserOut:
    return current_user
