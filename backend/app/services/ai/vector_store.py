"""向量存储服务。

基于 pgvector 的统一向量检索：语义搜索 + 全文搜索混合查询。
"""

import logging
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.embedding import Embedding

logger = logging.getLogger(__name__)


def upsert_embedding(
    db: Session,
    meeting_id: int,
    source_type: str,
    content: str,
    embedding: list[float],
    source_id: int | None = None,
    metadata: dict | None = None,
) -> Embedding | None:
    """插入一条 embedding 记录。

    Returns:
        创建的 Embedding 对象，或 None（向量为空时）
    """
    if not embedding:
        return None

    record = Embedding(
        meeting_id=meeting_id,
        source_type=source_type,
        source_id=source_id,
        content=content,
        metadata_=metadata or {},
    )
    db.add(record)
    db.flush()

    # 使用原生 SQL 写入 pgvector 列（ORM 不映射 vector 类型）
    vec_str = f"[{','.join(str(v) for v in embedding)}]"
    db.execute(
        text("UPDATE embeddings SET embedding = :vec::vector WHERE id = :id"),
        {"vec": vec_str, "id": record.id},
    )
    db.flush()
    return record


def delete_embeddings(
    db: Session,
    meeting_id: int,
    source_type: str,
    source_id: int | None = None,
) -> int:
    """删除指定来源的 embedding 记录。"""
    query = db.query(Embedding).filter(
        Embedding.meeting_id == meeting_id,
        Embedding.source_type == source_type,
    )
    if source_id is not None:
        query = query.filter(Embedding.source_id == source_id)
    count = query.count()
    query.delete(synchronize_session="fetch")
    return count


def search(
    db: Session,
    user_id: int,
    query_embedding: list[float],
    query_text: str = "",
    source_types: list[str] | None = None,
    limit: int = 20,
) -> list[dict]:
    """混合搜索：pgvector 语义 + tsvector 全文。

    Args:
        db: 数据库会话
        user_id: 当前用户 ID（用于权限过滤）
        query_embedding: 查询向量
        query_text: 查询文本（用于全文搜索）
        source_types: 过滤来源类型
        limit: 返回数量

    Returns:
        结果列表，每项包含 content, source_type, metadata, meeting_id, score
    """
    if not query_embedding:
        return []

    vec_str = f"[{','.join(str(v) for v in query_embedding)}]"

    # 构建权限子查询：用户是 organizer 或 participant 的会议
    access_subquery = """
        SELECT m.id FROM meetings m
        WHERE m.organizer_id = :user_id
        UNION
        SELECT mp.meeting_id FROM meeting_participants mp WHERE mp.user_id = :user_id
    """

    # 构建来源过滤
    source_filter = ""
    params: dict = {"user_id": user_id, "vec": vec_str, "limit": limit}
    if source_types:
        placeholders = ", ".join(f":st_{i}" for i in range(len(source_types)))
        source_filter = f"AND combined.source_type IN ({placeholders})"
        for i, st in enumerate(source_types):
            params[f"st_{i}"] = st

    # 全文搜索参数
    text_score_expr = "0"
    if query_text.strip():
        text_score_expr = "COALESCE(ts_rank(combined.search_vector, plainto_tsquery('simple', :query_text)), 0)"
        params["query_text"] = query_text

    sql = f"""
        SELECT
            combined.content,
            combined.source_type,
            combined.source_id,
            combined.metadata,
            combined.meeting_id,
            1 - (combined.embedding <=> :vec::vector) AS vector_score,
            {text_score_expr} AS text_score,
            (0.6 * (1 - (combined.embedding <=> :vec::vector)) + 0.4 * {text_score_expr}) AS score
        FROM (
            SELECT content, 'transcript' AS source_type, id AS source_id, metadata, meeting_id, embedding, search_vector
            FROM embeddings WHERE source_type = 'transcript'
            UNION ALL
            SELECT content, 'summary', id, metadata, meeting_id, embedding, search_vector
            FROM embeddings WHERE source_type = 'summary'
            UNION ALL
            SELECT content, 'title', id, metadata, meeting_id, embedding, search_vector
            FROM embeddings WHERE source_type = 'title'
            UNION ALL
            SELECT content, 'decision', id, '{{}}'::jsonb, meeting_id, embedding, search_vector
            FROM decisions WHERE status = 'confirmed' AND embedding IS NOT NULL
            UNION ALL
            SELECT content, 'commitment', id, '{{}}'::jsonb, meeting_id, embedding, search_vector
            FROM commitments WHERE status IN ('confirmed', 'in_progress', 'done') AND embedding IS NOT NULL
        ) combined
        WHERE combined.meeting_id IN ({access_subquery})
        {source_filter}
        ORDER BY score DESC
        LIMIT :limit
    """

    try:
        result = db.execute(text(sql), params)
        rows = result.fetchall()
        return [
            {
                "content": row[0],
                "source_type": row[1],
                "source_id": row[2],
                "metadata": row[3],
                "meeting_id": row[4],
                "vector_score": float(row[5]) if row[5] else 0,
                "text_score": float(row[6]) if row[6] else 0,
                "score": float(row[7]) if row[7] else 0,
            }
            for row in rows
        ]
    except Exception:
        logger.exception("Vector search failed")
        return []
