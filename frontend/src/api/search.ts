import { apiClient } from "./client";

export interface SearchResult {
  content: string;
  source_type: string;
  source_id: number | null;
  metadata: Record<string, unknown>;
  meeting_id: number;
  meeting_title: string;
  vector_score: number;
  text_score: number;
  score: number;
}

export interface SearchResultList {
  items: SearchResult[];
  total: number;
}

export interface SearchParams {
  q: string;
  team_id?: number;
  source_type?: string;
  limit?: number;
}

export async function searchMeetings(params: SearchParams): Promise<SearchResultList> {
  const { data } = await apiClient.get<SearchResultList>("/api/v1/search", { params });
  return data;
}
