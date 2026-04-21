import { computed, ref } from "vue";
import { defineStore } from "pinia";

import {
  chatStream,
  createConversation as apiCreateConversation,
  createTaskDraft as apiCreateTaskDraft,
  deleteConversation as apiDeleteConversation,
  getConversations as apiGetConversations,
  getMessages as apiGetMessages,
  type ChatContext,
  type ChatChunk,
  type Conversation,
  type ConversationMessage,
  type CreateTaskDraftPayload,
  type TaskDraft,
} from "../api/ai";
import { getApiErrorMessage } from "../api/client";

function getConversationTimestamp(conversation: Conversation): number {
  const raw = conversation.updatedAt || conversation.updated_at || conversation.createdAt || conversation.created_at;
  const timestamp = Date.parse(raw ?? "");
  return Number.isNaN(timestamp) ? 0 : timestamp;
}

function createLocalMessage(
  conversationId: number,
  role: ConversationMessage["role"],
  content: string,
): ConversationMessage {
  const now = new Date().toISOString();

  return {
    id: -Date.now(),
    conversationId,
    conversation_id: conversationId,
    role,
    content,
    createdAt: now,
    created_at: now,
  };
}

function normalizeChatChunk(data: string): ChatChunk | null {
  try {
    return JSON.parse(data) as ChatChunk;
  } catch {
    return null;
  }
}

export const useAiAssistantStore = defineStore("aiAssistant", () => {
  const conversations = ref<Conversation[]>([]);
  const currentConversation = ref<Conversation | null>(null);
  const messages = ref<ConversationMessage[]>([]);
  const isLoading = ref(false);
  const isStreaming = ref(false);
  const error = ref<string | null>(null);

  const sortedConversations = computed(() => {
    return [...conversations.value].sort((a, b) => getConversationTimestamp(b) - getConversationTimestamp(a));
  });

  const hasActiveConversation = computed(() => currentConversation.value !== null);

  async function fetchConversations() {
    isLoading.value = true;
    error.value = null;
    try {
      const result = await apiGetConversations();
      conversations.value = result;

      if (currentConversation.value) {
        const refreshed = result.find((conversation) => conversation.id === currentConversation.value?.id) ?? null;
        currentConversation.value = refreshed;
      }
    } catch (err) {
      error.value = getApiErrorMessage(err);
      throw err;
    } finally {
      isLoading.value = false;
    }
  }

  async function createConversation(title?: string) {
    isLoading.value = true;
    error.value = null;
    try {
      const conversation = await apiCreateConversation(title);
      conversations.value = [conversation, ...conversations.value.filter((item) => item.id !== conversation.id)];
      currentConversation.value = conversation;
      messages.value = [];
      return conversation;
    } catch (err) {
      error.value = getApiErrorMessage(err);
      throw err;
    } finally {
      isLoading.value = false;
    }
  }

  async function deleteConversation(id: number) {
    isLoading.value = true;
    error.value = null;
    try {
      await apiDeleteConversation(id);
      conversations.value = conversations.value.filter((conversation) => conversation.id !== id);

      if (currentConversation.value?.id === id) {
        currentConversation.value = null;
        messages.value = [];
      }
    } catch (err) {
      error.value = getApiErrorMessage(err);
      throw err;
    } finally {
      isLoading.value = false;
    }
  }

  async function selectConversation(id: number) {
    isLoading.value = true;
    error.value = null;
    try {
      const localConversation = conversations.value.find((conversation) => conversation.id === id) ?? null;
      if (!localConversation) {
        await fetchConversations();
      }

      const conversation = conversations.value.find((item) => item.id === id) ?? null;
      if (!conversation) {
        throw new Error("对话不存在或已被删除");
      }

      currentConversation.value = conversation;
      messages.value = await apiGetMessages(id);
    } catch (err) {
      error.value = getApiErrorMessage(err);
      throw err;
    } finally {
      isLoading.value = false;
    }
  }

  async function sendMessage(message: string, context?: ChatContext) {
    if (isStreaming.value) {
      const busyError = new Error("当前正在接收流式响应，请稍后再试");
      error.value = busyError.message;
      throw busyError;
    }

    isLoading.value = true;
    isStreaming.value = true;
    error.value = null;

    try {
      const content = message.trim();
      if (!content) {
        throw new Error("消息内容不能为空");
      }

      if (!currentConversation.value) {
        await createConversation();
      }

      const conversationId = currentConversation.value?.id;
      if (typeof conversationId !== "number") {
        throw new Error("当前没有可用的会话");
      }

      const userMessage = createLocalMessage(conversationId, "user", content);
      const assistantMessage = createLocalMessage(conversationId, "assistant", "");

      messages.value = [...messages.value, userMessage, assistantMessage];
      const assistantIndex = messages.value.length - 1;
      const stream = chatStream(content, conversationId, context);

      const finalAssistantMessage = await new Promise<ConversationMessage>((resolve, reject) => {
        let settled = false;

        const cleanup = () => {
          stream.close();
        };

        let chunkBuffer = "";
        let flushTimer: ReturnType<typeof setTimeout> | null = null;

        const flushBufferedChunks = () => {
          if (!chunkBuffer) return;
          const nextContent = `${messages.value[assistantIndex]?.content ?? ""}${chunkBuffer}`;
          messages.value[assistantIndex] = {
            ...messages.value[assistantIndex],
            content: nextContent,
          };
          assistantMessage.content = nextContent;
          chunkBuffer = "";
        };

        const scheduleFlush = () => {
          if (flushTimer !== null) return;
          flushTimer = setTimeout(() => {
            flushTimer = null;
            flushBufferedChunks();
          }, 60);
        };

        const finish = () => {
          if (settled) return;
          settled = true;
          if (flushTimer !== null) {
            clearTimeout(flushTimer);
            flushTimer = null;
          }
          flushBufferedChunks();
          cleanup();
          currentConversation.value = currentConversation.value
            ? { ...currentConversation.value, updatedAt: new Date().toISOString(), updated_at: new Date().toISOString() }
            : currentConversation.value;
          if (currentConversation.value) {
            conversations.value = conversations.value.map((conversation) => (
              conversation.id === currentConversation.value?.id
                ? { ...conversation, updatedAt: currentConversation.value.updatedAt, updated_at: currentConversation.value.updated_at }
                : conversation
            ));
          }
          resolve(messages.value[assistantIndex]);
        };

        const fail = (rawError: unknown) => {
          if (settled) return;
          settled = true;
          if (flushTimer !== null) {
            clearTimeout(flushTimer);
            flushTimer = null;
          }
          flushBufferedChunks();
          cleanup();
          reject(rawError instanceof Error ? rawError : new Error(getApiErrorMessage(rawError)));
        };

        stream.onmessage = (event) => {
          const chunk = normalizeChatChunk(event.data);

          if (!chunk) {
            const nextContent = `${messages.value[assistantIndex]?.content ?? ""}${event.data}`;
            messages.value[assistantIndex] = {
              ...messages.value[assistantIndex],
              content: nextContent,
            };
            assistantMessage.content = nextContent;
            return;
          }

          if (chunk.type === "error") {
            fail(new Error(chunk.content || "AI 流式响应失败"));
            return;
          }

          if (chunk.type === "chunk" && typeof chunk.content === "string") {
            chunkBuffer += chunk.content;
            scheduleFlush();
            return;
          }

          if (chunk.type === "end") {
            if (flushTimer !== null) {
              clearTimeout(flushTimer);
              flushTimer = null;
            }
            flushBufferedChunks();
            if (typeof chunk.content === "string" && chunk.content.length > 0) {
              const nextContent = `${messages.value[assistantIndex]?.content ?? ""}${chunk.content}`;
              messages.value[assistantIndex] = {
                ...messages.value[assistantIndex],
                content: nextContent,
              };
              assistantMessage.content = nextContent;
            }
            finish();
          }
        };

        stream.onerror = () => {
          fail(new Error("AI 流式连接已中断"));
        };
      });

      return finalAssistantMessage;
    } catch (err) {
      error.value = getApiErrorMessage(err);
      throw err;
    } finally {
      isLoading.value = false;
      isStreaming.value = false;
    }
  }

  async function createTaskDraft(data: CreateTaskDraftPayload): Promise<TaskDraft> {
    isLoading.value = true;
    error.value = null;
    try {
      return await apiCreateTaskDraft(data);
    } catch (err) {
      error.value = getApiErrorMessage(err);
      throw err;
    } finally {
      isLoading.value = false;
    }
  }

  return {
    conversations,
    currentConversation,
    messages,
    isLoading,
    isStreaming,
    error,
    sortedConversations,
    hasActiveConversation,
    fetchConversations,
    createConversation,
    deleteConversation,
    selectConversation,
    sendMessage,
    createTaskDraft,
  };
});
