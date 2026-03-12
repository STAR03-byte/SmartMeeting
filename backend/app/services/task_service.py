"""任务服务层。"""

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate


ASSIGNEE_MARKERS = ("请", "由", "让")


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
