import { describe, expect, it, vi } from "vitest";

import { apiClient } from "./client";

describe("meetings api module", () => {
  it("fetches meetings list with params", async () => {
    const getSpy = vi.spyOn(apiClient, "get").mockResolvedValueOnce({
      data: [{ id: 1, title: "Test Meeting" }],
    } as never);

    const mod = await import("./meetings");
    const result = await mod.getMeetings({ status: "planned", limit: 10 });

    expect(getSpy).toHaveBeenCalledWith("/api/v1/meetings", {
      params: { status: "planned", limit: 10 },
    });
    expect(result).toHaveLength(1);
    expect(result[0].title).toBe("Test Meeting");
  });

  it("creates a meeting", async () => {
    const postSpy = vi.spyOn(apiClient, "post").mockResolvedValueOnce({
      data: { id: 2, title: "New Meeting" },
    } as never);

    const mod = await import("./meetings");
    const result = await mod.createMeeting({
      title: "New Meeting",
      organizer_id: 1,
    });

    expect(postSpy).toHaveBeenCalledWith("/api/v1/meetings", {
      title: "New Meeting",
      organizer_id: 1,
    });
    expect(result.id).toBe(2);
  });

  it("deletes a meeting", async () => {
    const deleteSpy = vi.spyOn(apiClient, "delete").mockResolvedValueOnce({} as never);

    const mod = await import("./meetings");
    await mod.deleteMeeting(1);

    expect(deleteSpy).toHaveBeenCalledWith("/api/v1/meetings/1");
  });
});
