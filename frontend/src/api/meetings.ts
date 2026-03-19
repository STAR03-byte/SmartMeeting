import { apiClient } from "./client";
import type {
  Meeting,
  MeetingAudio,
  MeetingCreatePayload,
  MeetingDetail,
  MeetingListParams,
  MeetingPostprocessResult,
  TaskItem,
  Transcript,
} from "./types";

export type { Meeting, MeetingAudio, MeetingCreatePayload, MeetingDetail, MeetingListParams, MeetingPostprocessResult, TaskItem, Transcript } from "./types";

export async function getMeetings(params?: MeetingListParams): Promise<Meeting[]> {
  const resp = await apiClient.get<Meeting[]>("/api/v1/meetings", { params });
  return resp.data;
}

export async function createMeeting(payload: MeetingCreatePayload): Promise<Meeting> {
  const resp = await apiClient.post<Meeting>("/api/v1/meetings", payload);
  return resp.data;
}

export async function deleteMeeting(meetingId: number): Promise<void> {
  await apiClient.delete(`/api/v1/meetings/${meetingId}`);
}

export async function getMeeting(meetingId: number): Promise<MeetingDetail> {
  const resp = await apiClient.get<MeetingDetail>(`/api/v1/meetings/${meetingId}`);
  return resp.data;
}

export async function getMeetingTranscripts(meetingId: number): Promise<Transcript[]> {
  const resp = await apiClient.get<Transcript[]>(`/api/v1/transcripts?meeting_id=${meetingId}`);
  return resp.data;
}

export async function getTasksByAssignee(assigneeId: number): Promise<TaskItem[]> {
  const resp = await apiClient.get<TaskItem[]>(`/api/v1/tasks?assignee_id=${assigneeId}`);
  return resp.data;
}

export async function getTasksByMeeting(meetingId: number): Promise<TaskItem[]> {
  const resp = await apiClient.get<TaskItem[]>(`/api/v1/tasks?meeting_id=${meetingId}`);
  return resp.data;
}

export async function triggerPostprocess(meetingId: number): Promise<MeetingPostprocessResult> {
  const resp = await apiClient.post<MeetingPostprocessResult>(`/api/v1/meetings/${meetingId}/postprocess`);
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
