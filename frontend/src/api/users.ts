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

export async function getUsers(): Promise<UserItem[]> {
  const resp = await apiClient.get<UserItem[]>("/api/v1/users");
  return resp.data;
}

export async function createUser(payload: CreateUserPayload): Promise<UserItem> {
  const resp = await apiClient.post<UserItem>("/api/v1/users", payload);
  return resp.data;
}

export async function deleteUser(userId: number): Promise<void> {
  await apiClient.delete(`/api/v1/users/${userId}`);
}
