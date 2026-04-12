"""AI 助理服务层。"""

import logging
import re
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Protocol

from sqlalchemy.orm import Session

from app.models.conversation import Conversation, ConversationMessage
from app.models.meeting import Meeting
from app.models.task import Task

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

        # 4. 构建上下文信息
        context_info = await self.build_context_info(context, db)
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
