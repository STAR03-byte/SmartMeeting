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

  it("exports meeting summary", async () => {
    const postSpy = vi.spyOn(apiClient, "post").mockResolvedValueOnce({
      data: {
        meeting_id: 3,
        format: "txt",
        filename: "周会.txt",
        content: "会议主题：周会",
      },
    } as never);

    const mod = await import("./meetings");
    const result = await mod.exportMeetingSummary(3, { format: "txt" });

    expect(postSpy).toHaveBeenCalledWith("/api/v1/meetings/3/export", { format: "txt" });
    expect(result.filename).toBe("周会.txt");
  });

  it("creates meeting share link", async () => {
    const postSpy = vi.spyOn(apiClient, "post").mockResolvedValueOnce({
      data: {
        meeting_id: 7,
        share_token: "share-token-1",
        share_path: "/shared/meetings/share-token-1",
        created_now: true,
        shared_at: "2026-03-25T00:00:00Z",
      },
    } as never);

    const mod = await import("./meetings");
    const result = await mod.createMeetingShareLink(7);

    expect(postSpy).toHaveBeenCalledWith("/api/v1/meetings/7/share");
    expect(result.share_token).toBe("share-token-1");
  });

  it("loads shared meeting payload", async () => {
    const getSpy = vi.spyOn(apiClient, "get").mockResolvedValueOnce({
      data: {
        meeting: {
          id: 7,
          title: "Share",
          description: null,
          organizer_id: 1,
          scheduled_start_at: null,
          scheduled_end_at: null,
          actual_start_at: null,
          actual_end_at: null,
          location: null,
          status: "done",
          summary: "Summary",
          postprocessed_at: null,
          postprocess_version: null,
          share_token: "share-token-1",
          shared_at: "2026-03-25T00:00:00Z",
          created_at: "2026-03-25T00:00:00Z",
          updated_at: "2026-03-25T00:00:00Z",
          organizer: {
            id: 1,
            username: "alice",
            email: "alice@example.com",
            full_name: "Alice",
            role: "member",
            is_active: true,
            created_at: "2026-03-25T00:00:00Z",
            updated_at: "2026-03-25T00:00:00Z",
          },
        },
        transcripts: [],
        tasks: [],
      },
    } as never);

    const mod = await import("./meetings");
    const result = await mod.getSharedMeeting("share-token-1");

    expect(getSpy).toHaveBeenCalledWith("/api/v1/shared/meetings/share-token-1");
    expect(result.meeting.title).toBe("Share");
  });
});
