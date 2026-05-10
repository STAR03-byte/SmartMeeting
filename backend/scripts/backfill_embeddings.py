"""历史会议 Embedding 回填脚本。

遍历已完成的会议，为缺少向量数据的会议生成 Embedding 并存入 pgvector。

用法：
    python backend/scripts/backfill_embeddings.py --all            # 回填所有
    python backend/scripts/backfill_embeddings.py --meeting-id 42  # 回填单个
    python backend/scripts/backfill_embeddings.py --all --dry-run  # 预览模式
"""

import argparse
import sys
import time
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text as sql_text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.core.database import Base
from app.models.meeting import Meeting
from app.models.meeting_transcript import MeetingTranscript


def get_session() -> Session:
    url = settings.sqlite_database_uri if settings.db_backend == "sqlite" else settings.sqlalchemy_database_uri
    engine = create_engine(url, echo=False)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)()


def meeting_has_embeddings(db: Session, meeting_id: int) -> bool:
    row = db.execute(
        sql_text("SELECT COUNT(*) FROM embeddings WHERE meeting_id = :mid"),
        {"mid": meeting_id},
    ).scalar()
    return row > 0


def backfill_meeting(db: Session, meeting: Meeting, *, dry_run: bool = False) -> dict[str, int]:
    from app.services.ai.embedding_service import is_available, encode_texts, encode_single
    from app.services.ai.vector_store import upsert_embedding

    stats = {"title": 0, "summary": 0, "transcripts": 0, "decisions": 0, "commitments": 0}

    if not is_available():
        print("  [!] Embedding 服务不可用，跳过")
        return stats

    # 标题
    if not dry_run:
        emb = encode_single(meeting.title)
        if emb:
            upsert_embedding(db, meeting.id, "title", meeting.title, emb)
    stats["title"] = 1

    # 摘要
    if meeting.summary:
        if not dry_run:
            emb = encode_single(meeting.summary)
            if emb:
                upsert_embedding(db, meeting.id, "summary", meeting.summary, emb)
        stats["summary"] = 1

    # 转写段落
    transcripts = (
        db.query(MeetingTranscript)
        .filter(MeetingTranscript.meeting_id == meeting.id)
        .order_by(MeetingTranscript.segment_index.asc())
        .all()
    )
    if transcripts:
        if not dry_run:
            batch_texts = [f"[{t.speaker_name or '未知'}]: {t.content}" for t in transcripts]
            batch_embs = encode_texts(batch_texts)
            for t, emb in zip(transcripts, batch_embs):
                if emb:
                    upsert_embedding(
                        db, meeting.id, "transcript", t.content, emb,
                        source_id=t.id,
                        metadata={"speaker": t.speaker_name, "segment_index": t.segment_index},
                    )
        stats["transcripts"] = len(transcripts)

    # 决策
    decisions = db.execute(
        sql_text("SELECT id, content FROM decisions WHERE meeting_id = :mid AND embedding IS NULL"),
        {"mid": meeting.id},
    ).fetchall()
    if decisions and not dry_run:
        for d in decisions:
            emb = encode_single(d.content)
            if emb:
                vec_str = f"[{','.join(str(v) for v in emb)}]"
                db.execute(
                    sql_text("UPDATE decisions SET embedding = :vec::vector WHERE id = :id"),
                    {"vec": vec_str, "id": d.id},
                )
    stats["decisions"] = len(decisions)

    # 承诺
    commitments = db.execute(
        sql_text("SELECT id, content FROM commitments WHERE meeting_id = :mid AND embedding IS NULL"),
        {"mid": meeting.id},
    ).fetchall()
    if commitments and not dry_run:
        for c in commitments:
            emb = encode_single(c.content)
            if emb:
                vec_str = f"[{','.join(str(v) for v in emb)}]"
                db.execute(
                    sql_text("UPDATE commitments SET embedding = :vec::vector WHERE id = :id"),
                    {"vec": vec_str, "id": c.id},
                )
    stats["commitments"] = len(commitments)

    if not dry_run:
        db.commit()

    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="历史会议 Embedding 回填")
    parser.add_argument("--all", action="store_true", help="回填所有已完成会议")
    parser.add_argument("--meeting-id", type=int, help="回填指定会议 ID")
    parser.add_argument("--dry-run", action="store_true", help="预览模式，不实际写入")
    args = parser.parse_args()

    if not args.all and args.meeting_id is None:
        parser.error("需要指定 --all 或 --meeting-id")

    db = get_session()
    try:
        if args.meeting_id:
            meetings = [db.query(Meeting).filter(Meeting.id == args.meeting_id).first()]
            if not meetings[0]:
                print(f"[ERR] 会议 #{args.meeting_id} 不存在")
                sys.exit(1)
        else:
            meetings = db.query(Meeting).filter(Meeting.status == "done").order_by(Meeting.id).all()

        if not meetings:
            print("[!] 没有找到需要回填的会议")
            return

        total = len(meetings)
        skipped = 0
        processed = 0
        start = time.time()

        prefix = "[DRY-RUN] " if args.dry_run else ""
        print(f"{prefix}找到 {total} 个已完成会议，开始回填...\n")

        for i, meeting in enumerate(meetings, 1):
            if meeting_has_embeddings(db, meeting.id):
                skipped += 1
                print(f"  [{i}/{total}] #{meeting.id} \"{meeting.title}\" — 已有 Embedding，跳过")
                continue

            print(f"  [{i}/{total}] #{meeting.id} \"{meeting.title}\" — 生成中...", end="", flush=True)
            stats = backfill_meeting(db, meeting, dry_run=args.dry_run)
            processed += 1
            parts = [f"标题:{stats['title']}"]
            if stats["summary"]:
                parts.append(f"摘要:{stats['summary']}")
            if stats["transcripts"]:
                parts.append(f"转写:{stats['transcripts']}")
            if stats["decisions"]:
                parts.append(f"决策:{stats['decisions']}")
            if stats["commitments"]:
                parts.append(f"承诺:{stats['commitments']}")
            print(f" 完成 ({', '.join(parts)})")

        elapsed = time.time() - start
        print(f"\n{'=' * 50}")
        print(f"{prefix}回填完成：处理 {processed} 个，跳过 {skipped} 个，耗时 {elapsed:.1f}s")

    finally:
        db.close()


if __name__ == "__main__":
    main()
