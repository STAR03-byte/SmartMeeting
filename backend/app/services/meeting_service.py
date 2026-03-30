"""会议服务层。"""

from datetime import UTC, datetime
from secrets import token_urlsafe

from sqlalchemy.orm import Session

from app.models.meeting import Meeting
from app.models.meeting_transcript import MeetingTranscript
from app.models.task import Task
from app.models.user import User
from app.schemas.meeting import MeetingCreate, MeetingDetailOut, MeetingShareOut, MeetingUpdate, SharedMeetingOut
from app.schemas.meeting_transcript import MeetingTranscriptOut
from app.schemas.task import TaskOut
from app.services.task_service import extract_action_items, infer_assignee_name, infer_task_priority
from app.services.llm_service import (
    ExtractedTask,
    LLMServiceError,
    extract_action_items as llm_extract_action_items,
    generate_meeting_summary as llm_generate_meeting_summary,
)
from app.services.user_service import get_user
from app.services.task_service import serialize_task_out


def create_meeting(db: Session, payload: MeetingCreate) -> Meeting:
    """创建会议。"""

    meeting = Meeting(**payload.model_dump())
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    return meeting


def list_meetings(
    db: Session,
    status: str | None = None,
    organizer_id: int | None = None,
    keyword: str | None = None,
    sort_by: str | None = None,
    limit: int | None = None,
    offset: int = 0,
) -> list[Meeting]:
    """查询会议列表。"""

    query = db.query(Meeting)

    if status is not None:
        query = query.filter(Meeting.status == status)

    if organizer_id is not None:
        query = query.filter(Meeting.organizer_id == organizer_id)

    if keyword:
        normalized_keyword = keyword.strip()
        if normalized_keyword:
            query = query.filter(
                (Meeting.title.ilike(f"%{normalized_keyword}%"))
                | (Meeting.description.ilike(f"%{normalized_keyword}%"))
            )

    if sort_by == "scheduled_start_at":
        query = query.order_by(Meeting.scheduled_start_at.asc().nullslast(), Meeting.id.desc())
    else:
        query = query.order_by(Meeting.id.desc())

    query = query.offset(offset)

    if limit is not None:
        query = query.limit(limit)

    return query.all()


def match_meeting_keyword(meeting: Meeting, keyword: str) -> bool:
    normalized_keyword = keyword.strip()
    if not normalized_keyword:
        return True
    return normalized_keyword.lower() in (meeting.title or "").lower() or normalized_keyword.lower() in (meeting.description or "").lower()


def get_meeting(db: Session, meeting_id: int) -> Meeting | None:
    """按 ID 查询会议。"""

    return db.query(Meeting).filter(Meeting.id == meeting_id).first()


def create_or_get_meeting_share(db: Session, meeting: Meeting) -> tuple[MeetingShareOut, bool]:
    if not meeting.summary:
        raise ValueError("Meeting summary is required for sharing")

    created_now = False
    if not meeting.share_token:
        meeting.share_token = token_urlsafe(32)
        meeting.shared_at = datetime.now(UTC)
        db.add(meeting)
        db.commit()
        db.refresh(meeting)
        created_now = True

    assert meeting.share_token is not None
    assert meeting.shared_at is not None

    return (
        MeetingShareOut(
            meeting_id=meeting.id,
            share_token=meeting.share_token,
            share_path=f"/shared/meetings/{meeting.share_token}",
            created_now=created_now,
            shared_at=meeting.shared_at,
        ),
        created_now,
    )


def build_shared_meeting_out(db: Session, meeting: Meeting) -> SharedMeetingOut:
    organizer = get_user(db, meeting.organizer_id)
    if organizer is None:
        raise ValueError("Organizer not found")

    transcripts = (
        db.query(MeetingTranscript)
        .filter(MeetingTranscript.meeting_id == meeting.id)
        .order_by(MeetingTranscript.segment_index.asc(), MeetingTranscript.id.asc())
        .all()
    )
    tasks = db.query(Task).filter(Task.meeting_id == meeting.id).order_by(Task.id.desc()).all()

    return SharedMeetingOut(
        meeting=MeetingDetailOut.model_validate({**meeting.__dict__, "organizer": organizer}),
        transcripts=[MeetingTranscriptOut.model_validate(item) for item in transcripts],
        tasks=[TaskOut.model_validate(serialize_task_out(task)) for task in tasks],
    )


def update_meeting(db: Session, meeting: Meeting, payload: MeetingUpdate) -> Meeting:
    """更新会议。"""

    data: dict[str, object] = payload.model_dump(exclude_unset=True)
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


async def build_meeting_summary_with_llm(
    meeting: Meeting,
    transcripts: list[MeetingTranscript],
) -> tuple[str, str]:
    lines = [item.content.strip() for item in transcripts if item.content.strip()]
    if not lines:
        return "", "empty-v1"
    try:
        summary = await llm_generate_meeting_summary(lines, meeting.title)
        if summary.strip():
            return summary.strip(), "llm-summary-v1"
    except LLMServiceError:
        pass
    return build_meeting_summary(transcripts), "rule-v1"


def generate_tasks_from_transcripts(
    db: Session,
    meeting_id: int,
    transcripts: list[MeetingTranscript],
    force_regenerate: bool = False,
) -> list[Task]:
    """从转写中抽取行动项并创建任务。"""

    existing = db.query(Task).filter(Task.meeting_id == meeting_id).all()
    if existing and not force_regenerate:
        return existing

    if existing and force_regenerate:
        for task in existing:
            db.delete(task)
        db.commit()

    generated: list[Task] = []
    for transcript in transcripts:
        action_items = extract_action_items(transcript.content)
        for action in action_items:
            assignee_id = transcript.speaker_user_id
            assignee_name = infer_assignee_name(action)
            if assignee_name:
                user = db.query(User).filter(User.full_name == assignee_name).first()
                if user:
                    assignee_id = user.id

            task = Task(
                meeting_id=meeting_id,
                transcript_id=transcript.id,
                title=action[:200],
                description=action,
                assignee_id=assignee_id,
                reporter_id=None,
                priority=infer_task_priority(action),
                status="todo",
            )
            db.add(task)
            generated.append(task)

    db.commit()
    for task in generated:
        db.refresh(task)
    return generated


async def generate_tasks_from_transcripts_with_llm(
    db: Session,
    meeting_id: int,
    transcripts: list[MeetingTranscript],
    force_regenerate: bool = False,
) -> tuple[list[Task], str]:
    existing = db.query(Task).filter(Task.meeting_id == meeting_id).all()
    if existing and not force_regenerate:
        return existing, "existing-v1"

    if existing and force_regenerate:
        for task in existing:
            db.delete(task)
        db.commit()

    used_llm = False
    generated: list[Task] = []
    participants = [
        user.full_name
        for user in db.query(User).all()
        if getattr(user, "full_name", None)
    ]

    for transcript in transcripts:
        llm_items: list[ExtractedTask] = []
        try:
            llm_items = await llm_extract_action_items(transcript.content, participants)
        except LLMServiceError:
            llm_items = []

        if llm_items:
            used_llm = True
            for item in llm_items:
                assignee_id = transcript.speaker_user_id
                assignee_name = item["assignee_name"]
                if assignee_name:
                    user = db.query(User).filter(User.full_name == assignee_name).first()
                    if user:
                        assignee_id = user.id

                priority = (
                    item["priority"]
                    if item["priority"] in {"high", "medium", "low"}
                    else infer_task_priority(transcript.content)
                )
                task = Task(
                    meeting_id=meeting_id,
                    transcript_id=transcript.id,
                    title=item["title"][:200],
                    description=item["description"] or transcript.content,
                    assignee_id=assignee_id,
                    reporter_id=None,
                    priority=priority,
                    status="todo",
                )
                db.add(task)
                generated.append(task)
            continue

        action_items = extract_action_items(transcript.content)
        for action in action_items:
            assignee_id = transcript.speaker_user_id
            assignee_name = infer_assignee_name(action)
            if assignee_name:
                user = db.query(User).filter(User.full_name == assignee_name).first()
                if user:
                    assignee_id = user.id

            task = Task(
                meeting_id=meeting_id,
                transcript_id=transcript.id,
                title=action[:200],
                description=action,
                assignee_id=assignee_id,
                reporter_id=None,
                priority=infer_task_priority(action),
                status="todo",
            )
            db.add(task)
            generated.append(task)

    db.commit()
    for task in generated:
        db.refresh(task)
    version = "llm-task-v1" if used_llm else "rule-v1"
    return generated, version


def save_postprocess_result(
    db: Session,
    meeting: Meeting,
    summary: str,
    version: str = "rule-v1",
) -> Meeting:
    """持久化会议后处理结果。"""

    meeting.summary = summary
    meeting.postprocessed_at = datetime.now(UTC)
    meeting.postprocess_version = version
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    return meeting
