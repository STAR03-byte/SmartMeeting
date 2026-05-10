"""实体提取服务单元测试。"""

import pytest

from app.services.ai.entity_extraction_service import (
    _build_transcript_text,
    _parse_llm_response,
    _resolve_user_id,
)
from app.models.meeting_transcript import MeetingTranscript
from app.models.user import User


class TestBuildTranscriptText:
    """_build_transcript_text 测试。"""

    def test_empty_list(self):
        assert _build_transcript_text([]) == ""

    def test_single_transcript(self):
        t = MeetingTranscript(speaker_name="张三", content="我们决定用 PostgreSQL")
        result = _build_transcript_text([t])
        assert "[张三]: 我们决定用 PostgreSQL" == result

    def test_multiple_transcripts(self):
        t1 = MeetingTranscript(speaker_name="张三", content="第一段")
        t2 = MeetingTranscript(speaker_name="李四", content="第二段")
        result = _build_transcript_text([t1, t2])
        assert "[张三]: 第一段\n[李四]: 第二段" == result

    def test_unknown_speaker(self):
        t = MeetingTranscript(speaker_name=None, content="内容")
        result = _build_transcript_text([t])
        assert "[未知]: 内容" == result

    def test_respects_max_length(self):
        t1 = MeetingTranscript(speaker_name="A", content="x" * 5000)
        t2 = MeetingTranscript(speaker_name="B", content="y" * 5000)
        result = _build_transcript_text([t1, t2], max_length=100)
        assert len(result) <= 100 + 50  # speaker prefix overhead

    def test_max_length_cuts_at_boundary(self):
        t1 = MeetingTranscript(speaker_name="A", content="短内容")
        t2 = MeetingTranscript(speaker_name="B", content="很长的内容" * 100)
        result = _build_transcript_text([t1, t2], max_length=50)
        lines = result.split("\n")
        assert len(lines) == 1  # only first fits


class TestParseLLMResponse:
    """_parse_llm_response 测试。"""

    def test_json_block(self):
        response = '```json\n{"decisions": [{"content": "用PG"}], "commitments": [], "topics": []}\n```'
        result = _parse_llm_response(response)
        assert len(result["decisions"]) == 1
        assert result["decisions"][0]["content"] == "用PG"

    def test_raw_json(self):
        response = '{"decisions": [], "commitments": [{"content": "负责前端"}], "topics": []}'
        result = _parse_llm_response(response)
        assert len(result["commitments"]) == 1

    def test_invalid_json_returns_empty(self):
        response = "这不是JSON"
        result = _parse_llm_response(response)
        assert result["decisions"] == []
        assert result["commitments"] == []
        assert result["topics"] == []

    def test_missing_keys_default_to_empty(self):
        response = '{"decisions": [{"content": "test"}]}'
        result = _parse_llm_response(response)
        assert len(result["decisions"]) == 1
        assert result["commitments"] == []
        assert result["topics"] == []

    def test_empty_response(self):
        result = _parse_llm_response("")
        assert result["decisions"] == []


class TestResolveUserId:
    """_resolve_user_id 测试。"""

    @pytest.fixture()
    def db(self):
        """创建内存 SQLite 会话并插入测试用户。"""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.pool import StaticPool
        from app.core.database import Base

        engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()

        user1 = User(username="zhang3", email="zhang@example.com", full_name="张三", password_hash="x", is_active=True)
        user2 = User(username="li4", email="li@example.com", full_name="李四", password_hash="x", is_active=True)
        user3 = User(username="wang5", email="wang@example.com", full_name="王大明", password_hash="x", is_active=True)
        db.add_all([user1, user2, user3])
        db.commit()

        yield db
        db.close()

    def test_none_name_returns_none(self, db):
        assert _resolve_user_id(db, None, 1) is None

    def test_exact_match(self, db):
        result = _resolve_user_id(db, "张三", 1)
        assert result is not None
        user = db.query(User).filter(User.id == result).first()
        assert user.full_name == "张三"

    def test_fuzzy_match(self, db):
        result = _resolve_user_id(db, "大明", 1)
        assert result is not None
        user = db.query(User).filter(User.id == result).first()
        assert user.full_name == "王大明"

    def test_no_match_returns_none(self, db):
        assert _resolve_user_id(db, "不存在的人", 1) is None
