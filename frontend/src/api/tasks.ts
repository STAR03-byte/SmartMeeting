import { apiClient } from "./client";
import type { TaskItem, TaskStatus } from "./types";

export type { TaskItem, TaskStatus } from "./types";

export interface ListTasksParams {
  assigneeId?: number;
  meetingId?: number;
}

export async function getTasks(params: ListTasksParams = {}): Promise<TaskItem[]> {
  const searchParams = new URLSearchParams();
  if (typeof params.assigneeId === "number") {
    searchParams.set("assignee_id", String(params.assigneeId));
  }
  if (typeof params.meetingId === "number") {
    searchParams.set("meeting_id", String(params.meetingId));
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
