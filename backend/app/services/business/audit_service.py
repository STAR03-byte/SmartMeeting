from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def create_audit_log(
    db: Session,
    actor_user_id: int | None,
    entity_type: str,
    entity_id: int,
    action: str,
    before_data: dict[str, object] | None = None,
    after_data: dict[str, object] | None = None,
) -> AuditLog:
    log = AuditLog(
        actor_user_id=actor_user_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        before_data=before_data,
        after_data=after_data,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
