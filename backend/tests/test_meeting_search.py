from __future__ import annotations

from app.models.meeting import Meeting
from app.services.meeting_service import match_meeting_keyword


def test_match_meeting_keyword_matches_title_or_description() -> None:
    meeting1 = Meeting(title="项目推进会议", description="讨论接口联调", organizer_id=1)
    meeting2 = Meeting(title="周会", description="讨论预算与排期", organizer_id=1)

    assert match_meeting_keyword(meeting1, "接口") is True
    assert match_meeting_keyword(meeting2, "接口") is False
