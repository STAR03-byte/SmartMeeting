import { describe, expect, it } from "vitest";

import { getSharedMeetingErrorState } from "./shared-meeting-error";

describe("getSharedMeetingErrorState", () => {
  it("maps 404 token errors to friendly state", () => {
    expect(getSharedMeetingErrorState(new Error("404 Shared meeting not found"))).toEqual({
      kind: "not_found",
      title: "分享链接已失效或不存在",
      message: "请联系会议组织者重新分享链接，或返回首页查看其他会议。",
      showRetry: true,
      showHome: true,
      redirectToLogin: false,
    });
  });

  it("maps auth errors to login hint", () => {
    expect(getSharedMeetingErrorState(new Error("401 User not found"))).toEqual({
      kind: "auth",
      title: "分享链接需要重新登录",
      message: "当前登录状态已失效，请重新登录后继续查看。登录后会自动返回该分享页。",
      showRetry: false,
      showHome: true,
      redirectToLogin: true,
    });
  });

  it("falls back for unknown errors", () => {
    expect(getSharedMeetingErrorState(new Error("boom"))).toEqual({
      kind: "unknown",
      title: "加载分享内容失败",
      message: "请稍后重试，或返回首页查看其他会议。",
      showRetry: true,
      showHome: true,
      redirectToLogin: false,
    });
  });
});
