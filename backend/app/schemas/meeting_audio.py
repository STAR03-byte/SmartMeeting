"""会议音频 Schema 定义。"""

from datetime import datetime

from pydantic import BaseModel


class MeetingAudioOut(BaseModel):
    """会议音频响应。"""

    id: int
    meeting_id: int
    filename: str
    storage_path: str
    content_type: str
    size_bytes: int
    uploaded_at: datetime

    model_config = {"from_attributes": True}
