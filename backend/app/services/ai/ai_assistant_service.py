"""AI 助理服务层（facade）。

将知识查询、上下文构建、对话管理委托给子模块，
本文件只保留意图分发和 LLM 调用编排。
"""

import logging
import re
from collections.abc import AsyncGenerator
from typing import Protocol

from sqlalchemy.orm import Session

from app.models.meeting import Meeting
from app.models.meeting_transcript import MeetingTranscript
from app.models.task import Task
from app.services.ai.intent import AssistantIntent, get_intent_classifier
from app.services.ai import chat_service, context_builder, knowledge_service

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

    # ── 权限检查（委托 knowledge_service 的可见性逻辑） ──

    def user_can_access_meeting(self, db: Session, user_id: int, meeting_id: int) -> bool:
        from app.models.meeting_participant import MeetingParticipant
        from app.models.team_member import TeamMember

        meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
        if meeting is None:
            return False
        if meeting.organizer_id == user_id:
            return True
        participant = db.query(MeetingParticipant.id).filter(MeetingParticipant.meeting_id == meeting_id, MeetingParticipant.user_id == user_id).first()
        if participant is not None:
            return True
        if meeting.team_id is None:
            return False
        member = db.query(TeamMember.id).filter(TeamMember.team_id == meeting.team_id, TeamMember.user_id == user_id).first()
        return member is not None

    def user_can_access_task(self, db: Session, user_id: int, task_id: int) -> bool:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task is None:
            return False
        if task.assignee_id == user_id or task.reporter_id == user_id:
            return True
        return self.user_can_access_meeting(db, user_id, task.meeting_id)

    # ── 意图分类 ──

    def classify_intent(self, message: str, context: dict[str, object] | None = None) -> AssistantIntent:
        return get_intent_classifier().classify(message, context)

    # ── 知识查询（委托） ──

    async def query_meeting_knowledge(
        self, db: Session, user_id: int, question: str, *, team_id: int | None = None, limit: int = 5, is_admin: bool = False,
    ) -> dict[str, object]:
        result = await knowledge_service.query_meeting_knowledge(db, user_id, question, team_id=team_id, limit=limit, is_admin=is_admin)
        # 如果有 LLM 且有上下文，尝试生成更好的回答
        context_text = result.get("context_text")
        if context_text and not result.get("used_llm"):
            try:
                llm_result = await self.llm_service.chat_completion(
                    messages=[{"role": "user", "content": f"请只基于给定会议知识库片段回答问题；无法确定时说明证据不足。\n问题：{question}\n片段：\n{context_text}"}],
                    context_info={"source_count": str(len(result.get("sources", []))), "answer_policy": "cite-meeting-sources"},
                    stream=False,
                )
                if isinstance(llm_result, str) and llm_result.strip():
                    return {"answer": llm_result.strip(), "sources": result["sources"], "used_llm": True}
            except Exception:
                logger.exception("Meeting knowledge LLM answer failed; falling back to snippets")
        return result

    # ── 直接查询处理 ──

    async def _try_handle_direct_query(self, db: Session, user_id: int, message: str, context: dict[str, object] | None) -> str | None:
        effective_context = context_builder.resolve_effective_context(db, user_id, message, context)
        intent = self.classify_intent(message, effective_context)

        if intent == "my_tasks":
            normalized = message.strip().lower()
            if any(keyword in normalized for keyword in ("待办", "todo")):
                tasks = context_builder.query_user_tasks_by_status(db, user_id, "todo")
                return "你当前没有待办任务。" if not tasks else "这是你当前的待办任务：\n" + context_builder.format_task_list(tasks)
            if any(keyword in normalized for keyword in ("进行中", "in_progress")):
                tasks = context_builder.query_user_tasks_by_status(db, user_id, "in_progress")
                return "你当前没有进行中的任务。" if not tasks else "这是你当前进行中的任务：\n" + context_builder.format_task_list(tasks)
            if any(keyword in normalized for keyword in ("已完成", "完成了")):
                tasks = context_builder.query_user_tasks_by_status(db, user_id, "done")
                return "你当前没有已完成任务。" if not tasks else "这是你当前已完成的任务：\n" + context_builder.format_task_list(tasks)
            if any(keyword in normalized for keyword in ("快到期", "即将到期", "近期截止")):
                tasks = context_builder.query_due_soon_tasks(db, user_id)
                return "你当前没有 3 天内到期的任务。" if not tasks else "这是你近期快到期的任务：\n" + context_builder.format_task_list(tasks)
            tasks = context_builder.query_user_tasks(db, user_id)
            if not tasks:
                return "你当前没有查询到任务数据。可以先去会议中生成行动项，或手动创建任务。"
            return context_builder.format_task_overview(tasks) + "\n这是你当前最相关的任务：\n" + context_builder.format_task_list(tasks)

        if intent == "meeting_tasks":
            meeting_id_raw = effective_context.get("meeting_id")
            if isinstance(meeting_id_raw, int):
                tasks = context_builder.query_meeting_tasks(db, meeting_id_raw)
                meeting = db.query(Meeting).filter(Meeting.id == meeting_id_raw).first()
                meeting_title = meeting.title if meeting else f"#{meeting_id_raw}"
                if not tasks:
                    return f'当前会议"{meeting_title}"还没有生成任务。你可以先执行会议后处理，或手动新建任务。'
                return f'这是会议"{meeting_title}"的任务：\n' + context_builder.format_task_list(tasks)

        if intent == "meeting_summary":
            meeting_id_raw = effective_context.get("meeting_id")
            if isinstance(meeting_id_raw, int):
                meeting = db.query(Meeting).filter(Meeting.id == meeting_id_raw).first()
                if not meeting:
                    return f"会议 #{meeting_id_raw} 不存在或无权访问。"
                transcripts = db.query(MeetingTranscript).filter(MeetingTranscript.meeting_id == meeting_id_raw).order_by(MeetingTranscript.segment_index.asc(), MeetingTranscript.id.asc()).all()
                return context_builder.build_meeting_summary_direct_answer(meeting, transcripts, message)

        if intent == "knowledge_query":
            result = await self.query_meeting_knowledge(db, user_id, message, limit=5)
            sources = result.get("sources")
            if isinstance(sources, list) and sources:
                answer = str(result.get("answer") or "")
                source_lines = [f"- {item.get('meeting_title')} ({item.get('source_type')}): {item.get('snippet')}" for item in sources if isinstance(item, dict)]
                return answer + "\n\n来源：\n" + "\n".join(source_lines)

        return None

    # ── 动态上下文构建 ──

    async def _build_dynamic_context_info(self, db: Session, user_id: int, message: str, context: dict[str, object] | None) -> dict[str, str]:
        effective_context = context_builder.resolve_effective_context(db, user_id, message, context)
        context_info = context_builder.build_context_info(effective_context, db, user_id=user_id)
        intent = self.classify_intent(message, effective_context)
        context_info["assistant_intent"] = intent

        if intent == "my_tasks":
            tasks = context_builder.query_user_tasks(db, user_id)
            context_info["my_tasks_overview"] = context_builder.format_task_overview(tasks)
            context_info["my_tasks"] = context_builder.format_task_list(tasks)
            meetings = context_builder.query_recent_meetings(db, user_id)
            if meetings:
                context_info["recent_meetings"] = "；".join(meeting.title for meeting in meetings)
            return context_info

        meeting_id_raw = effective_context.get("meeting_id")
        if isinstance(meeting_id_raw, int) and intent in {"meeting_tasks", "meeting_summary", "execution_advice"}:
            context_info.update(context_builder.build_meeting_summary_context(db, meeting_id_raw))

        if intent == "execution_advice":
            tasks = context_builder.query_user_tasks(db, user_id)
            context_info["my_tasks_overview"] = context_builder.format_task_overview(tasks)
            context_info["my_tasks"] = context_builder.format_task_list(tasks)
            due_soon_tasks = context_builder.query_due_soon_tasks(db, user_id)
            if due_soon_tasks:
                context_info["due_soon_tasks"] = context_builder.format_task_list(due_soon_tasks)

        return context_info

    # ── 对话管理（委托） ──

    async def create_conversation(self, db: Session, user_id: int, title: str = "新对话"):
        return chat_service.create_conversation(db, user_id, title)

    async def get_conversations(self, db: Session, user_id: int, limit: int = 20, offset: int = 0):
        return chat_service.get_conversations(db, user_id, limit, offset)

    async def get_conversation(self, db: Session, conversation_id: int, user_id: int):
        return chat_service.get_conversation(db, conversation_id, user_id)

    async def delete_conversation(self, db: Session, conversation_id: int, user_id: int) -> bool:
        return chat_service.delete_conversation(db, conversation_id, user_id)

    async def get_messages(self, db: Session, conversation_id: int):
        return chat_service.get_messages(db, conversation_id)

    # ── 上下文信息构建（委托） ──

    async def build_context_info(self, context: dict[str, object] | None, db: Session, user_id: int | None = None) -> dict[str, str]:
        return context_builder.build_context_info(context, db, user_id)

    # ── 任务提及解析 ──

    async def parse_task_mentions(self, content: str, db: Session) -> list[Task]:
        task_id_matches = re.findall(r"@任务(\d+)", content)
        task_ids = [int(task_id) for task_id in task_id_matches]
        if not task_ids:
            return []
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

    # ── 主聊天入口 ──

    async def chat(
        self,
        db: Session,
        user_id: int,
        message: str,
        conversation_id: int | None = None,
        context: dict[str, object] | None = None,
    ) -> AsyncGenerator[str, None]:
        user_message_text = message.strip()
        if not user_message_text:
            raise ValueError("message cannot be empty")

        if conversation_id is None:
            conversation = await self.create_conversation(db, user_id=user_id, title=(user_message_text[:30] or "新对话"))
        else:
            conversation = await self.get_conversation(db, conversation_id, user_id)
            if conversation is None:
                raise ValueError("conversation not found or permission denied")

        try:
            chat_service.save_message(db, conversation.id, "user", user_message_text)
        except Exception:
            db.rollback()
            logger.exception("Failed to persist user message")
            raise

        mentioned_tasks = await self.parse_task_mentions(user_message_text, db)

        direct_answer = await self._try_handle_direct_query(db, user_id, user_message_text, context)
        if direct_answer:
            yield direct_answer
            try:
                chat_service.save_message(db, conversation.id, "assistant", direct_answer)
            except Exception:
                db.rollback()
                logger.exception("Failed to persist assistant direct answer, conversation_id=%s", conversation.id)
            return

        context_info = await self._build_dynamic_context_info(db, user_id, user_message_text, context)
        if mentioned_tasks:
            context_info["mentioned_tasks"] = "；".join(f"#{task.id} {task.title}" for task in mentioned_tasks)

        history_messages = await self.get_messages(db, conversation.id)
        llm_messages = [{"role": msg.role, "content": msg.content} for msg in history_messages if msg.role in {"user", "assistant"}]

        llm_result = await self.llm_service.chat_completion(messages=llm_messages, context_info=context_info or None, stream=True)
        if isinstance(llm_result, str):
            async def _single_chunk() -> AsyncGenerator[str, None]:
                if llm_result:
                    yield llm_result
            llm_stream = _single_chunk()
        else:
            llm_stream = llm_result

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
                    chat_service.save_message(db, conversation.id, "assistant", assistant_content)
                except Exception:
                    db.rollback()
                    logger.exception("Failed to persist assistant message, conversation_id=%s", conversation.id)
