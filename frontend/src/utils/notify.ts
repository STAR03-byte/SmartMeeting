import { ElMessage } from "element-plus";

import { getApiErrorMessage } from "../api/client";

export function notifyApiError(err: unknown, options?: { prefix?: string }): void {
  const message = getApiErrorMessage(err);
  const fullMessage = options?.prefix ? `${options.prefix}: ${message}` : message;
  ElMessage.error(fullMessage);
}
