import { describe, expect, it, vi } from "vitest";

import { apiClient } from "./client";

describe("health api module", () => {
  it("loads preflight status", async () => {
    const getSpy = vi.spyOn(apiClient, "get").mockResolvedValueOnce({
      data: {
        status: "degraded",
        checks: {
          database: true,
          jwt_secret: false,
          ffmpeg: true,
          storage: true,
        },
        database: {
          connected: true,
          backend: "sqlite",
        },
        private_deployment: {
          jwt_secret_configured: false,
          jwt_secret_uses_default: true,
          ffmpeg_available: true,
          storage_dir: "backend/storage/audio",
          storage_dir_exists: true,
          storage_dir_writable: true,
          llm_provider: "mock",
          llm_configured: true,
          whisper_allow_mock_fallback: true,
        },
      },
    } as never);

    const mod = await import("./health");
    const result = await mod.getPreflightStatus();

    expect(getSpy).toHaveBeenCalledWith("/api/v1/health/preflight");
    expect(result.status).toBe("degraded");
    expect(result.checks.jwt_secret).toBe(false);
  });

  it("loads liveness and readiness status", async () => {
    const getSpy = vi
      .spyOn(apiClient, "get")
      .mockResolvedValueOnce({ data: { status: "alive" } } as never)
      .mockResolvedValueOnce({ data: { status: "ready" } } as never);

    const mod = await import("./health");
    const live = await mod.getLivenessStatus();
    const ready = await mod.getReadinessStatus();

    expect(getSpy).toHaveBeenNthCalledWith(1, "/api/v1/health/live");
    expect(getSpy).toHaveBeenNthCalledWith(2, "/api/v1/health/ready");
    expect(live.status).toBe("alive");
    expect(ready.status).toBe("ready");
  });
});
