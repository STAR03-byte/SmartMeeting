from __future__ import annotations

from types import SimpleNamespace

from app.models.meeting_transcript import MeetingTranscript
from app.services.audio_service import _assign_speaker_labels


def test_assign_speaker_labels_cycles_participants() -> None:
    transcripts = [
        MeetingTranscript(
            meeting_id=1,
            speaker_user_id=None,
            speaker_name=None,
            segment_index=1,
            start_time_sec=0.0,
            end_time_sec=1.0,
            language_code="zh-CN",
            source="whisper",
            content="A",
        ),
        MeetingTranscript(
            meeting_id=1,
            speaker_user_id=None,
            speaker_name=None,
            segment_index=2,
            start_time_sec=1.0,
            end_time_sec=2.0,
            language_code="zh-CN",
            source="whisper",
            content="B",
        ),
        MeetingTranscript(
            meeting_id=1,
            speaker_user_id=None,
            speaker_name=None,
            segment_index=3,
            start_time_sec=2.0,
            end_time_sec=3.0,
            language_code="zh-CN",
            source="whisper",
            content="C",
        ),
    ]
    participants = [
        SimpleNamespace(id=101, full_name="张三"),
        SimpleNamespace(id=102, full_name="李四"),
    ]

    labeled = _assign_speaker_labels(transcripts, participants)

    assert [item.speaker_user_id for item in labeled] == [101, 102, 101]
    assert [item.speaker_name for item in labeled] == ["张三", "李四", "张三"]


def test_assign_speaker_labels_handles_empty_participants() -> None:
    transcripts = [
        MeetingTranscript(
            meeting_id=1,
            speaker_user_id=None,
            speaker_name=None,
            segment_index=1,
            start_time_sec=0.0,
            end_time_sec=1.0,
            language_code="zh-CN",
            source="whisper",
            content="A",
        )
    ]

    labeled = _assign_speaker_labels(transcripts, [])

    assert labeled[0].speaker_user_id is None
    assert labeled[0].speaker_name is None
