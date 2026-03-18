"""任务 REST API。"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.meeting_service import get_meeting
from app.services.meeting_transcript_service import get_transcript
from app.schemas.task import TaskPriority, TaskStatus
from app.schemas.task import TaskCreate, TaskOut, TaskUpdate
from app.services.task_service import (
    create_task,
    delete_task,
    get_task,
    list_tasks,
    serialize_task_out,
    update_task,
)
from app.services.user_service import get_user

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task_api(payload: TaskCreate, db: Session = Depends(get_db)) -> TaskOut:
    """创建任务。"""

    meeting = get_meeting(db, payload.meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if payload.transcript_id is not None:
        transcript = get_transcript(db, payload.transcript_id)
        if not transcript or transcript.meeting_id != payload.meeting_id:
            raise HTTPException(status_code=404, detail="Transcript not found")

    if payload.assignee_id is not None and not get_user(db, payload.assignee_id):
        raise HTTPException(status_code=404, detail="Assignee not found")

    if payload.reporter_id is not None and not get_user(db, payload.reporter_id):
        raise HTTPException(status_code=404, detail="Reporter not found")

    return create_task(db, payload)


@router.get("", response_model=list[TaskOut])
def list_tasks_api(
    assignee_id: int | None = Query(default=None),
    meeting_id: int | None = Query(default=None),
    status: TaskStatus | None = Query(default=None),
    priority: TaskPriority | None = Query(default=None),
    keyword: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[TaskOut]:
    """查询任务列表。"""

    tasks = list_tasks(
        db,
        assignee_id=assignee_id,
        meeting_id=meeting_id,
        status=status,
        priority=priority,
        keyword=keyword,
    )
    return [TaskOut.model_validate(serialize_task_out(task)) for task in tasks]


@router.get("/{task_id}", response_model=TaskOut)
def get_task_api(task_id: int, db: Session = Depends(get_db)) -> TaskOut:
    """查询任务详情。"""

    task = get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskOut.model_validate(serialize_task_out(task))


@router.patch("/{task_id}", response_model=TaskOut)
def update_task_api(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db)) -> TaskOut:
    """更新任务。"""

    task = get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    updated_task = update_task(db, task, payload)
    return TaskOut.model_validate(serialize_task_out(updated_task))


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task_api(task_id: int, db: Session = Depends(get_db)) -> None:
    """删除任务。"""

    task = get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    delete_task(db, task)
