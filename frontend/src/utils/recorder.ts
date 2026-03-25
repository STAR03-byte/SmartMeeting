const MIME_CANDIDATES = [
  "audio/webm;codecs=opus",
  "audio/webm",
  "audio/mp4",
  "audio/ogg;codecs=opus",
] as const;

function extensionFromMimeType(mimeType: string): string {
  if (mimeType.includes("webm")) return "webm";
  if (mimeType.includes("mp4")) return "mp4";
  if (mimeType.includes("ogg")) return "ogg";
  return "bin";
}

export function pickRecordingMimeType(
  supportsType: (mimeType: string) => boolean,
): string {
  for (const candidate of MIME_CANDIDATES) {
    if (supportsType(candidate)) {
      return candidate;
    }
  }
  return "audio/webm";
}

export function buildRecordingFile(
  chunks: BlobPart[],
  mimeType: string,
  meetingId: number,
  prefix = "meeting-recording",
): File {
  const extension = extensionFromMimeType(mimeType);
  const filename = `${prefix}-${meetingId}.${extension}`;
  return new File(chunks, filename, { type: mimeType || "audio/webm" });
}
