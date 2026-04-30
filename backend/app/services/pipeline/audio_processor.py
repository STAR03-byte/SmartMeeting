"""音频分段处理服务 - 处理长音频以避免 GPU 显存溢出。"""

import asyncio
import logging
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from app.core.config import settings
from app.services.pipeline.gpu_manager import (
    GPUManager,
    ProcessingStatus,
    ProgressInfo,
    get_gpu_manager,
)

logger = logging.getLogger(__name__)

MAX_CHUNK_DURATION_SECONDS = 30 * 60  # 30 分钟
CHUNK_OVERLAP_SECONDS = 5  # 分段重叠，避免边界词丢失


@dataclass
class AudioChunk:
    """音频分段信息。"""

    index: int
    start_time: float
    end_time: float
    file_path: Path


@dataclass
class MergedTranscript:
    """合并后的转写结果。"""

    text: str
    segments: List[dict]
    language: str


class AudioProcessor:
    """音频处理器 - 分段处理长音频。"""

    def __init__(self, gpu_manager: Optional[GPUManager] = None):
        self.gpu_manager = gpu_manager or get_gpu_manager()
        self._ffmpeg_available = shutil.which("ffmpeg") is not None

    def get_audio_duration(self, audio_path: Path) -> float:
        """获取音频时长（秒）。"""
        if not self._ffmpeg_available:
            logger.warning("ffmpeg not available, cannot determine audio duration")
            return 0.0

        import subprocess

        try:
            result = subprocess.run(
                [
                    "ffmpeg",
                    "-i", str(audio_path),
                    "-hide_banner",
                    "-f", "null",
                    "-",
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )
            for line in result.stderr.split("\n"):
                if "Duration:" in line:
                    parts = line.split("Duration:")[1].split(",")[0].strip()
                    h, m, s = parts.split(":")
                    return float(h) * 3600 + float(m) * 60 + float(s)
        except Exception as e:
            logger.error(f"Failed to get audio duration: {e}")

        return 0.0

    def split_audio(
        self,
        audio_path: Path,
        chunk_duration: float = MAX_CHUNK_DURATION_SECONDS,
        overlap: float = CHUNK_OVERLAP_SECONDS,
    ) -> List[AudioChunk]:
        """将长音频分割成多个片段。

        Args:
            audio_path: 音频文件路径
            chunk_duration: 每段最大时长（秒）
            overlap: 分段重叠时长（秒）

        Returns:
            音频分段列表
        """
        if not self._ffmpeg_available:
            logger.warning("ffmpeg not available, cannot split audio")
            return [AudioChunk(index=0, start_time=0.0, end_time=0.0, file_path=audio_path)]

        duration = self.get_audio_duration(audio_path)
        if duration <= chunk_duration:
            logger.info(f"Audio duration {duration}s <= {chunk_duration}s, no splitting needed")
            return [AudioChunk(index=0, start_time=0.0, end_time=duration, file_path=audio_path)]

        logger.info(f"Splitting audio {audio_path}: {duration}s into chunks of {chunk_duration}s")

        chunks: List[AudioChunk] = []
        temp_dir = Path(tempfile.mkdtemp(prefix="smartmeeting_chunks_"))

        index = 0
        start = 0.0

        while start < duration:
            end = min(start + chunk_duration, duration)
            chunk_path = temp_dir / f"chunk_{index:03d}{audio_path.suffix}"

            try:
                import subprocess

                subprocess.run(
                    [
                        "ffmpeg",
                        "-y",
                        "-i", str(audio_path),
                        "-ss", str(start),
                        "-to", str(end + overlap if end + overlap < duration else end),
                        "-c", "copy",
                        str(chunk_path),
                    ],
                    capture_output=True,
                    check=True,
                    timeout=300,
                )

                chunks.append(
                    AudioChunk(
                        index=index,
                        start_time=start,
                        end_time=end,
                        file_path=chunk_path,
                    )
                )
                logger.debug(f"Created chunk {index}: {start:.1f}s - {end:.1f}s")

            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to create chunk {index}: {e}")
                break
            except subprocess.TimeoutExpired:
                logger.error(f"Timeout creating chunk {index}")
                break

            index += 1
            start = end

        logger.info(f"Split audio into {len(chunks)} chunks")
        return chunks

    def cleanup_chunks(self, chunks: List[AudioChunk]) -> None:
        """清理临时分段文件。"""
        if not chunks:
            return

        temp_dir = chunks[0].file_path.parent
        try:
            shutil.rmtree(temp_dir)
            logger.debug(f"Cleaned up temp directory: {temp_dir}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temp directory: {e}")

    def merge_transcripts(
        self,
        transcripts: List[tuple[str, List[dict]]],
        chunks: List[AudioChunk],
    ) -> MergedTranscript:
        """合并多个转写结果。

        Args:
            transcripts: [(text, segments), ...] 每段的转写结果
            chunks: 音频分段信息

        Returns:
            合并后的转写结果
        """
        if not transcripts:
            return MergedTranscript(text="", segments=[], language="zh")

        all_text: List[str] = []
        all_segments: List[dict] = []

        for i, (text, segments) in enumerate(transcripts):
            chunk = chunks[i] if i < len(chunks) else chunks[-1]
            time_offset = chunk.start_time

            all_text.append(text)

            for seg in segments:
                adjusted_seg = seg.copy()
                adjusted_seg["start"] = seg.get("start", 0.0) + time_offset
                adjusted_seg["end"] = seg.get("end", 0.0) + time_offset
                all_segments.append(adjusted_seg)

        language = transcripts[0][1][0].get("language", "zh") if transcripts and transcripts[0][1] else "zh"

        return MergedTranscript(
            text=" ".join(all_text),
            segments=all_segments,
            language=language,
        )

    async def process_long_audio(
        self,
        audio_path: Path,
        transcribe_func,
        job_id: str,
        language: Optional[str] = None,
        hotwords: Optional[tuple[str, ...]] = None,
    ) -> MergedTranscript:
        """处理长音频，自动分段并合并结果。

        Args:
            audio_path: 音频文件路径
            transcribe_func: 转写函数，接受 (audio_path, language, hotwords) 参数
            job_id: 任务 ID
            language: 语言代码
            hotwords: 热词列表

        Returns:
            合并后的转写结果
        """
        self.gpu_manager.update_progress(
            job_id,
            ProcessingStatus.SEGMENTING,
            0.0,
            "Analyzing audio duration",
        )

        chunks = self.split_audio(audio_path)

        if len(chunks) == 1:
            self.gpu_manager.update_progress(
                job_id,
                ProcessingStatus.TRANSCRIBING,
                0.1,
                "Transcribing audio",
                current_chunk=1,
                total_chunks=1,
            )

            result = await transcribe_func(audio_path, language, hotwords)

            return MergedTranscript(
                text=result.get("text", ""),
                segments=result.get("segments", []),
                language=result.get("language", language or settings.whisper_language),
            )

        transcripts: List[tuple[str, List[dict]]] = []
        total_chunks = len(chunks)

        for i, chunk in enumerate(chunks):
            progress = 0.1 + (i / total_chunks) * 0.8

            self.gpu_manager.update_progress(
                job_id,
                ProcessingStatus.TRANSCRIBING,
                progress,
                f"Transcribing chunk {i + 1}/{total_chunks}",
                current_chunk=i + 1,
                total_chunks=total_chunks,
            )

            try:
                result = await transcribe_func(chunk.file_path, language, hotwords)
                transcripts.append((
                    result.get("text", ""),
                    result.get("segments", []),
                ))

                self.gpu_manager.clear_gpu_cache()

            except Exception as e:
                logger.error(f"Failed to transcribe chunk {i}: {e}")
                transcripts.append(("", []))

        self.gpu_manager.update_progress(
            job_id,
            ProcessingStatus.MERGING,
            0.95,
            "Merging transcript segments",
        )

        merged = self.merge_transcripts(transcripts, chunks)

        self.cleanup_chunks(chunks)

        return merged


audio_processor = AudioProcessor()


def get_audio_processor() -> AudioProcessor:
    """获取音频处理器实例。"""
    return audio_processor