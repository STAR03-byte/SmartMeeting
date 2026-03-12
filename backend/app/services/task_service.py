"""任务服务层。"""

from sqlalchemy.orm import Session

from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate


def create_task(db: Session, payload: TaskCreate) -> Task:
    """创建任务。"""

    task = Task(**payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def list_tasks(db: Session, assignee_id: int | None = None) -> list[Task]:
    """查询任务列表，可按执行人筛选。"""

    query = db.query(Task)
    if assignee_id is not None:
        query = query.filter(Task.assignee_id == assignee_id)
    return query.order_by(Task.id.desc()).all()


def get_task(db: Session, task_id: int) -> Task | None:
    """按 ID 查询任务。"""

    return db.query(Task).filter(Task.id == task_id).first()


def update_task(db: Session, task: Task, payload: TaskUpdate) -> Task:
    """更新任务。"""

    data = payload.model_dump(exclude_unset=True)
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
