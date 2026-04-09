import { describe, expect, it, vi } from "vitest";

import { apiClient } from "./client";

describe("meetings api module", () => {
  it("fetches meetings list with params", async () => {
    const getSpy = vi.spyOn(apiClient, "get").mockResolvedValueOnce({
      data: { items: [{ id: 1, title: "Test Meeting" }], total: 1 },
    } as never);

    const mod = await import("./meetings");
    const result = await mod.getMeetings({ status: "planned", limit: 10 });

    expect(getSpy).toHaveBeenCalledWith("/api/v1/meetings", {
      params: { status: "planned", limit: 10 },
    });
    expect(result.items).toHaveLength(1);
    expect(result.items[0].title).toBe("Test Meeting");
    expect(result.total).toBe(1);
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

  it("fetches tasks by meeting with paged contract", async () => {
    const getSpy = vi.spyOn(apiClient, "get").mockResolvedValueOnce({
      data: {
        items: [
          {
            id: 9,
            meeting_id: 3,
            transcript_id: null,
            title: "补齐联调文档",
            description: null,
            assignee_id: 1,
            reporter_id: null,
            priority: "medium",
            status: "todo",
             progress_note: null,
             due_at: null,
             reminder_at: null,
             completed_at: null,
            is_overdue: false,
            is_due_soon: false,
            created_at: "2026-03-25T00:00:00Z",
            updated_at: "2026-03-25T00:00:00Z",
          },
        ],
        total: 1,
      },
    } as never);

    const mod = await import("./meetings");
    const result = await mod.getTasksByMeeting(3);

    expect(getSpy).toHaveBeenCalledWith("/api/v1/tasks", {
      params: { meeting_id: 3 },
    });
    expect(result.total).toBe(1);
    expect(result.items[0].meeting_id).toBe(3);
  });

  it("fetches tasks by assignee", async () => {
    const getSpy = vi.spyOn(apiClient, "get").mockResolvedValueOnce({
      data: { items: [], total: 0 },
    } as never);

    const mod = await import("./meetings");
    await mod.getTasksByAssignee(8);

    expect(getSpy).toHaveBeenCalledWith("/api/v1/tasks", {
      params: { assignee_id: 8 },
    });
  });

  it("triggers postprocess for a meeting", async () => {
    const postSpy = vi.spyOn(apiClient, "post").mockResolvedValueOnce({
      data: {
        meeting_id: 3,
        summary: "总结",
        tasks: [],
      },
    } as never);

    const mod = await import("./meetings");
    const result = await mod.triggerPostprocess(3);

    expect(postSpy).toHaveBeenCalledWith("/api/v1/meetings/3/postprocess");
    expect(result.summary).toBe("总结");
  });

  it("uploads meeting audio with multipart headers", async () => {
    const postSpy = vi.spyOn(apiClient, "post").mockResolvedValueOnce({
      data: {
        id: 4,
        meeting_id: 3,
        filename: "recording.wav",
        storage_path: "backend/storage/audio/3/recording.wav",
        content_type: "audio/wav",
        size_bytes: 1024,
        uploaded_at: "2026-03-25T00:00:00Z",
      },
    } as never);

    const mod = await import("./meetings");
    const file = new File(["audio"], "recording.wav", { type: "audio/wav" });
    const result = await mod.uploadMeetingAudio(3, file);

    expect(postSpy).toHaveBeenCalledWith(
      "/api/v1/meetings/3/audio",
      expect.any(FormData),
      expect.objectContaining({
        headers: { "Content-Type": "multipart/form-data" },
      }),
    );
    expect(result.filename).toBe("recording.wav");
  });

  it("transcribes meeting audio", async () => {
    const postSpy = vi.spyOn(apiClient, "post").mockResolvedValueOnce({
      data: {
        id: 11,
        meeting_id: 3,
        speaker_user_id: null,
        speaker_name: "Whisper",
        segment_index: 1,
        start_time_sec: 0,
        end_time_sec: 2,
        language_code: "zh-CN",
        source: "whisper",
        content: "开始转写",
        created_at: "2026-03-25T00:00:00Z",
        updated_at: "2026-03-25T00:00:00Z",
      },
    } as never);

    const mod = await import("./meetings");
    const result = await mod.transcribeMeetingAudio(3);

    expect(postSpy).toHaveBeenCalledWith("/api/v1/meetings/3/audio/transcribe");
    expect(result.content).toBe("开始转写");
  });

  it("fetches transcripts by meeting query", async () => {
    const getSpy = vi.spyOn(apiClient, "get").mockResolvedValueOnce({
      data: [
        {
          id: 1,
          meeting_id: 3,
          speaker_user_id: 1,
          speaker_name: "PM",
          segment_index: 1,
          start_time_sec: null,
          end_time_sec: null,
          language_code: "zh-CN",
          source: "whisper",
          content: "请完善发布计划",
          created_at: "2026-03-25T00:00:00Z",
          updated_at: "2026-03-25T00:00:00Z",
        },
      ],
    } as never);

    const mod = await import("./meetings");
    const result = await mod.getMeetingTranscripts(3);

    expect(getSpy).toHaveBeenCalledWith("/api/v1/transcripts?meeting_id=3");
    expect(result).toHaveLength(1);
    expect(result[0].meeting_id).toBe(3);
  });
});
