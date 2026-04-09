from __future__ import annotations

import argparse
import os
import ssl
import sys
import warnings
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


def _inject_cert_store() -> None:
    try:
        truststore_module = __import__("truststore")
        inject = getattr(truststore_module, "inject_into_ssl", None)
        if callable(inject):
            inject()
    except Exception:
        pass

    try:
        import certifi

        ca_bundle = certifi.where()
        _ = os.environ.setdefault("SSL_CERT_FILE", ca_bundle)
        _ = os.environ.setdefault("REQUESTS_CA_BUNDLE", ca_bundle)
    except Exception:
        pass


def _warmup_faster_whisper(model_name: str, model_dir: Path, cache_dir: Path) -> None:
    from huggingface_hub import snapshot_download

    name_map = {
        "tiny": "Systran/faster-whisper-tiny",
        "base": "Systran/faster-whisper-base",
        "small": "Systran/faster-whisper-small",
        "medium": "Systran/faster-whisper-medium",
        "large-v2": "Systran/faster-whisper-large-v2",
        "large-v3": "Systran/faster-whisper-large-v3",
    }
    repo_id = name_map.get(model_name, model_name)
    model_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)

    _ = snapshot_download(
        repo_id=repo_id,
        local_dir=str(model_dir),
        cache_dir=str(cache_dir),
        force_download=False,
    )


def _warmup_pyannote(pipeline_id: str, cache_dir: Path, token: str | None) -> None:
    if token is None or not token.strip():
        raise RuntimeError("PYANNOTE_HF_TOKEN is required for pyannote warmup.")

    hf_endpoint = os.getenv("HF_ENDPOINT", "").strip()
    if hf_endpoint:
        os.environ["HF_ENDPOINT"] = hf_endpoint

    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=r".*torchcodec is not installed correctly.*",
            category=UserWarning,
        )
        from pyannote.audio import Pipeline

    cache_dir.mkdir(parents=True, exist_ok=True)
    _ = Pipeline.from_pretrained(
        pipeline_id,
        token=token.strip(),
        cache_dir=str(cache_dir),
    )


def main() -> int:
    project_root = Path(__file__).resolve().parents[2]
    backend_env = project_root / "backend" / ".env"
    if backend_env.exists():
        load_dotenv(backend_env)

    parser = argparse.ArgumentParser(description="Warm up offline ASR/diarization models")
    parser.add_argument("--skip-faster-whisper", action="store_true")
    parser.add_argument("--skip-pyannote", action="store_true")
    parser.add_argument("--model-name", default=os.getenv("WHISPER_MODEL", "medium"))
    parser.add_argument(
        "--model-dir",
        default=os.getenv("FASTER_WHISPER_MODEL_PATH", "storage/models/whisper-medium"),
    )
    parser.add_argument(
        "--cache-dir",
        default=os.getenv("FASTER_WHISPER_CACHE_DIR", "backend/storage/models/hf-cache"),
    )
    parser.add_argument(
        "--pyannote-pipeline",
        default=os.getenv("PYANNOTE_PIPELINE_ID", "pyannote/speaker-diarization-3.1"),
    )
    parser.add_argument("--pyannote-token", default=os.getenv("PYANNOTE_HF_TOKEN", ""))
    parsed = parser.parse_args()
    args = cast_args(parsed)

    model_dir = (project_root / args.model_dir).resolve()
    cache_dir = (project_root / args.cache_dir).resolve()

    print(f"[warmup] python={sys.executable}")
    print(f"[warmup] ssl={ssl.OPENSSL_VERSION}")
    _inject_cert_store()

    try:
        if not args.skip_faster_whisper:
            print(f"[warmup] warming faster-whisper model: {args.model_name}")
            print(f"[warmup] target model dir: {model_dir}")
            print(f"[warmup] cache dir: {cache_dir}")
            _warmup_faster_whisper(args.model_name, model_dir, cache_dir)
            print("[warmup] faster-whisper ready")

        if not args.skip_pyannote:
            print(f"[warmup] warming pyannote pipeline: {args.pyannote_pipeline}")
            _warmup_pyannote(args.pyannote_pipeline, cache_dir, args.pyannote_token)
            print("[warmup] pyannote ready")
    except Exception as exc:
        print(f"[warmup] failed: {exc}")
        return 1

    print("[warmup] done")
    return 0


def cast_args(parsed: Any) -> argparse.Namespace:
    return argparse.Namespace(
        skip_faster_whisper=bool(getattr(parsed, "skip_faster_whisper", False)),
        skip_pyannote=bool(getattr(parsed, "skip_pyannote", False)),
        model_name=str(getattr(parsed, "model_name", "medium")),
        model_dir=str(getattr(parsed, "model_dir", "storage/models/whisper-medium")),
        cache_dir=str(getattr(parsed, "cache_dir", "backend/storage/models/hf-cache")),
        pyannote_pipeline=str(
            getattr(parsed, "pyannote_pipeline", "pyannote/speaker-diarization-3.1")
        ),
        pyannote_token=str(getattr(parsed, "pyannote_token", "")),
    )


if __name__ == "__main__":
    raise SystemExit(main())
