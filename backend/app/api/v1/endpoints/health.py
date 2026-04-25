"""系统健康自检端点 - 提供运行时状态检查。"""

import os
import shutil
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db

router = APIRouter(prefix="/health", tags=["health"])


def _check_gpu() -> dict[str, Any]:
    """检查GPU可用性。"""
    try:
        import torch

        cuda_available = torch.cuda.is_available()
        device_count = torch.cuda.device_count() if cuda_available else 0
        device_name = torch.cuda.get_device_name(0) if cuda_available else None
        return {
            "available": cuda_available,
            "device_count": device_count,
            "device_name": device_name,
            "torch_version": torch.__version__,
        }
    except ImportError:
        return {"available": False, "error": "torch not installed"}
    except Exception as e:
        return {"available": False, "error": str(e)}


def _check_faster_whisper() -> dict[str, Any]:
    """检查faster-whisper模型状态。"""
    try:
        model_path = settings.faster_whisper_model_path.strip() or settings.whisper_model
        # 解析为绝对路径
        if not Path(model_path).is_absolute():
            project_root = Path(__file__).resolve().parents[3]
            model_path = str((project_root / model_path).resolve())

        path_exists = Path(model_path).exists()
        is_local_only = settings.faster_whisper_local_files_only

        # 尝试加载验证
        load_status = "unknown"
        try:
            from faster_whisper import WhisperModel

            _ = WhisperModel(
                model_path,
                device="cuda" if _check_gpu()["available"] else "cpu",
                local_files_only=True,
            )
            load_status = "ok"
        except Exception as e:
            load_status = f"failed: {e}"

        return {
            "model_path": model_path,
            "path_exists": path_exists,
            "local_files_only": is_local_only,
            "load_status": load_status,
            "require_gpu": settings.faster_whisper_require_gpu,
        }
    except Exception as e:
        return {"error": str(e)}


def _check_pyannote() -> dict[str, Any]:
    """检查pyannote说话人分离模型状态。"""
    try:
        cache_dir = settings.pyannote_cache_dir
        pipeline_id = settings.pyannote_pipeline_id
        token_configured = bool(settings.pyannote_hf_token.strip())

        # 检查缓存目录
        cache_path = Path(cache_dir)
        cache_exists = cache_path.exists()

        # 尝试懒加载检测
        load_status = "unknown"
        try:
            import warnings

            with warnings.catch_warnings():
                warnings.filterwarnings(
                    "ignore", message=r".*torchcodec.*", category=UserWarning
                )
                from pyannote.audio import Pipeline

                _ = Pipeline.from_pretrained(
                    pipeline_id,
                    token=settings.pyannote_hf_token or None,
                    cache_dir=str(cache_path),
                )
                load_status = "ok"
        except Exception as e:
            load_status = f"failed: {e}"

        return {
            "pipeline_id": pipeline_id,
            "cache_dir": str(cache_path),
            "cache_exists": cache_exists,
            "token_configured": token_configured,
            "local_files_only": settings.pyannote_local_files_only,
            "load_status": load_status,
            "require_gpu": settings.pyannote_require_gpu,
        }
    except Exception as e:
        return {"error": str(e)}


def _check_database(db: Session) -> dict[str, Any]:
    """检查数据库连接。"""
    try:
        from sqlalchemy import text

        result = db.execute(text("SELECT 1"))
        _ = result.scalar()
        return {"connected": True, "backend": settings.db_backend}
    except Exception as e:
        return {"connected": False, "error": str(e)}


def _check_private_deployment() -> dict[str, Any]:
    """Check private deployment prerequisites without loading heavy models."""
    storage_path = Path("backend/storage/audio")
    jwt_is_default = settings.jwt_secret_key in {"change-me-in-production", "dev-secret-key"}
    return {
        "jwt_secret_configured": bool(settings.jwt_secret_key.strip()) and not jwt_is_default,
        "jwt_secret_uses_default": jwt_is_default,
        "ffmpeg_available": shutil.which("ffmpeg") is not None,
        "storage_dir": str(storage_path),
        "storage_dir_exists": storage_path.exists(),
        "storage_dir_writable": os.access(storage_path, os.W_OK) if storage_path.exists() else False,
        "llm_provider": settings.llm_provider,
        "llm_configured": bool(settings.llm_api_key.strip()) or settings.llm_provider in {"mock", "none"},
        "whisper_allow_mock_fallback": settings.whisper_allow_mock_fallback,
    }


@router.get("/status")
def health_status(db: Session = Depends(get_db)) -> dict[str, Any]:
    """系统整体健康状态检查。"""
    return {
        "status": "ok",
        "environment": settings.app_env,
        "gpu": _check_gpu(),
        "faster_whisper": _check_faster_whisper(),
        "pyannote": _check_pyannote(),
        "database": _check_database(db),
        "private_deployment": _check_private_deployment(),
        "config": {
            "whisper_device": settings.whisper_device,
            "enable_speaker_diarization": settings.enable_speaker_diarization,
            "use_faster_whisper": settings.use_faster_whisper,
        },
    }


@router.get("/ready")
def readiness_check() -> dict[str, str]:
    """Kubernetes风格就绪检查。"""
    return {"status": "ready"}


@router.get("/live")
def liveness_check() -> dict[str, str]:
    """Kubernetes风格存活检查。"""
    return {"status": "alive"}


@router.get("/preflight")
def preflight_check(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Lightweight deployment readiness check for self-hosted installs."""
    database = _check_database(db)
    deployment = _check_private_deployment()
    checks = {
        "database": bool(database.get("connected")),
        "jwt_secret": bool(deployment.get("jwt_secret_configured")),
        "ffmpeg": bool(deployment.get("ffmpeg_available")),
        "storage": bool(deployment.get("storage_dir_exists")) and bool(deployment.get("storage_dir_writable")),
    }
    return {
        "status": "ok" if all(checks.values()) else "degraded",
        "checks": checks,
        "database": database,
        "private_deployment": deployment,
    }
