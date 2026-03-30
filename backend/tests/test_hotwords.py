from __future__ import annotations

import asyncio

from app.services.whisper_service import WhisperTranscriber


class _FakeWhisperModel:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def transcribe(self, audio: str, language: str, task: str, initial_prompt: str | None = None):
        self.calls.append(
            {
                "audio": audio,
                "language": language,
                "task": task,
                "initial_prompt": initial_prompt,
            }
        )
        return {
            "language": language,
            "segments": [
                {"start": 0.0, "end": 1.0, "text": "接口联调由 SmartMeeting 完成。"},
            ],
        }


def test_transcribe_file_passes_hotwords_prompt(tmp_path, monkeypatch) -> None:
    audio_path = tmp_path / "sample.wav"
    audio_path.write_bytes(b"fake-audio")

    fake_model = _FakeWhisperModel()
    transcriber = WhisperTranscriber()
    monkeypatch.setattr(transcriber, "_load_model", lambda: fake_model)
    monkeypatch.setattr(transcriber, "_build_speech_ranges", lambda _: [(0.0, 1.0)])
    monkeypatch.setattr(transcriber, "_build_initial_prompt", lambda: "SmartMeeting,WhisperX")

    result = asyncio.run(transcriber.transcribe_file(audio_path, language="zh"))

    assert result[0]["text"] == "接口联调由 SmartMeeting 完成。"
    assert fake_model.calls[0]["initial_prompt"] == "SmartMeeting,WhisperX"
