from __future__ import annotations

from types import SimpleNamespace

from app.models.meeting_transcript import MeetingTranscript
from app.services.pipeline.audio_service import _assign_speaker_labels


def test_assign_speaker_labels_uses_participant_order() -> None:
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
            content="第一句",
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
            content="第二句",
        ),
    ]

    participants = [
        SimpleNamespace(id=11, full_name="张三"),
        SimpleNamespace(id=12, full_name="李四"),
    ]

    labeled = _assign_speaker_labels(transcripts, participants)

    assert labeled[0].speaker_user_id == 11
    assert labeled[0].speaker_name == "张三"
    assert labeled[1].speaker_user_id == 12
    assert labeled[1].speaker_name == "李四"


def test_assign_speaker_labels_leaves_transcripts_untouched_without_participants() -> None:
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
            content="第一句",
        )
    ]

    labeled = _assign_speaker_labels(transcripts, [])

    assert labeled[0].speaker_user_id is None
    assert labeled[0].speaker_name is None
