import { describe, expect, it } from "vitest";

import { buildRecordingFile, pickRecordingMimeType } from "./recorder";

describe("recorder utils", () => {
  it("prefers opus webm when supported", () => {
    const mime = pickRecordingMimeType((value) => value === "audio/webm;codecs=opus");
    expect(mime).toBe("audio/webm;codecs=opus");
  });

  it("falls back to generic webm when opus is unavailable", () => {
    const mime = pickRecordingMimeType((value) => value === "audio/webm");
    expect(mime).toBe("audio/webm");
  });

  it("builds file with extension from mime type", () => {
    const file = buildRecordingFile([new Blob(["abc"])], "audio/mp4", 101, "online-recording");
    expect(file.name).toBe("online-recording-101.mp4");
    expect(file.type).toBe("audio/mp4");
  });
});
