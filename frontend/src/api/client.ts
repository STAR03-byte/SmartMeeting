import axios from "axios";

export interface ApiErrorResponse {
  detail?: string | Array<{ msg?: string }>;
  error_code?: string;
}

export const apiClient = axios.create({
  baseURL: "/",
  timeout: 600000,
});

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
    if (typeof detail === "string") {
      return detail;
    }
    if (Array.isArray(detail) && detail.length > 0) {
      const firstMsg = detail[0]?.msg;
      if (typeof firstMsg === "string") {
        return firstMsg;
      }
    }
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "请求失败，请稍后重试";
}
