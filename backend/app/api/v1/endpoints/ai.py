"""AI 助理 REST API。"""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from contextlib import suppress
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.ai_assistant import (
    ChatChunk,
    ChatRequest,
    ConversationCreateRequest,
    ConversationMessageResponse,
    ConversationResponse,
    TaskSuggestionsRequest,
    TaskSuggestionsResponse,
)
from app.schemas.auth import CurrentUserOut
from app.services.ai_assistant_service import AIAssistantService
from app.services.llm_service import llm_client
from app.services.meeting_service import get_meeting
from .auth import get_current_user

router = APIRouter(prefix="/ai", tags=["ai"], dependencies=[Depends(get_current_user)])

ai_service = AIAssistantService(llm_client)


def _build_chat_stream(
    *,
    db: Session,
    current_user: CurrentUserOut,
    message: str,
    conversation_id: int | None,
    meeting_id: int | None = None,
    task_id: int | None = None,
) -> StreamingResponse:
    context_dict: dict[str, object] = {}
    if meeting_id is not None:
        context_dict["meeting_id"] = meeting_id
    if task_id is not None:
        context_dict["task_id"] = task_id

    stream = ai_service.chat(
        db=db,
        user_id=current_user.id,
        message=message,
        conversation_id=conversation_id,
        context=context_dict or None,
    )

    async def event_stream() -> AsyncGenerator[str, None]:
        try:
            async for chunk in stream:
                event = ChatChunk(type="chunk", content=chunk)
                yield f"data: {event.model_dump_json()}\n\n"
            yield f"data: {ChatChunk(type='end').model_dump_json()}\n\n"
        except ValueError:
            error_event = ChatChunk(type="error", content="Invalid chat request")
            yield f"data: {json.dumps(error_event.model_dump(), ensure_ascii=False)}\n\n"
        except Exception:
            error_event = ChatChunk(type="error", content="Chat stream failed")
            yield f"data: {json.dumps(error_event.model_dump(), ensure_ascii=False)}\n\n"
        finally:
            with suppress(Exception):
                await stream.aclose()

    return StreamingResponse(event_stream(), media_type="text/event-stream")


async def _require_conversation_owner(
    db: Session,
    conversation_id: int,
    current_user: CurrentUserOut,
) -> None:
    conversation = await ai_service.get_conversation(db, conversation_id, current_user.id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")


@router.post("/task-suggestions", response_model=TaskSuggestionsResponse)
async def get_task_suggestions(
    payload: TaskSuggestionsRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
) -> TaskSuggestionsResponse:
    """获取任务建议。"""
    meeting_context: str | None = None

    if payload.meeting_id is not None:
        meeting = get_meeting(db, payload.meeting_id)
        if meeting is None:
            raise HTTPException(status_code=404, detail="Meeting not found")
        if current_user.role != "admin" and meeting.organizer_id != current_user.id:
            raise HTTPException(status_code=403, detail="Forbidden")
        meeting_context = f"会议标题：{meeting.title}\n会议描述：{meeting.description or ''}"

    try:
        suggestions = await llm_client.generate_task_suggestions(
            title=payload.title,
            description=payload.description or "",
            meeting_context=meeting_context,
        )
        return TaskSuggestionsResponse.model_validate(suggestions)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to generate suggestions") from exc


@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ConversationResponse]:
    """获取用户对话列表。"""
    conversations = await ai_service.get_conversations(db, current_user.id, limit=limit, offset=offset)
    return [ConversationResponse.model_validate(item) for item in conversations]


@router.post(
    "/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation(
    payload: ConversationCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
) -> ConversationResponse:
    """创建新对话。"""
    title = (payload.title or "新对话").strip() or "新对话"
    conversation = await ai_service.create_conversation(db, user_id=current_user.id, title=title)
    return ConversationResponse.model_validate(conversation)


@router.delete("/conversations/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
) -> None:
    """删除对话。"""
    await _require_conversation_owner(db, id, current_user)
    deleted = await ai_service.delete_conversation(db, conversation_id=id, user_id=current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")


@router.get("/conversations/{id}/messages", response_model=list[ConversationMessageResponse])
async def get_conversation_messages(
    id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
) -> list[ConversationMessageResponse]:
    """获取对话消息。"""
    await _require_conversation_owner(db, id, current_user)
    messages = await ai_service.get_messages(db, conversation_id=id)
    return [ConversationMessageResponse.model_validate(msg) for msg in messages]


@router.post("/chat")
async def chat(
    payload: ChatRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
) -> StreamingResponse:
    """SSE 流式聊天。"""
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="message cannot be empty")

    if payload.conversation_id is not None:
        await _require_conversation_owner(db, payload.conversation_id, current_user)

    meeting_id = payload.context.meeting_id if payload.context is not None else None
    task_id = payload.context.task_ids[0] if payload.context is not None and payload.context.task_ids else None

    return _build_chat_stream(
        db=db,
        current_user=current_user,
        message=payload.message,
        conversation_id=payload.conversation_id,
        meeting_id=meeting_id,
        task_id=task_id,
    )


@router.get("/chat")
async def chat_get(
    message: Annotated[str, Query(min_length=1)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
    conversation_id: int | None = Query(default=None),
    meeting_id: int | None = Query(default=None),
    task_id: int | None = Query(default=None),
) -> StreamingResponse:
    """兼容 EventSource 的 GET SSE 聊天入口。"""
    if conversation_id is not None:
        await _require_conversation_owner(db, conversation_id, current_user)

    return _build_chat_stream(
        db=db,
        current_user=current_user,
        message=message,
        conversation_id=conversation_id,
        meeting_id=meeting_id,
        task_id=task_id,
    )
