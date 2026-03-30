import { beforeEach, describe, expect, it, vi } from "vitest";

import { createPinia, setActivePinia } from "pinia";

const mocks = vi.hoisted(() => ({
  uploadMeetingAudio: vi.fn(async () => ({ id: 1 })),
  transcribeMeetingAudio: vi.fn(async () => ({
    id: 1,
    meeting_id: 1,
    speaker_user_id: null,
    speaker_name: "ASR",
    segment_index: 1,
    start_time_sec: 0,
    end_time_sec: 1,
    language_code: "zh-CN",
    source: "whisper",
    content: "实时转写片段",
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
  })),
}));

vi.mock("../api/meetings", () => ({
  uploadMeetingAudio: mocks.uploadMeetingAudio,
  transcribeMeetingAudio: mocks.transcribeMeetingAudio,
  getMeeting: vi.fn(),
  getMeetings: vi.fn(),
  getMeetingTranscripts: vi.fn(),
  getTasksByMeeting: vi.fn(),
  exportMeetingSummary: vi.fn(),
  triggerPostprocess: vi.fn(),
  createMeeting: vi.fn(),
  deleteMeeting: vi.fn(),
  getTasksByAssignee: vi.fn(),
  createTask: vi.fn(),
}));

import { useMeetingStore } from "./meetingStore";

describe("meeting store realtime flow", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    mocks.uploadMeetingAudio.mockClear();
    mocks.transcribeMeetingAudio.mockClear();
  });

  it("appends realtime transcripts after upload", async () => {
    const store = useMeetingStore();

    const transcript = await store.appendRealtimeTranscript(1, new File(["chunk"], "chunk.webm", { type: "audio/webm" }));

    expect(mocks.uploadMeetingAudio).toHaveBeenCalledTimes(1);
    expect(mocks.transcribeMeetingAudio).toHaveBeenCalledTimes(1);
    expect(store.transcripts).toEqual([transcript]);
    expect(transcript.content).toBe("实时转写片段");
  });
});
