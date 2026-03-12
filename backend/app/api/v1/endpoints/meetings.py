"""会议 REST API。"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.meeting_transcript import MeetingTranscript
from app.schemas.meeting import MeetingCreate, MeetingOut, MeetingPostprocessOut, MeetingUpdate
from app.services.meeting_service import (
    build_meeting_summary,
    create_meeting,
    delete_meeting,
    generate_tasks_from_transcripts,
    get_meeting,
    list_meetings,
    update_meeting,
)

router = APIRouter(prefix="/meetings", tags=["meetings"])


@router.post("", response_model=MeetingOut, status_code=status.HTTP_201_CREATED)
def create_meeting_api(payload: MeetingCreate, db: Session = Depends(get_db)) -> MeetingOut:
    """创建会议。"""

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
def postprocess_meeting_api(meeting_id: int, db: Session = Depends(get_db)) -> MeetingPostprocessOut:
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
    tasks = generate_tasks_from_transcripts(db, meeting_id, transcripts)

    return MeetingPostprocessOut(meeting_id=meeting_id, summary=summary, tasks=tasks)
