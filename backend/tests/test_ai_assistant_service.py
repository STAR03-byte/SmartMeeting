import asyncio
from datetime import datetime, timedelta

from app.models.meeting import Meeting
from app.models.task import Task
from app.models.user import User
from app.services.ai_assistant_service import AIAssistantService


class DummyLLMService:
    def __init__(self) -> None:
        self.called = False

    async def chat_completion(self, messages, context_info=None, stream=False):
        self.called = True
        if stream:
            async def _generator():
                yield "LLM fallback"

            return _generator()
        return "LLM fallback"


def _make_db(auth_client):
    override_get_db = auth_client.app.dependency_overrides[next(iter(auth_client.app.dependency_overrides.keys()))]
    db_gen = override_get_db()
    db = next(db_gen)
    return db, db_gen


def test_ai_assistant_returns_my_tasks_directly(auth_client) -> None:
    db, db_gen = _make_db(auth_client)
    try:
        user = User(
            username="ai_owner",
            email="ai_owner@example.com",
            password_hash="hashed",
            full_name="AI Owner",
            role="admin",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        meeting = Meeting(title="AI 助手测试会议", organizer_id=user.id)
        db.add(meeting)
        db.commit()
        db.refresh(meeting)

        task = Task(
            meeting_id=meeting.id,
            title="整理测试报告",
            description="今天完成整理",
            assignee_id=user.id,
            reporter_id=user.id,
            priority="high",
            status="todo",
        )
        db.add(task)
        db.commit()

        llm = DummyLLMService()
        service = AIAssistantService(llm)

        async def run():
            chunks = []
            async for chunk in service.chat(db, user.id, "我的任务有什么"):
                chunks.append(chunk)
            return "".join(chunks)

        result = asyncio.run(run())

        assert "整理测试报告" in result
        assert "状态：todo" in result
        assert llm.called is False
    finally:
        db.close()
        db_gen.close()


def test_ai_assistant_can_match_meeting_title_without_manual_context(auth_client) -> None:
    db, db_gen = _make_db(auth_client)
    try:
        user = User(
            username="ai_meeting_owner",
            email="ai_meeting_owner@example.com",
            password_hash="hashed",
            full_name="AI Meeting Owner",
            role="admin",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        meeting = Meeting(title="w测试会议", organizer_id=user.id)
        db.add(meeting)
        db.commit()
        db.refresh(meeting)

        task = Task(
            meeting_id=meeting.id,
            title="提交会议报告",
            description="本周内提交",
            assignee_id=user.id,
            reporter_id=user.id,
            priority="medium",
            status="todo",
        )
        db.add(task)
        db.commit()

        llm = DummyLLMService()
        service = AIAssistantService(llm)

        async def run():
            chunks = []
            async for chunk in service.chat(db, user.id, "w测试会议的任务有哪些"):
                chunks.append(chunk)
            return "".join(chunks)

        result = asyncio.run(run())

        assert "w测试会议" in result
        assert "提交会议报告" in result
        assert llm.called is False
    finally:
        db.close()
        db_gen.close()


def test_ai_assistant_can_answer_due_soon_tasks_directly(auth_client) -> None:
    db, db_gen = _make_db(auth_client)
    try:
        user = User(
            username="ai_due_owner",
            email="ai_due_owner@example.com",
            password_hash="hashed",
            full_name="AI Due Owner",
            role="admin",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        meeting = Meeting(title="截止时间测试会议", organizer_id=user.id)
        db.add(meeting)
        db.commit()
        db.refresh(meeting)

        due_task = Task(
            meeting_id=meeting.id,
            title="完成上线检查",
            description="需要尽快完成",
            assignee_id=user.id,
            reporter_id=user.id,
            priority="high",
            status="todo",
            due_at=datetime.now() + timedelta(days=1),
        )
        db.add(due_task)
        db.commit()

        llm = DummyLLMService()
        service = AIAssistantService(llm)

        async def run():
            chunks = []
            async for chunk in service.chat(db, user.id, "我有哪些快到期的任务"):
                chunks.append(chunk)
            return "".join(chunks)

        result = asyncio.run(run())

        assert "快到期" in result
        assert "完成上线检查" in result
        assert llm.called is False
    finally:
        db.close()
        db_gen.close()


def test_ai_assistant_meeting_context_marks_missing_fields_for_grounding(auth_client) -> None:
    db, db_gen = _make_db(auth_client)
    try:
        user = User(
            username="ai_grounding_owner",
            email="ai_grounding_owner@example.com",
            password_hash="hashed",
            full_name="AI Grounding Owner",
            role="admin",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        meeting = Meeting(title="Grounding 测试会议", organizer_id=user.id)
        db.add(meeting)
        db.commit()
        db.refresh(meeting)

        llm = DummyLLMService()
        service = AIAssistantService(llm)

        async def run() -> dict[str, str]:
            return await service._build_dynamic_context_info(  # noqa: SLF001
                db,
                user.id,
                "这个会议讲了什么",
                {"meeting_id": meeting.id},
            )

        context_info = asyncio.run(run())

        assert context_info["meeting_title"] == "Grounding 测试会议"
        assert context_info["meeting_summary_missing"] == "当前没有记录会议摘要"
        assert context_info["meeting_participants_missing"] == "当前没有记录参会人员"
        assert context_info["meeting_tasks_missing"] == "当前没有记录该会议的任务"
        assert context_info["meeting_transcript_missing"] == "当前没有记录会议转写内容"
    finally:
        db.close()
        db_gen.close()
