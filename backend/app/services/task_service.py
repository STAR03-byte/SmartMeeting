"""任务服务层。"""

from datetime import UTC, datetime, timedelta
from typing import Literal

from fastapi import HTTPException
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.meeting import Meeting
from app.models.meeting_participant import MeetingParticipant
from app.models.task import Task
from app.models.team_member import TeamMember
from app.schemas.ai_assistant import TaskDraftRequest
from app.schemas.task import TaskCreate, TaskUpdate


ASSIGNEE_MARKERS = ("请", "由", "让")
ALLOWED_STATUS_TRANSITIONS: dict[str, set[str]] = {
    "todo": {"in_progress"},
    "in_progress": {"done", "todo"},
    "done": {"todo"},
}


def create_task(db: Session, payload: TaskCreate) -> Task:
    """创建任务。"""

    task = Task(**payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def create_task_draft(
    db: Session,
    payload: TaskDraftRequest,
    reporter_id: int | None = None,
) -> Task:
    """创建任务草稿。"""

    task = Task(
        meeting_id=payload.meeting_id,
        title=payload.title,
        description=payload.description,
        assignee_id=payload.assignee_id,
        reporter_id=reporter_id,
        priority=payload.priority,
        status="draft",
        due_at=payload.due_date,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def list_tasks(
    db: Session,
    assignee_id: int | None = None,
    meeting_id: int | None = None,
    status: Literal["todo", "in_progress", "done"] | None = None,
    priority: Literal["high", "medium", "low"] | None = None,
    keyword: str | None = None,
    sort_by: str | None = None,
    limit: int | None = None,
    offset: int = 0,
    current_user_id: int | None = None,
    is_admin: bool = False,
) -> list[Task]:
    """查询任务列表，可按执行人筛选。"""

    query = db.query(Task)

    if not is_admin and current_user_id is not None:
        participant_meeting_ids = db.query(MeetingParticipant.meeting_id).filter(
            MeetingParticipant.user_id == current_user_id
        )
        user_team_ids = db.query(TeamMember.team_id).filter(TeamMember.user_id == current_user_id)
        query = query.join(Meeting, Meeting.id == Task.meeting_id).filter(
            or_(
                Meeting.organizer_id == current_user_id,
                Task.assignee_id == current_user_id,
                Task.reporter_id == current_user_id,
                Task.meeting_id.in_(participant_meeting_ids),
                Meeting.team_id.in_(user_team_ids),
            )
        )
    if assignee_id is not None:
        query = query.filter(Task.assignee_id == assignee_id)
    if meeting_id is not None:
        query = query.filter(Task.meeting_id == meeting_id)
    if status is not None:
        query = query.filter(Task.status == status)
    if priority is not None:
        query = query.filter(Task.priority == priority)
    if keyword:
        normalized_keyword = keyword.strip()
        if normalized_keyword:
            query = query.filter(Task.title.ilike(f"%{normalized_keyword}%"))

    if sort_by == "due_at_asc":
        # MySQL 兼容：使用 (due_at IS NULL) 先排序，让 NULL 值排在最后
        from sqlalchemy import case
        query = query.order_by(case((Task.due_at.is_(None), 1), else_=0), Task.due_at.asc(), Task.id.desc())
    elif sort_by == "due_at_desc":
        # MySQL 兼容：DESC 时 NULL 自然排在最后
        query = query.order_by(Task.due_at.desc(), Task.id.desc())
    else:
        query = query.order_by(Task.id.desc())

    query = query.offset(offset)

    if limit is not None:
        query = query.limit(limit)

    return query.all()


def count_tasks(
    db: Session,
    assignee_id: int | None = None,
    meeting_id: int | None = None,
    status: Literal["todo", "in_progress", "done"] | None = None,
    priority: Literal["high", "medium", "low"] | None = None,
    keyword: str | None = None,
    current_user_id: int | None = None,
    is_admin: bool = False,
) -> int:
    query = db.query(func.count(Task.id))
    if not is_admin and current_user_id is not None:
        participant_meeting_ids = db.query(MeetingParticipant.meeting_id).filter(
            MeetingParticipant.user_id == current_user_id
        )
        user_team_ids = db.query(TeamMember.team_id).filter(TeamMember.user_id == current_user_id)
        query = query.join(Meeting, Meeting.id == Task.meeting_id).filter(
            or_(
                Meeting.organizer_id == current_user_id,
                Task.assignee_id == current_user_id,
                Task.reporter_id == current_user_id,
                Task.meeting_id.in_(participant_meeting_ids),
                Meeting.team_id.in_(user_team_ids),
            )
        )
    if assignee_id is not None:
        query = query.filter(Task.assignee_id == assignee_id)
    if meeting_id is not None:
        query = query.filter(Task.meeting_id == meeting_id)
    if status is not None:
        query = query.filter(Task.status == status)
    if priority is not None:
        query = query.filter(Task.priority == priority)
    if keyword:
        normalized_keyword = keyword.strip()
        if normalized_keyword:
            query = query.filter(Task.title.ilike(f"%{normalized_keyword}%"))
    result = query.scalar()
    return int(result or 0)


def serialize_task_out(task: Task, meeting: Meeting | None = None) -> dict[str, object]:
    meeting_title = meeting.title if meeting else None
    now = datetime.now(UTC)
    due_soon_deadline = now + timedelta(hours=48)

    is_done = task.status == "done"
    due_at = task.due_at
    is_overdue = False
    is_due_soon = False

    if due_at is not None and not is_done:
        due_at_utc = due_at if due_at.tzinfo is not None else due_at.replace(tzinfo=UTC)
        is_overdue = due_at_utc < now
        is_due_soon = now <= due_at_utc < due_soon_deadline

    return {
        "id": task.id,
        "meeting_id": task.meeting_id,
        "meeting_title": meeting_title,
        "transcript_id": task.transcript_id,
        "title": task.title,
        "description": task.description,
        "assignee_id": task.assignee_id,
        "reporter_id": task.reporter_id,
        "priority": task.priority,
        "status": task.status,
        "progress_note": task.progress_note,
        "due_at": task.due_at,
        "reminder_at": task.reminder_at,
        "completed_at": task.completed_at,
        "is_overdue": is_overdue,
        "is_due_soon": is_due_soon,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
    }


def get_task(db: Session, task_id: int) -> Task | None:
    """按 ID 查询任务。"""

    return db.query(Task).filter(Task.id == task_id).first()


def update_task(db: Session, task: Task, payload: TaskUpdate) -> Task:
    """更新任务。"""

    data = payload.model_dump(exclude_unset=True)

    next_due_at = data.get("due_at", task.due_at)
    next_reminder_at = data.get("reminder_at", task.reminder_at)
    if next_due_at is not None and next_reminder_at is not None and next_reminder_at >= next_due_at:
        raise HTTPException(status_code=400, detail="reminder_at must be before due_at")

    if "status" in data:
        next_status = data["status"]
        if next_status != task.status:
            allowed = ALLOWED_STATUS_TRANSITIONS.get(task.status, set())
            if next_status not in allowed:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid task status transition: {task.status} -> {next_status}",
                )

        if next_status == "done":
            now_local = datetime.now()
            created_at = task.created_at
            if created_at.tzinfo is not None:
                created_at = created_at.replace(tzinfo=None)
            data["completed_at"] = now_local if now_local >= created_at else created_at
        elif task.status == "done" and next_status != "done":
            data["completed_at"] = None

    for key, value in data.items():
        setattr(task, key, value)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task: Task) -> None:
    """删除任务。"""

    db.delete(task)
    db.commit()


def extract_action_items(content: str) -> list[str]:
    """从转写文本中提取待办句子。"""

    normalized = content.replace("；", "。").replace(";", ".")
    clauses = [clause.strip(" ，。") for clause in normalized.split("。")]
    items: list[str] = []
    for clause in clauses:
        if not clause:
            continue
        if any(keyword in clause for keyword in settings.action_keyword_list):
            items.append(clause)
    return items


def infer_task_priority(content: str) -> str:
    """根据语句内容推断任务优先级。"""

    if any(keyword in content for keyword in settings.high_priority_keyword_list):
        return "high"
    return "medium"


def infer_assignee_name(content: str) -> str | None:
    """根据语句内容抽取负责人姓名。"""

    for marker in ASSIGNEE_MARKERS:
        if marker not in content:
            continue
        candidate = content.split(marker, 1)[1].strip()
        if not candidate:
            continue
        for stop_word in (
            "负责",
            "完成",
            "提交",
            "跟进",
            "本周",
            "下周",
            "今天",
            "今日",
            "明天",
            "后天",
            "前",
            "在",
            "于",
        ):
            if stop_word in candidate:
                candidate = candidate.split(stop_word, 1)[0].strip()
        if 1 <= len(candidate) <= 12:
            return candidate

    if "负责" in content:
        prefix = content.split("负责", 1)[0].strip()
        if prefix:
            tail = prefix[-4:]
            for size in (3, 2):
                if len(tail) >= size:
                    name = tail[-size:]
                    if all(ch not in name for ch in ("，", "。", "；", ":", "：", " ")):
                        return name
    return None
