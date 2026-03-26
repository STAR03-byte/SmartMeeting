import { describe, expect, it, vi } from "vitest";

describe("share link utils", () => {
  it("builds full share url from origin and path", async () => {
    const { buildShareUrl } = await import("./share-link");

    expect(buildShareUrl("http://localhost:5173", "/shared/meetings/token-1")).toBe(
      "http://localhost:5173/shared/meetings/token-1",
    );
  });

  it("copies share url to clipboard", async () => {
    const writeText = vi.fn().mockResolvedValueOnce(undefined);
    vi.stubGlobal("navigator", { clipboard: { writeText } } as never);

    const { copyShareLinkToClipboard } = await import("./share-link");
    const url = await copyShareLinkToClipboard("http://localhost:5173", "/shared/meetings/token-2");

    expect(url).toBe("http://localhost:5173/shared/meetings/token-2");
    expect(writeText).toHaveBeenCalledWith("http://localhost:5173/shared/meetings/token-2");
  });
});
