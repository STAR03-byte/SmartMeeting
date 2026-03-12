"""用户 REST API。"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.user import UserCreate, UserOut, UserUpdate
from app.services.user_service import create_user, delete_user, get_user, list_users, update_user

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user_api(payload: UserCreate, db: Session = Depends(get_db)) -> UserOut:
    """创建用户。"""

    return create_user(db, payload)


@router.get("", response_model=list[UserOut])
def list_users_api(db: Session = Depends(get_db)) -> list[UserOut]:
    """查询用户列表。"""

    return list_users(db)


@router.get("/{user_id}", response_model=UserOut)
def get_user_api(user_id: int, db: Session = Depends(get_db)) -> UserOut:
    """查询用户详情。"""

    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserOut)
def update_user_api(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)) -> UserOut:
    """更新用户。"""

    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return update_user(db, user, payload)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_api(user_id: int, db: Session = Depends(get_db)) -> None:
    """删除用户。"""

    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    delete_user(db, user)
