"""跨会议语义搜索 API 端点。"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import get_current_user
from app.core.database import get_db

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
def search_meetings(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
    q: str = Query(default="", description="搜索关键词"),
    team_id: int | None = Query(default=None, description="限定团队"),
    source_type: str | None = Query(default=None, description="来源类型：transcript|summary|title|decision|commitment"),
    limit: int = Query(default=20, ge=1, le=100),
) -> dict:
    """跨会议语义搜索。

    混合查询：pgvector 语义搜索 + tsvector 全文搜索。
    结果按相关度排序，只返回用户有权限访问的会议内容。
    """
    from app.services.ai.embedding_service import is_available, encode_single
    from app.services.ai.vector_store import search as vector_search

    if not q.strip():
        return {"items": [], "total": 0}

    # 生成查询向量
    query_embedding = encode_single(q) if is_available() else []

    # 构建来源过滤
    source_types = [source_type] if source_type else None

    results = vector_search(
        db=db,
        user_id=current_user["id"],
        query_embedding=query_embedding,
        query_text=q,
        source_types=source_types,
        limit=limit,
    )

    # 补充会议标题
    from app.models.meeting import Meeting
    meeting_ids = list({r["meeting_id"] for r in results})
    meetings = {}
    if meeting_ids:
        for m in db.query(Meeting).filter(Meeting.id.in_(meeting_ids)).all():
            meetings[m.id] = m.title

    items = []
    for r in results:
        items.append({
            **r,
            "meeting_title": meetings.get(r["meeting_id"], ""),
        })

    return {"items": items, "total": len(items)}
