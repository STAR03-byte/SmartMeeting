"""实体提取服务。

从会议转写中提取决策、承诺和主题。
"""

import json
import logging
import re
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.commitment import Commitment
from app.models.decision import Decision
from app.models.meeting import Meeting
from app.models.meeting_topic import MeetingTopic
from app.models.meeting_transcript import MeetingTranscript
from app.models.user import User

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """你是一个专业的会议分析助手。请从以下会议转写内容中提取：

1. **决策 (decisions)**：会议中做出的决定、结论、共识
2. **承诺 (commitments)**：参会人员做出的承诺、任务分配、待办事项
3. **主题 (topics)**：会议讨论的主要话题（3-5 个）

请严格以 JSON 格式输出，格式如下：
```json
{
  "decisions": [
    {
      "content": "决策内容",
      "proposer_name": "提出者姓名（如有）",
      "context": "相关背景（如有）",
      "confidence": 0.8
    }
  ],
  "commitments": [
    {
      "content": "承诺/任务内容",
      "assignee_name": "负责人姓名（如有）",
      "due_hint": "截止时间提示（如有，如'下周五'、'月底前'）"
    }
  ],
  "topics": [
    {
      "topic": "主题名称",
      "relevance_score": 0.9
    }
  ]
}
```

注意：
- 如果某类信息不存在，返回空数组
- confidence 范围 0-1，表示提取的置信度
- relevance_score 范围 0-1，表示主题的相关度
- 只提取明确的信息，不要推测

会议转写内容：
{transcript_text}
"""


def _build_transcript_text(transcripts: list[MeetingTranscript], max_length: int = 8000) -> str:
    """构建转写文本，限制长度。"""
    parts: list[str] = []
    total_length = 0
    for t in transcripts:
        speaker = t.speaker_name or "未知"
        line = f"[{speaker}]: {t.content}"
        if total_length + len(line) > max_length:
            break
        parts.append(line)
        total_length += len(line)
    return "\n".join(parts)


def _parse_llm_response(response: str) -> dict:
    """解析 LLM 返回的 JSON 响应。"""
    # 尝试提取 JSON 块
    json_match = re.search(r"```json\s*(.*?)\s*```", response, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        # 尝试直接解析整个响应
        json_str = response.strip()

    try:
        data = json.loads(json_str)
        return {
            "decisions": data.get("decisions", []),
            "commitments": data.get("commitments", []),
            "topics": data.get("topics", []),
        }
    except json.JSONDecodeError:
        logger.warning("Failed to parse LLM extraction response as JSON")
        return {"decisions": [], "commitments": [], "topics": []}


def _resolve_user_id(db: Session, name: str | None, meeting_id: int) -> int | None:
    """根据姓名查找用户 ID。"""
    if not name:
        return None
    # 先尝试精确匹配
    user = db.query(User).filter(User.full_name == name).first()
    if user:
        return user.id
    # 尝试模糊匹配
    user = db.query(User).filter(User.full_name.ilike(f"%{name}%")).first()
    return user.id if user else None


async def extract_entities(
    db: Session,
    meeting: Meeting,
    transcripts: list[MeetingTranscript],
    llm_service,
) -> dict[str, list]:
    """从会议转写中提取实体。

    Args:
        db: 数据库会话
        meeting: 会议对象
        transcripts: 转写列表
        llm_service: LLM 服务实例

    Returns:
        包含 decisions, commitments, topics 的字典
    """
    if not transcripts:
        return {"decisions": [], "commitments": [], "topics": []}

    transcript_text = _build_transcript_text(transcripts)
    if not transcript_text.strip():
        return {"decisions": [], "commitments": [], "topics": []}

    prompt = EXTRACTION_PROMPT.format(transcript_text=transcript_text)

    try:
        response = await llm_service.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            stream=False,
        )
        if isinstance(response, str):
            result = _parse_llm_response(response)
        else:
            # 如果返回的是 generator，收集所有 chunk
            chunks = []
            async for chunk in response:
                chunks.append(chunk)
            result = _parse_llm_response("".join(chunks))
    except Exception:
        logger.exception("Entity extraction LLM call failed for meeting %s", meeting.id)
        return {"decisions": [], "commitments": [], "topics": []}

    # 保存提取结果到数据库
    saved_decisions: list[Decision] = []
    saved_commitments: list[Commitment] = []
    saved_topics: list[MeetingTopic] = []

    for item in result.get("decisions", []):
        proposer_id = _resolve_user_id(db, item.get("proposer_name"), meeting.id)
        decision = Decision(
            meeting_id=meeting.id,
            content=item.get("content", ""),
            proposer_name=item.get("proposer_name"),
            proposer_user_id=proposer_id,
            context=item.get("context"),
            confidence=item.get("confidence", 0.7),
            status="candidate",
        )
        db.add(decision)
        saved_decisions.append(decision)

    for item in result.get("commitments", []):
        assignee_id = _resolve_user_id(db, item.get("assignee_name"), meeting.id)
        commitment = Commitment(
            meeting_id=meeting.id,
            content=item.get("content", ""),
            assignee_name=item.get("assignee_name"),
            assignee_user_id=assignee_id,
            due_hint=item.get("due_hint"),
            status="candidate",
        )
        db.add(commitment)
        saved_commitments.append(commitment)

    for item in result.get("topics", []):
        topic = MeetingTopic(
            meeting_id=meeting.id,
            topic=item.get("topic", ""),
            relevance_score=item.get("relevance_score", 1.0),
        )
        db.add(topic)
        saved_topics.append(topic)

    try:
        db.commit()
        # Refresh to get IDs
        for d in saved_decisions:
            db.refresh(d)
        for c in saved_commitments:
            db.refresh(c)
        for t in saved_topics:
            db.refresh(t)
    except Exception:
        db.rollback()
        logger.exception("Failed to save extracted entities for meeting %s", meeting.id)
        return {"decisions": [], "commitments": [], "topics": []}

    logger.info(
        "Extracted entities for meeting %s: %d decisions, %d commitments, %d topics",
        meeting.id, len(saved_decisions), len(saved_commitments), len(saved_topics),
    )

    return {
        "decisions": saved_decisions,
        "commitments": saved_commitments,
        "topics": saved_topics,
    }
