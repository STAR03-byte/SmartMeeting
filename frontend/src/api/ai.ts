import { apiClient, getApiErrorMessage } from "./client";
import type {
  ChatContext,
  ChatChunk,
  ChatStreamContext,
  Conversation,
  ConversationMessage,
  CreateTaskDraftPayload,
  KnowledgeQueryRequest,
  KnowledgeQueryResponse,
  TaskDraft,
  TaskSuggestionRequest,
  TaskSuggestionResponse,
} from "./types";

export type {
  ChatContext,
  ChatChunk,
  ChatStreamContext,
  Conversation,
  ConversationMessage,
  CreateTaskDraftPayload,
  KnowledgeQueryRequest,
  KnowledgeQueryResponse,
  TaskDraft,
  TaskSuggestionRequest,
  TaskSuggestionResponse,
} from "./types";

export type Message = ConversationMessage;

function normalizeTaskSuggestions(payload: unknown): TaskSuggestionResponse {
  const data = (payload ?? {}) as Record<string, unknown>;
  const steps = Array.isArray(data.steps) ? data.steps.filter((v): v is string => typeof v === "string") : [];
  const risks = Array.isArray(data.risks) ? data.risks.filter((v): v is string => typeof v === "string") : [];

  const rawRoles = Array.isArray(data.suggestedRoles)
    ? data.suggestedRoles
    : Array.isArray(data.suggested_roles)
      ? data.suggested_roles
      : [];
  const suggestedRoles = rawRoles.filter((v): v is string => typeof v === "string");

  const rawRelated = Array.isArray(data.relatedTasks)
    ? data.relatedTasks
    : Array.isArray(data.related_tasks)
      ? data.related_tasks
      : [];
  const relatedTasks = rawRelated
    .map((item) => {
      const rec = item as Record<string, unknown>;
      const id = typeof rec.id === "number" ? rec.id : Number(rec.id);
      const title = typeof rec.title === "string" ? rec.title : "";
      if (!Number.isFinite(id) || !title) return null;
      return { id, title };
    })
    .filter((item): item is { id: number; title: string } => item !== null);

  return {
    steps,
    risks,
    suggestedRoles,
    relatedTasks,
  };
}

function resolveApiUrl(path: string): URL {
  const baseURL = apiClient.defaults.baseURL ?? "/";
  const base = new URL(baseURL, window.location.origin);
  return new URL(path.replace(/^\//, ""), base);
}

function getAccessToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }

  const sessionToken = window.sessionStorage.getItem("smartmeeting_access_token");
  return sessionToken || window.localStorage.getItem("smartmeeting_access_token");
}

function rethrowApiError(error: unknown): never {
  throw new Error(getApiErrorMessage(error));
}

export async function getTaskSuggestions(
  title: string,
  description: string = "",
  meetingId?: number,
): Promise<TaskSuggestionResponse> {
  try {
    const resp = await apiClient.post<TaskSuggestionResponse>("/api/v1/ai/task-suggestions", {
      title: title.trim(),
      description: description.trim() || undefined,
      meeting_id: meetingId,
    } satisfies TaskSuggestionRequest);
    return normalizeTaskSuggestions(resp.data);
  } catch (error: unknown) {
    rethrowApiError(error);
  }
}

export async function getConversations(): Promise<Conversation[]> {
  try {
    const resp = await apiClient.get<Conversation[]>("/api/v1/ai/conversations");
    return resp.data;
  } catch (error: unknown) {
    rethrowApiError(error);
  }
}

export async function createConversation(title?: string): Promise<Conversation> {
  try {
    const payload = typeof title === "string" && title.trim().length > 0 ? { title: title.trim() } : {};
    const resp = await apiClient.post<Conversation>("/api/v1/ai/conversations", payload);
    return resp.data;
  } catch (error: unknown) {
    rethrowApiError(error);
  }
}

export async function deleteConversation(id: number): Promise<void> {
  try {
    await apiClient.delete(`/api/v1/ai/conversations/${id}`);
  } catch (error: unknown) {
    rethrowApiError(error);
  }
}

export async function getMessages(conversationId: number): Promise<Message[]> {
  try {
    const resp = await apiClient.get<Message[]>(`/api/v1/ai/conversations/${conversationId}/messages`);
    return resp.data;
  } catch (error: unknown) {
    rethrowApiError(error);
  }
}

export function chatStream(
  message: string,
  conversationId?: number,
  context?: ChatStreamContext,
): EventSource {
  if (typeof window === "undefined") {
    throw new Error("EventSource 只能在浏览器环境中创建");
  }

  const url = resolveApiUrl("/api/v1/ai/chat");
  const params = new URLSearchParams();
  params.set("message", message.trim());

  if (typeof conversationId === "number") {
    params.set("conversation_id", String(conversationId));
  }

  if (typeof context?.meetingId === "number") {
    params.set("meeting_id", String(context.meetingId));
  }

  const taskId = context?.taskIds?.[0];
  if (typeof taskId === "number") {
    params.set("task_id", String(taskId));
  }

  const token = getAccessToken();
  if (token) {
    params.set("access_token", token);
  }

  url.search = params.toString();
  return new EventSource(url.toString());
}

export async function createTaskDraft(data: CreateTaskDraftPayload): Promise<TaskDraft> {
  try {
    const resp = await apiClient.post<TaskDraft>("/api/v1/tasks/draft", {
      meeting_id: data.meeting_id,
      title: data.title.trim(),
      description: data.description.trim(),
      due_date: data.due_date instanceof Date ? data.due_date.toISOString() : data.due_date,
      priority: data.priority ?? "medium",
      assignee_id: data.assignee_id,
    });
    return resp.data;
  } catch (error: unknown) {
    rethrowApiError(error);
  }
}

export async function queryMeetingKnowledge(data: KnowledgeQueryRequest): Promise<KnowledgeQueryResponse> {
  try {
    const resp = await apiClient.post<KnowledgeQueryResponse>("/api/v1/ai/knowledge/query", {
      question: data.question.trim(),
      team_id: data.team_id ?? undefined,
      limit: data.limit ?? 5,
    });
    return resp.data;
  } catch (error: unknown) {
    rethrowApiError(error);
  }
}
