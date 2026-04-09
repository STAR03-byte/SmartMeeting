"""Speaker Diarization 服务层。"""

import importlib
import logging
import os
import warnings
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)

class SpeakerSegment(BaseModel):
    start: float
    end: float
    speaker: str
    speaker_id: int

class SpeakerDiarizationService:
    def __init__(self):
        self._pipeline: Any | None = None
        self._pipeline_cls: Any | None = None
        self._torch_module: Any | None = None
        self._pyannote_available: bool | None = None

    @staticmethod
    def _suppress_pyannote_warnings() -> None:
        warnings.filterwarnings(
            "ignore",
            message=r".*torchcodec is not installed correctly.*",
            category=UserWarning,
        )
        warnings.filterwarnings(
            "ignore",
            message=r".*TensorFloat-32.*",
            category=UserWarning,
        )

    def _ensure_pyannote(self) -> bool:
        if self._pyannote_available is not None:
            return self._pyannote_available

        try:
            with warnings.catch_warnings():
                self._suppress_pyannote_warnings()
                pyannote_audio = importlib.import_module("pyannote.audio")
            torch_module = importlib.import_module("torch")
            self._pipeline_cls = pyannote_audio.Pipeline
            self._torch_module = torch_module
            self._pyannote_available = True
        except Exception as e:
            logger.warning("pyannote/audio dependencies unavailable: %s", e)
            self._pyannote_available = False

        return self._pyannote_available

    def preload_pipeline(self) -> None:
        if not settings.enable_speaker_diarization:
            return
        if not self._ensure_pyannote():
            return
        if self._pipeline_cls is None or self._torch_module is None:
            return
        if self._pipeline is not None:
            return

        logger.info("Loading pyannote.audio diarization pipeline")
        
        try:
            from_pretrained_kwargs: dict[str, object] = {
                "cache_dir": settings.pyannote_cache_dir,
            }
            token = settings.pyannote_hf_token.strip() or settings.llm_api_key.strip() or None
            if token:
                from_pretrained_kwargs["token"] = token

            offline_prev = os.environ.get("HF_HUB_OFFLINE")
            if settings.pyannote_local_files_only:
                os.environ["HF_HUB_OFFLINE"] = "1"

            self._pipeline = self._pipeline_cls.from_pretrained(
                settings.pyannote_pipeline_id,
                **from_pretrained_kwargs,
            )
            if settings.pyannote_local_files_only:
                if offline_prev is None:
                    os.environ.pop("HF_HUB_OFFLINE", None)
                else:
                    os.environ["HF_HUB_OFFLINE"] = offline_prev
            if self._pipeline is None:
                raise RuntimeError("Failed to initialize pyannote pipeline")
            pipeline = self._pipeline
            
            device_name = (
                "cuda"
                if self._torch_module.cuda.is_available() and settings.whisper_device == "cuda"
                else "cpu"
            )
            if settings.pyannote_require_gpu and device_name != "cuda":
                raise RuntimeError("Speaker diarization requires GPU, but CUDA is unavailable")

            device = self._torch_module.device(device_name)
            pipeline.to(device)
            
            logger.info(f"Diarization pipeline loaded successfully on {device}")
        except Exception as e:
            logger.error(f"Failed to load diarization pipeline: {e}")
            self._pipeline = None

    def diarize_audio(
        self,
        audio_path: str | Path,
        min_speakers: int = 2,
        max_speakers: int = 5,
    ) -> list[SpeakerSegment]:
        if not settings.enable_speaker_diarization:
            return []
        if not self._ensure_pyannote():
            return []
            
        self.preload_pipeline()
        if self._pipeline is None:
            return []
        pipeline = self._pipeline

        try:
            with warnings.catch_warnings():
                self._suppress_pyannote_warnings()

                if self._torch_module is not None and self._torch_module.cuda.is_available():
                    self._torch_module.cuda.empty_cache()

                try:
                    # 使用 librosa 加载音频，绕过 torchcodec 在 Windows 上的兼容性问题
                    librosa = importlib.import_module("librosa")
                    y, sr = librosa.load(str(audio_path), sr=None, mono=True)
                    # 转换为 torch tensor 格式 (1, samples)
                    waveform = self._torch_module.from_numpy(y).unsqueeze(0).float()
                    input_audio: dict[str, Any] = {
                        "waveform": waveform,
                        "sample_rate": int(sr),
                    }
                    diarization = pipeline(
                        input_audio,
                        min_speakers=min_speakers,
                        max_speakers=max_speakers,
                    )
                except Exception as e:
                    # librosa 加载失败，记录错误并返回空列表
                    logger.error("Diarization librosa decode failed: %s", e)
                    return []

                segments = []
                speaker_mapping = {}
                current_id = 0

                for turn, _, speaker in diarization.itertracks(yield_label=True):
                    if speaker not in speaker_mapping:
                        speaker_mapping[speaker] = current_id
                        current_id += 1

                    segments.append(SpeakerSegment(
                        start=turn.start,
                        end=turn.end,
                        speaker=f"SPEAKER_{speaker_mapping[speaker]:02d}",
                        speaker_id=speaker_mapping[speaker]
                    ))

                return segments
        except Exception as e:
            logger.error(f"Diarization failed: {e}")
            return []
        finally:
            if self._torch_module is not None and self._torch_module.cuda.is_available():
                self._torch_module.cuda.empty_cache()

speaker_diarization_service = SpeakerDiarizationService()

def diarize_audio(audio_path: str | Path) -> list[SpeakerSegment]:
    return speaker_diarization_service.diarize_audio(audio_path)
