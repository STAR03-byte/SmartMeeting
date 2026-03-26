import { apiClient } from "./client";
import type { MeetingParticipantOut } from "./types";

export type { MeetingParticipantOut } from "./types";

export interface CreateParticipantPayload {
  meeting_id: number;
  user_id: number;
  participant_role?: string;
  attendance_status?: string;
  joined_at?: string | null;
  left_at?: string | null;
}

export async function getMeetingParticipants(meetingId: number): Promise<MeetingParticipantOut[]> {
  const resp = await apiClient.get<MeetingParticipantOut[]>("/api/v1/participants", {
    params: { meeting_id: meetingId },
  });
  return resp.data;
}

export async function createMeetingParticipant(payload: CreateParticipantPayload): Promise<MeetingParticipantOut> {
  const resp = await apiClient.post<MeetingParticipantOut>("/api/v1/participants", payload);
  return resp.data;
}
