import { apiClient } from "./client";

export interface Commitment {
  id: number;
  meeting_id: number;
  content: string;
  assignee_name: string | null;
  assignee_user_id: number | null;
  due_hint: string | null;
  status: string;
  linked_task_id: number | null;
  created_at: string;
  updated_at: string;
  confirmed_at: string | null;
}

export interface CommitmentListResult {
  items: Commitment[];
  total: number;
}

export interface CommitmentCreatePayload {
  meeting_id: number;
  content: string;
  assignee_name?: string;
  assignee_user_id?: number;
  due_hint?: string;
  linked_task_id?: number;
}

export interface CommitmentUpdatePayload {
  content?: string;
  assignee_name?: string;
  assignee_user_id?: number;
  due_hint?: string;
  status?: string;
  linked_task_id?: number;
}

export interface CommitmentListParams {
  meeting_id?: number;
  status?: string;
  assignee_user_id?: number;
  limit?: number;
  offset?: number;
}

export async function listCommitments(params?: CommitmentListParams): Promise<CommitmentListResult> {
  const { data } = await apiClient.get<CommitmentListResult>("/api/v1/commitments", { params });
  return data;
}

export async function getCommitment(id: number): Promise<Commitment> {
  const { data } = await apiClient.get<Commitment>(`/api/v1/commitments/${id}`);
  return data;
}

export async function createCommitment(payload: CommitmentCreatePayload): Promise<Commitment> {
  const { data } = await apiClient.post<Commitment>("/api/v1/commitments", payload);
  return data;
}

export async function updateCommitment(id: number, payload: CommitmentUpdatePayload): Promise<Commitment> {
  const { data } = await apiClient.patch<Commitment>(`/api/v1/commitments/${id}`, payload);
  return data;
}

export async function deleteCommitment(id: number): Promise<void> {
  await apiClient.delete(`/api/v1/commitments/${id}`);
}
