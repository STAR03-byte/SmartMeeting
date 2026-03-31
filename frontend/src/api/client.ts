import axios from "axios";

export interface ApiErrorResponse {
  detail?: string | Array<{ msg?: string }>;
  error_code?: string;
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
  AI_SERVICE_UNAVAILABLE: "AI 服务暂时不可用，请稍后重试",
  INTERNAL_SERVER_ERROR: "服务暂时不可用，请稍后重试",
};

function getErrorCodeMessage(errorCode?: string): string | undefined {
  if (typeof errorCode !== "string" || errorCode.length === 0) {
    return undefined;
  }
  return ERROR_CODE_MESSAGES[errorCode];
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
    const errorCodeMessage = getErrorCodeMessage(error.response?.data?.error_code);
    if (typeof detail === "string") {
      return detail;
    }
    if (Array.isArray(detail) && detail.length > 0) {
      const firstMsg = detail[0]?.msg;
      if (typeof firstMsg === "string") {
        return firstMsg;
      }
    }
    if (errorCodeMessage) {
      return errorCodeMessage;
    }
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "请求失败，请稍后重试";
}
