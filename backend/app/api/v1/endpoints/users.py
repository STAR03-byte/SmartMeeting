"""用户 REST API。"""

from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.auth import CurrentUserOut
from app.schemas.user import UserCreate, UserOut
from app.services.user_service import create_user, delete_user, get_user, list_selectable_users, list_users, search_invitable_users
from .auth import get_current_user

router = APIRouter(prefix="/users", tags=["users"], dependencies=[Depends(get_current_user)])
open_router = APIRouter(tags=["register"])


@open_router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate, db: Session = Depends(get_db)) -> UserOut:
    payload = payload.model_copy(update={"role": "member"})
    try:
        return create_user(db, payload)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="用户名或邮箱已存在") from exc


@router.get("", response_model=list[UserOut])
def list_users_api(
    db: Session = Depends(get_db),
    current_user: CurrentUserOut = Depends(get_current_user),
    team_id: Annotated[int | None, Query()] = None,
    meeting_id: Annotated[int | None, Query()] = None,
    scope: Annotated[str, Query(pattern="^(selectable|all)$")] = "selectable",
) -> list[UserOut]:
    if scope == "all":
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="仅系统管理员可查看全部用户")
        return cast(list[UserOut], list_users(db))

    return cast(
        list[UserOut],
        list_selectable_users(
            db,
            current_user_id=current_user.id,
            is_admin=(current_user.role == "admin"),
            team_id=team_id,
            meeting_id=meeting_id,
        ),
    )


@router.get("/search", response_model=list[UserOut])
def search_users_api(
    db: Session = Depends(get_db),
    current_user: CurrentUserOut = Depends(get_current_user),
    team_id: Annotated[int, Query(ge=1)] = 0,
    keyword: Annotated[str, Query(min_length=2)] = "",
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
) -> list[UserOut]:
    if team_id <= 0:
        raise HTTPException(status_code=400, detail="team_id is required")

    return cast(
        list[UserOut],
        search_invitable_users(
            db,
            team_id=team_id,
            current_user_id=current_user.id,
            keyword=keyword,
            is_admin=(current_user.role == "admin"),
            limit=limit,
        ),
    )


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user_api(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUserOut = Depends(get_current_user),
) -> UserOut:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅系统管理员可创建用户")

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
