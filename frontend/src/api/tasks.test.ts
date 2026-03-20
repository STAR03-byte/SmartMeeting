import { describe, expect, it, vi } from "vitest";

import { apiClient } from "./client";

describe("tasks api module", () => {
  it("fetches tasks with filters", async () => {
    const getSpy = vi.spyOn(apiClient, "get").mockResolvedValueOnce({
      data: [{ id: 1, title: "Task 1", status: "todo" }],
    } as never);

    const mod = await import("./tasks");
    const result = await mod.getTasks({ status: "todo", priority: "high" });

    expect(getSpy).toHaveBeenCalledWith("/api/v1/tasks?status=todo&priority=high");
    expect(result).toHaveLength(1);
  });

  it("updates task status", async () => {
    const patchSpy = vi.spyOn(apiClient, "patch").mockResolvedValueOnce({
      data: { id: 1, status: "done" },
    } as never);

    const mod = await import("./tasks");
    const result = await mod.updateTaskStatus(1, "done");

    expect(patchSpy).toHaveBeenCalledWith("/api/v1/tasks/1", { status: "done" });
    expect(result.status).toBe("done");
  });
});
