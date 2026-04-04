import { apiClient } from './client';

export interface TeamCreate {
  name: string;
  description?: string;
  is_public?: boolean;
}

export interface Team {
  id: number;
  name: string;
  description: string | null;
  is_public: boolean;
  owner_id: number;
  created_at: string;
  updated_at: string;
  my_role?: string;
}

export interface TeamMember {
  user_id: number;
  user_name: string;
  full_name: string;
  email: string;
  role: string;
  joined_at: string;
  invitation_status?: 'pending' | 'accepted' | 'rejected';
}

export const getTeams = async () => {
  const response = await apiClient.get<Team[]>('/api/v1/teams');
  return response.data;
};

export const getPublicTeams = async () => {
  const response = await apiClient.get<Team[]>('/api/v1/teams/public');
  return response.data;
};

export const getTeam = async (teamId: number) => {
  const response = await apiClient.get<Team>(`/api/v1/teams/${teamId}`);
  return response.data;
};

export const createTeam = async (data: TeamCreate) => {
  const response = await apiClient.post<Team>('/api/v1/teams', data);
  return response.data;
};

export const joinPublicTeam = async (teamId: number) => {
  const response = await apiClient.post<Team>(`/api/v1/teams/${teamId}/join`);
  return response.data;
};

export const getTeamMembers = async (teamId: number) => {
  const response = await apiClient.get<TeamMember[]>(`/api/v1/teams/${teamId}/members`);
  return response.data;
};

export const addTeamMember = async (teamId: number, data: { user_id: number, role: string }) => {
  const response = await apiClient.post<TeamMember>(`/api/v1/teams/${teamId}/members`, data);
  return response.data;
};

export const removeTeamMember = async (teamId: number, userId: number) => {
  const response = await apiClient.delete(`/api/v1/teams/${teamId}/members/${userId}`);
  return response.data;
};

export const updateMemberRole = async (teamId: number, userId: number, role: string) => {
  const response = await apiClient.patch<TeamMember>(`/api/v1/teams/${teamId}/members/${userId}`, { role });
  return response.data;
};

export const deleteTeam = async (teamId: number) => {
  const response = await apiClient.delete(`/api/v1/teams/${teamId}`);
  return response.data;
};
