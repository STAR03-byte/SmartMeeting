import { apiClient } from "./client";
import type { UserItem, UserRole } from "./types";

export type { UserItem, UserRole } from "./types";

export interface CreateUserPayload {
  username: string;
  email: string;
  password_hash: string;
  full_name: string;
  role: UserRole;
}

export interface GetUsersParams {
  team_id?: number;
  scope?: "selectable" | "all";
  meeting_id?: number;
}

export async function getUsers(params: GetUsersParams = {}): Promise<UserItem[]> {
  const searchParams = new URLSearchParams();
  if (typeof params.team_id === "number") searchParams.set("team_id", String(params.team_id));
  if (typeof params.meeting_id === "number") searchParams.set("meeting_id", String(params.meeting_id));
  if (params.scope) searchParams.set("scope", params.scope);
  const query = searchParams.toString();
  const url = query ? `/api/v1/users?${query}` : "/api/v1/users";
  const resp = await apiClient.get<UserItem[]>(url);
  return resp.data;
}

export async function searchInvitableUsers(teamId: number, keyword: string, limit = 20): Promise<UserItem[]> {
  const searchParams = new URLSearchParams();
  searchParams.set("team_id", String(teamId));
  searchParams.set("keyword", keyword.trim());
  searchParams.set("limit", String(limit));
  const resp = await apiClient.get<UserItem[]>(`/api/v1/users/search?${searchParams.toString()}`);
  return resp.data;
}

export async function createUser(payload: CreateUserPayload): Promise<UserItem> {
  const resp = await apiClient.post<UserItem>("/api/v1/users", payload);
  return resp.data;
}

export async function deleteUser(userId: number): Promise<void> {
  await apiClient.delete(`/api/v1/users/${userId}`);
}

export async function registerUser(payload: CreateUserPayload): Promise<UserItem> {
  const resp = await apiClient.post<UserItem>("/api/v1/register", payload);
  return resp.data;
}
