"""统一错误类型定义。

提供细粒度错误码和用户友好的错误消息。
"""

from enum import Enum


class ErrorCode(str, Enum):
    """错误码枚举。"""

    # 通用错误 (1xxx)
    BAD_REQUEST = "BAD_REQUEST"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    REQUEST_VALIDATION_ERROR = "REQUEST_VALIDATION_ERROR"
    TOO_MANY_REQUESTS = "TOO_MANY_REQUESTS"
    PAYLOAD_TOO_LARGE = "PAYLOAD_TOO_LARGE"
    CLIENT_ERROR = "CLIENT_ERROR"
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"

    # GPU 相关错误 (2xxx)
    GPU_OUT_OF_MEMORY = "GPU_OUT_OF_MEMORY"
    GPU_NOT_AVAILABLE = "GPU_NOT_AVAILABLE"
    GPU_PROCESSING_FAILED = "GPU_PROCESSING_FAILED"

    # 模型相关错误 (3xxx)
    MODEL_LOADING_TIMEOUT = "MODEL_LOADING_TIMEOUT"
    MODEL_LOADING_FAILED = "MODEL_LOADING_FAILED"
    MODEL_NOT_FOUND = "MODEL_NOT_FOUND"

    # 转写相关错误 (4xxx)
    TRANSCRIPTION_FAILED = "TRANSCRIPTION_FAILED"
    TRANSCRIPTION_TIMEOUT = "TRANSCRIPTION_TIMEOUT"
    AUDIO_PROCESSING_FAILED = "AUDIO_PROCESSING_FAILED"
    INVALID_AUDIO_FORMAT = "INVALID_AUDIO_FORMAT"

    # 说话人分离错误 (5xxx)
    SPEAKER_DIARIZATION_FAILED = "SPEAKER_DIARIZATION_FAILED"
    SPEAKER_DIARIZATION_TIMEOUT = "SPEAKER_DIARIZATION_TIMEOUT"

    # AI 服务错误 (6xxx)
    AI_SERVICE_UNAVAILABLE = "AI_SERVICE_UNAVAILABLE"
    LLM_TIMEOUT = "LLM_TIMEOUT"
    LLM_RATE_LIMITED = "LLM_RATE_LIMITED"

    # 网络错误 (7xxx)
    NETWORK_TIMEOUT = "NETWORK_TIMEOUT"
    NETWORK_ERROR = "NETWORK_ERROR"


class AppError(Exception):
    """应用基础异常类。"""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.INTERNAL_SERVER_ERROR,
        details: dict[str, str] | None = None,
        user_message: str | None = None,
        suggestion: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.user_message = user_message or message
        self.suggestion = suggestion

    def to_dict(self) -> dict[str, object]:
        """转换为字典格式用于 API 响应。"""
        result: dict[str, object] = {
            "detail": self.user_message,
            "error_code": self.error_code.value,
        }
        if self.details:
            result["details"] = self.details
        if self.suggestion:
            result["suggestion"] = self.suggestion
        return result


class GPUError(AppError):
    """GPU 相关错误。"""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.GPU_PROCESSING_FAILED,
        details: dict[str, str] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            user_message="GPU 处理失败",
            suggestion="请尝试使用 CPU 模式或减少音频文件大小",
        )


class GPUOutOfMemoryError(GPUError):
    """GPU 显存不足错误。"""

    def __init__(self, message: str = "GPU 显存不足") -> None:
        super().__init__(
            message=message,
            error_code=ErrorCode.GPU_OUT_OF_MEMORY,
            details={"reason": "out_of_memory"},
        )
        self.user_message = "GPU 显存不足，无法处理当前音频"
        self.suggestion = "建议：1) 使用 CPU 模式；2) 减少音频文件大小；3) 关闭其他 GPU 应用程序"


class GPUNotAvailableError(GPUError):
    """GPU 不可用错误。"""

    def __init__(self, message: str = "GPU 不可用") -> None:
        super().__init__(
            message=message,
            error_code=ErrorCode.GPU_NOT_AVAILABLE,
            details={"reason": "not_available"},
        )
        self.user_message = "GPU 不可用，系统将自动切换到 CPU 模式"
        self.suggestion = "如需使用 GPU 加速，请确保已安装 CUDA 驱动"


class ModelError(AppError):
    """模型相关错误。"""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.MODEL_LOADING_FAILED,
        details: dict[str, str] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            user_message="模型加载失败",
            suggestion="请检查模型配置或联系管理员",
        )


class ModelLoadingTimeoutError(ModelError):
    """模型加载超时错误。"""

    def __init__(self, model_name: str = "unknown", timeout_seconds: int = 60) -> None:
        super().__init__(
            message=f"模型 {model_name} 加载超时（{timeout_seconds}秒）",
            error_code=ErrorCode.MODEL_LOADING_TIMEOUT,
            details={"model": model_name, "timeout_seconds": str(timeout_seconds)},
        )
        self.user_message = f"模型加载超时，请稍后重试"
        self.suggestion = "模型首次加载可能需要较长时间，请耐心等待或联系管理员"


class ModelLoadingFailedError(ModelError):
    """模型加载失败错误。"""

    def __init__(self, model_name: str = "unknown", reason: str = "unknown") -> None:
        super().__init__(
            message=f"模型 {model_name} 加载失败: {reason}",
            error_code=ErrorCode.MODEL_LOADING_FAILED,
            details={"model": model_name, "reason": reason},
        )
        self.user_message = "模型加载失败，系统将使用备用方案"
        self.suggestion = "请检查模型文件是否存在，或联系管理员"


class TranscriptionError(AppError):
    """转写相关错误。"""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.TRANSCRIPTION_FAILED,
        details: dict[str, str] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            user_message="音频转写失败",
            suggestion="请检查音频文件格式或稍后重试",
        )


class TranscriptionTimeoutError(TranscriptionError):
    """转写超时错误。"""

    def __init__(self, audio_duration: float = 0, timeout_seconds: int = 300) -> None:
        super().__init__(
            message=f"转写超时（音频时长: {audio_duration}秒，超时: {timeout_seconds}秒）",
            error_code=ErrorCode.TRANSCRIPTION_TIMEOUT,
            details={"audio_duration": str(audio_duration), "timeout_seconds": str(timeout_seconds)},
        )
        self.user_message = "转写处理超时，请稍后重试"
        self.suggestion = "音频文件较大时处理时间较长，请耐心等待或尝试使用较短的音频文件"


class AudioProcessingError(TranscriptionError):
    """音频处理错误。"""

    def __init__(self, message: str = "音频处理失败") -> None:
        super().__init__(
            message=message,
            error_code=ErrorCode.AUDIO_PROCESSING_FAILED,
            details={"reason": "processing_failed"},
        )
        self.user_message = "音频处理失败"
        self.suggestion = "请检查音频文件是否损坏，或尝试其他格式的音频文件"


class InvalidAudioFormatError(TranscriptionError):
    """无效音频格式错误。"""

    def __init__(self, format_name: str = "unknown") -> None:
        super().__init__(
            message=f"不支持的音频格式: {format_name}",
            error_code=ErrorCode.INVALID_AUDIO_FORMAT,
            details={"format": format_name},
        )
        self.user_message = f"不支持的音频格式: {format_name}"
        self.suggestion = "支持的格式: MP3, WAV, M4A, FLAC, OGG, WEBM"


class SpeakerDiarizationError(AppError):
    """说话人分离错误。"""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.SPEAKER_DIARIZATION_FAILED,
        details: dict[str, str] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            user_message="说话人识别失败",
            suggestion="说话人识别功能暂时不可用，转写结果将不包含说话人信息",
        )


class NetworkError(AppError):
    """网络相关错误。"""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.NETWORK_ERROR,
        details: dict[str, str] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            user_message="网络连接失败",
            suggestion="请检查网络连接后重试",
        )


class NetworkTimeoutError(NetworkError):
    """网络超时错误。"""

    def __init__(self, operation: str = "请求", timeout_seconds: int = 30) -> None:
        super().__init__(
            message=f"{operation}超时（{timeout_seconds}秒）",
            error_code=ErrorCode.NETWORK_TIMEOUT,
            details={"operation": operation, "timeout_seconds": str(timeout_seconds)},
        )
        self.user_message = f"{operation}超时，请稍后重试"
        self.suggestion = "网络响应较慢，请稍后重试或检查网络连接"