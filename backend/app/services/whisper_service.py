"""Whisper ASR 服务层 - 支持本地转写。"""

import asyncio
import importlib
import logging
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Protocol, TypedDict, cast

from app.core.config import settings

logger = logging.getLogger(__name__)

_MIN_SILENCE_SECONDS = 0.5
_SILENCE_NOISE_DB = -35.0
_KEEP_SILENCE_SECONDS = 0.2
_MIN_SEGMENT_SECONDS = 0.4

_SILENCE_START_RE = re.compile(r"silence_start:\s*(?P<time>\d+(?:\.\d+)?)")
_SILENCE_END_RE = re.compile(r"silence_end:\s*(?P<time>\d+(?:\.\d+)?)")


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
    def transcribe(
        self,
        audio: str,
        language: str,
        task: str,
        initial_prompt: str | None = None,
    ) -> WhisperRawResult: ...


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

    def _build_initial_prompt(self) -> str | None:
        hotwords = [item.strip() for item in settings.whisper_hot_words.split(",") if item.strip()]
        if not hotwords:
            return None
        return "，".join(hotwords)

    def _normalize_to_simplified(self, text: str) -> str:
        if not settings.whisper_normalize_to_simplified:
            return text

        try:
            opencc_module = importlib.import_module("opencc")
        except ImportError:
            logger.warning("OpenCC not installed; skip simplified Chinese normalization")
            return text

        try:
            converter = getattr(opencc_module, "OpenCC")("t2s")
            return converter.convert(text)
        except Exception as exc:  # noqa: BLE001
            logger.warning("OpenCC conversion failed, keep original text: %s", exc)
            return text

    def _get_audio_duration_seconds(self, file_path: Path) -> float:
        if shutil.which("ffprobe") is None:
            raise WhisperServiceError("ffprobe not found. Install ffmpeg or add it to PATH.")

        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(file_path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise WhisperServiceError("ffprobe failed to inspect audio duration")

        try:
            duration = float(result.stdout.strip())
        except ValueError as exc:
            raise WhisperServiceError("Failed to parse audio duration") from exc

        if duration <= 0:
            raise WhisperServiceError("Invalid audio duration")
        return duration

    def _build_speech_ranges(self, file_path: Path) -> list[tuple[float, float]]:
        duration = self._get_audio_duration_seconds(file_path)
        if shutil.which("ffmpeg") is None:
            raise WhisperServiceError("ffmpeg not found. Install ffmpeg or add it to PATH.")

        result = subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-nostdin",
                "-i",
                str(file_path),
                "-af",
                f"silencedetect=noise={_SILENCE_NOISE_DB}dB:d={_MIN_SILENCE_SECONDS}",
                "-f",
                "null",
                "-",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode not in (0, 1):
            raise WhisperServiceError("ffmpeg silence detection failed")

        silence_events: list[tuple[str, float]] = []
        for line in result.stderr.splitlines():
            start_match = _SILENCE_START_RE.search(line)
            if start_match:
                silence_events.append(("start", float(start_match.group("time"))))
                continue
            end_match = _SILENCE_END_RE.search(line)
            if end_match:
                silence_events.append(("end", float(end_match.group("time"))))

        if not silence_events:
            return [(0.0, duration)]

        silence_ranges: list[tuple[float, float]] = []
        current_start: float | None = None
        for event_type, event_time in silence_events:
            if event_type == "start":
                current_start = event_time
            elif event_type == "end" and current_start is not None:
                silence_ranges.append((current_start, event_time))
                current_start = None

        if current_start is not None:
            silence_ranges.append((current_start, duration))

        speech_ranges: list[tuple[float, float]] = []
        cursor = 0.0
        for silence_start, silence_end in silence_ranges:
            if silence_start > cursor:
                speech_ranges.append((cursor, silence_start))
            cursor = max(cursor, silence_end)
        if cursor < duration:
            speech_ranges.append((cursor, duration))

        merged: list[tuple[float, float]] = []
        for start_sec, end_sec in speech_ranges:
            start = max(0.0, start_sec - _KEEP_SILENCE_SECONDS)
            end = min(duration, end_sec + _KEEP_SILENCE_SECONDS)
            if end - start < _MIN_SEGMENT_SECONDS:
                continue
            if merged and start - merged[-1][1] <= _KEEP_SILENCE_SECONDS:
                merged[-1] = (merged[-1][0], max(merged[-1][1], end))
            else:
                merged.append((start, end))

        return merged or [(0.0, duration)]

    async def _transcribe_chunk(
        self,
        model: WhisperModelProtocol,
        audio_path: Path,
        language: str,
        offset_seconds: float,
    ) -> list[WhisperSegment]:
        initial_prompt = self._build_initial_prompt()

        def _sync_transcribe() -> WhisperRawResult:
            try:
                return model.transcribe(
                    str(audio_path),
                    language=language,
                    task="transcribe",
                    initial_prompt=initial_prompt,
                )
            except (FileNotFoundError, OSError, RuntimeError) as exc:
                raise WhisperServiceError(
                    "Whisper transcription failed. Check ffmpeg installation and audio format."
                ) from exc

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, _sync_transcribe)

        raw_segments = result.get("segments", [])
        detected_language = result.get("language", language)
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
                        "start": (float(start) if isinstance(start, (int, float)) else 0.0)
                        + offset_seconds,
                        "end": (float(end) if isinstance(end, (int, float)) else 0.0)
                        + offset_seconds,
                        "text": self._normalize_to_simplified(text.strip()) if isinstance(text, str) else "",
                        "language": detected_language if isinstance(detected_language, str) else language,
                    }
                )
        return segments

    async def transcribe_file(
        self,
        audio_path: str | Path,
        language: str | None = None,
    ) -> list[WhisperSegment]:
        model = self._load_model()
        file_path = Path(audio_path)

        if not file_path.exists():
            raise WhisperServiceError(f"Audio file not found: {file_path}")

        language_code = language or settings.whisper_language

        try:
            ranges = self._build_speech_ranges(file_path)
        except WhisperServiceError as exc:
            logger.warning("VAD preprocessing failed, falling back to whole-file transcription: %s", exc)
            return await self._transcribe_chunk(model, file_path, language_code, 0.0)

        if len(ranges) <= 1:
            return await self._transcribe_chunk(model, file_path, language_code, 0.0)

        segments: list[WhisperSegment] = []
        with tempfile.TemporaryDirectory() as tmpdir:
            for index, (start_sec, end_sec) in enumerate(ranges, start=1):
                if end_sec <= start_sec:
                    continue
                chunk_path = Path(tmpdir) / f"vad_chunk_{index}.wav"
                cut_result = subprocess.run(
                    [
                        "ffmpeg",
                        "-hide_banner",
                        "-nostdin",
                        "-y",
                        "-i",
                        str(file_path),
                        "-ss",
                        str(start_sec),
                        "-to",
                        str(end_sec),
                        "-vn",
                        "-ac",
                        "1",
                        "-ar",
                        "16000",
                        "-c:a",
                        "pcm_s16le",
                        str(chunk_path),
                    ],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if cut_result.returncode != 0 or not chunk_path.exists():
                    logger.warning("VAD chunk extraction failed, falling back to whole-file transcription")
                    return await self._transcribe_chunk(model, file_path, language_code, 0.0)
                segments.extend(
                    await self._transcribe_chunk(
                        model=model,
                        audio_path=chunk_path,
                        language=language_code,
                        offset_seconds=start_sec,
                    )
                )

        if not segments:
            return await self._transcribe_chunk(model, file_path, language_code, 0.0)
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
