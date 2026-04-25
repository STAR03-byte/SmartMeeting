"""任务 REST API。"""

from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.meeting import Meeting
from app.models.meeting_participant import MeetingParticipant
from app.models.team_member import TeamMember
from app.schemas.ai_assistant import TaskDraftRequest, TaskDraftResponse
from app.schemas.auth import CurrentUserOut
from app.schemas.task import TaskPriority, TaskStatus
from app.schemas.task import TaskCreate, TaskListOut, TaskOut, TaskUpdate
from app.services.meeting_service import get_meeting
from app.services.meeting_transcript_service import get_transcript
from app.services.task_service import (
    count_tasks,
    create_task,
    create_task_draft,
    delete_task,
    get_task,
    list_tasks,
    serialize_task_out,
    update_task,
)
from app.services.user_service import get_user
from .auth import get_current_user

router = APIRouter(prefix="/tasks", tags=["tasks"], dependencies=[Depends(get_current_user)])


def _assert_meeting_task_permission(meeting: Meeting, current_user: CurrentUserOut) -> None:
    if current_user.role == "admin":
        return
    if meeting.organizer_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权管理此会议的任务")


def _assert_meeting_draft_permission(db: Session, meeting: Meeting, current_user: CurrentUserOut) -> None:
    if current_user.role == "admin" or meeting.organizer_id == current_user.id:
        return

    participant = (
        db.query(MeetingParticipant)
        .filter(MeetingParticipant.meeting_id == meeting.id, MeetingParticipant.user_id == current_user.id)
        .first()
    )
    if participant:
        return

    raise HTTPException(status_code=403, detail="无权创建此会议的任务草稿")


def _assert_assignee_permission(db: Session, meeting: Meeting, assignee_id: int, current_user: CurrentUserOut) -> None:
    if current_user.role == "admin":
        return
    if assignee_id == meeting.organizer_id:
        return

    participant = (
        db.query(MeetingParticipant)
        .filter(MeetingParticipant.meeting_id == meeting.id, MeetingParticipant.user_id == assignee_id)
        .first()
    )
    if participant:
        return

    if meeting.team_id is not None:
        team_member = (
            db.query(TeamMember)
            .filter(TeamMember.team_id == meeting.team_id, TeamMember.user_id == assignee_id)
            .first()
        )
        if team_member:
            return

    raise HTTPException(status_code=400, detail="任务负责人必须是会议参与者或团队成员")


def _assert_task_permission(_task: object, meeting: Meeting, current_user: CurrentUserOut) -> None:
    if current_user.role == "admin":
        return
    if meeting.organizer_id == current_user.id:
        return
    if getattr(_task, "assignee_id", None) == current_user.id:
        return
    raise HTTPException(status_code=403, detail="无权管理此任务")


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task_api(
    payload: TaskCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
) -> TaskOut:
    """创建任务。"""

    meeting = get_meeting(db, payload.meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    _assert_meeting_task_permission(meeting, current_user)

    if payload.transcript_id is not None:
        transcript = get_transcript(db, payload.transcript_id)
        if not transcript or transcript.meeting_id != payload.meeting_id:
            raise HTTPException(status_code=404, detail="Transcript not found")

    if payload.assignee_id is not None and not get_user(db, payload.assignee_id):
        raise HTTPException(status_code=404, detail="Assignee not found")

    if payload.assignee_id is not None:
        _assert_assignee_permission(db, meeting, payload.assignee_id, current_user)

    if payload.reporter_id is not None and not get_user(db, payload.reporter_id):
        raise HTTPException(status_code=404, detail="Reporter not found")

    task = create_task(db, payload)
    return TaskOut.model_validate(
        serialize_task_out(
            task,
            meeting,
            current_user_id=current_user.id,
            is_admin=(current_user.role == "admin"),
        )
    )


@router.post("/draft", response_model=TaskDraftResponse, status_code=status.HTTP_201_CREATED)
def create_task_draft_api(
    payload: TaskDraftRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
) -> TaskDraftResponse:
    """创建任务草稿。"""

    meeting = get_meeting(db, payload.meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    _assert_meeting_draft_permission(db, meeting, current_user)

    if not get_user(db, payload.assignee_id):
        raise HTTPException(status_code=404, detail="Assignee not found")

    _assert_assignee_permission(db, meeting, payload.assignee_id, current_user)

    draft = create_task_draft(db, payload, reporter_id=current_user.id)
    return TaskDraftResponse(
        id=draft.id,
        title=draft.title,
        description=draft.description,
        meeting_id=draft.meeting_id,
        due_date=draft.due_at,
        priority=cast(TaskPriority, draft.priority),
        assignee_id=draft.assignee_id,
        status=draft.status,
    )


@router.get("", response_model=TaskListOut)
def list_tasks_api(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
    assignee_id: Annotated[int | None, Query()] = None,
    meeting_id: Annotated[int | None, Query()] = None,
    team_id: Annotated[int | None, Query()] = None,
    status: Annotated[TaskStatus | None, Query()] = None,
    priority: Annotated[TaskPriority | None, Query()] = None,
    keyword: Annotated[str | None, Query()] = None,
    sort_by: Annotated[str | None, Query()] = None,
    limit: Annotated[int | None, Query(ge=1, le=100)] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> TaskListOut:
    """查询任务列表。"""

    total = count_tasks(
        db,
        assignee_id=assignee_id,
        meeting_id=meeting_id,
        team_id=team_id,
        status=status,
        priority=priority,
        keyword=keyword,
        current_user_id=current_user.id,
        is_admin=(current_user.role == "admin"),
    )

    tasks = list_tasks(
        db,
        assignee_id=assignee_id,
        meeting_id=meeting_id,
        team_id=team_id,
        status=status,
        priority=priority,
        keyword=keyword,
        sort_by=sort_by,
        limit=limit,
        offset=offset,
        current_user_id=current_user.id,
        is_admin=(current_user.role == "admin"),
    )

    meeting_ids = {task.meeting_id for task in tasks}
    meetings = {m.id: m for m in [get_meeting(db, mid) for mid in meeting_ids] if m}
    
    return TaskListOut(
        items=[
            TaskOut.model_validate(
                serialize_task_out(
                    task,
                    meetings.get(task.meeting_id, None),
                    current_user_id=current_user.id,
                    is_admin=(current_user.role == "admin"),
                )
            )
            for task in tasks
        ],
        total=total,
    )


@router.get("/{task_id}", response_model=TaskOut)
def get_task_api(
    task_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
) -> TaskOut:
    """查询任务详情。"""

    task = get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    meeting = get_meeting(db, task.meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    _assert_task_permission(task, meeting, current_user)
    return TaskOut.model_validate(
        serialize_task_out(
            task,
            meeting,
            current_user_id=current_user.id,
            is_admin=(current_user.role == "admin"),
        )
    )


@router.patch("/{task_id}", response_model=TaskOut)
def update_task_api(
    task_id: Annotated[int, Path(ge=1)],
    payload: TaskUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
) -> TaskOut:
    """更新任务。"""

    task = get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    meeting = get_meeting(db, task.meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    _assert_task_permission(task, meeting, current_user)
    updated_task = update_task(db, task, payload)
    return TaskOut.model_validate(
        serialize_task_out(
            updated_task,
            meeting,
            current_user_id=current_user.id,
            is_admin=(current_user.role == "admin"),
        )
    )


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task_api(
    task_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
) -> None:
    """删除任务。"""

    task = get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    meeting = get_meeting(db, task.meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    _assert_task_permission(task, meeting, current_user)
    delete_task(db, task)
