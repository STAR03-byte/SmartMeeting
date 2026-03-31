import { apiClient } from "./client";
import type { TaskItem, TaskListParams, TaskListResult, TaskPriority, TaskStatus } from "./types";

export type { TaskItem, TaskListParams, TaskListResult, TaskPriority, TaskStatus } from "./types";

export async function getTasks(params: TaskListParams = {}): Promise<TaskListResult> {
  const searchParams = new URLSearchParams();
  if (typeof params.assignee_id === "number") searchParams.set("assignee_id", String(params.assignee_id));
  if (typeof params.meeting_id === "number") searchParams.set("meeting_id", String(params.meeting_id));
  if (typeof params.status === "string") {
    searchParams.set("status", params.status);
  }
  if (typeof params.priority === "string") {
    searchParams.set("priority", params.priority);
  }
  if (typeof params.keyword === "string") {
    const normalizedKeyword = params.keyword.trim();
    if (normalizedKeyword.length > 0) {
      searchParams.set("keyword", normalizedKeyword);
    }
  }
  if (typeof params.sort_by === "string" && params.sort_by.trim().length > 0) {
    searchParams.set("sort_by", params.sort_by);
  }
  if (typeof params.limit === "number") {
    searchParams.set("limit", String(params.limit));
  }
  if (typeof params.offset === "number") {
    searchParams.set("offset", String(params.offset));
  }
  const query = searchParams.toString();
  const url = query ? `/api/v1/tasks?${query}` : "/api/v1/tasks";
  const resp = await apiClient.get<TaskListResult>(url);
  return resp.data;
}

export async function updateTaskStatus(taskId: number, status: TaskStatus): Promise<TaskItem> {
  const resp = await apiClient.patch<TaskItem>(`/api/v1/tasks/${taskId}`, { status });
  return resp.data;
}
