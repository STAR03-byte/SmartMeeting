import { describe, expect, it } from "vitest";

import { resolveSafeRedirect } from "./redirect";

describe("resolveSafeRedirect", () => {
  it("keeps safe in-app redirects and rejects external urls", () => {
    expect(resolveSafeRedirect("/shared/meetings/abc")).toBe("/shared/meetings/abc");
    expect(resolveSafeRedirect("//evil.com")).toBe("/");
    expect(resolveSafeRedirect("https://evil.com")).toBe("/");
    expect(resolveSafeRedirect(undefined)).toBe("/");
  });
});
