import { describe, expect, it, vi } from "vitest";

vi.mock("element-plus", () => ({
  ElMessage: {
    error: vi.fn(),
  },
}));

vi.mock("../api/client", async () => {
  const actual = await vi.importActual<typeof import("../api/client")>("../api/client");
  return {
    ...actual,
    getApiErrorMessage: () => "normalized message",
  };
});

describe("notifyApiError", () => {
  it("shows normalized error message", async () => {
    const { ElMessage } = await import("element-plus");
    const { notifyApiError } = await import("./notify");

    notifyApiError(new Error("boom"));
    expect(ElMessage.error).toHaveBeenCalledWith("normalized message");
  });

  it("adds prefix when provided", async () => {
    const { ElMessage } = await import("element-plus");
    const { notifyApiError } = await import("./notify");

    const fullMessage = notifyApiError(new Error("boom"), { prefix: "操作失败" });
    expect(ElMessage.error).toHaveBeenCalledWith("操作失败: normalized message");
    expect(fullMessage).toBe("操作失败: normalized message");
  });
});
