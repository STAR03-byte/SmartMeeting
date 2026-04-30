"""会议服务层。"""

from datetime import UTC, datetime
import logging
from pathlib import Path
from secrets import token_urlsafe
import re

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.meeting import Meeting
from app.models.meeting_audio import MeetingAudio
from app.models.meeting_participant import MeetingParticipant
from app.models.meeting_transcript import MeetingTranscript
from app.models.team_member import TeamMember
from app.models.task import Task
from app.models.user import User
from app.schemas.meeting import MeetingCreate, MeetingDetailOut, MeetingShareOut, MeetingUpdate, SharedMeetingOut
from app.schemas.meeting_transcript import MeetingTranscriptOut
from app.schemas.task import TaskOut
from app.services.business.task_service import extract_action_items, infer_assignee_name, infer_task_priority
from app.services.business.task_service import is_actionable_task_text
from app.services.ai.llm_service import (
    ExtractedTask,
    LLMServiceError,
    extract_action_items as llm_extract_action_items,
    extract_action_items_for_batch as llm_extract_action_items_for_batch,
    generate_fallback_tasks,
    generate_meeting_summary as llm_generate_meeting_summary,
)
from app.core.config import settings
from app.services.business.user_service import get_user
from app.services.business.task_service import serialize_task_out

logger = logging.getLogger(__name__)

TASK_EXTRACTION_BATCH_SIZE = 4


def normalize_person_key(value: str | None) -> str:
    if not value:
        return ""
    normalized = value.strip().lower()
    normalized = re.sub(r"[\s._\-]+", "", normalized)
    return normalized


def _build_user_name_map(db: Session) -> list[tuple[int, str]]:
    """Build a list of (user_id, normalized_alias) for all users. Loads once per call."""
    users = db.query(User).all()
    alias_index: list[tuple[int, str]] = []
    for user in users:
        aliases = {
            user.full_name,
            user.username,
            user.email.split("@", 1)[0] if user.email and "@" in user.email else user.email,
        }
        for alias in aliases:
            normalized_alias = normalize_person_key(alias)
            if normalized_alias:
                alias_index.append((user.id, normalized_alias))
    return alias_index


def resolve_assignee_id_by_name(
    db: Session,
    assignee_name: str | None,
    alias_index: list[tuple[int, str]] | None = None,
) -> int | None:
    target = normalize_person_key(assignee_name)
    if not target:
        return None

    if alias_index is None:
        alias_index = _build_user_name_map(db)

    for user_id, alias in alias_index:
        if alias == target:
            return user_id

    if len(target) >= 3:
        for user_id, alias in alias_index:
            if target in alias or alias in target:
                return user_id

    return None


def resolve_assignee_id_from_text(
    db: Session,
    text: str | None,
    alias_index: list[tuple[int, str]] | None = None,
) -> int | None:
    normalized_text = normalize_person_key(text)
    if not normalized_text:
        return None

    if alias_index is None:
        alias_index = _build_user_name_map(db)

    for user_id, alias in alias_index:
        if len(alias) >= 3 and alias in normalized_text:
            return user_id

    return None


def normalize_summary_text(summary: str) -> str:
    normalized = summary
    normalized = normalized.replace("\r\n", "\n")
    normalized = normalized.replace("\r", "\n")

    lines = [line.rstrip() for line in normalized.split("\n")]
    cleaned_lines: list[str] = []
    for raw_line in lines:
        stripped = raw_line.lstrip(" \u00A0·•")
        while stripped.startswith("#"):
            stripped = stripped[1:].lstrip()
        if stripped.startswith("- ") or stripped.startswith("* ") or stripped.startswith("+ "):
            stripped = f"• {stripped[2:].strip()}"
        if stripped.startswith("***") and stripped.endswith("***") and len(stripped) > 6:
            stripped = stripped[3:-3].strip()
        if stripped.startswith("**") and stripped.endswith("**") and len(stripped) > 4:
            stripped = stripped[2:-2].strip()
        if stripped.startswith("*") and stripped.endswith("*") and len(stripped) > 2:
            stripped = stripped[1:-1].strip()
        previous = None
        while previous != stripped:
            previous = stripped
            stripped = re.sub(r"\*\*(.+?)\*\*", r"\1", stripped)
            stripped = re.sub(r"\*(.+?)\*", r"\1", stripped)
        if re.fullmatch(r"\*+", stripped):
            stripped = ""
        stripped = stripped.replace("***", "")
        stripped = stripped.replace("**", "")
        stripped = stripped.replace("*", "")
        cleaned_lines.append(stripped)

    compacted: list[str] = []
    previous_blank = False
    for line in cleaned_lines:
        is_blank = line.strip() == ""
        if is_blank and previous_blank:
            continue
        compacted.append(line)
        previous_blank = is_blank

    return "\n".join(compacted).strip()


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
    team_id: int | None = None,
    keyword: str | None = None,
    sort_by: str | None = None,
    limit: int | None = None,
    offset: int = 0,
    current_user_id: int | None = None,
    is_admin: bool = False,
) -> list[Meeting]:
    """查询会议列表。"""

    query = db.query(Meeting)

    if not is_admin and current_user_id is not None:
        participant_meeting_ids = db.query(MeetingParticipant.meeting_id).filter(
            MeetingParticipant.user_id == current_user_id
        )
        user_team_ids = db.query(TeamMember.team_id).filter(TeamMember.user_id == current_user_id)
        query = query.filter(
            or_(
                Meeting.organizer_id == current_user_id,
                Meeting.id.in_(participant_meeting_ids),
                Meeting.team_id.in_(user_team_ids),
            )
        )

    if status is not None:
        query = query.filter(Meeting.status == status)

    if organizer_id is not None:
        query = query.filter(Meeting.organizer_id == organizer_id)

    if team_id is not None:
        query = query.filter(Meeting.team_id == team_id)

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


def count_meetings(
    db: Session,
    status: str | None = None,
    organizer_id: int | None = None,
    team_id: int | None = None,
    keyword: str | None = None,
    current_user_id: int | None = None,
    is_admin: bool = False,
) -> int:
    query = db.query(Meeting)

    if not is_admin and current_user_id is not None:
        participant_meeting_ids = db.query(MeetingParticipant.meeting_id).filter(
            MeetingParticipant.user_id == current_user_id
        )
        user_team_ids = db.query(TeamMember.team_id).filter(TeamMember.user_id == current_user_id)
        query = query.filter(
            or_(
                Meeting.organizer_id == current_user_id,
                Meeting.id.in_(participant_meeting_ids),
                Meeting.team_id.in_(user_team_ids),
            )
        )

    if status is not None:
        query = query.filter(Meeting.status == status)

    if organizer_id is not None:
        query = query.filter(Meeting.organizer_id == organizer_id)

    if team_id is not None:
        query = query.filter(Meeting.team_id == team_id)

    if keyword:
        normalized_keyword = keyword.strip()
        if normalized_keyword:
            query = query.filter(
                (Meeting.title.ilike(f"%{normalized_keyword}%"))
                | (Meeting.description.ilike(f"%{normalized_keyword}%"))
            )

    return query.count()


def match_meeting_keyword(meeting: Meeting, keyword: str) -> bool:
    normalized_keyword = keyword.strip()
    if not normalized_keyword:
        return True
    return normalized_keyword.lower() in (meeting.title or "").lower() or normalized_keyword.lower() in (meeting.description or "").lower()


def get_meeting(db: Session, meeting_id: int) -> Meeting | None:
    """按 ID 查询会议。"""

    return db.query(Meeting).filter(Meeting.id == meeting_id).first()


def _utc_now_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _normalize_naive_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)


def is_meeting_share_active(meeting: Meeting, now: datetime | None = None) -> bool:
    if not meeting.share_token:
        return False
    if meeting.share_revoked_at is not None:
        return False
    expires_at = _normalize_naive_utc(meeting.share_expires_at)
    compare_now = _normalize_naive_utc(now) if now else _utc_now_naive()
    if expires_at is not None and compare_now is not None and expires_at <= compare_now:
        return False
    return True


def create_or_get_meeting_share(
    db: Session,
    meeting: Meeting,
    expires_at: datetime | None = None,
) -> tuple[MeetingShareOut, bool]:
    if not meeting.summary:
        raise ValueError("Meeting summary is required for sharing")

    normalized_expires_at = _normalize_naive_utc(expires_at)
    created_now = False
    if not is_meeting_share_active(meeting):
        meeting.share_token = token_urlsafe(32)
        meeting.shared_at = _utc_now_naive()
        created_now = True

    meeting.share_revoked_at = None
    meeting.share_expires_at = normalized_expires_at
    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    assert meeting.share_token is not None
    assert meeting.shared_at is not None

    return (
        MeetingShareOut(
            meeting_id=meeting.id,
            share_token=meeting.share_token,
            share_path=f"/shared/meetings/{meeting.share_token}",
            created_now=created_now,
            shared_at=meeting.shared_at,
            expires_at=meeting.share_expires_at,
            revoked_at=meeting.share_revoked_at,
        ),
        created_now,
    )


def revoke_meeting_share(db: Session, meeting: Meeting) -> Meeting:
    meeting.share_revoked_at = _utc_now_naive()
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    return meeting


def build_shared_meeting_out(db: Session, meeting: Meeting, my_role: str = "guest") -> SharedMeetingOut:
    if meeting.organizer is None:
        raise ValueError("Organizer not found")

    transcripts = sorted(
        meeting.transcripts,
        key=lambda t: (t.segment_index, t.id),
    )
    tasks = sorted(meeting.tasks, key=lambda t: t.id, reverse=True)

    return SharedMeetingOut(
        meeting=MeetingDetailOut.model_validate(meeting),
        transcripts=[MeetingTranscriptOut.model_validate(item) for item in transcripts],
        tasks=[TaskOut.model_validate(serialize_task_out(task)) for task in tasks],
        my_role=my_role,
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
    """删除会议。participants 需手动删除（无 cascade），其余由 ORM cascade 级联删除。"""
    db.query(MeetingParticipant).filter(MeetingParticipant.meeting_id == meeting.id).delete(synchronize_session=False)
    db.delete(meeting)
    db.commit()


def clear_meeting_content(
    db: Session,
    meeting: Meeting,
    *,
    clear_transcripts: bool = True,
    clear_tasks: bool = True,
    clear_summary: bool = True,
    clear_audios: bool = True,
    reset_status: bool = True,
) -> Meeting:
    if clear_audios:
        for audio in list(meeting.audios):
            storage_path = Path(audio.storage_path)
            try:
                storage_path.unlink(missing_ok=True)
            except OSError as exc:
                logger.warning("Failed to remove audio file when clearing meeting %s: %s", meeting.id, exc)
        meeting.audios.clear()

    if clear_tasks:
        meeting.tasks.clear()

    if clear_transcripts:
        meeting.transcripts.clear()

    if clear_summary:
        meeting.summary = None
        meeting.postprocessed_at = None
        meeting.postprocess_version = None

    if reset_status:
        meeting.actual_start_at = None
        meeting.actual_end_at = None
        meeting.status = "planned"

    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    return meeting


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
            return normalize_summary_text(summary), "llm-summary-v1"
    except LLMServiceError:
        pass
    return build_meeting_summary(transcripts), "rule-v1"


def generate_tasks_from_transcripts(
    db: Session,
    meeting_id: int,
    transcripts: list[MeetingTranscript],
    force_regenerate: bool = False,
    reporter_id: int | None = None,
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
    alias_index = _build_user_name_map(db)
    for transcript in transcripts:
        action_items = extract_action_items(transcript.content)
        if not action_items:
            should_try_fallback = any(keyword in transcript.content for keyword in settings.action_keyword_list)
            if should_try_fallback:
                fallback_items = generate_fallback_tasks(transcript.content)
                action_items = [item["description"] for item in fallback_items if item.get("description")]
        for action in action_items:
            assignee_id = transcript.speaker_user_id
            assignee_name = infer_assignee_name(action)
            if assignee_name:
                matched_user_id = resolve_assignee_id_by_name(db, assignee_name, alias_index)
                if matched_user_id is not None:
                    assignee_id = matched_user_id
            if assignee_id is None:
                assignee_id = resolve_assignee_id_from_text(db, action, alias_index)

            task = Task(
                meeting_id=meeting_id,
                transcript_id=transcript.id,
                title=action[:200],
                description=action,
                assignee_id=assignee_id,
                reporter_id=reporter_id,
                priority=infer_task_priority(action),
                status="draft",
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
    reporter_id: int | None = None,
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
    alias_index = _build_user_name_map(db)
    participants = list({alias for _, alias in alias_index if len(alias) >= 2})

    transcript_batches = [
        transcripts[index : index + TASK_EXTRACTION_BATCH_SIZE]
        for index in range(0, len(transcripts), TASK_EXTRACTION_BATCH_SIZE)
    ]
    llm_items_by_transcript: dict[int, list[ExtractedTask]] = {}

    for batch in transcript_batches:
        batch_contents = [transcript.content for transcript in batch]
        try:
            batch_items = await llm_extract_action_items_for_batch(batch_contents, participants)
        except LLMServiceError:
            batch_items = []

        for item in batch_items:
            segment_index = item.get("segment_index")
            if not isinstance(segment_index, int) or segment_index < 0 or segment_index >= len(batch):
                continue
            target_transcript = batch[segment_index]
            llm_items_by_transcript.setdefault(target_transcript.id, []).append(
                {
                    "title": item["title"],
                    "description": item["description"],
                    "assignee_name": item["assignee_name"],
                    "priority": item["priority"],
                    "due_hint": item["due_hint"],
                }
            )

    for transcript in transcripts:
        llm_items = llm_items_by_transcript.get(transcript.id, [])
        if not llm_items:
            try:
                llm_items = await llm_extract_action_items(transcript.content, participants)
            except LLMServiceError:
                llm_items = []

        if llm_items:
            used_llm = True
            for item in llm_items:
                if not is_actionable_task_text(item["title"]):
                    continue
                assignee_id = transcript.speaker_user_id
                assignee_name = item["assignee_name"]
                if assignee_name:
                    matched_user_id = resolve_assignee_id_by_name(db, assignee_name, alias_index)
                    if matched_user_id is not None:
                        assignee_id = matched_user_id
                if assignee_id is None:
                    assignee_id = resolve_assignee_id_from_text(
                        db,
                        item.get("description") or item.get("title") or transcript.content,
                        alias_index,
                    )

                priority = (
                    item["priority"]
                    if item["priority"] in {"high", "medium", "low"}
                    else infer_task_priority(transcript.content)
                )
                task = Task(
                    meeting_id=meeting_id,
                    transcript_id=transcript.id,
                    title=item["title"][:200],
                    description=(
                        f"负责人：{assignee_name}；{item['description'] or transcript.content}"
                        if assignee_id is None and assignee_name
                        else (item["description"] or transcript.content)
                    ),
                    assignee_id=assignee_id,
                    reporter_id=reporter_id,
                    priority=priority,
                    status="draft",
                )
                db.add(task)
                generated.append(task)
            continue

        action_items = extract_action_items(transcript.content)
        if not action_items:
            should_try_fallback = any(keyword in transcript.content for keyword in settings.action_keyword_list)
            if should_try_fallback:
                fallback_items = generate_fallback_tasks(transcript.content)
                action_items = [item["description"] for item in fallback_items if item.get("description")]
        for action in action_items:
            if not is_actionable_task_text(action):
                continue
            assignee_id = transcript.speaker_user_id
            assignee_name = infer_assignee_name(action)
            if assignee_name:
                matched_user_id = resolve_assignee_id_by_name(db, assignee_name, alias_index)
                if matched_user_id is not None:
                    assignee_id = matched_user_id
            if assignee_id is None:
                assignee_id = resolve_assignee_id_from_text(db, action, alias_index)

            task = Task(
                meeting_id=meeting_id,
                transcript_id=transcript.id,
                title=action[:200],
                description=action,
                assignee_id=assignee_id,
                reporter_id=reporter_id,
                priority=infer_task_priority(action),
                status="draft",
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
