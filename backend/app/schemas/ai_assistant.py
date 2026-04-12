# pyright: reportDeprecated=false
"""AI 助理 Schema 定义。"""

from datetime import datetime
from typing import ClassVar, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

TaskPriority = Literal["high", "medium", "low"]
ChatMessageRole = Literal["user", "assistant"]
ChatChunkType = Literal["chunk", "end", "error"]


class SuggestedRelatedTask(BaseModel):
    """建议关联任务。"""

    id: int
    """相关任务 ID。"""

    title: str
    """相关任务标题。"""


class SuggestedTask(BaseModel):
    """建议的任务结构。"""

    title: str
    """任务标题。"""

    description: Optional[str] = None
    """任务描述。"""

    assignee_name: Optional[str] = None
    """建议负责人名称。"""

    priority: TaskPriority = Field(default="medium")
    """建议优先级。"""

    due_hint: Optional[str] = None
    """截止时间提示。"""


class TaskSuggestionsRequest(BaseModel):
    """任务建议请求。"""

    title: str = Field(..., min_length=1, max_length=200)
    """任务标题。"""

    description: Optional[str] = None
    """任务描述。"""

    meeting_id: Optional[int] = None
    """关联会议 ID。"""


class TaskSuggestionsResponse(BaseModel):
    """任务建议响应。"""

    steps: list[str] = Field(default_factory=list)
    """建议执行步骤。"""

    risks: list[str] = Field(default_factory=list)
    """潜在风险。"""

    suggested_roles: list[str] = Field(default_factory=list)
    """建议参与角色。"""

    related_tasks: list[SuggestedRelatedTask] = Field(default_factory=list)
    """相关任务列表。"""


class ConversationCreateRequest(BaseModel):
    """创建对话请求。"""

    title: Optional[str] = None
    """对话标题。"""


class ConversationResponse(BaseModel):
    """对话响应。"""

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: int
    """对话 ID。"""

    title: str
    """对话标题。"""

    created_at: datetime
    """创建时间。"""

    updated_at: datetime
    """更新时间。"""


class ConversationMessageResponse(BaseModel):
    """消息响应。"""

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: int
    """消息 ID。"""

    conversation_id: int
    """所属对话 ID。"""

    role: ChatMessageRole
    """消息角色。"""

    content: str
    """消息内容。"""

    created_at: datetime
    """创建时间。"""


class ChatContext(BaseModel):
    """聊天上下文信息。"""

    meeting_id: Optional[int] = None
    """会议 ID。"""

    task_ids: Optional[list[int]] = None
    """任务 ID 列表。"""


class ChatRequest(BaseModel):
    """聊天请求。"""

    message: str = Field(..., min_length=1)
    """用户消息。"""

    conversation_id: Optional[int] = None
    """对话 ID。"""

    context: Optional[ChatContext] = None
    """上下文信息。"""


class ConversationCreate(BaseModel):
    """创建对话请求（兼容旧接口）。"""

    title: str = Field(default="新对话", max_length=255)
    """对话标题。"""


class MessageCreate(BaseModel):
    """发送消息请求（兼容旧接口）。"""

    conversation_id: Optional[int] = None
    """对话 ID。"""

    message: str = Field(..., min_length=1)
    """用户消息。"""

    context: dict[str, int | str | None] = Field(default_factory=dict)
    """上下文信息。"""


class TaskDraftRequest(BaseModel):
    """任务草稿请求。"""

    title: str = Field(..., min_length=1, max_length=200)
    """任务标题。"""

    description: str = Field(..., min_length=1)
    """任务描述。"""

    meeting_id: int
    """关联会议 ID。"""

    due_date: datetime
    """截止时间。"""

    priority: TaskPriority = Field(default="medium")
    """优先级。"""

    assignee_id: int
    """负责人 ID。"""


class TaskDraftResponse(BaseModel):
    """任务草稿响应。"""

    id: Optional[int] = None
    """任务草稿 ID。"""

    title: str
    """任务标题。"""

    description: Optional[str] = None
    """任务描述。"""

    meeting_id: int
    """关联会议 ID。"""

    due_date: Optional[datetime] = None
    """截止时间。"""

    priority: TaskPriority
    """优先级。"""

    assignee_id: Optional[int] = None
    """负责人 ID。"""

    status: str = "draft"
    """草稿状态。"""


class TaskDraftCreate(BaseModel):
    """创建任务草稿请求（兼容旧接口）。"""

    meeting_id: int
    """关联会议 ID。"""

    title: str = Field(..., min_length=1, max_length=200)
    """任务标题。"""

    description: Optional[str] = None
    """任务描述。"""

    assignee_id: Optional[int] = None
    """负责人 ID。"""

    priority: str = Field(default="medium")
    """优先级。"""

    due_at: Optional[datetime] = None
    """截止时间。"""


class TaskDraftOut(BaseModel):
    """任务草稿响应（兼容旧接口）。"""

    id: int
    """任务草稿 ID。"""

    meeting_id: int
    """关联会议 ID。"""

    title: str
    """任务标题。"""

    description: Optional[str] = None
    """任务描述。"""

    assignee_id: Optional[int] = None
    """负责人 ID。"""

    priority: str
    """优先级。"""

    due_at: Optional[datetime] = None
    """截止时间。"""

    status: str = "draft"
    """草稿状态。"""


class ChatChunk(BaseModel):
    """SSE 流式响应块。"""

    type: ChatChunkType
    """块类型。"""

    content: Optional[str] = None
    """增量内容。"""

    task_draft: Optional[TaskDraftResponse] = None
    """任务草稿内容。"""


# Backward-compatible aliases.
TaskSuggestionRequest = TaskSuggestionsRequest
TaskSuggestionResponse = TaskSuggestionsResponse
ConversationOut = ConversationResponse
MessageOut = ConversationMessageResponse
RelatedTaskInfo = SuggestedRelatedTask


__all__ = [
    "TaskPriority",
    "ChatMessageRole",
    "ChatChunkType",
    "SuggestedRelatedTask",
    "SuggestedTask",
    "TaskSuggestionsRequest",
    "TaskSuggestionsResponse",
    "ConversationCreateRequest",
    "ConversationResponse",
    "ConversationMessageResponse",
    "ChatContext",
    "ChatRequest",
    "ConversationCreate",
    "MessageCreate",
    "TaskDraftRequest",
    "TaskDraftResponse",
    "TaskDraftCreate",
    "TaskDraftOut",
    "ChatChunk",
    "TaskSuggestionRequest",
    "TaskSuggestionResponse",
    "ConversationOut",
    "MessageOut",
    "RelatedTaskInfo",
]
