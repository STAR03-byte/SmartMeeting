import { describe, expect, it, vi } from "vitest";

import { apiClient } from "./client";

describe("tasks api module", () => {
  it("fetches tasks with filters", async () => {
    const getSpy = vi.spyOn(apiClient, "get").mockResolvedValueOnce({
      data: { items: [{ id: 1, title: "Task 1", status: "todo" }], total: 1 },
    } as never);

    const mod = await import("./tasks");
    const result = await mod.getTasks({ status: "todo", priority: "high" });

    expect(getSpy).toHaveBeenCalledWith("/api/v1/tasks?status=todo&priority=high");
    expect(result.items).toHaveLength(1);
    expect(result.total).toBe(1);
  });

  it("serializes pagination and sort params", async () => {
    const getSpy = vi.spyOn(apiClient, "get").mockResolvedValueOnce({
      data: { items: [], total: 0 },
    } as never);

    const mod = await import("./tasks");
    await mod.getTasks({
      meeting_id: 10,
      keyword: "  hello  ",
      sort_by: "due_at_asc",
      limit: 20,
      offset: 40,
    });

    expect(getSpy).toHaveBeenCalledWith(
      "/api/v1/tasks?meeting_id=10&keyword=hello&sort_by=due_at_asc&limit=20&offset=40"
    );
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
