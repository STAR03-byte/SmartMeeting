import pytest
from unittest.mock import patch, MagicMock

from app.services.faster_whisper_service import FasterWhisperTranscriber

import importlib as real_importlib

@pytest.fixture
def mock_faster_whisper():
    real_import = real_importlib.import_module
    with patch("app.services.faster_whisper_service.importlib.import_module") as mock_import:
        mock_fw = MagicMock()
        mock_model = MagicMock()
        mock_fw.WhisperModel.return_value = mock_model
        
        def side_effect(name, *args, **kwargs):
            if name == "faster_whisper":
                return mock_fw
            if name == "torch":
                mock_torch = MagicMock()
                mock_torch.cuda.is_available.return_value = True
                return mock_torch
            return real_import(name, *args, **kwargs)
            
        mock_import.side_effect = side_effect
        yield mock_fw, mock_model

def test_faster_whisper_transcriber_gpu_load(mock_faster_whisper):
    mock_fw, mock_model = mock_faster_whisper
    
    with patch("app.services.faster_whisper_service.settings") as mock_settings:
        mock_settings.whisper_device = "auto"
        mock_settings.whisper_model = "small"
        mock_settings.faster_whisper_compute_type = "int8_float16"
        
        transcriber = FasterWhisperTranscriber()
        transcriber.preload_model()
        
        mock_fw.WhisperModel.assert_called_once()
        args, kwargs = mock_fw.WhisperModel.call_args
        assert kwargs.get("device") == "cuda"
        assert kwargs.get("compute_type") == "int8_float16"

def test_faster_whisper_cpu_fallback():
    real_import = real_importlib.import_module
    with patch("app.services.faster_whisper_service.importlib.import_module") as mock_import, \
         patch("app.services.faster_whisper_service.settings") as mock_settings:
        mock_settings.whisper_device = "auto"
        mock_settings.whisper_model = "small"
        
        mock_fw = MagicMock()
        
        def side_effect(name, *args, **kwargs):
            if name == "faster_whisper":
                return mock_fw
            if name == "torch":
                mock_torch = MagicMock()
                mock_torch.cuda.is_available.return_value = False
                return mock_torch
            return real_import(name, *args, **kwargs)
            
        mock_import.side_effect = side_effect
        
        transcriber = FasterWhisperTranscriber()
        transcriber.preload_model()
        
        args, kwargs = mock_fw.WhisperModel.call_args
        assert kwargs.get("device") == "cpu"
        assert kwargs.get("compute_type") == "int8"
