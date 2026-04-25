from app.models.meeting import Meeting
from app.models.meeting_transcript import MeetingTranscript
from app.models.task import Task
from app.models.user import User


def _make_db(auth_client):
    override_get_db = auth_client.app.dependency_overrides[next(iter(auth_client.app.dependency_overrides.keys()))]
    db_gen = override_get_db()
    db = next(db_gen)
    return db, db_gen


def test_knowledge_query_returns_grounded_sources(auth_client) -> None:
    db, db_gen = _make_db(auth_client)
    try:
        user = User(
            username="knowledge_owner",
            email="knowledge_owner@example.com",
            password_hash="hashed",
            full_name="Knowledge Owner",
            role="admin",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        meeting = Meeting(
            title="Project Alpha sync",
            organizer_id=user.id,
            summary="Alpha launch risk is API latency. Decision: finish load testing this week.",
        )
        db.add(meeting)
        db.commit()
        db.refresh(meeting)

        db.add(
            MeetingTranscript(
                meeting_id=meeting.id,
                speaker_user_id=user.id,
                speaker_name="Knowledge Owner",
                segment_index=1,
                content="We confirmed the Alpha API latency mitigation and release checklist.",
            )
        )
        db.add(
            Task(
                meeting_id=meeting.id,
                title="Finish Alpha load testing",
                description="Complete load testing before release.",
                assignee_id=user.id,
                reporter_id=user.id,
                priority="high",
                status="todo",
            )
        )
        db.commit()

        response = auth_client.post(
            "/api/v1/ai/knowledge/query",
            json={"question": "What are the Alpha launch risks?", "limit": 5},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["sources"]
        assert any(item["meeting_id"] == meeting.id for item in data["sources"])
        assert "answer" in data
    finally:
        db.close()
        db_gen.close()


def test_knowledge_query_respects_member_visibility(member_client) -> None:
    db, db_gen = _make_db(member_client)
    try:
        owner = User(
            username="private_owner",
            email="private_owner@example.com",
            password_hash="hashed",
            full_name="Private Owner",
            role="member",
        )
        db.add(owner)
        db.commit()
        db.refresh(owner)

        private_meeting = Meeting(
            title="Private acquisition meeting",
            organizer_id=owner.id,
            summary="Secret acquisition plan should not be visible.",
        )
        db.add(private_meeting)
        db.commit()

        response = member_client.post(
            "/api/v1/ai/knowledge/query",
            json={"question": "acquisition plan", "limit": 5},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["sources"] == []
        assert "Secret acquisition" not in data["answer"]
    finally:
        db.close()
        db_gen.close()
