"""用户服务层。"""

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


def create_user(db: Session, payload: UserCreate) -> User:
    """创建用户。"""

    data = payload.model_dump()
    raw_password = data["password_hash"]
    if not raw_password.startswith("$pbkdf2-sha256$"):
        data["password_hash"] = get_password_hash(raw_password)

    user = User(**data)
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
