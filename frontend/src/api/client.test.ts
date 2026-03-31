import axios, { AxiosError } from "axios";
import { describe, expect, it } from "vitest";

import { getApiErrorMessage, type ApiErrorResponse } from "./client";

function buildAxiosError(data: ApiErrorResponse): AxiosError<ApiErrorResponse> {
  return new AxiosError<ApiErrorResponse>(
    "Request failed",
    "400",
    undefined,
    undefined,
    {
      data,
      status: 400,
      statusText: "Bad Request",
      headers: {},
      config: { headers: axios.AxiosHeaders.from({}) },
    },
  );
}

describe("getApiErrorMessage", () => {
  it("returns detail string first when present", () => {
    const error = buildAxiosError({
      detail: "Meeting not found",
      error_code: "NOT_FOUND",
    });

    expect(getApiErrorMessage(error)).toBe("Meeting not found");
  });

  it("returns first validation message when detail is array", () => {
    const error = buildAxiosError({
      detail: [{ msg: "Field required" }],
      error_code: "REQUEST_VALIDATION_ERROR",
    });

    expect(getApiErrorMessage(error)).toBe("Field required");
  });

  it("falls back to mapped error_code message", () => {
    const error = buildAxiosError({ error_code: "UNAUTHORIZED" });

    expect(getApiErrorMessage(error)).toBe("登录已失效，请重新登录");
  });

  it("falls back to axios message when code is unknown", () => {
    const error = buildAxiosError({ error_code: "UNKNOWN_CODE" });

    expect(getApiErrorMessage(error)).toBe("Request failed");
  });
});
