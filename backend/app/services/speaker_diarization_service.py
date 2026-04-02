"""Speaker Diarization 服务层。"""

import logging
from pathlib import Path
from typing import List

from pydantic import BaseModel
try:
    from pyannote.audio import Pipeline
    import torch
    PYANNOTE_AVAILABLE = True
except ImportError:
    PYANNOTE_AVAILABLE = False


from app.core.config import settings

logger = logging.getLogger(__name__)

class SpeakerSegment(BaseModel):
    start: float
    end: float
    speaker: str
    speaker_id: int

class SpeakerDiarizationService:
    def __init__(self):
        self._pipeline = None

    def preload_pipeline(self) -> None:
        if not settings.enable_speaker_diarization or not PYANNOTE_AVAILABLE:
            return
        if self._pipeline is not None:
            return

        logger.info("Loading pyannote.audio diarization pipeline")
        
        try:
            self._pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=settings.llm_api_key or True
            )
            
            device = torch.device("cuda" if torch.cuda.is_available() and settings.whisper_device == "cuda" else "cpu")
            self._pipeline.to(device)
            
            logger.info(f"Diarization pipeline loaded successfully on {device}")
        except Exception as e:
            logger.error(f"Failed to load diarization pipeline: {e}")
            self._pipeline = None

    def diarize_audio(self, audio_path: str | Path, min_speakers: int = 2, max_speakers: int = 5) -> List[SpeakerSegment]:
        if not settings.enable_speaker_diarization or not PYANNOTE_AVAILABLE:
            return []
            
        self.preload_pipeline()
        if self._pipeline is None:
            return []

        try:
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            diarization = self._pipeline(str(audio_path), min_speakers=min_speakers, max_speakers=max_speakers)
            
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
            if PYANNOTE_AVAILABLE and torch.cuda.is_available():
                torch.cuda.empty_cache()

speaker_diarization_service = SpeakerDiarizationService()

def diarize_audio(audio_path: str | Path) -> List[SpeakerSegment]:
    return speaker_diarization_service.diarize_audio(audio_path)
