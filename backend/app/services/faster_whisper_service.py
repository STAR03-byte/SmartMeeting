"""Faster Whisper ASR 服务层 - 支持本地高性能转写并兼容 GPU。"""

import asyncio
import importlib
import logging
import shutil
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.services.whisper_service import (
    WhisperResult,
    WhisperSegment,
    WhisperServiceError,
    whisper_transcriber as fallback_transcriber,
)

logger = logging.getLogger(__name__)


class FasterWhisperTranscriber:
    def __init__(self) -> None:
        self._model: Any = None
        self._device: str | None = None
        self._compute_type: str | None = None

    def preload_model(self) -> None:
        if self._model is not None:
            return

        try:
            faster_whisper = importlib.import_module("faster_whisper")
        except ImportError as exc:
            raise WhisperServiceError("faster-whisper not installed.") from exc

        if shutil.which("ffmpeg") is None:
            raise WhisperServiceError("ffmpeg not found.")

        device = settings.whisper_device
        if device == "auto":
            try:
                torch = importlib.import_module("torch")
                device = "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                device = "cpu"

        if device == "cuda":
            compute_type = settings.faster_whisper_compute_type
        else:
            compute_type = "int8"

        logger.info(
            "Loading faster-whisper model: %s on %s with %s",
            settings.whisper_model,
            device,
            compute_type,
        )

        try:
            self._model = faster_whisper.WhisperModel(
                settings.whisper_model,
                device=device,
                compute_type=compute_type,
            )
            self._device = device
            self._compute_type = compute_type
        except Exception as exc:
            raise WhisperServiceError(f"Failed to load faster-whisper model: {exc}") from exc

    def _build_initial_prompt(self, hotwords: tuple[str, ...] | None = None) -> str | None:
        prompt_terms = hotwords if hotwords is not None else tuple(
            item.strip() for item in settings.whisper_hot_words.split(",") if item.strip()
        )
        if not prompt_terms:
            return None
        return "，".join(prompt_terms)

    def _normalize_language_code(self, language: str | None) -> str:
        language_code = (language or settings.whisper_language).strip().lower()
        if language_code in {"zh", "zh-cn", "zh_hans", "zh-hans", "chinese"}:
            return "zh"
        return language_code

    async def transcribe_file(
        self,
        audio_path: str | Path,
        language: str | None = None,
        hotwords: tuple[str, ...] | None = None,
    ) -> list[WhisperSegment]:
        
        file_path = Path(audio_path)
        if not file_path.exists():
            raise WhisperServiceError(f"Audio file not found: {file_path}")
            
        try:
            self.preload_model()
        except WhisperServiceError as exc:
            logger.warning("faster-whisper preload failed, falling back to original whisper: %s", exc)
            return await fallback_transcriber.transcribe_file(audio_path, language)

        language_code = self._normalize_language_code(language)
        initial_prompt = self._build_initial_prompt(hotwords)

        def _sync_transcribe() -> list[WhisperSegment]:
            try:
                segments, info = self._model.transcribe(
                    str(file_path),
                    language=language_code,
                    initial_prompt=initial_prompt,
                    vad_filter=True,
                )
                
                result_segments: list[WhisperSegment] = []
                for segment in segments:
                    result_segments.append(
                        {
                            "start": segment.start,
                            "end": segment.end,
                            "text": fallback_transcriber._normalize_to_simplified(segment.text.strip()),
                            "language": info.language,
                        }
                    )
                return result_segments
            except Exception as exc:
                raise WhisperServiceError(f"faster-whisper transcription failed: {exc}") from exc

        loop = asyncio.get_running_loop()
        try:
            return await loop.run_in_executor(None, _sync_transcribe)
        except WhisperServiceError as exc:
            logger.warning("faster-whisper execution failed, falling back: %s", exc)
            return await fallback_transcriber.transcribe_file(audio_path, language)

    async def transcribe_with_timestamps(
        self,
        audio_path: str | Path,
        language: str | None = None,
        hotwords: tuple[str, ...] | None = None,
    ) -> WhisperResult:
        if not getattr(settings, "use_faster_whisper", True):
            return await fallback_transcriber.transcribe_with_timestamps(audio_path, language)
            
        segments = await self.transcribe_file(audio_path, language, hotwords)
        full_text = " ".join(segment["text"] for segment in segments)
        return {
            "text": full_text,
            "segments": segments,
            "language": segments[0]["language"] if segments else self._normalize_language_code(language),
        }


faster_whisper_transcriber = FasterWhisperTranscriber()

async def transcribe_audio_file(
    audio_path: str | Path,
    language: str | None = None,
    hotwords: tuple[str, ...] | None = None,
) -> WhisperResult:
    if getattr(settings, "use_faster_whisper", True):
        return await faster_whisper_transcriber.transcribe_with_timestamps(audio_path, language, hotwords)
    return await fallback_transcriber.transcribe_with_timestamps(audio_path, language)
