import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";

const fakeSessionStorage = {
  data: new Map<string, string>(),
  getItem(key: string) { return this.data.get(key) ?? null; },
  setItem(key: string, val: string) { this.data.set(key, val); },
  removeItem(key: string) { this.data.delete(key); },
  clear() { this.data.clear(); },
};

const fakeLocalStorage = {
  data: new Map<string, string>(),
  getItem(key: string) { return this.data.get(key) ?? null; },
  setItem(key: string, val: string) { this.data.set(key, val); },
  removeItem(key: string) { this.data.delete(key); },
  clear() { this.data.clear(); },
};

vi.stubGlobal("window", {} as Window);
vi.stubGlobal("sessionStorage", fakeSessionStorage);
vi.stubGlobal("localStorage", fakeLocalStorage);

vi.mock("../api/auth", () => ({
  login: vi.fn(),
  fetchCurrentUser: vi.fn(),
}));

vi.mock("../utils/notify", () => ({
  notifyApiError: vi.fn(),
}));

vi.mock("../stores/meetingStore", () => ({
  useMeetingStore: () => ({ clearAllState: vi.fn() }),
}));

vi.mock("../stores/taskCenterStore", () => ({
  useTaskCenterStore: () => ({ clearAllState: vi.fn() }),
}));

describe("authStore token isolation", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    sessionStorage.clear();
    localStorage.clear();
  });

  it("reads token from sessionStorage first", async () => {
    sessionStorage.setItem("smartmeeting_access_token", "session-token");
    localStorage.setItem("smartmeeting_access_token", "local-token");

    const { useAuthStore } = await import("./authStore");
    const store = useAuthStore();

    expect(store.token).toBe("session-token");
  });

  it("setToken stores in sessionStorage and clears localStorage", async () => {
    const { useAuthStore } = await import("./authStore");
    const store = useAuthStore();

    localStorage.setItem("smartmeeting_access_token", "legacy");
    store.setToken("new-token");

    expect(sessionStorage.getItem("smartmeeting_access_token")).toBe("new-token");
    expect(localStorage.getItem("smartmeeting_access_token")).toBeNull();
  });
});
