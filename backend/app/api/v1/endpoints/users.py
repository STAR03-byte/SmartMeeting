"""用户 REST API。"""

from typing import cast

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.user import UserCreate, UserOut
from app.services.user_service import create_user, delete_user, get_user, list_users

router = APIRouter(prefix="/users", tags=["users"])
open_router = APIRouter(tags=["register"])


@open_router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate, db: Session = Depends(get_db)) -> UserOut:
    try:
        return create_user(db, payload)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="用户名或邮箱已存在") from exc


@router.get("", response_model=list[UserOut])
def list_users_api(db: Session = Depends(get_db)) -> list[UserOut]:
    return cast(list[UserOut], list_users(db))


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user_api(payload: UserCreate, db: Session = Depends(get_db)) -> UserOut:
    try:
        return create_user(db, payload)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Username or email already exists") from exc


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_api(user_id: int, db: Session = Depends(get_db)) -> None:
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    delete_user(db, user)
