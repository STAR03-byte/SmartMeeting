import { apiClient } from "./client";
import type { TaskItem, TaskPriority, TaskStatus } from "./types";

export type { TaskItem, TaskPriority, TaskStatus } from "./types";

export interface ListTasksParams {
  assigneeId?: number;
  meetingId?: number;
  status?: TaskStatus;
  priority?: TaskPriority;
  keyword?: string;
}

export async function getTasks(params: ListTasksParams = {}): Promise<TaskItem[]> {
  const searchParams = new URLSearchParams();
  if (typeof params.assigneeId === "number") {
    searchParams.set("assignee_id", String(params.assigneeId));
  }
  if (typeof params.meetingId === "number") {
    searchParams.set("meeting_id", String(params.meetingId));
  }
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
  const query = searchParams.toString();
  const url = query ? `/api/v1/tasks?${query}` : "/api/v1/tasks";
  const resp = await apiClient.get<TaskItem[]>(url);
  return resp.data;
}

export async function updateTaskStatus(taskId: number, status: TaskStatus): Promise<TaskItem> {
  const resp = await apiClient.patch<TaskItem>(`/api/v1/tasks/${taskId}`, { status });
  return resp.data;
}
