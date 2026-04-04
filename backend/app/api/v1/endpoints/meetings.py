"""会议 REST API。"""

from pathlib import Path as FilePath
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Path, Query, UploadFile, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.auth import CurrentUserOut
from app.schemas.meeting_audio import MeetingAudioOut
from app.models.meeting_audio import MeetingAudio
from app.models.meeting_transcript import MeetingTranscript
from app.schemas.meeting import (
    MeetingCreate,
    MeetingDetailOut,
    MeetingExportOut,
    MeetingExportRequest,
    MeetingListOut,
    MeetingOut,
    MeetingPostprocessOut,
    MeetingUpdate,
)
from app.schemas.meeting_transcript import MeetingTranscriptOut
from app.schemas.task import TaskOut
from app.services.audio_service import save_meeting_audio, transcribe_latest_audio
from app.services.meeting_service import (
    build_meeting_summary_with_llm,
    count_meetings,
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


def _assert_meeting_permission(meeting: MeetingOut, current_user: CurrentUserOut) -> None:
    if current_user.role == "admin":
        return
    if meeting.organizer_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权管理此会议")


def _check_meeting_access(
    meeting_id: int,
    user_id: int,
    db: Session,
) -> str | None:
    """检查用户是否有权访问会议，返回角色或 None。

    权限规则：
    - 团队会议：团队成员可查看
    - 个人会议：参与者可查看

    返回：
    - "organizer": 会议组织者
    - "participant": 会议参与者
    - "team_member": 团队成员（团队会议）
    - None: 无权访问
    """
    from app.models.meeting_participant import MeetingParticipant
    from app.models.team_member import TeamMember

    # 检查会议参与者身份
    participant = (
        db.query(MeetingParticipant)
        .filter(
            MeetingParticipant.meeting_id == meeting_id,
            MeetingParticipant.user_id == user_id,
        )
        .first()
    )

    if participant:
        return participant.role

    # 如果是团队会议，检查团队成员身份
    meeting = get_meeting(db, meeting_id)
    if meeting and meeting.team_id:
        team_member = (
            db.query(TeamMember)
            .filter(
                TeamMember.team_id == meeting.team_id,
                TeamMember.user_id == user_id,
            )
            .first()
        )
        if team_member:
            return "team_member"

    return None


@router.post("", response_model=MeetingOut, status_code=status.HTTP_201_CREATED)
def create_meeting_api(
    payload: MeetingCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
) -> MeetingOut:
    from app.models.meeting_participant import MeetingParticipant
    from app.models.team_member import TeamMember

    organizer = get_user(db, payload.organizer_id)
    if not organizer:
        raise HTTPException(status_code=404, detail="Organizer not found")
    if current_user.role != "admin" and current_user.id != payload.organizer_id:
        raise HTTPException(status_code=403, detail="无权管理此会议")

    # 验证团队成员身份（如果是团队会议）
    if payload.team_id is not None:
        membership = (
            db.query(TeamMember)
            .filter(TeamMember.team_id == payload.team_id, TeamMember.user_id == payload.organizer_id)
            .first()
        )
        if not membership:
            raise HTTPException(status_code=403, detail="无权在此团队创建会议")

    if (
        payload.scheduled_start_at is not None
        and payload.scheduled_end_at is not None
        and payload.scheduled_end_at < payload.scheduled_start_at
    ):
        raise HTTPException(
            status_code=400,
            detail="scheduled_end_at must be after or equal to scheduled_start_at",
        )

    meeting = create_meeting(db, payload)

    # 自动添加组织者到 participants（role=organizer）
    participant = MeetingParticipant(
        meeting_id=meeting.id,
        user_id=payload.organizer_id,
        role="organizer",
        participant_role="required",
        attendance_status="invited",
    )
    db.add(participant)
    db.commit()

    return meeting


@router.get("", response_model=MeetingListOut)
def list_meetings_api(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
    status: Annotated[str | None, Query()] = None,
    organizer_id: Annotated[int | None, Query()] = None,
    keyword: Annotated[str | None, Query()] = None,
    sort_by: Annotated[str | None, Query()] = None,
    limit: Annotated[int | None, Query(ge=1, le=100)] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> MeetingListOut:
    """查询会议列表。"""

    total = count_meetings(
        db,
        status=status,
        organizer_id=organizer_id,
        keyword=keyword,
        current_user_id=current_user.id,
        is_admin=(current_user.role == "admin"),
    )

    meetings = list_meetings(
        db,
        status=status,
        organizer_id=organizer_id,
        keyword=keyword,
        sort_by=sort_by,
        limit=limit,
        offset=offset,
        current_user_id=current_user.id,
        is_admin=(current_user.role == "admin"),
    )
    return MeetingListOut(items=[MeetingOut.model_validate(meeting) for meeting in meetings], total=total)


@router.get("/{meeting_id}", response_model=MeetingDetailOut)
def get_meeting_api(
    meeting_id: Annotated[int, Path(ge=1)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
) -> MeetingDetailOut:
    """查询会议详情。"""

    meeting = get_meeting(db, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if current_user.role != "admin":
        access_role = _check_meeting_access(meeting_id, current_user.id, db)
        if not access_role:
            raise HTTPException(status_code=403, detail="无权查看此会议")

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
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
) -> MeetingOut:
    """更新会议。"""

    meeting = get_meeting(db, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    _assert_meeting_permission(meeting, current_user)

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
def delete_meeting_api(
    meeting_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
) -> None:
    """删除会议。"""

    meeting = get_meeting(db, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    _assert_meeting_permission(meeting, current_user)
    delete_meeting(db, meeting)


@router.post("/{meeting_id}/postprocess", response_model=MeetingPostprocessOut)
async def postprocess_meeting_api(
    meeting_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
    force_regenerate: Annotated[bool, Query()] = False,
) -> MeetingPostprocessOut:
    """对会议转写进行后处理并生成摘要与任务。"""

    meeting = get_meeting(db, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    _assert_meeting_permission(meeting, current_user)

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
    _ = save_postprocess_result(db, meeting, summary, version=version)

    return MeetingPostprocessOut(
        meeting_id=meeting_id,
        summary=summary,
        tasks=[TaskOut.model_validate(task) for task in tasks],
    )


@router.post("/{meeting_id}/audio", response_model=MeetingAudioOut, status_code=status.HTTP_201_CREATED)
def upload_meeting_audio_api(
    meeting_id: int,
    file: Annotated[UploadFile, File()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
) -> MeetingAudioOut:
    """上传会议音频文件。"""

    meeting = get_meeting(db, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    _assert_meeting_permission(meeting, current_user)

    try:
        return save_meeting_audio(db, meeting_id, file)
    except ValueError as exc:
        raise HTTPException(
            status_code=413,
            detail={
                "detail": str(exc),
                "error_code": "PAYLOAD_TOO_LARGE",
            },
        ) from exc


@router.post(
    "/{meeting_id}/audio/transcribe",
    response_model=MeetingTranscriptOut,
    status_code=status.HTTP_201_CREATED,
)
async def transcribe_meeting_audio_api(
    meeting_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
) -> MeetingTranscriptOut:
    """对最新上传音频执行 Whisper 语音识别。"""

    meeting = get_meeting(db, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    _assert_meeting_permission(meeting, current_user)

    transcripts = await transcribe_latest_audio(db, meeting_id, current_user.id)
    if not transcripts:
        raise HTTPException(status_code=400, detail="No audio found for meeting")
    return MeetingTranscriptOut.model_validate(transcripts[0])


@router.post("/{meeting_id}/export", response_model=MeetingExportOut)
def export_meeting_api(
    meeting_id: int,
    payload: MeetingExportRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
) -> MeetingExportOut:
    """导出会议纪要。"""

    meeting = get_meeting(db, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    _assert_meeting_permission(meeting, current_user)
    if not meeting.summary:
        raise HTTPException(status_code=400, detail="No summary available for export")

    title = meeting.title or "未命名会议"
    filename = f"{title}.{payload.format}"
    content = (
        f"title={title}\n"
        f"summary=\n{meeting.summary}\n"
        f"format={payload.format}"
    )
    return MeetingExportOut(
        meeting_id=meeting_id,
        format=payload.format,
        filename=filename,
        content=content,
    )


@router.get("/{meeting_id}/audios", response_model=list[MeetingAudioOut])
def list_meeting_audios_api(
    meeting_id: Annotated[int, Path(ge=1)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
) -> list[MeetingAudioOut]:
    """获取会议音频列表。"""

    meeting = get_meeting(db, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    # 权限检查：会议参与者才能访问
    if current_user.role != "admin":
        access_role = _check_meeting_access(meeting_id, current_user.id, db)
        if not access_role:
            raise HTTPException(status_code=403, detail="无权访问此会议")

    audios = (
        db.query(MeetingAudio)
        .filter(MeetingAudio.meeting_id == meeting_id)
        .order_by(MeetingAudio.uploaded_at.desc())
        .all()
    )
    return [MeetingAudioOut.model_validate(audio) for audio in audios]


@router.get("/{meeting_id}/audios/{audio_id}/download")
def download_audio_api(
    meeting_id: Annotated[int, Path(ge=1)],
    audio_id: Annotated[int, Path(ge=1)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
) -> FileResponse:
    """下载会议音频文件。"""

    meeting = get_meeting(db, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    # 权限检查：会议参与者才能下载
    if current_user.role != "admin":
        access_role = _check_meeting_access(meeting_id, current_user.id, db)
        if not access_role:
            raise HTTPException(status_code=403, detail="无权下载此音频")

    audio = (
        db.query(MeetingAudio)
        .filter(MeetingAudio.id == audio_id, MeetingAudio.meeting_id == meeting_id)
        .first()
    )
    if not audio:
        raise HTTPException(status_code=404, detail="Audio not found")

    file_path = FilePath(audio.storage_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")

    return FileResponse(
        path=str(file_path),
        media_type=audio.content_type,
        filename=audio.filename,
    )


@router.get("/{meeting_id}/audios/{audio_id}/stream")
def stream_audio_api(
    meeting_id: Annotated[int, Path(ge=1)],
    audio_id: Annotated[int, Path(ge=1)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
) -> StreamingResponse:
    """在线播放会议音频（流式响应）。"""

    meeting = get_meeting(db, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    # 权限检查：会议参与者才能播放
    if current_user.role != "admin":
        access_role = _check_meeting_access(meeting_id, current_user.id, db)
        if not access_role:
            raise HTTPException(status_code=403, detail="无权播放此音频")

    audio = (
        db.query(MeetingAudio)
        .filter(MeetingAudio.id == audio_id, MeetingAudio.meeting_id == meeting_id)
        .first()
    )
    if not audio:
        raise HTTPException(status_code=404, detail="Audio not found")

    file_path = FilePath(audio.storage_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")

    def iterfile():
        with open(file_path, "rb") as f:
            yield from f

    return StreamingResponse(
        iterfile(),
        media_type=audio.content_type,
        headers={
            "Accept-Ranges": "bytes",
            "Content-Disposition": f'inline; filename="{audio.filename}"',
        },
    )
