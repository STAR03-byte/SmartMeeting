"""GPU 资源管理服务 - 监控显存、控制并发、追踪进度。"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class ProcessingStatus(str, Enum):
    """处理状态枚举。"""

    IDLE = "idle"
    QUEUED = "queued"
    LOADING_MODELS = "loading_models"
    PROCESSING = "processing"
    SEGMENTING = "segmenting"
    TRANSCRIBING = "transcribing"
    DIARIZING = "diarizing"
    MERGING = "merging"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ProgressInfo:
    """处理进度信息。"""

    job_id: str
    status: ProcessingStatus
    progress: float  # 0.0 - 1.0
    message: str
    started_at: float
    current_chunk: int = 0
    total_chunks: int = 1
    error: Optional[str] = None
    completed_at: Optional[float] = None


@dataclass
class GPUInfo:
    """GPU 信息。"""

    available: bool
    device_name: str = ""
    total_memory_mb: int = 0
    used_memory_mb: int = 0
    free_memory_mb: int = 0


class GPUManager:
    """GPU 资源管理器 - 单例模式。"""

    _instance: Optional["GPUManager"] = None
    _lock = asyncio.Lock()
    _initialized: bool

    def __new__(cls) -> "GPUManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True

        # 并发控制
        self._processing_lock = asyncio.Lock()
        self._current_job: Optional[str] = None
        self._queue: asyncio.Queue[str] = asyncio.Queue()

        # 进度追踪
        self._progress: dict[str, ProgressInfo] = {}

        # GPU 状态
        self._gpu_available = False
        self._torch_available = False
        self._device_name = "CPU"

        # 回调函数
        self._progress_callbacks: list[Callable[[ProgressInfo], None]] = []

        # 检测 GPU
        self._detect_gpu()

    def _detect_gpu(self) -> None:
        """检测 GPU 可用性。"""
        try:
            import torch

            self._torch_available = True
            if torch.cuda.is_available():
                self._gpu_available = True
                self._device_name = torch.cuda.get_device_name(0)
                logger.info(f"GPU detected: {self._device_name}")
            else:
                logger.info("No GPU available, using CPU")
        except ImportError:
            self._torch_available = False
            logger.info("PyTorch not installed, GPU features disabled")

    def get_gpu_info(self) -> GPUInfo:
        """获取 GPU 信息。"""
        if not self._torch_available or not self._gpu_available:
            return GPUInfo(available=False)

        try:
            import torch

            total_memory = torch.cuda.get_device_properties(0).total_memory // (1024 * 1024)
            reserved = torch.cuda.memory_reserved(0) // (1024 * 1024)
            allocated = torch.cuda.memory_allocated(0) // (1024 * 1024)
            free = total_memory - reserved

            return GPUInfo(
                available=True,
                device_name=self._device_name,
                total_memory_mb=total_memory,
                used_memory_mb=allocated,
                free_memory_mb=free,
            )
        except Exception as e:
            logger.error(f"Failed to get GPU info: {e}")
            return GPUInfo(available=False)

    def clear_gpu_cache(self) -> None:
        """清理 GPU 缓存。"""
        if not self._torch_available or not self._gpu_available:
            return

        try:
            import torch

            torch.cuda.empty_cache()
            logger.debug("GPU cache cleared")
        except Exception as e:
            logger.error(f"Failed to clear GPU cache: {e}")

    async def acquire_processing_lock(
        self, job_id: str, description: str = "Processing audio"
    ) -> bool:
        """获取处理锁。

        Args:
            job_id: 任务 ID
            description: 任务描述

        Returns:
            是否成功获取锁
        """
        # 如果当前有任务在处理，加入队列
        if self._current_job is not None and self._current_job != job_id:
            logger.info(f"Job {job_id} queued, current job: {self._current_job}")
            await self._queue.put(job_id)
            self._progress[job_id] = ProgressInfo(
                job_id=job_id,
                status=ProcessingStatus.QUEUED,
                progress=0.0,
                message=f"Queued behind {self._current_job}",
                started_at=time.time(),
            )
            self._notify_progress(self._progress[job_id])

            # 等待轮到这个任务
            while self._current_job != job_id:
                await asyncio.sleep(0.5)

        # 获取锁
        acquired = await self._processing_lock.acquire()
        if acquired:
            self._current_job = job_id
            self._progress[job_id] = ProgressInfo(
                job_id=job_id,
                status=ProcessingStatus.LOADING_MODELS,
                progress=0.0,
                message=description,
                started_at=time.time(),
            )
            self._notify_progress(self._progress[job_id])
            logger.info(f"Job {job_id} acquired processing lock")

        return acquired

    async def release_processing_lock(self, job_id: str) -> None:
        """释放处理锁。"""
        if self._current_job != job_id:
            logger.warning(f"Job {job_id} tried to release lock it doesn't own")
            return

        # 清理 GPU 缓存
        self.clear_gpu_cache()

        # 更新状态
        if job_id in self._progress:
            self._progress[job_id].completed_at = time.time()

        # 释放锁
        self._processing_lock.release()
        self._current_job = None
        logger.info(f"Job {job_id} released processing lock")

        # 处理队列中的下一个任务
        if not self._queue.empty():
            next_job_id = await self._queue.get()
            self._current_job = next_job_id
            logger.info(f"Next job in queue: {next_job_id}")

    def update_progress(
        self,
        job_id: str,
        status: ProcessingStatus,
        progress: float,
        message: str,
        current_chunk: int = 0,
        total_chunks: int = 1,
        error: Optional[str] = None,
    ) -> None:
        """更新处理进度。"""
        if job_id not in self._progress:
            self._progress[job_id] = ProgressInfo(
                job_id=job_id,
                status=status,
                progress=progress,
                message=message,
                started_at=time.time(),
                current_chunk=current_chunk,
                total_chunks=total_chunks,
                error=error,
            )
        else:
            self._progress[job_id].status = status
            self._progress[job_id].progress = progress
            self._progress[job_id].message = message
            self._progress[job_id].current_chunk = current_chunk
            self._progress[job_id].total_chunks = total_chunks
            if error:
                self._progress[job_id].error = error

        self._notify_progress(self._progress[job_id])

    def get_progress(self, job_id: str) -> Optional[ProgressInfo]:
        """获取任务进度。"""
        return self._progress.get(job_id)

    def get_all_progress(self) -> dict[str, ProgressInfo]:
        """获取所有任务进度。"""
        return self._progress.copy()

    def register_progress_callback(self, callback: Callable[[ProgressInfo], None]) -> None:
        """注册进度回调函数。"""
        self._progress_callbacks.append(callback)

    def _notify_progress(self, progress: ProgressInfo) -> None:
        """通知进度更新。"""
        for callback in self._progress_callbacks:
            try:
                callback(progress)
            except Exception as e:
                logger.error(f"Progress callback error: {e}")

    @staticmethod
    def generate_job_id() -> str:
        """生成任务 ID。"""
        return str(uuid4())

    @property
    def is_processing(self) -> bool:
        """是否有任务正在处理。"""
        return self._current_job is not None

    @property
    def queue_size(self) -> int:
        """队列中等待的任务数。"""
        return self._queue.qsize()


# 全局单例
gpu_manager = GPUManager()


def get_gpu_manager() -> GPUManager:
    """获取 GPU 管理器单例。"""
    return gpu_manager