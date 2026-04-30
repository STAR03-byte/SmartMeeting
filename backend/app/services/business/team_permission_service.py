"""团队权限检查服务。"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.team_member import TeamMember


def get_user_team_role(db: Session, team_id: int, user_id: int) -> str | None:
    """获取用户在团队中的角色。

    Args:
        db: 数据库会话
        team_id: 团队ID
        user_id: 用户ID

    Returns:
        用户角色（"owner", "admin", "member"），如果用户不在团队中则返回 None
    """
    member = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == user_id,
    ).first()

    return member.role if member else None


def check_team_permission(
    db: Session,
    team_id: int,
    user_id: int,
    required_role: str,
) -> bool:
    """检查用户是否有指定权限级别。

    权限层级：owner > admin > member
    - owner 拥有所有权限
    - admin 拥有 admin 和 member 权限
    - member 只有 member 权限

    Args:
        db: 数据库会话
        team_id: 团队ID
        user_id: 用户ID
        required_role: 需要的角色（"owner", "admin", "member"）

    Returns:
        True 如果用户有足够权限，False 否則
    """
    role = get_user_team_role(db, team_id, user_id)
    if not role:
        return False

    hierarchy = {"owner": 3, "admin": 2, "member": 1}
    user_level = hierarchy.get(role, 0)
    required_level = hierarchy.get(required_role, 0)

    return user_level >= required_level


def require_team_owner(db: Session, team_id: int, user_id: int) -> None:
    """验证用户是团队所有者，否则抛出 HTTPException。

    Args:
        db: 数据库会话
        team_id: 团队ID
        user_id: 用户ID

    Raises:
        HTTPException: 403 如果用户不是所有者，404 如果用户不在团队中
    """
    role = get_user_team_role(db, team_id, user_id)

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不在该团队中",
        )

    if role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要团队所有者权限",
        )


def require_team_admin(db: Session, team_id: int, user_id: int) -> None:
    """验证用户是团队所有者或管理员，否则抛出 HTTPException。

    Args:
        db: 数据库会话
        team_id: 团队ID
        user_id: 用户ID

    Raises:
        HTTPException: 403 如果用户不是管理员或所有者，404 如果用户不在团队中
    """
    role = get_user_team_role(db, team_id, user_id)

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不在该团队中",
        )

    if role not in ("owner", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要团队管理员或所有者权限",
        )