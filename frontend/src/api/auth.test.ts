import { describe, expect, it, vi } from "vitest";

import { apiClient } from "./client";

describe("auth api module", () => {
  it("posts login form data to auth endpoint", async () => {
    const postSpy = vi.spyOn(apiClient, "post").mockResolvedValueOnce({
      data: { access_token: "token-1", token_type: "bearer" },
    } as never);

    const mod = await import("./auth");
    const resp = await mod.login("alice", "secret");

    expect(postSpy).toHaveBeenCalledWith(
      "/api/v1/auth/login",
      expect.any(URLSearchParams),
      expect.objectContaining({
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      }),
    );
    expect(resp.access_token).toBe("token-1");
  });

  it("loads current user from auth endpoint", async () => {
    const getSpy = vi.spyOn(apiClient, "get").mockResolvedValueOnce({
      data: { id: 1, username: "alice" },
    } as never);

    const mod = await import("./auth");
    const resp = await mod.fetchCurrentUser<{ id: number; username: string }>();

    expect(getSpy).toHaveBeenCalledWith("/api/v1/auth/me");
    expect(resp.username).toBe("alice");
  });
});
