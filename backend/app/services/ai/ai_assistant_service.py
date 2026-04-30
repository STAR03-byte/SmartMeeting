"""AI 助理服务层。"""

import logging
import re
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from typing import Protocol

from sqlalchemy import or_
from sqlalchemy.orm import Session, aliased

from app.models.conversation import Conversation, ConversationMessage
from app.models.meeting import Meeting
from app.models.meeting_participant import MeetingParticipant
from app.models.meeting_transcript import MeetingTranscript
from app.models.team_member import TeamMember
from app.models.task import Task
from app.models.user import User
from app.services.ai.intent import AssistantIntent, get_intent_classifier

logger = logging.getLogger(__name__)


class LLMService(Protocol):
    """LLM 服务协议，便于注入与类型检查。"""

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        context_info: dict[str, str] | None = None,
        stream: bool = False,
    ) -> str | AsyncGenerator[str, None]:
        ...


class AIAssistantService:
    """AI 助理服务，处理对话和上下文注入。"""

    def __init__(self, llm_service: LLMService):
        self.llm_service: LLMService = llm_service

    def user_can_access_meeting(self, db: Session, user_id: int, meeting_id: int) -> bool:
        meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
        if meeting is None:
            return False
        if meeting.organizer_id == user_id:
            return True
        participant = (
            db.query(MeetingParticipant.id)
            .filter(MeetingParticipant.meeting_id == meeting_id, MeetingParticipant.user_id == user_id)
            .first()
        )
        if participant is not None:
            return True
        if meeting.team_id is None:
            return False
        member = (
            db.query(TeamMember.id)
            .filter(TeamMember.team_id == meeting.team_id, TeamMember.user_id == user_id)
            .first()
        )
        return member is not None

    def user_can_access_task(self, db: Session, user_id: int, task_id: int) -> bool:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task is None:
            return False
        if task.assignee_id == user_id or task.reporter_id == user_id:
            return True
        return self.user_can_access_meeting(db, user_id, task.meeting_id)

    def _visible_meeting_query(self, db: Session, user_id: int, is_admin: bool = False):
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

    def _knowledge_terms(self, question: str) -> list[str]:
        tokens = [item.strip() for item in re.split(r"[\s,.;:!?，。；：！？、]+", question) if item.strip()]
        terms = [item for item in tokens if len(item) >= 2]
        if not terms and question.strip():
            terms = [question.strip()]
        return terms[:6]

    def _clip_snippet(self, text: str | None, limit: int = 220) -> str:
        normalized = re.sub(r"\s+", " ", (text or "").strip())
        if len(normalized) <= limit:
            return normalized
        return f"{normalized[:limit].rstrip()}..."

    def _append_source(
        self,
        sources: list[dict[str, object]],
        seen: set[tuple[int, str, str]],
        *,
        meeting: Meeting,
        source_type: str,
        snippet: str | None,
    ) -> None:
        clipped = self._clip_snippet(snippet)
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

    async def query_meeting_knowledge(
        self,
        db: Session,
        user_id: int,
        question: str,
        *,
        team_id: int | None = None,
        limit: int = 5,
        is_admin: bool = False,
    ) -> dict[str, object]:
        """Search accessible meetings and build a grounded answer."""

        terms = self._knowledge_terms(question)
        sources: list[dict[str, object]] = []
        seen: set[tuple[int, str, str]] = set()

        meeting_query = self._visible_meeting_query(db, user_id, is_admin=is_admin)
        if team_id is not None:
            meeting_query = meeting_query.filter(Meeting.team_id == team_id)

        if terms:
            text_filters = []
            for term in terms:
                like = f"%{term}%"
                text_filters.extend(
                    [
                        Meeting.title.ilike(like),
                        Meeting.description.ilike(like),
                        Meeting.summary.ilike(like),
                    ]
                )
            matching_meetings = (
                meeting_query.filter(or_(*text_filters))
                .order_by(Meeting.updated_at.desc(), Meeting.id.desc())
                .limit(limit)
                .all()
            )
        else:
            matching_meetings = meeting_query.order_by(Meeting.updated_at.desc(), Meeting.id.desc()).limit(limit).all()

        for meeting in matching_meetings:
            self._append_source(
                sources,
                seen,
                meeting=meeting,
                source_type="meeting",
                snippet=f"{meeting.title}\n{meeting.description or ''}",
            )
            self._append_source(sources, seen, meeting=meeting, source_type="summary", snippet=meeting.summary)
            if len(sources) >= limit:
                break

        if len(sources) < limit:
            transcript_query = (
                db.query(MeetingTranscript, Meeting)
                .join(Meeting, Meeting.id == MeetingTranscript.meeting_id)
                .outerjoin(MeetingParticipant, MeetingParticipant.meeting_id == Meeting.id)
                .outerjoin(TeamMember, TeamMember.team_id == Meeting.team_id)
            )
            if not is_admin:
                transcript_query = transcript_query.filter(
                    or_(
                        Meeting.organizer_id == user_id,
                        MeetingParticipant.user_id == user_id,
                        TeamMember.user_id == user_id,
                    )
                )
            if team_id is not None:
                transcript_query = transcript_query.filter(Meeting.team_id == team_id)
            if terms:
                transcript_query = transcript_query.filter(
                    or_(*(MeetingTranscript.content.ilike(f"%{term}%") for term in terms))
                )
            transcript_rows = (
                transcript_query.order_by(Meeting.updated_at.desc(), MeetingTranscript.segment_index.asc())
                .limit(limit * 2)
                .all()
            )
            for transcript, meeting in transcript_rows:
                self._append_source(
                    sources,
                    seen,
                    meeting=meeting,
                    source_type="transcript",
                    snippet=transcript.content,
                )
                if len(sources) >= limit:
                    break

        if len(sources) < limit:
            task_query = (
                db.query(Task, Meeting)
                .join(Meeting, Meeting.id == Task.meeting_id)
                .outerjoin(MeetingParticipant, MeetingParticipant.meeting_id == Meeting.id)
                .outerjoin(TeamMember, TeamMember.team_id == Meeting.team_id)
            )
            if not is_admin:
                task_query = task_query.filter(
                    or_(
                        Meeting.organizer_id == user_id,
                        MeetingParticipant.user_id == user_id,
                        TeamMember.user_id == user_id,
                    )
                )
            if team_id is not None:
                task_query = task_query.filter(Meeting.team_id == team_id)
            if terms:
                task_query = task_query.filter(
                    or_(
                        *(
                            field.ilike(f"%{term}%")
                            for term in terms
                            for field in (Task.title, Task.description, Task.progress_note)
                        )
                    )
                )
            task_rows = task_query.order_by(Task.updated_at.desc(), Task.id.desc()).limit(limit * 2).all()
            for task, meeting in task_rows:
                self._append_source(
                    sources,
                    seen,
                    meeting=meeting,
                    source_type="task",
                    snippet=f"{task.title}: {task.description or ''}",
                )
                if len(sources) >= limit:
                    break

        if len(sources) < limit:
            participant_match = aliased(MeetingParticipant)
            participant_access = aliased(MeetingParticipant)
            participant_query = (
                db.query(User, Meeting, participant_match)
                .join(participant_match, participant_match.user_id == User.id)
                .join(Meeting, Meeting.id == participant_match.meeting_id)
                .outerjoin(participant_access, participant_access.meeting_id == Meeting.id)
                .outerjoin(TeamMember, TeamMember.team_id == Meeting.team_id)
            )
            if not is_admin:
                participant_query = participant_query.filter(
                    or_(
                        Meeting.organizer_id == user_id,
                        participant_access.user_id == user_id,
                        TeamMember.user_id == user_id,
                    )
                )
            if team_id is not None:
                participant_query = participant_query.filter(Meeting.team_id == team_id)
            if terms:
                participant_query = participant_query.filter(
                    or_(
                        *(
                            field.ilike(f"%{term}%")
                            for term in terms
                            for field in (User.full_name, User.username, User.email)
                        )
                    )
                )
            participant_rows = (
                participant_query.order_by(Meeting.updated_at.desc(), participant_match.id.asc())
                .limit(limit * 2)
                .all()
            )
            for participant_user, meeting, participant in participant_rows:
                display_name = participant_user.full_name or participant_user.username
                self._append_source(
                    sources,
                    seen,
                    meeting=meeting,
                    source_type="participant",
                    snippet=(
                        f"{display_name} attended this meeting as {participant.role or 'participant'}; "
                        f"attendance status: {participant.attendance_status}."
                    ),
                )
                if len(sources) >= limit:
                    break

        if not sources:
            return {
                "answer": "没有在你有权限访问的会议知识库中找到相关内容。",
                "sources": [],
                "used_llm": False,
            }

        context_text = "\n".join(
            f"[{index}] {item['meeting_title']} / {item['source_type']}: {item['snippet']}"
            for index, item in enumerate(sources, start=1)
        )
        fallback_answer = (
            "根据你有权限访问的会议知识库，找到以下相关线索：\n"
            + "\n".join(
                f"{index}. {item['meeting_title']}：{item['snippet']}"
                for index, item in enumerate(sources, start=1)
            )
        )

        try:
            llm_result = await self.llm_service.chat_completion(
                messages=[
                    {
                        "role": "user",
                        "content": (
                            "请只基于给定会议知识库片段回答问题；无法确定时说明证据不足。"
                            f"\n问题：{question}\n片段：\n{context_text}"
                        ),
                    }
                ],
                context_info={"source_count": str(len(sources)), "answer_policy": "cite-meeting-sources"},
                stream=False,
            )
            if isinstance(llm_result, str) and llm_result.strip():
                return {"answer": llm_result.strip(), "sources": sources, "used_llm": True}
        except Exception:
            logger.exception("Meeting knowledge LLM answer failed; falling back to snippets")

        return {"answer": fallback_answer, "sources": sources, "used_llm": False}

    def classify_intent(self, message: str, context: dict[str, object] | None = None) -> AssistantIntent:
        """委托给可替换的意图分类器。"""
        return get_intent_classifier().classify(message, context)

    def _resolve_effective_context(
        self,
        db: Session,
        user_id: int,
        message: str,
        context: dict[str, object] | None,
    ) -> dict[str, object]:
        effective_context = dict(context) if isinstance(context, dict) else {}
        if "meeting_id" not in effective_context:
            matched_meeting_id = self._resolve_meeting_id_from_message(db, user_id, message)
            if matched_meeting_id is not None:
                effective_context["meeting_id"] = matched_meeting_id
        return effective_context

    def _resolve_meeting_id_from_message(self, db: Session, user_id: int, message: str) -> int | None:
        normalized = message.strip()
        if not normalized:
            return None

        meetings = self._query_recent_meetings(db, user_id, limit=20)
        for meeting in meetings:
            title = (meeting.title or "").strip()
            if title and title in normalized:
                return meeting.id

        extracted_candidates = [segment.strip("“”\"'《》[]（）() ") for segment in re.split(r"[，。！？?\n]", normalized) if segment.strip()]
        for candidate in extracted_candidates:
            if len(candidate) < 2:
                continue
            meeting = (
                db.query(Meeting)
                .outerjoin(TeamMember, TeamMember.team_id == Meeting.team_id)
                .filter(
                    or_(Meeting.organizer_id == user_id, TeamMember.user_id == user_id),
                    Meeting.title.ilike(f"%{candidate}%"),
                )
                .order_by(Meeting.updated_at.desc(), Meeting.id.desc())
                .first()
            )
            if meeting:
                return meeting.id
        return None

    def _query_user_tasks(self, db: Session, user_id: int, limit: int = 8) -> list[Task]:
        return (
            db.query(Task)
            .join(Meeting, Meeting.id == Task.meeting_id)
            .outerjoin(TeamMember, TeamMember.team_id == Meeting.team_id)
            .filter(
                or_(
                    Meeting.organizer_id == user_id,
                    Task.assignee_id == user_id,
                    Task.reporter_id == user_id,
                    TeamMember.user_id == user_id,
                )
            )
            .order_by(Task.updated_at.desc(), Task.id.desc())
            .limit(limit)
            .all()
        )

    def _query_user_tasks_by_status(
        self,
        db: Session,
        user_id: int,
        status: str,
        limit: int = 8,
    ) -> list[Task]:
        return (
            db.query(Task)
            .join(Meeting, Meeting.id == Task.meeting_id)
            .outerjoin(TeamMember, TeamMember.team_id == Meeting.team_id)
            .filter(
                or_(
                    Meeting.organizer_id == user_id,
                    Task.assignee_id == user_id,
                    Task.reporter_id == user_id,
                    TeamMember.user_id == user_id,
                ),
                Task.status == status,
            )
            .order_by(Task.updated_at.desc(), Task.id.desc())
            .limit(limit)
            .all()
        )

    def _query_due_soon_tasks(self, db: Session, user_id: int, limit: int = 5) -> list[Task]:
        now = datetime.now(UTC).replace(tzinfo=None)
        deadline = now + timedelta(days=3)
        return (
            db.query(Task)
            .join(Meeting, Meeting.id == Task.meeting_id)
            .outerjoin(TeamMember, TeamMember.team_id == Meeting.team_id)
            .filter(
                or_(
                    Meeting.organizer_id == user_id,
                    Task.assignee_id == user_id,
                    Task.reporter_id == user_id,
                    TeamMember.user_id == user_id,
                ),
                Task.status != "done",
                Task.due_at.isnot(None),
                Task.due_at <= deadline,
            )
            .order_by(Task.due_at.asc(), Task.id.desc())
            .limit(limit)
            .all()
        )

    def _query_meeting_tasks(self, db: Session, meeting_id: int, limit: int = 8) -> list[Task]:
        return (
            db.query(Task)
            .filter(Task.meeting_id == meeting_id)
            .order_by(Task.updated_at.desc(), Task.id.desc())
            .limit(limit)
            .all()
        )

    def _query_recent_meetings(self, db: Session, user_id: int, limit: int = 5) -> list[Meeting]:
        return (
            db.query(Meeting)
            .outerjoin(TeamMember, TeamMember.team_id == Meeting.team_id)
            .filter(or_(Meeting.organizer_id == user_id, TeamMember.user_id == user_id))
            .order_by(Meeting.updated_at.desc(), Meeting.id.desc())
            .limit(limit)
            .all()
        )

    def _query_meeting_transcript_preview(self, db: Session, meeting_id: int, limit: int = 3) -> list[MeetingTranscript]:
        return (
            db.query(MeetingTranscript)
            .filter(MeetingTranscript.meeting_id == meeting_id)
            .order_by(MeetingTranscript.segment_index.asc())
            .limit(limit)
            .all()
        )

    def _format_task_list(self, tasks: list[Task]) -> str:
        if not tasks:
            return "当前没有查询到相关任务。"
        lines: list[str] = []
        for index, task in enumerate(tasks, start=1):
            due = task.due_at.strftime("%Y-%m-%d") if task.due_at else "无截止时间"
            lines.append(f"{index}. {task.title}｜状态：{task.status}｜优先级：{task.priority}｜截止：{due}")
        return "\n".join(lines)

    def _format_task_overview(self, tasks: list[Task]) -> str:
        if not tasks:
            return "当前没有查询到相关任务。"
        counts = {"todo": 0, "in_progress": 0, "done": 0}
        for task in tasks:
            if task.status in counts:
                counts[task.status] += 1
        return (
            f"共 {len(tasks)} 条任务，其中待办 {counts['todo']} 条，"
            f"进行中 {counts['in_progress']} 条，已完成 {counts['done']} 条。"
        )

    def _extract_resolution_lines(self, transcripts: list[MeetingTranscript], limit: int = 3) -> list[str]:
        resolution_keywords = ("决定", "确定", "通过", "定为", "最终决定", "结论")
        lines: list[str] = []
        seen: set[str] = set()

        for transcript in transcripts:
            content = transcript.content.strip()
            if not content:
                continue
            if not any(keyword in content for keyword in resolution_keywords):
                continue
            if content in seen:
                continue
            seen.add(content)
            lines.append(content)
            if len(lines) >= limit:
                break

        return lines

    def _build_meeting_summary_direct_answer(
        self,
        meeting: Meeting,
        transcripts: list[MeetingTranscript],
        message: str,
    ) -> str:
        normalized = message.strip().lower()

        if any(keyword in normalized for keyword in ("决议", "决定")):
            resolution_lines = self._extract_resolution_lines(transcripts)
            if resolution_lines:
                return f"会议“{meeting.title}”当前记录到的决议如下：\n" + "\n".join(
                    f"- {line}" for line in resolution_lines
                )
            if meeting.summary:
                return f"会议“{meeting.title}”当前没有单独整理出的决议列表，这是现有会议纪要：\n{meeting.summary}"
            return f"会议“{meeting.title}”当前没有记录到明确决议。"

        if meeting.summary:
            if any(keyword in normalized for keyword in ("纪要", "摘要", "总结")):
                return f"会议“{meeting.title}”的会议纪要如下：\n{meeting.summary}"
            return f"会议“{meeting.title}”当前记录到的主要内容如下：\n{meeting.summary}"

        preview_lines = [item.content.strip() for item in transcripts if item.content.strip()][:5]
        if preview_lines:
            return f"会议“{meeting.title}”当前还没有整理好的会议纪要，但已有转写内容如下：\n" + "\n".join(
                f"- {line}" for line in preview_lines
            )

        return f"会议“{meeting.title}”当前没有记录到会议纪要或转写内容。"

    def _build_meeting_summary_context(self, db: Session, meeting_id: int) -> dict[str, str]:
        context_info: dict[str, str] = {}
        meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
        if not meeting:
            context_info["meeting_not_found"] = f"会议 #{meeting_id} 不存在或无权访问"
            return context_info
        context_info["meeting_id"] = str(meeting.id)
        context_info["meeting_title"] = meeting.title
        if meeting.description:
            context_info["meeting_description"] = meeting.description
        else:
            context_info["meeting_description_missing"] = "当前没有记录会议描述"
        if meeting.summary:
            context_info["meeting_summary"] = meeting.summary
        else:
            context_info["meeting_summary_missing"] = "当前没有记录会议摘要"
        tasks = self._query_meeting_tasks(db, meeting.id)
        context_info["meeting_tasks"] = self._format_task_list(tasks)
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
        transcripts = self._query_meeting_transcript_preview(db, meeting.id)
        if transcripts:
            context_info["meeting_transcript_preview"] = "\n".join(
                f"- {item.speaker_name or '未知'}：{item.content}" for item in transcripts
            )
            resolution_lines = self._extract_resolution_lines(transcripts)
            if resolution_lines:
                context_info["meeting_resolution_preview"] = "\n".join(f"- {line}" for line in resolution_lines)
        else:
            context_info["meeting_transcript_missing"] = "当前没有记录会议转写内容"
        return context_info

    async def _build_dynamic_context_info(
        self,
        db: Session,
        user_id: int,
        message: str,
        context: dict[str, object] | None,
    ) -> dict[str, str]:
        effective_context = self._resolve_effective_context(db, user_id, message, context)

        context_info = await self.build_context_info(effective_context, db, user_id=user_id)
        intent = self.classify_intent(message, effective_context)
        context_info["assistant_intent"] = intent

        if intent == "my_tasks":
            tasks = self._query_user_tasks(db, user_id)
            context_info["my_tasks_overview"] = self._format_task_overview(tasks)
            context_info["my_tasks"] = self._format_task_list(tasks)
            meetings = self._query_recent_meetings(db, user_id)
            if meetings:
                context_info["recent_meetings"] = "；".join(meeting.title for meeting in meetings)
            return context_info

        meeting_id_raw = effective_context.get("meeting_id")
        if isinstance(meeting_id_raw, int) and intent in {"meeting_tasks", "meeting_summary", "execution_advice"}:
            context_info.update(self._build_meeting_summary_context(db, meeting_id_raw))

        if intent == "execution_advice":
            tasks = self._query_user_tasks(db, user_id)
            context_info["my_tasks_overview"] = self._format_task_overview(tasks)
            context_info["my_tasks"] = self._format_task_list(tasks)
            due_soon_tasks = self._query_due_soon_tasks(db, user_id)
            if due_soon_tasks:
                context_info["due_soon_tasks"] = self._format_task_list(due_soon_tasks)

        return context_info

    async def _try_handle_direct_query(
        self,
        db: Session,
        user_id: int,
        message: str,
        context: dict[str, object] | None,
    ) -> str | None:
        effective_context = self._resolve_effective_context(db, user_id, message, context)
        intent = self.classify_intent(message, effective_context)
        if intent == "my_tasks":
            normalized = message.strip().lower()
            if any(keyword in normalized for keyword in ("待办", "todo")):
                tasks = self._query_user_tasks_by_status(db, user_id, "todo")
                if not tasks:
                    return "你当前没有待办任务。"
                return "这是你当前的待办任务：\n" + self._format_task_list(tasks)
            if any(keyword in normalized for keyword in ("进行中", "in_progress")):
                tasks = self._query_user_tasks_by_status(db, user_id, "in_progress")
                if not tasks:
                    return "你当前没有进行中的任务。"
                return "这是你当前进行中的任务：\n" + self._format_task_list(tasks)
            if any(keyword in normalized for keyword in ("已完成", "完成了")):
                tasks = self._query_user_tasks_by_status(db, user_id, "done")
                if not tasks:
                    return "你当前没有已完成任务。"
                return "这是你当前已完成的任务：\n" + self._format_task_list(tasks)
            if any(keyword in normalized for keyword in ("快到期", "即将到期", "近期截止")):
                tasks = self._query_due_soon_tasks(db, user_id)
                if not tasks:
                    return "你当前没有 3 天内到期的任务。"
                return "这是你近期快到期的任务：\n" + self._format_task_list(tasks)

            tasks = self._query_user_tasks(db, user_id)
            if not tasks:
                return "你当前没有查询到任务数据。可以先去会议中生成行动项，或手动创建任务。"
            return self._format_task_overview(tasks) + "\n这是你当前最相关的任务：\n" + self._format_task_list(tasks)

        if intent == "meeting_tasks":
            meeting_id_raw = effective_context.get("meeting_id")
            if isinstance(meeting_id_raw, int):
                tasks = self._query_meeting_tasks(db, meeting_id_raw)
                meeting = db.query(Meeting).filter(Meeting.id == meeting_id_raw).first()
                meeting_title = meeting.title if meeting else f"#{meeting_id_raw}"
                if not tasks:
                    return f"当前会议“{meeting_title}”还没有生成任务。你可以先执行会议后处理，或手动新建任务。"
                return f"这是会议“{meeting_title}”的任务：\n" + self._format_task_list(tasks)

        if intent == "meeting_summary":
            meeting_id_raw = effective_context.get("meeting_id")
            if isinstance(meeting_id_raw, int):
                meeting = db.query(Meeting).filter(Meeting.id == meeting_id_raw).first()
                if not meeting:
                    return f"会议 #{meeting_id_raw} 不存在或无权访问。"
                transcripts = (
                    db.query(MeetingTranscript)
                    .filter(MeetingTranscript.meeting_id == meeting_id_raw)
                    .order_by(MeetingTranscript.segment_index.asc(), MeetingTranscript.id.asc())
                    .all()
                )
                return self._build_meeting_summary_direct_answer(meeting, transcripts, message)

        if intent == "knowledge_query":
            result = await self.query_meeting_knowledge(db, user_id, message, limit=5)
            sources = result.get("sources")
            if isinstance(sources, list) and sources:
                answer = str(result.get("answer") or "")
                source_lines = [
                    f"- {item.get('meeting_title')} ({item.get('source_type')}): {item.get('snippet')}"
                    for item in sources
                    if isinstance(item, dict)
                ]
                return answer + "\n\n来源：\n" + "\n".join(source_lines)

        return None

    async def create_conversation(
        self, db: Session, user_id: int, title: str = "新对话"
    ) -> Conversation:
        """创建新对话。"""
        conversation = Conversation(user_id=user_id, title=title)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return conversation

    async def get_conversations(
        self, db: Session, user_id: int, limit: int = 20, offset: int = 0
    ) -> list[Conversation]:
        """获取用户对话列表。"""
        return (
            db.query(Conversation)
            .filter(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    async def get_conversation(
        self, db: Session, conversation_id: int, user_id: int
    ) -> Conversation | None:
        """获取单个对话（验证用户权限）。"""
        return (
            db.query(Conversation)
            .filter(Conversation.id == conversation_id, Conversation.user_id == user_id)
            .first()
        )

    async def delete_conversation(
        self, db: Session, conversation_id: int, user_id: int
    ) -> bool:
        """删除对话。"""
        conversation = await self.get_conversation(db, conversation_id, user_id)
        if not conversation:
            return False
        db.delete(conversation)
        db.commit()
        return True

    async def get_messages(
        self, db: Session, conversation_id: int
    ) -> list[ConversationMessage]:
        """获取对话消息历史。"""
        return (
            db.query(ConversationMessage)
            .filter(ConversationMessage.conversation_id == conversation_id)
            .order_by(ConversationMessage.created_at)
            .all()
        )

    async def chat(
        self,
        db: Session,
        user_id: int,
        message: str,
        conversation_id: int | None = None,
        context: dict[str, object] | None = None,
    ) -> AsyncGenerator[str, None]:
        """
        发送消息并获取 AI 流式回复。

        Args:
            db: 数据库会话
            user_id: 用户ID
            message: 用户消息
            conversation_id: 对话ID（None则创建新对话）
            context: 上下文信息 {meeting_id, task_id}

        Yields:
            AI 回复的文本片段
        """
        user_message_text = message.strip()
        if not user_message_text:
            raise ValueError("message cannot be empty")

        # 1. 如果没有 conversation_id，创建新对话
        if conversation_id is None:
            conversation = await self.create_conversation(
                db,
                user_id=user_id,
                title=(user_message_text[:30] or "新对话"),
            )
        else:
            conversation = await self.get_conversation(db, conversation_id, user_id)
            if conversation is None:
                raise ValueError("conversation not found or permission denied")

        # 2. 保存用户消息
        try:
            db.add(
                ConversationMessage(
                    conversation_id=conversation.id,
                    role="user",
                    content=user_message_text,
                )
            )
            conversation.updated_at = datetime.now()
            db.add(conversation)
            db.commit()
        except Exception:
            db.rollback()
            logger.exception("Failed to persist user message")
            raise

        # 3. 解析 @任务123 提及
        mentioned_tasks = await self.parse_task_mentions(user_message_text, db)

        direct_answer = await self._try_handle_direct_query(db, user_id, user_message_text, context)
        if direct_answer:
            yield direct_answer
            try:
                db.add(
                    ConversationMessage(
                        conversation_id=conversation.id,
                        role="assistant",
                        content=direct_answer,
                    )
                )
                conversation.updated_at = datetime.now()
                db.add(conversation)
                db.commit()
            except Exception:
                db.rollback()
                logger.exception(
                    "Failed to persist assistant direct answer, conversation_id=%s",
                    conversation.id,
                )
            return

        # 4. 构建上下文信息
        context_info = await self._build_dynamic_context_info(db, user_id, user_message_text, context)
        if mentioned_tasks:
            context_info["mentioned_tasks"] = "；".join(
                f"#{task.id} {task.title}" for task in mentioned_tasks
            )

        # 5. 获取历史消息作为上下文
        history_messages = await self.get_messages(db, conversation.id)
        llm_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in history_messages
            if msg.role in {"user", "assistant"}
        ]

        # 6. 调用 llm_service.chat_completion(stream=True)
        llm_result = await self.llm_service.chat_completion(
            messages=llm_messages,
            context_info=context_info or None,
            stream=True,
        )
        if isinstance(llm_result, str):
            async def _single_chunk() -> AsyncGenerator[str, None]:
                if llm_result:
                    yield llm_result

            llm_stream = _single_chunk()
        else:
            llm_stream = llm_result

        # 7. 流式返回并保存 AI 回复
        chunks: list[str] = []
        try:
            async for chunk in llm_stream:
                if not chunk:
                    continue
                chunks.append(chunk)
                yield chunk
        except Exception:
            logger.exception("LLM streaming failed for conversation_id=%s", conversation.id)
            raise
        finally:
            assistant_content = "".join(chunks).strip()
            if assistant_content:
                try:
                    db.add(
                        ConversationMessage(
                            conversation_id=conversation.id,
                            role="assistant",
                            content=assistant_content,
                        )
                    )
                    conversation.updated_at = datetime.now()
                    db.add(conversation)
                    db.commit()
                except Exception:
                    db.rollback()
                    logger.exception(
                        "Failed to persist assistant message, conversation_id=%s",
                        conversation.id,
                    )

    async def parse_task_mentions(self, content: str, db: Session) -> list[Task]:
        """解析 @任务123 格式的提及，返回任务详情。"""
        task_id_matches: list[str] = re.findall(r"@任务(\d+)", content)
        task_ids = [int(task_id) for task_id in task_id_matches]
        if not task_ids:
            return []

        # 保留顺序去重
        deduped_ids: list[int] = []
        seen: set[int] = set()
        for task_id in task_ids:
            if task_id in seen:
                continue
            seen.add(task_id)
            deduped_ids.append(task_id)

        tasks = db.query(Task).filter(Task.id.in_(deduped_ids)).all()
        tasks_map = {task.id: task for task in tasks}
        return [tasks_map[task_id] for task_id in deduped_ids if task_id in tasks_map]

    async def build_context_info(
        self, context: dict[str, object] | None, db: Session, user_id: int | None = None
    ) -> dict[str, str]:
        """根据 meeting_id/task_id 构建上下文信息。"""
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
