from sqlalchemy.orm import Session

from ..core.security import create_access_token, verify_password
from ..models.user import User


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def create_user_access_token(user: User) -> str:
    return create_access_token(subject=str(user.id))
