"""异步任务端点：状态轮询、SSE 进度流、结果获取。"""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.auth import CurrentUserOut
from .auth import get_current_user
from app.models.processing_job import ProcessingJob
from app.schemas.processing_job import ProcessingJobOut, ProcessingJobResultOut
from app.services.pipeline.job_manager import job_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}", response_model=ProcessingJobOut)
async def get_job_status(
    job_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
) -> ProcessingJobOut:
    """轮询任务状态。"""
    job = db.query(ProcessingJob).filter(ProcessingJob.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return ProcessingJobOut.model_validate(job)


@router.get("/{job_id}/events")
async def job_events(
    job_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
) -> StreamingResponse:
    """SSE 实时进度流。"""
    job = db.query(ProcessingJob).filter(ProcessingJob.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # 如果任务已完成，直接返回最终事件
    if job.status in ("completed", "failed", "interrupted"):
        event = {
            "type": job.status,
            "status": job.status,
            "progress": job.progress,
            "message": job.message,
        }
        if job.error:
            event["error"] = job.error
        if job.result_json:
            event["result"] = job.result_json

        async def single_event() -> AsyncGenerator[str, None]:
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

        return StreamingResponse(single_event(), media_type="text/event-stream")

    # 活跃任务：订阅 SSE 事件流
    async def event_stream() -> AsyncGenerator[str, None]:
        try:
            async for event in job_manager.subscribe(job_id):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception("SSE stream error for job %s", job_id)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/{job_id}/result", response_model=ProcessingJobResultOut)
async def get_job_result(
    job_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
) -> ProcessingJobResultOut:
    """获取完成结果。"""
    job = db.query(ProcessingJob).filter(ProcessingJob.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status not in ("completed", "failed", "interrupted"):
        raise HTTPException(status_code=202, detail="Job still in progress")
    return ProcessingJobResultOut.model_validate(job)


@router.post("/{job_id}/cancel")
async def cancel_job(
    job_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
) -> dict[str, str]:
    """取消任务。"""
    job = db.query(ProcessingJob).filter(ProcessingJob.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status in ("completed", "failed", "interrupted"):
        raise HTTPException(status_code=400, detail="Job already finished")

    cancelled = await job_manager.cancel_job(job_id)
    if not cancelled:
        raise HTTPException(status_code=400, detail="Job not cancellable")
    return {"status": "cancelled"}
