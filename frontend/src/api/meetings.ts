import { apiClient } from "./client";

export interface Meeting {
  id: number;
  title: string;
  description: string | null;
  organizer_id: number;
  status: string;
  summary: string | null;
  postprocessed_at: string | null;
  postprocess_version: string | null;
  created_at: string;
  updated_at: string;
}

export interface Transcript {
  id: number;
  meeting_id: number;
  speaker_user_id: number | null;
  speaker_name: string | null;
  segment_index: number;
  source: string;
  content: string;
  created_at: string;
  updated_at: string;
}

export interface TaskItem {
  id: number;
  meeting_id: number;
  transcript_id: number | null;
  title: string;
  description: string | null;
  assignee_id: number | null;
  priority: string;
  status: string;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export async function getMeetings(): Promise<Meeting[]> {
  const resp = await apiClient.get<Meeting[]>("/api/v1/meetings");
  return resp.data;
}

export async function getMeeting(meetingId: number): Promise<Meeting> {
  const resp = await apiClient.get<Meeting>(`/api/v1/meetings/${meetingId}`);
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

export async function triggerPostprocess(meetingId: number): Promise<void> {
  await apiClient.post(`/api/v1/meetings/${meetingId}/postprocess`);
}

export async function uploadMeetingAudio(meetingId: number, file: File): Promise<void> {
  const formData = new FormData();
  formData.append("file", file);
  await apiClient.post(`/api/v1/meetings/${meetingId}/audio`, formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
}

export async function transcribeMeetingAudio(meetingId: number): Promise<void> {
  await apiClient.post(`/api/v1/meetings/${meetingId}/audio/transcribe`);
}
