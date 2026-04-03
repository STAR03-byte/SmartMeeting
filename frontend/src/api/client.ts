import axios from "axios";

export interface ApiErrorResponse {
  detail?: string | Array<{ msg?: string }>;
  error_code?: string;
  suggestion?: string;
  errors?: Array<{ loc?: string[]; msg?: string }>;
}

export const apiClient = axios.create({
  baseURL: "/",
  timeout: 600000,
});

const ERROR_CODE_MESSAGES: Record<string, string> = {
  BAD_REQUEST: "请求参数不合法，请检查后重试",
  UNAUTHORIZED: "登录已失效，请重新登录",
  FORBIDDEN: "当前账号无权限执行该操作",
  NOT_FOUND: "请求的资源不存在或已被删除",
  CONFLICT: "请求冲突，请刷新后重试",
  REQUEST_VALIDATION_ERROR: "请求参数校验失败，请检查输入",
  CLIENT_ERROR: "请求失败，请稍后重试",
  INTERNAL_SERVER_ERROR: "服务暂时不可用，请稍后重试",

  GPU_OUT_OF_MEMORY: "GPU 显存不足，无法处理当前音频",
  GPU_NOT_AVAILABLE: "GPU 不可用，系统将自动切换到 CPU 模式",
  GPU_PROCESSING_FAILED: "GPU 处理失败，请尝试使用 CPU 模式",

  MODEL_LOADING_TIMEOUT: "模型加载超时，请稍后重试",
  MODEL_LOADING_FAILED: "模型加载失败，系统将使用备用方案",
  MODEL_NOT_FOUND: "模型文件不存在，请联系管理员",

  TRANSCRIPTION_FAILED: "音频转写失败，请检查音频文件格式",
  TRANSCRIPTION_TIMEOUT: "转写处理超时，请稍后重试",
  AUDIO_PROCESSING_FAILED: "音频处理失败，请检查音频文件是否损坏",
  INVALID_AUDIO_FORMAT: "不支持的音频格式，支持的格式: MP3, WAV, M4A, FLAC, OGG, WEBM",

  SPEAKER_DIARIZATION_FAILED: "说话人识别失败，转写结果将不包含说话人信息",
  SPEAKER_DIARIZATION_TIMEOUT: "说话人识别超时，请稍后重试",

  AI_SERVICE_UNAVAILABLE: "AI 服务暂时不可用，请稍后重试",
  LLM_TIMEOUT: "AI 处理超时，请稍后重试",
  LLM_RATE_LIMITED: "请求过于频繁，请稍后重试",

  NETWORK_TIMEOUT: "网络连接超时，请检查网络后重试",
  NETWORK_ERROR: "网络连接失败，请检查网络设置",
};

const ERROR_SUGGESTIONS: Record<string, string> = {
  GPU_OUT_OF_MEMORY: "建议：1) 使用 CPU 模式；2) 减少音频文件大小；3) 关闭其他 GPU 应用程序",
  GPU_NOT_AVAILABLE: "如需使用 GPU 加速，请确保已安装 CUDA 驱动",
  MODEL_LOADING_TIMEOUT: "模型首次加载可能需要较长时间，请耐心等待或联系管理员",
  MODEL_LOADING_FAILED: "请检查模型文件是否存在，或联系管理员",
  TRANSCRIPTION_TIMEOUT: "音频文件较大时处理时间较长，请耐心等待或尝试使用较短的音频文件",
  INVALID_AUDIO_FORMAT: "支持的格式: MP3, WAV, M4A, FLAC, OGG, WEBM",
  SPEAKER_DIARIZATION_FAILED: "说话人识别功能暂时不可用，转写结果将不包含说话人信息",
  AI_SERVICE_UNAVAILABLE: "系统将自动使用备用方案处理您的请求，或请稍后重试",
  NETWORK_TIMEOUT: "网络响应较慢，请稍后重试或检查网络连接",
};

function getErrorCodeMessage(errorCode?: string): string | undefined {
  if (typeof errorCode !== "string" || errorCode.length === 0) {
    return undefined;
  }
  return ERROR_CODE_MESSAGES[errorCode];
}

function getErrorSuggestion(errorCode?: string): string | undefined {
  if (typeof errorCode !== "string" || errorCode.length === 0) {
    return undefined;
  }
  return ERROR_SUGGESTIONS[errorCode];
}

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("smartmeeting_access_token");
  if (token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export function getApiErrorMessage(error: unknown): string {
  if (axios.isAxiosError<ApiErrorResponse>(error)) {
    const detail = error.response?.data?.detail;
    const errorCode = error.response?.data?.error_code;
    const suggestion = error.response?.data?.suggestion;

    const errorCodeMessage = getErrorCodeMessage(errorCode);
    const errorSuggestion = suggestion || getErrorSuggestion(errorCode);

    if (typeof detail === "string") {
      let message = detail;
      if (errorSuggestion) {
        message += `\n\n建议：${errorSuggestion}`;
      }
      return message;
    }

    if (Array.isArray(detail) && detail.length > 0) {
      const firstMsg = detail[0]?.msg;
      if (typeof firstMsg === "string") {
        return firstMsg;
      }
    }

    if (errorCodeMessage) {
      let message = errorCodeMessage;
      if (errorSuggestion) {
        message += `\n\n建议：${errorSuggestion}`;
      }
      return message;
    }

    if (error.code === "ECONNABORTED") {
      return "请求超时，请检查网络连接后重试";
    }

    if (error.code === "ERR_NETWORK") {
      return "网络连接失败，请检查网络设置";
    }

    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "请求失败，请稍后重试";
}

export function isGPUError(error: unknown): boolean {
  if (axios.isAxiosError<ApiErrorResponse>(error)) {
    const errorCode = error.response?.data?.error_code;
    return typeof errorCode === "string" && errorCode.includes("GPU");
  }
  return false;
}

export function isModelError(error: unknown): boolean {
  if (axios.isAxiosError<ApiErrorResponse>(error)) {
    const errorCode = error.response?.data?.error_code;
    return typeof errorCode === "string" && errorCode.includes("MODEL");
  }
  return false;
}

export function isTranscriptionError(error: unknown): boolean {
  if (axios.isAxiosError<ApiErrorResponse>(error)) {
    const errorCode = error.response?.data?.error_code;
    if (typeof errorCode !== "string") {
      return false;
    }
    return errorCode.includes("TRANSCRIPTION") || errorCode.includes("AUDIO");
  }
  return false;
}

export function isNetworkError(error: unknown): boolean {
  if (axios.isAxiosError<ApiErrorResponse>(error)) {
    const errorCode = error.response?.data?.error_code;
    if (typeof errorCode === "string") {
      if (errorCode.includes("NETWORK") || errorCode.includes("TIMEOUT")) {
        return true;
      }
    }
    return error.code === "ECONNABORTED" || error.code === "ERR_NETWORK";
  }
  return false;
}
