"""用户 REST API。"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.auth import CurrentUserOut
from app.schemas.user import UserCreate, UserOut, UserUpdate
from app.services.user_service import create_user, delete_user, get_user, list_users, update_user
from .auth import get_current_user

router = APIRouter(prefix="/users", tags=["users"])
open_router = APIRouter(tags=["register"])


@open_router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate, db: Session = Depends(get_db)) -> UserOut:
    try:
        return create_user(db, payload)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="用户名或邮箱已存在") from exc


def _require_admin(current_user: CurrentUserOut) -> None:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user_api(payload: UserCreate, db: Session = Depends(get_db)) -> UserOut:
    """创建用户。"""
    try:
        return create_user(db, payload)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Username or email already exists") from exc


@router.get("", response_model=list[UserOut])
def list_users_api(
    db: Session = Depends(get_db),
    current_user: CurrentUserOut = Depends(get_current_user),
) -> list[UserOut]:
    """查询用户列表。"""

    _require_admin(current_user)
    return [UserOut.model_validate(user) for user in list_users(db)]


@router.get("/{user_id}", response_model=UserOut)
def get_user_api(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUserOut = Depends(get_current_user),
) -> UserOut:
    """查询用户详情。"""

    _require_admin(current_user)
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserOut)
def update_user_api(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUserOut = Depends(get_current_user),
) -> UserOut:
    """更新用户。"""

    _require_admin(current_user)
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return update_user(db, user, payload)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_api(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUserOut = Depends(get_current_user),
) -> None:
    """删除用户。"""

    _require_admin(current_user)
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Admin cannot delete self")
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    delete_user(db, user)
