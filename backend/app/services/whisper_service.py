"""Whisper ASR 服务层 - 支持本地转写。"""

import asyncio
import importlib
import logging
import shutil
from pathlib import Path
from typing import Protocol, TypedDict, cast

from app.core.config import settings

logger = logging.getLogger(__name__)


class WhisperServiceError(Exception):
    pass


class WhisperSegment(TypedDict):
    start: float
    end: float
    text: str
    language: str


class WhisperResult(TypedDict):
    text: str
    segments: list[WhisperSegment]
    language: str


WhisperRawResult = dict[str, object]


class WhisperModelProtocol(Protocol):
    def transcribe(self, audio: str, language: str, task: str) -> WhisperRawResult: ...


class WhisperTranscriber:
    def __init__(self) -> None:
        self._model: WhisperModelProtocol | None = None
        self._device: str | None = None

    def _load_model(self) -> WhisperModelProtocol:
        if self._model is None:
            try:
                whisper_module = importlib.import_module("whisper")
            except ImportError as exc:
                raise WhisperServiceError(
                    "Whisper not installed. Run: pip install openai-whisper"
                ) from exc

            if shutil.which("ffmpeg") is None:
                raise WhisperServiceError(
                    "ffmpeg not found. Install ffmpeg or add it to PATH."
                )

            device = settings.whisper_device
            if device == "auto":
                torch_module = importlib.import_module("torch")
                cuda = getattr(torch_module, "cuda", None)
                is_available = getattr(cuda, "is_available", None)
                device = "cuda" if callable(is_available) and bool(is_available()) else "cpu"
            logger.info("Loading Whisper model: %s on %s", settings.whisper_model, device)
            self._model = cast(
                WhisperModelProtocol,
                whisper_module.load_model(settings.whisper_model, device=device),
            )
            self._device = device
        return self._model

    async def transcribe_file(
        self,
        audio_path: str | Path,
        language: str | None = None,
    ) -> list[WhisperSegment]:
        model = self._load_model()
        file_path = Path(audio_path)

        if not file_path.exists():
            raise WhisperServiceError(f"Audio file not found: {file_path}")

        def _sync_transcribe() -> WhisperRawResult:
            try:
                return model.transcribe(
                    str(file_path),
                    language=language or settings.whisper_language,
                    task="transcribe",
                )
            except (FileNotFoundError, OSError, RuntimeError) as exc:
                raise WhisperServiceError(
                    "Whisper transcription failed. Check ffmpeg installation and audio format."
                ) from exc

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, _sync_transcribe)

        raw_segments = result.get("segments", [])
        detected_language = result.get("language", language or settings.whisper_language)
        segments: list[WhisperSegment] = []
        if isinstance(raw_segments, list):
            for segment in raw_segments:
                if not isinstance(segment, dict):
                    continue
                start = segment.get("start", 0.0)
                end = segment.get("end", 0.0)
                text = segment.get("text", "")
                segments.append(
                    {
                        "start": float(start) if isinstance(start, (int, float)) else 0.0,
                        "end": float(end) if isinstance(end, (int, float)) else 0.0,
                        "text": text.strip() if isinstance(text, str) else "",
                        "language": detected_language if isinstance(detected_language, str) else settings.whisper_language,
                    }
                )
        return segments

    async def transcribe_with_timestamps(
        self,
        audio_path: str | Path,
        language: str | None = None,
    ) -> WhisperResult:
        segments = await self.transcribe_file(audio_path, language)
        full_text = " ".join(segment["text"] for segment in segments)
        return {
            "text": full_text,
            "segments": segments,
            "language": segments[0]["language"] if segments else (language or settings.whisper_language),
        }


whisper_transcriber = WhisperTranscriber()


async def transcribe_audio_file(
    audio_path: str | Path,
    language: str | None = None,
) -> WhisperResult:
    return await whisper_transcriber.transcribe_with_timestamps(audio_path, language)
