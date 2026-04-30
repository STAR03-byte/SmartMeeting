"""异步任务管理器。

管理 processing_jobs 的生命周期：创建、执行、进度追踪、SSE 通知、关闭恢复。
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.processing_job import ProcessingJob

logger = logging.getLogger(__name__)


class JobManager:
    """异步任务编排器。"""

    def __init__(self) -> None:
        self._active_tasks: dict[str, asyncio.Task[None]] = {}
        self._subscribers: dict[str, list[asyncio.Queue[dict[str, Any]]]] = {}

    # ── 任务创建 ──────────────────────────────────────────────

    def create_job(
        self,
        meeting_id: int,
        user_id: int,
        job_type: str,
    ) -> ProcessingJob:
        """创建任务记录并返回。由调用方负责 commit。"""
        from app.services.pipeline.gpu_manager import gpu_manager

        job = ProcessingJob(
            job_id=gpu_manager.generate_job_id(),
            meeting_id=meeting_id,
            user_id=user_id,
            job_type=job_type,
            status="pending",
            progress=0.0,
            message="任务已创建",
        )
        return job

    # ── SSE 订阅 ──────────────────────────────────────────────

    async def subscribe(self, job_id: str) -> AsyncGenerator[dict[str, Any], None]:
        """SSE 事件流生成器。客户端断开时自动清理。"""
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=100)
        self._subscribers.setdefault(job_id, []).append(queue)
        try:
            while True:
                event = await queue.get()
                yield event
                if event.get("type") in ("completed", "error", "cancelled"):
                    break
        finally:
            subscribers = self._subscribers.get(job_id, [])
            if queue in subscribers:
                subscribers.remove(queue)
            if not subscribers:
                self._subscribers.pop(job_id, None)

    def _notify_subscribers(self, job_id: str, event: dict[str, Any]) -> None:
        """向所有订阅者推送事件。队列满时丢弃最旧消息。"""
        for queue in self._subscribers.get(job_id, []):
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                try:
                    queue.get_nowait()
                    queue.put_nowait(event)
                except (asyncio.QueueEmpty, asyncio.QueueFull):
                    pass

    # ── 进度更新 ──────────────────────────────────────────────

    def _update_job_progress(
        self,
        job_id: str,
        status: str,
        progress: float,
        message: str,
        *,
        current_chunk: int = 0,
        total_chunks: int = 1,
        error: str | None = None,
        result_json: str | None = None,
    ) -> None:
        """更新 DB 中的任务状态并通知 SSE 订阅者。"""
        db = SessionLocal()
        try:
            job = db.query(ProcessingJob).filter(ProcessingJob.job_id == job_id).first()
            if not job:
                return
            job.status = status
            job.progress = progress
            job.message = message
            job.current_chunk = current_chunk
            job.total_chunks = total_chunks
            if job.started_at is None and status not in ("pending",):
                job.started_at = datetime.now(timezone.utc)
            if error is not None:
                job.error = error
            if result_json is not None:
                job.result_json = result_json
            if status in ("completed", "failed", "interrupted"):
                job.completed_at = datetime.now(timezone.utc)
            db.commit()
        except Exception:
            db.rollback()
            logger.exception("Failed to update job progress: %s", job_id)
        finally:
            db.close()

        # 通知 SSE 订阅者
        event: dict[str, Any] = {
            "type": "progress" if status not in ("completed", "failed", "interrupted") else status,
            "status": status,
            "progress": progress,
            "message": message,
            "current_chunk": current_chunk,
            "total_chunks": total_chunks,
        }
        if error:
            event["error"] = error
        if result_json:
            event["result"] = result_json
        self._notify_subscribers(job_id, event)

    # ── 后台任务: 转写 ────────────────────────────────────────

    async def run_transcription_job(
        self,
        job_id: str,
        meeting_id: int,
        user_id: int | None,
    ) -> None:
        """后台执行转写任务。"""
        self._update_job_progress(job_id, "transcribing", 0.05, "正在加载模型...")

        db = SessionLocal()
        try:
            from app.services.pipeline.audio_service import (
                _assign_speaker_labels,
                _fetch_meeting_participants,
                _generate_mock_transcripts,
            )
            from app.services.business.hotword_service import get_hotword_terms
            from app.services.business.meeting_service import get_meeting
            from app.services.ai.faster_whisper_service import transcribe_audio_file
            from app.services.ai.whisper_service import WhisperServiceError
            from app.services.ai.speaker_diarization_service import diarize_audio
            from app.models.meeting_audio import MeetingAudio
            from app.models.meeting_transcript import MeetingTranscript

            meeting = get_meeting(db, meeting_id)
            if not meeting:
                self._update_job_progress(job_id, "failed", 0.0, "会议不存在", error="会议不存在")
                return

            latest_audio = (
                db.query(MeetingAudio)
                .filter(MeetingAudio.meeting_id == meeting_id)
                .order_by(MeetingAudio.id.desc())
                .first()
            )
            if not latest_audio:
                self._update_job_progress(job_id, "failed", 0.0, "无音频文件", error="无音频文件")
                return

            latest_segment = (
                db.query(MeetingTranscript)
                .filter(MeetingTranscript.meeting_id == meeting_id)
                .order_by(MeetingTranscript.segment_index.desc())
                .first()
            )
            next_segment_index = 1 if not latest_segment else latest_segment.segment_index + 1

            # Whisper 转写（在 executor 中执行，不阻塞 event loop）
            self._update_job_progress(job_id, "transcribing", 0.1, "正在转写音频...")
            hotwords = get_hotword_terms(db, user_id)

            try:
                loop = asyncio.get_running_loop()
                transcription = await loop.run_in_executor(
                    None, lambda: asyncio.run(transcribe_audio_file(latest_audio.storage_path, hotwords=hotwords))
                )
            except (WhisperServiceError, Exception) as exc:
                if not settings.whisper_allow_mock_fallback:
                    self._update_job_progress(job_id, "failed", 0.1, f"转写失败: {exc}", error=str(exc))
                    return
                self._update_job_progress(job_id, "transcribing", 0.3, "使用模拟数据...")
                segments = _generate_mock_transcripts(meeting_id, next_segment_index)
                participants = _fetch_meeting_participants(db, meeting_id)
                for segment in segments:
                    db.add(segment)
                db.commit()
                for segment in segments:
                    db.refresh(segment)
                _assign_speaker_labels(segments, participants)
                db.commit()
                result_ids = [s.id for s in segments]
                self._update_job_progress(
                    job_id, "completed", 1.0, "转写完成（模拟数据）",
                    result_json=json.dumps({"transcript_ids": result_ids}),
                )
                return

            # 创建转写记录
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
            for t in created_segments:
                db.refresh(t)

            self._update_job_progress(job_id, "transcribing", 0.6, f"转写完成，共 {len(created_segments)} 段")

            # 说话人分离（在 executor 中执行）
            diarization_success = False
            if settings.enable_speaker_diarization:
                self._update_job_progress(job_id, "diarizing", 0.65, "正在识别说话人...")
                try:
                    loop = asyncio.get_running_loop()
                    diarization_segments = await loop.run_in_executor(
                        None, lambda: diarize_audio(latest_audio.storage_path)
                    )
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
                                closest = None
                                min_dist = float("inf")
                                for d_seg in diarization_segments:
                                    dist = min(abs(t_mid - d_seg.start), abs(t_mid - d_seg.end))
                                    if dist < min_dist:
                                        min_dist = dist
                                        closest = d_seg
                                best_match = closest
                            if best_match:
                                transcript.speaker_id = best_match.speaker_id
                                transcript.speaker_name = best_match.speaker
                        db.commit()
                        for t in created_segments:
                            db.refresh(t)
                except Exception:
                    logger.exception("Speaker diarization failed in job %s", job_id)

            if not diarization_success:
                participants = _fetch_meeting_participants(db, meeting_id)
                _assign_speaker_labels(created_segments, participants)
                db.commit()

            result_ids = [t.id for t in created_segments]
            self._update_job_progress(
                job_id, "completed", 1.0, f"转写完成，共 {len(created_segments)} 段",
                result_json=json.dumps({"transcript_ids": result_ids}),
            )

        except asyncio.CancelledError:
            self._update_job_progress(job_id, "interrupted", 0.0, "任务被中断", error="服务器关闭")
            raise
        except Exception as exc:
            logger.exception("Transcription job failed: %s", job_id)
            self._update_job_progress(job_id, "failed", 0.0, f"转写失败: {exc}", error=str(exc))
        finally:
            db.close()
            self._active_tasks.pop(job_id, None)

    # ── 后台任务: 后处理 ──────────────────────────────────────

    async def run_postprocess_job(
        self,
        job_id: str,
        meeting_id: int,
    ) -> None:
        """后台执行后处理任务（摘要 + 任务提取）。"""
        self._update_job_progress(job_id, "generating_summary", 0.1, "正在生成摘要...")

        db = SessionLocal()
        try:
            from app.services.business.meeting_service import (
                build_meeting_summary_with_llm,
                generate_tasks_from_transcripts_with_llm,
                save_postprocess_result,
                get_meeting,
            )

            meeting = get_meeting(db, meeting_id)
            if not meeting:
                self._update_job_progress(job_id, "failed", 0.0, "会议不存在", error="会议不存在")
                return

            loop = asyncio.get_running_loop()

            self._update_job_progress(job_id, "generating_summary", 0.3, "正在调用 LLM 生成摘要...")
            summary = await loop.run_in_executor(
                None, lambda: build_meeting_summary_with_llm(db, meeting_id)
            )

            self._update_job_progress(job_id, "extracting_tasks", 0.6, "正在提取行动项...")
            tasks = await loop.run_in_executor(
                None, lambda: generate_tasks_from_transcripts_with_llm(db, meeting_id)
            )

            save_postprocess_result(db, meeting, summary, tasks)

            result = {
                "summary_length": len(summary) if summary else 0,
                "task_count": len(tasks) if tasks else 0,
            }
            self._update_job_progress(
                job_id, "completed", 1.0, "后处理完成",
                result_json=json.dumps(result),
            )

        except asyncio.CancelledError:
            self._update_job_progress(job_id, "interrupted", 0.0, "任务被中断", error="服务器关闭")
            raise
        except Exception as exc:
            logger.exception("Postprocess job failed: %s", job_id)
            self._update_job_progress(job_id, "failed", 0.0, f"后处理失败: {exc}", error=str(exc))
        finally:
            db.close()
            self._active_tasks.pop(job_id, None)

    # ── 任务启动 ──────────────────────────────────────────────

    def start_transcription_job(self, job_id: str, meeting_id: int, user_id: int | None) -> None:
        """启动转写后台任务。"""
        task = asyncio.create_task(
            self.run_transcription_job(job_id, meeting_id, user_id),
            name=f"transcribe-{job_id}",
        )
        self._active_tasks[job_id] = task

    def start_postprocess_job(self, job_id: str, meeting_id: int) -> None:
        """启动后处理后台任务。"""
        task = asyncio.create_task(
            self.run_postprocess_job(job_id, meeting_id),
            name=f"postprocess-{job_id}",
        )
        self._active_tasks[job_id] = task

    # ── 任务取消 ──────────────────────────────────────────────

    async def cancel_job(self, job_id: str) -> bool:
        """取消指定任务。"""
        task = self._active_tasks.get(job_id)
        if not task:
            return False
        task.cancel()
        self._update_job_progress(job_id, "interrupted", 0.0, "任务已取消", error="用户取消")
        self._notify_subscribers(job_id, {"type": "cancelled", "status": "interrupted"})
        self._subscribers.pop(job_id, None)
        return True

    # ── 生命周期管理 ──────────────────────────────────────────

    async def shutdown(self) -> None:
        """优雅关闭：取消所有活跃任务，标记为 interrupted。"""
        if not self._active_tasks:
            return

        logger.info("JobManager shutting down, cancelling %d active tasks", len(self._active_tasks))

        for task in self._active_tasks.values():
            task.cancel()

        results = await asyncio.gather(*self._active_tasks.values(), return_exceptions=True)
        for result in results:
            if isinstance(result, Exception) and not isinstance(result, asyncio.CancelledError):
                logger.error("Task raised during shutdown: %s", result)

        # 标记所有未完成任务为 interrupted
        db = SessionLocal()
        try:
            db.execute(
                text(
                    "UPDATE processing_jobs SET status = 'interrupted', error = '服务器关闭', "
                    "completed_at = NOW() WHERE status IN "
                    "('pending', 'queued', 'transcribing', 'diarizing', 'generating_summary', 'extracting_tasks')"
                )
            )
            db.commit()
        except Exception:
            db.rollback()
            logger.exception("Failed to mark stale jobs as interrupted during shutdown")
        finally:
            db.close()

        self._active_tasks.clear()
        self._subscribers.clear()
        logger.info("JobManager shutdown complete")

    async def recover_stale_jobs(self) -> None:
        """启动时恢复僵死任务。"""
        db = SessionLocal()
        try:
            result = db.execute(
                text(
                    "UPDATE processing_jobs SET status = 'failed', error = '服务器重启导致任务中断', "
                    "completed_at = NOW() WHERE status IN "
                    "('pending', 'queued', 'transcribing', 'diarizing', 'generating_summary', 'extracting_tasks')"
                )
            )
            db.commit()
            if result.rowcount > 0:
                logger.info("Recovered %d stale processing jobs", result.rowcount)
        except Exception:
            db.rollback()
            logger.exception("Failed to recover stale jobs")
        finally:
            db.close()

        # 清理残留的 SSE 订阅者
        self._subscribers.clear()

    # ── 查询 ──────────────────────────────────────────────────

    def get_job(self, job_id: str) -> ProcessingJob | None:
        """从 DB 查询任务状态。"""
        db = SessionLocal()
        try:
            return db.query(ProcessingJob).filter(ProcessingJob.job_id == job_id).first()
        finally:
            db.close()


# 全局单例
job_manager = JobManager()
