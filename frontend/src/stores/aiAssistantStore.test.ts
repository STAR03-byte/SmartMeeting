import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";

const mocks = vi.hoisted(() => ({
  chatStream: vi.fn(),
  createConversation: vi.fn(async () => ({ id: 1, title: "新对话", createdAt: "2026-01-01T00:00:00Z", updatedAt: "2026-01-01T00:00:00Z" })),
  getConversations: vi.fn(async () => []),
  getMessages: vi.fn(async () => []),
  deleteConversation: vi.fn(async () => undefined),
  createTaskDraft: vi.fn(async () => ({ id: 1, conversationId: 1, title: "草稿", priority: "medium", status: "draft" })),
}));

vi.mock("../api/ai", () => ({
  chatStream: mocks.chatStream,
  createConversation: mocks.createConversation,
  getConversations: mocks.getConversations,
  getMessages: mocks.getMessages,
  deleteConversation: mocks.deleteConversation,
  createTaskDraft: mocks.createTaskDraft,
}));

import { useAiAssistantStore } from "./aiAssistantStore";

describe("ai assistant store streaming pacing", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    setActivePinia(createPinia());
    mocks.chatStream.mockReset();
  });

  it("coalesces rapid streaming chunks before rendering", async () => {
    let onmessage: ((event: MessageEvent<string>) => void) | null = null;
    const close = vi.fn();
    mocks.chatStream.mockImplementation(() => ({
      close,
      set onmessage(handler) {
        onmessage = handler;
      },
      get onmessage() {
        return onmessage;
      },
      onerror: null,
    }));

    const store = useAiAssistantStore();
    const sendPromise = store.sendMessage("你好");

    await Promise.resolve();
    await Promise.resolve();

    expect(store.messages).toHaveLength(2);

    onmessage?.({ data: JSON.stringify({ type: "chunk", content: "你" }) } as MessageEvent<string>);
    onmessage?.({ data: JSON.stringify({ type: "chunk", content: "好" }) } as MessageEvent<string>);

    expect(store.messages.at(-1)?.content).toBe("");

    await vi.advanceTimersByTimeAsync(60);
    expect(store.messages.at(-1)?.content).toBe("你好");

    onmessage?.({ data: JSON.stringify({ type: "end" }) } as MessageEvent<string>);
    await sendPromise;

    expect(close).toHaveBeenCalled();
  });
});
