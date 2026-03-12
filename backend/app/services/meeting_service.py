"""会议服务层。"""

from sqlalchemy.orm import Session

from app.models.meeting import Meeting
from app.models.meeting_transcript import MeetingTranscript
from app.models.task import Task
from app.schemas.meeting import MeetingCreate, MeetingUpdate
from app.services.task_service import extract_action_items


def create_meeting(db: Session, payload: MeetingCreate) -> Meeting:
    """创建会议。"""

    meeting = Meeting(**payload.model_dump())
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    return meeting


def list_meetings(db: Session) -> list[Meeting]:
    """查询会议列表。"""

    return db.query(Meeting).order_by(Meeting.id.desc()).all()


def get_meeting(db: Session, meeting_id: int) -> Meeting | None:
    """按 ID 查询会议。"""

    return db.query(Meeting).filter(Meeting.id == meeting_id).first()


def update_meeting(db: Session, meeting: Meeting, payload: MeetingUpdate) -> Meeting:
    """更新会议。"""

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(meeting, key, value)
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    return meeting


def delete_meeting(db: Session, meeting: Meeting) -> None:
    """删除会议。"""

    db.delete(meeting)
    db.commit()


def build_meeting_summary(transcripts: list[MeetingTranscript]) -> str:
    """基于转写内容生成简要摘要。"""

    lines = [item.content.strip() for item in transcripts if item.content.strip()]
    if not lines:
        return ""
    if len(lines) == 1:
        return lines[0]
    return f"{lines[0]}\n{lines[1]}"


def generate_tasks_from_transcripts(
    db: Session,
    meeting_id: int,
    transcripts: list[MeetingTranscript],
) -> list[Task]:
    """从转写中抽取行动项并创建任务。"""

    existing = db.query(Task).filter(Task.meeting_id == meeting_id).all()
    if existing:
        return existing

    generated: list[Task] = []
    for transcript in transcripts:
        action_items = extract_action_items(transcript.content)
        for action in action_items:
            task = Task(
                meeting_id=meeting_id,
                transcript_id=transcript.id,
                title=action[:200],
                description=action,
                assignee_id=transcript.speaker_user_id,
                reporter_id=None,
                priority="medium",
                status="todo",
            )
            db.add(task)
            generated.append(task)

    db.commit()
    for task in generated:
        db.refresh(task)
    return generated
