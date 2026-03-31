import { describe, expect, it, vi } from "vitest";

import { apiClient } from "./client";

describe("participants api module", () => {
  it("loads participants by meeting", async () => {
    const getSpy = vi.spyOn(apiClient, "get").mockResolvedValueOnce({
      data: [{ id: 1, meeting_id: 10, user_id: 2, participant_role: "required", attendance_status: "invited" }],
    } as never);

    const mod = await import("./participants");
    const result = await mod.getMeetingParticipants(10);

    expect(getSpy).toHaveBeenCalledWith("/api/v1/participants", {
      params: { meeting_id: 10 },
    });
    expect(result).toHaveLength(1);
  });

  it("creates participant", async () => {
    const postSpy = vi.spyOn(apiClient, "post").mockResolvedValueOnce({
      data: { id: 2, meeting_id: 10, user_id: 3, participant_role: "optional", attendance_status: "invited" },
    } as never);

    const mod = await import("./participants");
    const result = await mod.createMeetingParticipant({
      meeting_id: 10,
      user_id: 3,
      participant_role: "optional",
    });

    expect(postSpy).toHaveBeenCalledWith("/api/v1/participants", {
      meeting_id: 10,
      user_id: 3,
      participant_role: "optional",
    });
    expect(result.user_id).toBe(3);
  });

  it("updates participant", async () => {
    const patchSpy = vi.spyOn(apiClient, "patch").mockResolvedValueOnce({
      data: { id: 2, meeting_id: 10, user_id: 3, participant_role: "required", attendance_status: "accepted" },
    } as never);

    const mod = await import("./participants");
    const result = await mod.updateMeetingParticipant(2, {
      participant_role: "required",
      attendance_status: "accepted",
    });

    expect(patchSpy).toHaveBeenCalledWith("/api/v1/participants/2", {
      participant_role: "required",
      attendance_status: "accepted",
    });
    expect(result.attendance_status).toBe("accepted");
  });

  it("deletes participant", async () => {
    const deleteSpy = vi.spyOn(apiClient, "delete").mockResolvedValueOnce({} as never);

    const mod = await import("./participants");
    await mod.deleteMeetingParticipant(5);

    expect(deleteSpy).toHaveBeenCalledWith("/api/v1/participants/5");
  });
});
