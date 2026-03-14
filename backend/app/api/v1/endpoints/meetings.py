"""会议 REST API。"""

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.meeting_audio import MeetingAudioOut
from app.models.meeting_transcript import MeetingTranscript
from app.schemas.meeting import MeetingCreate, MeetingOut, MeetingPostprocessOut, MeetingUpdate
from app.schemas.meeting_transcript import MeetingTranscriptOut
from app.services.audio_service import save_meeting_audio, transcribe_latest_audio
from app.services.meeting_service import (
    build_meeting_summary,
    create_meeting,
    delete_meeting,
    generate_tasks_from_transcripts,
    get_meeting,
    list_meetings,
    save_postprocess_result,
    update_meeting,
)
from app.services.user_service import get_user

router = APIRouter(prefix="/meetings", tags=["meetings"])


@router.post("", response_model=MeetingOut, status_code=status.HTTP_201_CREATED)
def create_meeting_api(payload: MeetingCreate, db: Session = Depends(get_db)) -> MeetingOut:
    organizer = get_user(db, payload.organizer_id)
    if not organizer:
        raise HTTPException(status_code=404, detail="Organizer not found")

    if (
        payload.scheduled_start_at is not None
        and payload.scheduled_end_at is not None
        and payload.scheduled_end_at < payload.scheduled_start_at
    ):
        raise HTTPException(
            status_code=400,
            detail="scheduled_end_at must be after or equal to scheduled_start_at",
        )

    return create_meeting(db, payload)


@router.get("", response_model=list[MeetingOut])
def list_meetings_api(db: Session = Depends(get_db)) -> list[MeetingOut]:
    """查询会议列表。"""

    return list_meetings(db)


@router.get("/{meeting_id}", response_model=MeetingOut)
def get_meeting_api(meeting_id: int, db: Session = Depends(get_db)) -> MeetingOut:
    """查询会议详情。"""

    meeting = get_meeting(db, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting


@router.patch("/{meeting_id}", response_model=MeetingOut)
def update_meeting_api(
    meeting_id: int,
    payload: MeetingUpdate,
    db: Session = Depends(get_db),
) -> MeetingOut:
    """更新会议。"""

    meeting = get_meeting(db, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return update_meeting(db, meeting, payload)


@router.delete("/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meeting_api(meeting_id: int, db: Session = Depends(get_db)) -> None:
    """删除会议。"""

    meeting = get_meeting(db, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    delete_meeting(db, meeting)


@router.post("/{meeting_id}/postprocess", response_model=MeetingPostprocessOut)
def postprocess_meeting_api(
    meeting_id: int,
    force_regenerate: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> MeetingPostprocessOut:
    """对会议转写进行后处理并生成摘要与任务。"""

    meeting = get_meeting(db, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    transcripts = (
        db.query(MeetingTranscript)
        .filter(MeetingTranscript.meeting_id == meeting_id)
        .order_by(MeetingTranscript.segment_index.asc(), MeetingTranscript.id.asc())
        .all()
    )
    if not transcripts:
        raise HTTPException(status_code=400, detail="No transcripts found for meeting")

    summary = build_meeting_summary(transcripts)
    tasks = generate_tasks_from_transcripts(
        db,
        meeting_id,
        transcripts,
        force_regenerate=force_regenerate,
    )
    save_postprocess_result(db, meeting, summary, version="rule-v1")

    return MeetingPostprocessOut(meeting_id=meeting_id, summary=summary, tasks=tasks)


@router.post("/{meeting_id}/audio", response_model=MeetingAudioOut, status_code=status.HTTP_201_CREATED)
def upload_meeting_audio_api(
    meeting_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> MeetingAudioOut:
    """上传会议音频文件。"""

    meeting = get_meeting(db, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    return save_meeting_audio(db, meeting_id, file)


@router.post(
    "/{meeting_id}/audio/transcribe",
    response_model=MeetingTranscriptOut,
    status_code=status.HTTP_201_CREATED,
)
def transcribe_meeting_audio_api(meeting_id: int, db: Session = Depends(get_db)) -> MeetingTranscriptOut:
    """对最新上传音频执行占位语音识别。"""

    meeting = get_meeting(db, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    transcript = transcribe_latest_audio(db, meeting_id)
    if not transcript:
        raise HTTPException(status_code=400, detail="No audio found for meeting")
    return transcript
