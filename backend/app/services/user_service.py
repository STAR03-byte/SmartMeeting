"""用户服务层。"""

from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


def create_user(db: Session, payload: UserCreate) -> User:
    """创建用户。"""

    user = User(**payload.model_dump())
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def list_users(db: Session) -> list[User]:
    """查询用户列表。"""

    return db.query(User).order_by(User.id.desc()).all()


def get_user(db: Session, user_id: int) -> User | None:
    """按 ID 查询用户。"""

    return db.query(User).filter(User.id == user_id).first()


def update_user(db: Session, user: User, payload: UserUpdate) -> User:
    """更新用户。"""

    data: dict[str, object] = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(user, key, value)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user: User) -> None:
    """删除用户。"""

    db.delete(user)
    db.commit()
