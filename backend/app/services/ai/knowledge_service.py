"""会议知识查询服务。

负责跨会议的关键词搜索与知识片段收集。
"""

import logging
import re

from sqlalchemy import or_
from sqlalchemy.orm import Session, aliased

from app.models.meeting import Meeting
from app.models.meeting_participant import MeetingParticipant
from app.models.meeting_transcript import MeetingTranscript
from app.models.team_member import TeamMember
from app.models.task import Task
from app.models.user import User

logger = logging.getLogger(__name__)


def visible_meeting_query(db: Session, user_id: int, is_admin: bool = False):
    """构建用户可见的会议查询（组织者 / 参与者 / 团队成员）。"""
    if is_admin:
        return db.query(Meeting)
    return (
        db.query(Meeting)
        .outerjoin(MeetingParticipant, MeetingParticipant.meeting_id == Meeting.id)
        .outerjoin(TeamMember, TeamMember.team_id == Meeting.team_id)
        .filter(
            or_(
                Meeting.organizer_id == user_id,
                MeetingParticipant.user_id == user_id,
                TeamMember.user_id == user_id,
            )
        )
    )


def knowledge_terms(question: str) -> list[str]:
    """从问题中提取关键词（>=2 字符，最多 6 个）。"""
    tokens = [item.strip() for item in re.split(r"[\s,.;:!?，。；：！？、]+", question) if item.strip()]
    terms = [item for item in tokens if len(item) >= 2]
    if not terms and question.strip():
        terms = [question.strip()]
    return terms[:6]


def clip_snippet(text: str | None, limit: int = 220) -> str:
    """裁剪文本片段到指定长度。"""
    normalized = re.sub(r"\s+", " ", (text or "").strip())
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[:limit].rstrip()}..."


def _append_source(
    sources: list[dict[str, object]],
    seen: set[tuple[int, str, str]],
    *,
    meeting: Meeting,
    source_type: str,
    snippet: str | None,
) -> None:
    clipped = clip_snippet(snippet)
    if not clipped:
        return
    key = (meeting.id, source_type, clipped)
    if key in seen:
        return
    seen.add(key)
    sources.append(
        {
            "meeting_id": meeting.id,
            "meeting_title": meeting.title,
            "source_type": source_type,
            "snippet": clipped,
            "created_at": meeting.created_at,
        }
    )


def search_meetings(
    db: Session,
    user_id: int,
    terms: list[str],
    meeting_query,
    team_id: int | None,
    limit: int,
    sources: list[dict[str, object]],
    seen: set[tuple[int, str, str]],
) -> None:
    """搜索匹配的会议标题/描述/摘要。"""
    query = meeting_query
    if team_id is not None:
        query = query.filter(Meeting.team_id == team_id)
    if terms:
        text_filters = []
        for term in terms:
            like = f"%{term}%"
            text_filters.extend(
                [Meeting.title.ilike(like), Meeting.description.ilike(like), Meeting.summary.ilike(like)]
            )
        matching = query.filter(or_(*text_filters)).order_by(Meeting.updated_at.desc(), Meeting.id.desc()).limit(limit).all()
    else:
        matching = query.order_by(Meeting.updated_at.desc(), Meeting.id.desc()).limit(limit).all()

    for meeting in matching:
        _append_source(sources, seen, meeting=meeting, source_type="meeting", snippet=f"{meeting.title}\n{meeting.description or ''}")
        _append_source(sources, seen, meeting=meeting, source_type="summary", snippet=meeting.summary)
        if len(sources) >= limit:
            break


def search_transcripts(
    db: Session,
    user_id: int,
    terms: list[str],
    team_id: int | None,
    is_admin: bool,
    limit: int,
    sources: list[dict[str, object]],
    seen: set[tuple[int, str, str]],
) -> None:
    """搜索匹配的转写内容。"""
    query = (
        db.query(MeetingTranscript, Meeting)
        .join(Meeting, Meeting.id == MeetingTranscript.meeting_id)
        .outerjoin(MeetingParticipant, MeetingParticipant.meeting_id == Meeting.id)
        .outerjoin(TeamMember, TeamMember.team_id == Meeting.team_id)
    )
    if not is_admin:
        query = query.filter(or_(Meeting.organizer_id == user_id, MeetingParticipant.user_id == user_id, TeamMember.user_id == user_id))
    if team_id is not None:
        query = query.filter(Meeting.team_id == team_id)
    if terms:
        query = query.filter(or_(*(MeetingTranscript.content.ilike(f"%{term}%") for term in terms)))
    rows = query.order_by(Meeting.updated_at.desc(), MeetingTranscript.segment_index.asc()).limit(limit * 2).all()
    for transcript, meeting in rows:
        _append_source(sources, seen, meeting=meeting, source_type="transcript", snippet=transcript.content)
        if len(sources) >= limit:
            break


def search_tasks(
    db: Session,
    user_id: int,
    terms: list[str],
    team_id: int | None,
    is_admin: bool,
    limit: int,
    sources: list[dict[str, object]],
    seen: set[tuple[int, str, str]],
) -> None:
    """搜索匹配的任务。"""
    query = (
        db.query(Task, Meeting)
        .join(Meeting, Meeting.id == Task.meeting_id)
        .outerjoin(MeetingParticipant, MeetingParticipant.meeting_id == Meeting.id)
        .outerjoin(TeamMember, TeamMember.team_id == Meeting.team_id)
    )
    if not is_admin:
        query = query.filter(or_(Meeting.organizer_id == user_id, MeetingParticipant.user_id == user_id, TeamMember.user_id == user_id))
    if team_id is not None:
        query = query.filter(Meeting.team_id == team_id)
    if terms:
        query = query.filter(or_(*(field.ilike(f"%{term}%") for term in terms for field in (Task.title, Task.description, Task.progress_note))))
    rows = query.order_by(Task.updated_at.desc(), Task.id.desc()).limit(limit * 2).all()
    for task, meeting in rows:
        _append_source(sources, seen, meeting=meeting, source_type="task", snippet=f"{task.title}: {task.description or ''}")
        if len(sources) >= limit:
            break


def search_participants(
    db: Session,
    user_id: int,
    terms: list[str],
    team_id: int | None,
    is_admin: bool,
    limit: int,
    sources: list[dict[str, object]],
    seen: set[tuple[int, str, str]],
) -> None:
    """搜索匹配的参与者。"""
    participant_match = aliased(MeetingParticipant)
    participant_access = aliased(MeetingParticipant)
    query = (
        db.query(User, Meeting, participant_match)
        .join(participant_match, participant_match.user_id == User.id)
        .join(Meeting, Meeting.id == participant_match.meeting_id)
        .outerjoin(participant_access, participant_access.meeting_id == Meeting.id)
        .outerjoin(TeamMember, TeamMember.team_id == Meeting.team_id)
    )
    if not is_admin:
        query = query.filter(or_(Meeting.organizer_id == user_id, participant_access.user_id == user_id, TeamMember.user_id == user_id))
    if team_id is not None:
        query = query.filter(Meeting.team_id == team_id)
    if terms:
        query = query.filter(or_(*(field.ilike(f"%{term}%") for term in terms for field in (User.full_name, User.username, User.email))))
    rows = query.order_by(Meeting.updated_at.desc(), participant_match.id.asc()).limit(limit * 2).all()
    for participant_user, meeting, participant in rows:
        display_name = participant_user.full_name or participant_user.username
        _append_source(
            sources, seen, meeting=meeting, source_type="participant",
            snippet=f"{display_name} attended this meeting as {participant.participant_role}; attendance status: {participant.attendance_status}.",
        )
        if len(sources) >= limit:
            break


async def query_meeting_knowledge(
    db: Session,
    user_id: int,
    question: str,
    *,
    team_id: int | None = None,
    limit: int = 5,
    is_admin: bool = False,
) -> dict[str, object]:
    """搜索可访问的会议并构建知识回答。"""
    terms = knowledge_terms(question)
    sources: list[dict[str, object]] = []
    seen: set[tuple[int, str, str]] = set()

    meeting_query = visible_meeting_query(db, user_id, is_admin=is_admin)

    search_meetings(db, user_id, terms, meeting_query, team_id, limit, sources, seen)

    if len(sources) < limit:
        search_transcripts(db, user_id, terms, team_id, is_admin, limit, sources, seen)

    if len(sources) < limit:
        search_tasks(db, user_id, terms, team_id, is_admin, limit, sources, seen)

    if len(sources) < limit:
        search_participants(db, user_id, terms, team_id, is_admin, limit, sources, seen)

    if not sources:
        return {"answer": "没有在你有权限访问的会议知识库中找到相关内容。", "sources": [], "used_llm": False}

    context_text = "\n".join(
        f"[{index}] {item['meeting_title']} / {item['source_type']}: {item['snippet']}"
        for index, item in enumerate(sources, start=1)
    )
    fallback_answer = (
        "根据你有权限访问的会议知识库，找到以下相关线索：\n"
        + "\n".join(f"{index}. {item['meeting_title']}：{item['snippet']}" for index, item in enumerate(sources, start=1))
    )

    return {"answer": fallback_answer, "sources": sources, "context_text": context_text, "used_llm": False}
