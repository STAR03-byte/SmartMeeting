export interface SharedMeetingErrorState {
  kind: "auth" | "not_found" | "unknown";
  title: string;
  message: string;
  showRetry: boolean;
  showHome: boolean;
  redirectToLogin: boolean;
}

export function getSharedMeetingErrorState(error: unknown): SharedMeetingErrorState {
  if (error instanceof Error) {
    if (error.message.includes("401") || error.message.includes("User not found")) {
      return {
        kind: "auth",
        title: "分享链接需要重新登录",
        message: "当前登录状态已失效，请重新登录后继续查看。登录后会自动返回该分享页。",
        showRetry: false,
        showHome: true,
        redirectToLogin: true,
      };
    }
    if (error.message.includes("404") || error.message.includes("Shared meeting not found")) {
      return {
        kind: "not_found",
        title: "分享链接已失效或不存在",
        message: "请联系会议组织者重新分享链接，或返回首页查看其他会议。",
        showRetry: true,
        showHome: true,
        redirectToLogin: false,
      };
    }
  }

  return {
    kind: "unknown",
    title: "加载分享内容失败",
    message: "请稍后重试，或返回首页查看其他会议。",
    showRetry: true,
    showHome: true,
    redirectToLogin: false,
  };
}
