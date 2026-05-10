import { apiClient } from "./client";

export interface Decision {
  id: number;
  meeting_id: number;
  content: string;
  proposer_name: string | null;
  proposer_user_id: number | null;
  context: string | null;
  confidence: number | null;
  status: string;
  created_at: string;
  updated_at: string;
  confirmed_at: string | null;
}

export interface DecisionListResult {
  items: Decision[];
  total: number;
}

export interface DecisionCreatePayload {
  meeting_id: number;
  content: string;
  proposer_name?: string;
  proposer_user_id?: number;
  context?: string;
  confidence?: number;
}

export interface DecisionUpdatePayload {
  content?: string;
  proposer_name?: string;
  proposer_user_id?: number;
  context?: string;
  confidence?: number;
  status?: string;
}

export interface DecisionListParams {
  meeting_id?: number;
  status?: string;
  limit?: number;
  offset?: number;
}

export async function listDecisions(params?: DecisionListParams): Promise<DecisionListResult> {
  const { data } = await apiClient.get<DecisionListResult>("/api/v1/decisions", { params });
  return data;
}

export async function getDecision(id: number): Promise<Decision> {
  const { data } = await apiClient.get<Decision>(`/api/v1/decisions/${id}`);
  return data;
}

export async function createDecision(payload: DecisionCreatePayload): Promise<Decision> {
  const { data } = await apiClient.post<Decision>("/api/v1/decisions", payload);
  return data;
}

export async function updateDecision(id: number, payload: DecisionUpdatePayload): Promise<Decision> {
  const { data } = await apiClient.patch<Decision>(`/api/v1/decisions/${id}`, payload);
  return data;
}

export async function deleteDecision(id: number): Promise<void> {
  await apiClient.delete(`/api/v1/decisions/${id}`);
}
