"""上下文构建服务。

负责为 AI 助手构建对话上下文信息。
"""

import logging
import re
from datetime import UTC, datetime, timedelta

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.meeting import Meeting
from app.models.meeting_participant import MeetingParticipant
from app.models.meeting_transcript import MeetingTranscript
from app.models.team_member import TeamMember
from app.models.task import Task
from app.models.user import User

logger = logging.getLogger(__name__)


def query_user_tasks(db: Session, user_id: int, limit: int = 8) -> list[Task]:
    return (
        db.query(Task)
        .join(Meeting, Meeting.id == Task.meeting_id)
        .outerjoin(TeamMember, TeamMember.team_id == Meeting.team_id)
        .filter(or_(Meeting.organizer_id == user_id, Task.assignee_id == user_id, Task.reporter_id == user_id, TeamMember.user_id == user_id))
        .order_by(Task.updated_at.desc(), Task.id.desc())
        .limit(limit)
        .all()
    )


def query_user_tasks_by_status(db: Session, user_id: int, status: str, limit: int = 8) -> list[Task]:
    return (
        db.query(Task)
        .join(Meeting, Meeting.id == Task.meeting_id)
        .outerjoin(TeamMember, TeamMember.team_id == Meeting.team_id)
        .filter(or_(Meeting.organizer_id == user_id, Task.assignee_id == user_id, Task.reporter_id == user_id, TeamMember.user_id == user_id), Task.status == status)
        .order_by(Task.updated_at.desc(), Task.id.desc())
        .limit(limit)
        .all()
    )


def query_due_soon_tasks(db: Session, user_id: int, limit: int = 5) -> list[Task]:
    now = datetime.now(UTC).replace(tzinfo=None)
    deadline = now + timedelta(days=3)
    return (
        db.query(Task)
        .join(Meeting, Meeting.id == Task.meeting_id)
        .outerjoin(TeamMember, TeamMember.team_id == Meeting.team_id)
        .filter(or_(Meeting.organizer_id == user_id, Task.assignee_id == user_id, Task.reporter_id == user_id, TeamMember.user_id == user_id), Task.status != "done", Task.due_at.isnot(None), Task.due_at <= deadline)
        .order_by(Task.due_at.asc(), Task.id.desc())
        .limit(limit)
        .all()
    )


def query_meeting_tasks(db: Session, meeting_id: int, limit: int = 8) -> list[Task]:
    return db.query(Task).filter(Task.meeting_id == meeting_id).order_by(Task.updated_at.desc(), Task.id.desc()).limit(limit).all()


def query_recent_meetings(db: Session, user_id: int, limit: int = 5) -> list[Meeting]:
    return (
        db.query(Meeting)
        .outerjoin(TeamMember, TeamMember.team_id == Meeting.team_id)
        .filter(or_(Meeting.organizer_id == user_id, TeamMember.user_id == user_id))
        .order_by(Meeting.updated_at.desc(), Meeting.id.desc())
        .limit(limit)
        .all()
    )


def query_meeting_transcript_preview(db: Session, meeting_id: int, limit: int = 3) -> list[MeetingTranscript]:
    return db.query(MeetingTranscript).filter(MeetingTranscript.meeting_id == meeting_id).order_by(MeetingTranscript.segment_index.asc()).limit(limit).all()


def format_task_list(tasks: list[Task]) -> str:
    if not tasks:
        return "当前没有查询到相关任务。"
    lines: list[str] = []
    for index, task in enumerate(tasks, start=1):
        due = task.due_at.strftime("%Y-%m-%d") if task.due_at else "无截止时间"
        lines.append(f"{index}. {task.title}｜状态：{task.status}｜优先级：{task.priority}｜截止：{due}")
    return "\n".join(lines)


def format_task_overview(tasks: list[Task]) -> str:
    if not tasks:
        return "当前没有查询到相关任务。"
    counts = {"todo": 0, "in_progress": 0, "done": 0}
    for task in tasks:
        if task.status in counts:
            counts[task.status] += 1
    return f"共 {len(tasks)} 条任务，其中待办 {counts['todo']} 条，进行中 {counts['in_progress']} 条，已完成 {counts['done']} 条。"


def extract_resolution_lines(transcripts: list[MeetingTranscript], limit: int = 3) -> list[str]:
    resolution_keywords = ("决定", "确定", "通过", "定为", "最终决定", "结论")
    lines: list[str] = []
    seen: set[str] = set()
    for transcript in transcripts:
        content = transcript.content.strip()
        if not content or not any(kw in content for kw in resolution_keywords) or content in seen:
            continue
        seen.add(content)
        lines.append(content)
        if len(lines) >= limit:
            break
    return lines


def build_meeting_summary_direct_answer(meeting: Meeting, transcripts: list[MeetingTranscript], message: str) -> str:
    normalized = message.strip().lower()
    if any(keyword in normalized for keyword in ("决议", "决定")):
        resolution_lines = extract_resolution_lines(transcripts)
        if resolution_lines:
            return f'会议"{meeting.title}"当前记录到的决议如下：\n' + "\n".join(f"- {line}" for line in resolution_lines)
        if meeting.summary:
            return f'会议"{meeting.title}"当前没有单独整理出的决议列表，这是现有会议纪要：\n{meeting.summary}'
        return f'会议"{meeting.title}"当前没有记录到明确决议。'
    if meeting.summary:
        if any(keyword in normalized for keyword in ("纪要", "摘要", "总结")):
            return f'会议"{meeting.title}"的会议纪要如下：\n{meeting.summary}'
        return f'会议"{meeting.title}"当前记录到的主要内容如下：\n{meeting.summary}'
    preview_lines = [item.content.strip() for item in transcripts if item.content.strip()][:5]
    if preview_lines:
        return f'会议"{meeting.title}"当前还没有整理好的会议纪要，但已有转写内容如下：\n' + "\n".join(f"- {line}" for line in preview_lines)
    return f'会议"{meeting.title}"当前没有记录到会议纪要或转写内容。'


def build_meeting_summary_context(db: Session, meeting_id: int) -> dict[str, str]:
    context_info: dict[str, str] = {}
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        context_info["meeting_not_found"] = f"会议 #{meeting_id} 不存在或无权访问"
        return context_info
    context_info["meeting_id"] = str(meeting.id)
    context_info["meeting_title"] = meeting.title
    context_info["meeting_description"] = meeting.description if meeting.description else ""
    if meeting.summary:
        context_info["meeting_summary"] = meeting.summary
    else:
        context_info["meeting_summary_missing"] = "当前没有记录会议摘要"
    tasks = query_meeting_tasks(db, meeting.id)
    context_info["meeting_tasks"] = format_task_list(tasks)
    if not tasks:
        context_info["meeting_tasks_missing"] = "当前没有记录该会议的任务"
    participants = (
        db.query(User.full_name)
        .join(MeetingParticipant, MeetingParticipant.user_id == User.id)
        .filter(MeetingParticipant.meeting_id == meeting.id)
        .order_by(MeetingParticipant.id.asc())
        .all()
    )
    participant_names = [name for (name,) in participants if name]
    if participant_names:
        context_info["meeting_participants"] = "、".join(participant_names)
    else:
        context_info["meeting_participants_missing"] = "当前没有记录参会人员"
    transcripts = query_meeting_transcript_preview(db, meeting.id)
    if transcripts:
        context_info["meeting_transcript_preview"] = "\n".join(f"- {item.speaker_name or '未知'}：{item.content}" for item in transcripts)
        resolution_lines = extract_resolution_lines(transcripts)
        if resolution_lines:
            context_info["meeting_resolution_preview"] = "\n".join(f"- {line}" for line in resolution_lines)
    else:
        context_info["meeting_transcript_missing"] = "当前没有记录会议转写内容"
    return context_info


def resolve_meeting_id_from_message(db: Session, user_id: int, message: str) -> int | None:
    normalized = message.strip()
    if not normalized:
        return None
    meetings = query_recent_meetings(db, user_id, limit=20)
    for meeting in meetings:
        title = (meeting.title or "").strip()
        if title and title in normalized:
            return meeting.id
    extracted_candidates = [segment.strip("\"'《》[]（）()“” ") for segment in re.split(r"[，。！？?\n]", normalized) if segment.strip()]
    for candidate in extracted_candidates:
        if len(candidate) < 2:
            continue
        meeting = (
            db.query(Meeting)
            .outerjoin(TeamMember, TeamMember.team_id == Meeting.team_id)
            .filter(or_(Meeting.organizer_id == user_id, TeamMember.user_id == user_id), Meeting.title.ilike(f"%{candidate}%"))
            .order_by(Meeting.updated_at.desc(), Meeting.id.desc())
            .first()
        )
        if meeting:
            return meeting.id
    return None


def resolve_effective_context(db: Session, user_id: int, message: str, context: dict[str, object] | None) -> dict[str, object]:
    effective_context = dict(context) if isinstance(context, dict) else {}
    if "meeting_id" not in effective_context:
        matched_meeting_id = resolve_meeting_id_from_message(db, user_id, message)
        if matched_meeting_id is not None:
            effective_context["meeting_id"] = matched_meeting_id
    return effective_context


def build_context_info(context: dict[str, object] | None, db: Session, user_id: int | None = None) -> dict[str, str]:
    if not context:
        return {}
    context_info: dict[str, str] = {}
    meeting_id_raw = context.get("meeting_id")
    if isinstance(meeting_id_raw, int):
        meeting = db.query(Meeting).filter(Meeting.id == meeting_id_raw).first()
        if meeting:
            context_info["meeting_id"] = str(meeting.id)
            context_info["meeting_title"] = meeting.title
            if meeting.description:
                context_info["meeting_description"] = meeting.description
    task_id_raw = context.get("task_id")
    if isinstance(task_id_raw, int):
        task = db.query(Task).filter(Task.id == task_id_raw).first()
        if task:
            context_info["task_id"] = str(task.id)
            context_info["task_title"] = task.title
            if task.description:
                context_info["task_description"] = task.description
            context_info["task_status"] = task.status
            context_info["task_priority"] = task.priority
        else:
            context_info["task_not_found"] = f"任务 #{task_id_raw} 不存在或无权访问"
    return context_info
