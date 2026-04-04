import { apiClient } from './client';

export type InvitationStatus = 'pending' | 'accepted' | 'rejected';

export interface InvitationTeamRef {
  id: number;
  name: string;
}

export interface InvitationUserRef {
  id: number;
  full_name: string;
  email: string;
}

export interface Invitation {
  id: number;
  team_id: number;
  invitee_id: number;
  inviter_id: number;
  status: InvitationStatus;
  created_at: string;
  updated_at: string;
  team?: InvitationTeamRef;
  inviter?: InvitationUserRef;
  invitee?: InvitationUserRef;
  team_name?: string;
  inviter_name?: string;
}

export async function sendInvitation(teamId: number, inviteeId: number): Promise<Invitation> {
  const response = await apiClient.post<Invitation>(`/api/v1/teams/${teamId}/invitations`, {
    invitee_id: inviteeId,
  });
  return response.data;
}

export async function getMyInvitations(): Promise<Invitation[]> {
  const response = await apiClient.get<Invitation[]>('/api/v1/team-invitations/me');
  return response.data;
}

export async function acceptInvitation(id: number): Promise<void> {
  await apiClient.post(`/api/v1/team-invitations/${id}/accept`);
}

export async function rejectInvitation(id: number): Promise<void> {
  await apiClient.post(`/api/v1/team-invitations/${id}/reject`);
}
