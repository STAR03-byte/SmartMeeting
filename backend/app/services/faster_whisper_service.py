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
        self._disabled_reason: str | None = None

    def preload_model(self) -> None:
        if self._disabled_reason is not None:
            raise WhisperServiceError(self._disabled_reason)
        if self._model is not None:
            return

        try:
            faster_whisper = importlib.import_module("faster_whisper")
        except ImportError as exc:
            raise WhisperServiceError("faster-whisper not installed.") from exc

        if shutil.which("ffmpeg") is None:
            raise WhisperServiceError("ffmpeg not found.")

        def _bool_setting(name: str, default: bool) -> bool:
            value = getattr(settings, name, default)
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.strip().lower() in {"1", "true", "yes", "on"}
            return default

        device = settings.whisper_device
        require_gpu = _bool_setting("faster_whisper_require_gpu", False)
        current_python = importlib.import_module("sys").executable
        if device == "auto":
            try:
                torch_module = importlib.import_module("torch")
                torch = torch_module
                device = "cuda" if getattr(torch, "cuda").is_available() else "cpu"
            except ImportError:
                device = "cpu"
        elif device == "cuda":
            try:
                torch_module = importlib.import_module("torch")
                torch = torch_module
                if not getattr(torch, "cuda").is_available():
                    if require_gpu:
                        raise WhisperServiceError(
                            f"CUDA requested and required, but GPU not available (python={current_python})"
                        )
                    logger.warning("CUDA requested but GPU not available, falling back to CPU")
                    device = "cpu"
            except ImportError:
                if require_gpu:
                    raise WhisperServiceError(
                        f"PyTorch not available while GPU is required (python={current_python})"
                    )
                logger.warning("PyTorch not available, falling back to CPU")
                device = "cpu"

        if require_gpu and device != "cuda":
            raise WhisperServiceError(
                f"GPU is required for faster-whisper, but current device is CPU (python={current_python})"
            )

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
            model_path_raw = getattr(settings, "faster_whisper_model_path", "")
            model_path_value = model_path_raw.strip() if isinstance(model_path_raw, str) else ""
            model_name_or_path = model_path_value or settings.whisper_model
            model_path_obj = Path(model_name_or_path)
            if model_path_obj.is_absolute():
                resolved_model = str(model_path_obj)
            else:
                resolved_model = str((Path(__file__).resolve().parents[3] / model_path_obj).resolve())

            local_files_only = _bool_setting("faster_whisper_local_files_only", False)
            cache_dir_raw = getattr(settings, "faster_whisper_cache_dir", "")
            cache_dir = cache_dir_raw if isinstance(cache_dir_raw, str) else ""
            if local_files_only and not Path(resolved_model).exists():
                raise WhisperServiceError(
                    f"faster-whisper local model path not found: {resolved_model}. "
                    f"Set FASTER_WHISPER_MODEL_PATH to an existing local model directory."
                )

            self._model = faster_whisper.WhisperModel(
                resolved_model if Path(resolved_model).exists() else model_name_or_path,
                device=device,
                compute_type=compute_type,
                local_files_only=local_files_only,
                download_root=cache_dir,
            )
            self._device = device
            self._compute_type = compute_type
        except Exception as exc:
            self._disabled_reason = f"Failed to load faster-whisper model: {exc}"
            raise WhisperServiceError(self._disabled_reason) from exc

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
            if settings.faster_whisper_fallback_to_whisper:
                logger.warning("faster-whisper preload failed, falling back to original whisper: %s", exc)
                return await fallback_transcriber.transcribe_file(audio_path, language)
            raise

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
            if settings.faster_whisper_fallback_to_whisper:
                logger.warning("faster-whisper execution failed, falling back: %s", exc)
                return await fallback_transcriber.transcribe_file(audio_path, language)
            raise

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
