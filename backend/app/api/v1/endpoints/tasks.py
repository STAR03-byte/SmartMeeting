"""任务 REST API。"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.task import TaskCreate, TaskOut, TaskUpdate
from app.services.task_service import create_task, delete_task, get_task, list_tasks, update_task

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task_api(payload: TaskCreate, db: Session = Depends(get_db)) -> TaskOut:
    """创建任务。"""

    return create_task(db, payload)


@router.get("", response_model=list[TaskOut])
def list_tasks_api(
    assignee_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[TaskOut]:
    """查询任务列表。"""

    return list_tasks(db, assignee_id=assignee_id)


@router.get("/{task_id}", response_model=TaskOut)
def get_task_api(task_id: int, db: Session = Depends(get_db)) -> TaskOut:
    """查询任务详情。"""

    task = get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.patch("/{task_id}", response_model=TaskOut)
def update_task_api(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db)) -> TaskOut:
    """更新任务。"""

    task = get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return update_task(db, task, payload)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task_api(task_id: int, db: Session = Depends(get_db)) -> None:
    """删除任务。"""

    task = get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    delete_task(db, task)
