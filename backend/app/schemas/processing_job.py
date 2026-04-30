"""异步处理任务 Schema。"""

from datetime import datetime
from typing import ClassVar

from pydantic import BaseModel, ConfigDict


class ProcessingJobOut(BaseModel):
    """任务状态响应。"""

    job_id: str
    meeting_id: int
    job_type: str
    status: str
    progress: float
    message: str
    current_chunk: int
    total_chunks: int
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)


class ProcessingJobResultOut(ProcessingJobOut):
    """任务完成结果响应。"""

    result_json: str | None = None
