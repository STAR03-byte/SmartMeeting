import { apiClient } from "./client";
import type {
  Meeting,
  MeetingAudio,
  MeetingCreatePayload,
  MeetingDetail,
  MeetingListParams,
  MeetingListResult,
  MeetingPostprocessResult,
  MeetingShareCreatePayload,
  MeetingShareCreateResult,
  ProcessingJob,
  SharedMeetingDetail,
  MeetingStatus,
  TaskCreatePayload,
  TaskItem,
  TaskListResult,
  Transcript,
} from "./types";

export type { Meeting, MeetingAudio, MeetingCreatePayload, MeetingDetail, MeetingListParams, MeetingListResult, MeetingPostprocessResult, MeetingShareCreatePayload, MeetingShareCreateResult, SharedMeetingDetail, TaskCreatePayload, TaskItem, Transcript } from "./types";

export interface MeetingUpdatePayload {
  title?: string;
  description?: string | null;
  scheduled_start_at?: string | null;
  scheduled_end_at?: string | null;
  actual_start_at?: string | null;
  actual_end_at?: string | null;
  location?: string | null;
  status?: MeetingStatus;
}

export interface MeetingExportPayload {
  format?: "txt" | "md";
}

export interface MeetingExportResult {
  meeting_id: number;
  format: "txt" | "md";
  filename: string;
  content: string;
}

export async function getMeetings(params?: MeetingListParams): Promise<MeetingListResult> {
  const resp = await apiClient.get<MeetingListResult>("/api/v1/meetings", { params });
  return resp.data;
}

export async function createMeeting(payload: MeetingCreatePayload): Promise<Meeting> {
  const resp = await apiClient.post<Meeting>("/api/v1/meetings", payload);
  return resp.data;
}

export interface MeetingClearContentPayload {
  clear_transcripts?: boolean;
  clear_tasks?: boolean;
  clear_summary?: boolean;
  clear_audios?: boolean;
  reset_status?: boolean;
}

export async function updateMeeting(meetingId: number, data: MeetingUpdatePayload): Promise<Meeting> {
  const resp = await apiClient.patch<Meeting>(`/api/v1/meetings/${meetingId}`, data);
  return resp.data;
}

export async function deleteMeeting(meetingId: number): Promise<void> {
  await apiClient.delete(`/api/v1/meetings/${meetingId}`);
}

export async function clearMeetingContent(
  meetingId: number,
  payload: MeetingClearContentPayload,
): Promise<Meeting> {
  const resp = await apiClient.post<Meeting>(`/api/v1/meetings/${meetingId}/clear-content`, payload);
  return resp.data;
}

export async function getMeeting(meetingId: number): Promise<MeetingDetail> {
  const resp = await apiClient.get<MeetingDetail>(`/api/v1/meetings/${meetingId}`);
  return resp.data;
}

export async function getMeetingTranscripts(meetingId: number): Promise<Transcript[]> {
  const resp = await apiClient.get<Transcript[]>(`/api/v1/transcripts?meeting_id=${meetingId}`);
  return resp.data;
}

export async function deleteTranscript(transcriptId: number): Promise<void> {
  await apiClient.delete(`/api/v1/transcripts/${transcriptId}`);
}

export async function getTasksByAssignee(assigneeId: number): Promise<TaskListResult> {
  const resp = await apiClient.get<TaskListResult>("/api/v1/tasks", {
    params: { assignee_id: assigneeId },
  });
  return resp.data;
}

export async function getTasksByMeeting(meetingId: number): Promise<TaskListResult> {
  const resp = await apiClient.get<TaskListResult>("/api/v1/tasks", {
    params: { meeting_id: meetingId },
  });
  return resp.data;
}

export async function triggerPostprocess(meetingId: number): Promise<MeetingPostprocessResult> {
  const resp = await apiClient.post<MeetingPostprocessResult>(`/api/v1/meetings/${meetingId}/postprocess`);
  return resp.data;
}

export async function triggerPostprocessAsync(meetingId: number): Promise<ProcessingJob> {
  const resp = await apiClient.post<ProcessingJob>(
    `/api/v1/meetings/${meetingId}/postprocess`,
    null,
    { params: { async_mode: true } },
  );
  return resp.data;
}

export async function uploadMeetingAudio(meetingId: number, file: File): Promise<MeetingAudio> {
  const formData = new FormData();
  formData.append("file", file);
  const resp = await apiClient.post<MeetingAudio>(`/api/v1/meetings/${meetingId}/audio`, formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return resp.data;
}

export async function transcribeMeetingAudio(meetingId: number): Promise<Transcript> {
  const resp = await apiClient.post<Transcript>(`/api/v1/meetings/${meetingId}/audio/transcribe`);
  return resp.data;
}

export async function transcribeMeetingAudioAsync(meetingId: number): Promise<ProcessingJob> {
  const resp = await apiClient.post<ProcessingJob>(
    `/api/v1/meetings/${meetingId}/audio/transcribe`,
    null,
    { params: { async_mode: true } },
  );
  return resp.data;
}

export async function exportMeetingSummary(
  meetingId: number,
  payload: MeetingExportPayload = {},
): Promise<MeetingExportResult> {
  const resp = await apiClient.post<MeetingExportResult>(`/api/v1/meetings/${meetingId}/export`, {
    format: payload.format ?? "txt",
  });
  return resp.data;
}

export async function createMeetingShareLink(
  meetingId: number,
  payload?: MeetingShareCreatePayload,
): Promise<MeetingShareCreateResult> {
  const url = `/api/v1/meetings/${meetingId}/share`;
  const resp = payload
    ? await apiClient.post<MeetingShareCreateResult>(url, payload)
    : await apiClient.post<MeetingShareCreateResult>(url);
  return resp.data;
}

export async function revokeMeetingShareLink(meetingId: number): Promise<void> {
  await apiClient.delete(`/api/v1/meetings/${meetingId}/share`);
}

export async function listMeetingAudios(meetingId: number): Promise<MeetingAudio[]> {
  const resp = await apiClient.get<MeetingAudio[]>(`/api/v1/meetings/${meetingId}/audios`);
  return resp.data;
}

export async function downloadAudio(audioId: number, meetingId: number): Promise<Blob> {
  const resp = await apiClient.get(`/api/v1/meetings/${meetingId}/audios/${audioId}/download`, {
    responseType: "blob",
  });
  return resp.data;
}

export async function streamAudio(audioId: number, meetingId: number): Promise<Blob> {
  const resp = await apiClient.get(`/api/v1/meetings/${meetingId}/audios/${audioId}/stream`, {
    responseType: "blob",
  });
  return resp.data;
}

export async function getSharedMeeting(shareToken: string): Promise<SharedMeetingDetail> {
  const resp = await apiClient.get<SharedMeetingDetail>(`/api/v1/shared/meetings/${shareToken}`);
  return resp.data;
}

export async function createTask(payload: TaskCreatePayload): Promise<TaskItem> {
  const resp = await apiClient.post<TaskItem>("/api/v1/tasks", payload);
  return resp.data;
}
