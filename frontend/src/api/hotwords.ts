import { apiClient } from "./client";
import type { HotwordItem } from "./types";

export type { HotwordItem } from "./types";

export interface CreateHotwordPayload {
  word: string;
}

export async function getHotwords(): Promise<HotwordItem[]> {
  const resp = await apiClient.get<HotwordItem[]>("/api/v1/hotwords");
  return resp.data;
}

export async function createHotword(payload: CreateHotwordPayload): Promise<HotwordItem> {
  const resp = await apiClient.post<HotwordItem>("/api/v1/hotwords", payload);
  return resp.data;
}

export async function deleteHotword(hotwordId: number): Promise<void> {
  await apiClient.delete(`/api/v1/hotwords/${hotwordId}`);
}
