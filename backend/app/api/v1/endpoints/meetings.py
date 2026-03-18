"""会议 REST API。"""

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.meeting_audio import MeetingAudioOut
from app.models.meeting_transcript import MeetingTranscript
from app.schemas.meeting import (
    MeetingCreate,
    MeetingDetailOut,
    MeetingOut,
    MeetingPostprocessOut,
    MeetingUpdate,
)
from app.schemas.meeting_transcript import MeetingTranscriptOut
from app.schemas.task import TaskOut
from app.services.audio_service import save_meeting_audio, transcribe_latest_audio
from app.services.meeting_service import (
    build_meeting_summary_with_llm,
    create_meeting,
    delete_meeting,
    generate_tasks_from_transcripts_with_llm,
    get_meeting,
    list_meetings,
    save_postprocess_result,
    update_meeting,
)
from app.services.user_service import get_user
from .auth import get_current_user

router = APIRouter(prefix="/meetings", tags=["meetings"], dependencies=[Depends(get_current_user)])


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
def list_meetings_api(
    status: str | None = Query(default=None),
    organizer_id: int | None = Query(default=None),
    limit: int | None = Query(default=None, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[MeetingOut]:
    """查询会议列表。"""

    meetings = list_meetings(
        db,
        status=status,
        organizer_id=organizer_id,
        limit=limit,
        offset=offset,
    )
    return [MeetingOut.model_validate(meeting) for meeting in meetings]


@router.get("/{meeting_id}", response_model=MeetingDetailOut)
def get_meeting_api(meeting_id: int, db: Session = Depends(get_db)) -> MeetingDetailOut:
    """查询会议详情。"""

    meeting = get_meeting(db, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    organizer = get_user(db, meeting.organizer_id)
    if not organizer:
        raise HTTPException(status_code=404, detail="Organizer not found")

    return MeetingDetailOut.model_validate(
        {
            **meeting.__dict__,
            "organizer": organizer,
        }
    )


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

    scheduled_start_at = payload.scheduled_start_at
    scheduled_end_at = payload.scheduled_end_at
    if scheduled_start_at is None:
        scheduled_start_at = meeting.scheduled_start_at
    if scheduled_end_at is None:
        scheduled_end_at = meeting.scheduled_end_at
    if (
        scheduled_start_at is not None
        and scheduled_end_at is not None
        and scheduled_end_at < scheduled_start_at
    ):
        raise HTTPException(
            status_code=400,
            detail="scheduled_end_at must be after or equal to scheduled_start_at",
        )

    actual_start_at = payload.actual_start_at
    actual_end_at = payload.actual_end_at
    if actual_start_at is None:
        actual_start_at = meeting.actual_start_at
    if actual_end_at is None:
        actual_end_at = meeting.actual_end_at
    if (
        actual_start_at is not None
        and actual_end_at is not None
        and actual_end_at < actual_start_at
    ):
        raise HTTPException(
            status_code=400,
            detail="actual_end_at must be after or equal to actual_start_at",
        )

    return update_meeting(db, meeting, payload)


@router.delete("/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meeting_api(meeting_id: int, db: Session = Depends(get_db)) -> None:
    """删除会议。"""

    meeting = get_meeting(db, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    delete_meeting(db, meeting)


@router.post("/{meeting_id}/postprocess", response_model=MeetingPostprocessOut)
async def postprocess_meeting_api(
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

    summary, summary_version = await build_meeting_summary_with_llm(meeting, transcripts)
    tasks, task_version = await generate_tasks_from_transcripts_with_llm(
        db,
        meeting_id,
        transcripts,
        force_regenerate=force_regenerate,
    )
    version = summary_version if "llm" in summary_version else task_version
    save_postprocess_result(db, meeting, summary, version=version)

    return MeetingPostprocessOut(
        meeting_id=meeting_id,
        summary=summary,
        tasks=[TaskOut.model_validate(task) for task in tasks],
    )


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
async def transcribe_meeting_audio_api(
    meeting_id: int,
    db: Session = Depends(get_db),
) -> MeetingTranscriptOut:
    """对最新上传音频执行 Whisper 语音识别。"""

    meeting = get_meeting(db, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    transcripts = await transcribe_latest_audio(db, meeting_id)
    if not transcripts:
        raise HTTPException(status_code=400, detail="No audio found for meeting")
    return MeetingTranscriptOut.model_validate(transcripts[0])
