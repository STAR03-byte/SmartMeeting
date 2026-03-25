from app.models.meeting import Meeting


def test_meeting_model_includes_share_columns() -> None:
    columns = Meeting.__table__.columns.keys()

    assert "share_token" in columns
    assert "shared_at" in columns
