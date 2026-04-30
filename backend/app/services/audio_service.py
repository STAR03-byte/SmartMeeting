"""音频上传与转写服务。"""

import random
from pathlib import Path
from collections.abc import Sequence
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.meeting_audio import MeetingAudio
from app.models.meeting_transcript import MeetingTranscript
from app.core.config import settings
from app.services.business.hotword_service import get_hotword_terms
from app.services.business.meeting_participant_service import list_participants
from app.services.meeting_service import get_meeting
from app.services.ai.faster_whisper_service import transcribe_audio_file
from app.services.ai.whisper_service import WhisperServiceError
from app.services.ai.speaker_diarization_service import diarize_audio


def _assign_speaker_labels(
    transcripts: list[MeetingTranscript],
    participants: Sequence[object],
) -> list[MeetingTranscript]:
    labeled: list[MeetingTranscript] = []
    participant_count = len(participants)
    for index, transcript in enumerate(transcripts):
        if participant_count == 0:
            labeled.append(transcript)
            continue

        participant = participants[index % participant_count]
        speaker_user_id = getattr(participant, "id", None)
        speaker_name = getattr(participant, "full_name", None)
        if speaker_user_id is not None:
            transcript.speaker_user_id = speaker_user_id
        if speaker_name:
            transcript.speaker_name = speaker_name
        labeled.append(transcript)
    return labeled


def _fetch_meeting_participants(db: Session, meeting_id: int) -> Sequence[object]:
    return list(list_participants(db, meeting_id))


MOCK_TRANSCRIPT_TEMPLATES = [
    [
        ("ASR 演讲者", "大家好，今天我们来讨论这个季度的产品迭代计划。"),
        ("ASR 演讲者", "首先回顾一下上周的进展，然后讨论下周的优先事项。"),
        ("ASR 演讲者", "前端团队已经完成了登录页面和会议列表的开发。"),
        ("ASR 演讲者", "后端团队完成了音频上传和转写的 API。"),
        ("ASR 演讲者", "接下来需要对接 AI 摘要生成功能。"),
    ],
    [
        ("ASR 演讲者", "会议开始，我们先确认一下上周遗留的问题。"),
        ("ASR 演讲者", "数据库迁移脚本已经测试通过，可以部署到生产环境。"),
        ("ASR 演讲者", "前端页面的响应式适配还需要继续优化。"),
        ("ASR 演讲者", "建议在下周三之前完成所有功能的集成测试。"),
        ("ASR 演讲者", "今天会议的结论是：下周三之前完成集成测试。"),
    ],
    [
        ("ASR 演讲者", "今天的主题是 AI 功能集成方案讨论。"),
        ("ASR 演讲者", "我们需要决定使用哪个 LLM 提供商来生成会议摘要。"),
        ("ASR 演讲者", "建议先支持 OpenAI API，后续再扩展其他提供商。"),
        ("ASR 演讲者", "任务提取功能需要使用结构化输出来确保 JSON 格式正确。"),
        ("ASR 演讲者", "下一步：小王负责完成 LLM 集成，下周交付。"),
    ],
]


def save_meeting_audio(db: Session, meeting_id: int, upload: UploadFile) -> MeetingAudio:
    """保存会议音频并记录元数据。"""

    suffix = Path(upload.filename or "audio.bin").suffix or ".bin"
    safe_name = f"{uuid4().hex}{suffix}"
    storage_dir = Path("backend/storage/audio") / str(meeting_id)
    storage_dir.mkdir(parents=True, exist_ok=True)
    storage_path = storage_dir / safe_name

    content = upload.file.read()
    if len(content) > settings.meeting_audio_max_size_bytes:
        raise ValueError("Uploaded audio file exceeds size limit")
    _ = storage_path.write_bytes(content)

    audio = MeetingAudio(
        meeting_id=meeting_id,
        filename=upload.filename or safe_name,
        storage_path=str(storage_path),
        content_type=upload.content_type or "application/octet-stream",
        size_bytes=len(content),
    )
    db.add(audio)
    db.commit()
    db.refresh(audio)
    return audio


def _generate_mock_transcripts(meeting_id: int, start_index: int) -> list[MeetingTranscript]:

    template = random.choice(MOCK_TRANSCRIPT_TEMPLATES)
    segments: list[MeetingTranscript] = []
    time_cursor = 0.0

    for i, (speaker, text) in enumerate(template):
        duration = round(random.uniform(8.0, 25.0), 2)
        segment = MeetingTranscript(
            meeting_id=meeting_id,
            speaker_user_id=None,
            speaker_name=speaker,
            segment_index=start_index + i,
            start_time_sec=round(time_cursor, 2),
            end_time_sec=round(time_cursor + duration, 2),
            language_code="zh-CN",
            source="manual",
            content=text,
        )
        segments.append(segment)
        time_cursor += duration + round(random.uniform(0.5, 3.0), 2)

    return segments


async def transcribe_latest_audio(db: Session, meeting_id: int, user_id: int | None = None) -> list[MeetingTranscript]:

    meeting = get_meeting(db, meeting_id)
    if not meeting:
        return []

    latest_audio = (
        db.query(MeetingAudio)
        .filter(MeetingAudio.meeting_id == meeting_id)
        .order_by(MeetingAudio.id.desc())
        .first()
    )
    if not latest_audio:
        return []

    latest_segment = (
        db.query(MeetingTranscript)
        .filter(MeetingTranscript.meeting_id == meeting_id)
        .order_by(MeetingTranscript.segment_index.desc())
        .first()
    )
    next_segment_index = 1 if not latest_segment else latest_segment.segment_index + 1

    try:
        hotwords = get_hotword_terms(db, user_id)
        transcription = await transcribe_audio_file(latest_audio.storage_path, hotwords=hotwords)
    except WhisperServiceError:
        if not settings.whisper_allow_mock_fallback:
            raise
        segments = _generate_mock_transcripts(meeting_id, next_segment_index)
        participants = _fetch_meeting_participants(db, meeting_id)
        for segment in segments:
            db.add(segment)
        db.commit()
        for segment in segments:
            db.refresh(segment)
        return _assign_speaker_labels(segments, participants)

    created_segments: list[MeetingTranscript] = []

    for index, segment_data in enumerate(transcription["segments"], start=next_segment_index):
        content = segment_data["text"].strip()
        if not content:
            continue
        transcript = MeetingTranscript(
            meeting_id=meeting_id,
            speaker_user_id=None,
            speaker_name="Whisper",
            segment_index=index,
            start_time_sec=segment_data.get("start"),
            end_time_sec=segment_data.get("end"),
            language_code=(segment_data.get("language") or "zh").replace("zh", "zh-CN", 1),
            source="whisper",
            content=content,
        )
        db.add(transcript)
        created_segments.append(transcript)

    db.commit()
    for transcript in created_segments:
        db.refresh(transcript)

    # Diarization Logic
    diarization_success = False
    if settings.enable_speaker_diarization:
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Speaker diarization enabled, processing audio: {latest_audio.storage_path}")
        diarization_segments = diarize_audio(latest_audio.storage_path)
        logger.info(f"Diarization returned {len(diarization_segments)} segments")
        if diarization_segments:
            diarization_success = True
            for transcript in created_segments:
                start_sec = float(transcript.start_time_sec or 0)
                end_sec = float(transcript.end_time_sec or 0)
                t_mid = start_sec + (end_sec - start_sec) / 2
                best_match = None
                for d_seg in diarization_segments:
                    if d_seg.start <= t_mid <= d_seg.end:
                        best_match = d_seg
                        break

                if best_match is None:
                    # find closest
                    closest = None
                    min_dist = float('inf')
                    for d_seg in diarization_segments:
                        dist = min(abs(t_mid - d_seg.start), abs(t_mid - d_seg.end))
                        if dist < min_dist:
                            min_dist = dist
                            closest = d_seg
                    best_match = closest

                if best_match:
                    transcript.speaker_id = best_match.speaker_id
                    transcript.speaker_name = best_match.speaker
                    logger.debug(f"Assigned speaker {best_match.speaker} to segment {transcript.segment_index}")
            db.commit()
            for transcript in created_segments:
                db.refresh(transcript)
            logger.info(f"Speaker diarization completed for {len(created_segments)} transcripts")

    if not diarization_success:
        participants = _fetch_meeting_participants(db, meeting_id)
        return _assign_speaker_labels(created_segments, participants)

    return created_segments
