"""会议转写 REST API。"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.auth import CurrentUserOut
from app.schemas.meeting_transcript import (
    MeetingTranscriptCreate,
    MeetingTranscriptOut,
    MeetingTranscriptUpdate,
)
from app.services.business.meeting_service import get_meeting
from app.services.business.meeting_transcript_service import (
    create_transcript,
    delete_transcript,
    get_transcript,
    list_transcripts,
    update_transcript,
)
from .auth import get_current_user

router = APIRouter(prefix="/transcripts", tags=["transcripts"], dependencies=[Depends(get_current_user)])


def _assert_transcript_permission(meeting, current_user: CurrentUserOut) -> None:
    if current_user.role == "admin":
        return
    if meeting.organizer_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权管理此会议的转写内容")


@router.post("", response_model=MeetingTranscriptOut, status_code=status.HTTP_201_CREATED)
def create_transcript_api(
    payload: MeetingTranscriptCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUserOut = Depends(get_current_user),
) -> MeetingTranscriptOut:
    """创建会议转写。"""

    meeting = get_meeting(db, payload.meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    _assert_transcript_permission(meeting, current_user)

    return create_transcript(db, payload)


@router.get("", response_model=list[MeetingTranscriptOut])
def list_transcripts_api(
    meeting_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: CurrentUserOut = Depends(get_current_user),
) -> list[MeetingTranscriptOut]:
    """查询转写列表。"""

    if meeting_id is not None:
        meeting = get_meeting(db, meeting_id)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        _assert_transcript_permission(meeting, current_user)

    transcripts = list_transcripts(db, meeting_id=meeting_id)
    return [MeetingTranscriptOut.model_validate(transcript) for transcript in transcripts]


@router.get("/{transcript_id}", response_model=MeetingTranscriptOut)
def get_transcript_api(
    transcript_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUserOut = Depends(get_current_user),
) -> MeetingTranscriptOut:
    """查询转写详情。"""

    transcript = get_transcript(db, transcript_id)
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")
    meeting = get_meeting(db, transcript.meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    _assert_transcript_permission(meeting, current_user)
    return transcript


@router.patch("/{transcript_id}", response_model=MeetingTranscriptOut)
def update_transcript_api(
    transcript_id: int,
    payload: MeetingTranscriptUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUserOut = Depends(get_current_user),
) -> MeetingTranscriptOut:
    """更新转写。"""

    transcript = get_transcript(db, transcript_id)
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")
    meeting = get_meeting(db, transcript.meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    _assert_transcript_permission(meeting, current_user)
    return update_transcript(db, transcript, payload)


@router.delete("/{transcript_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transcript_api(
    transcript_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUserOut = Depends(get_current_user),
) -> None:
    """删除转写。"""

    transcript = get_transcript(db, transcript_id)
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")
    meeting = get_meeting(db, transcript.meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    _assert_transcript_permission(meeting, current_user)
    delete_transcript(db, transcript)
