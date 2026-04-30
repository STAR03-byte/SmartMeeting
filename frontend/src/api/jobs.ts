import { apiClient } from "./client";
import type { ProcessingJob, ProcessingJobResult } from "./types";

function resolveApiUrl(path: string): URL {
  const baseURL = apiClient.defaults.baseURL ?? "/";
  const base = new URL(baseURL, window.location.origin);
  return new URL(path.replace(/^\//, ""), base);
}

function getAccessToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  const sessionToken = window.sessionStorage.getItem("smartmeeting_access_token");
  return sessionToken || window.localStorage.getItem("smartmeeting_access_token");
}

export async function getJobStatus(jobId: string): Promise<ProcessingJob> {
  const resp = await apiClient.get<ProcessingJob>(`/api/v1/jobs/${jobId}`);
  return resp.data;
}

export async function getJobResult(jobId: string): Promise<ProcessingJobResult> {
  const resp = await apiClient.get<ProcessingJobResult>(`/api/v1/jobs/${jobId}/result`);
  return resp.data;
}

export async function cancelJob(jobId: string): Promise<void> {
  await apiClient.post(`/api/v1/jobs/${jobId}/cancel`);
}

export function subscribeJobEvents(jobId: string): EventSource {
  if (typeof window === "undefined") {
    throw new Error("EventSource 只能在浏览器环境中创建");
  }

  const url = resolveApiUrl(`/api/v1/jobs/${jobId}/events`);
  const token = getAccessToken();
  if (token) {
    url.searchParams.set("access_token", token);
  }
  return new EventSource(url.toString());
}
