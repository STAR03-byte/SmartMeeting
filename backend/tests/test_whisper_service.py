from __future__ import annotations

import math
import shutil
import subprocess
import wave
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.services.ai.whisper_service import WhisperTranscriber


def _find_ffmpeg() -> str:
    result = shutil.which("ffmpeg")
    if result:
        return result
    common_paths = [
        Path(r"C:\ffmpeg\bin"),
        Path(r"C:\Program Files\ffmpeg\bin"),
        Path(r"C:\Program Files (x86)\ffmpeg\bin"),
        Path(r"D:\tools\ffmpeg-8.1-full_build-shared\bin"),
        Path.home() / "ffmpeg" / "bin",
    ]
    for base in common_paths:
        candidate = base / "ffmpeg.exe"
        if candidate.exists():
            return str(candidate)
    return "ffmpeg"


def _write_tone_wav(path: Path) -> None:
    sample_rate = 16000
    duration_seconds = 1.0
    amplitude = 12000

    def write_silence(handle: wave.Wave_write, seconds: float) -> None:
        total_frames = int(sample_rate * seconds)
        handle.writeframes(b"\x00\x00" * total_frames)

    def write_tone(handle: wave.Wave_write, seconds: float) -> None:
        total_frames = int(sample_rate * seconds)
        frames = bytearray()
        for index in range(total_frames):
            value = int(amplitude * math.sin(2 * math.pi * 440 * (index / sample_rate)))
            frames.extend(int(value).to_bytes(2, byteorder="little", signed=True))
        handle.writeframes(bytes(frames))

    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        write_tone(handle, duration_seconds)
        write_silence(handle, duration_seconds * 1.5)
        write_tone(handle, duration_seconds)


def _run_silencedetect(path: Path) -> str:
    ffmpeg_path = _find_ffmpeg()
    result = subprocess.run(
        [
            ffmpeg_path,
            "-hide_banner",
            "-nostdin",
            "-i",
            str(path),
            "-af",
            "silencedetect=noise=-35dB:d=0.7",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    return result.stderr


def test_vad_segments_audio_and_offsets(tmp_path: Path) -> None:
    audio_path = tmp_path / "vad_input.wav"
    _write_tone_wav(audio_path)

    transcriber = WhisperTranscriber()
    ranges = transcriber._build_speech_ranges(audio_path)

    assert len(ranges) == 2
    assert abs(ranges[0][0] - 0.0) <= 0.25
    assert abs(ranges[0][1] - 1.0) <= 0.35
    assert abs(ranges[1][0] - 2.5) <= 0.35
    assert abs(ranges[1][1] - 3.5) <= 0.35

    stderr = _run_silencedetect(audio_path)
    assert "silence_start: 1" in stderr
    assert "silence_end: 2" in stderr


def test_normalize_to_simplified_uses_opencc_when_enabled() -> None:
    transcriber = WhisperTranscriber()

    fake_opencc = MagicMock()
    fake_converter = MagicMock()
    fake_converter.convert.return_value = "简体中文"
    fake_opencc.OpenCC.return_value = fake_converter

    with patch("app.services.whisper_service.settings.whisper_normalize_to_simplified", True), patch(
        "app.services.whisper_service.importlib.import_module",
        return_value=fake_opencc,
    ):
        assert transcriber._normalize_to_simplified("繁體中文") == "简体中文"


def test_normalize_to_simplified_passthrough_when_disabled() -> None:
    transcriber = WhisperTranscriber()

    with patch("app.services.whisper_service.settings.whisper_normalize_to_simplified", False):
        assert transcriber._normalize_to_simplified("繁體中文") == "繁體中文"
