import { describe, expect, it, vi } from "vitest";

import { apiClient } from "./client";

describe("ai api module", () => {
  it("normalizes snake_case task suggestions response", async () => {
    const postSpy = vi.spyOn(apiClient, "post").mockResolvedValueOnce({
      data: {
        steps: ["步骤1", "步骤2"],
        risks: ["风险A"],
        suggested_roles: ["产品", "研发"],
        related_tasks: [{ id: 12, title: "已有任务" }],
      },
    } as never);

    const mod = await import("./ai");
    const result = await mod.getTaskSuggestions("优化需求", "描述", 1001);

    expect(postSpy).toHaveBeenCalledWith("/api/v1/ai/task-suggestions", {
      title: "优化需求",
      description: "描述",
      meeting_id: 1001,
    });
    expect(result.steps).toEqual(["步骤1", "步骤2"]);
    expect(result.risks).toEqual(["风险A"]);
    expect(result.suggestedRoles).toEqual(["产品", "研发"]);
    expect(result.relatedTasks).toEqual([{ id: 12, title: "已有任务" }]);
  });

  it("keeps camelCase task suggestions response compatible", async () => {
    vi.spyOn(apiClient, "post").mockResolvedValueOnce({
      data: {
        steps: ["A"],
        risks: [],
        suggestedRoles: ["测试"],
        relatedTasks: [{ id: 7, title: "任务7" }],
      },
    } as never);

    const mod = await import("./ai");
    const result = await mod.getTaskSuggestions("标题");

    expect(result.suggestedRoles).toEqual(["测试"]);
    expect(result.relatedTasks).toEqual([{ id: 7, title: "任务7" }]);
  });
});
