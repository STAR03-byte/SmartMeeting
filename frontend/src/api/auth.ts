import { apiClient } from "./client";

export interface LoginResponse {
  access_token: string;
  token_type: "bearer";
}

export async function login(username: string, password: string): Promise<LoginResponse> {
  const formData = new URLSearchParams();
  formData.set("username", username);
  formData.set("password", password);

  const resp = await apiClient.post<LoginResponse>("/api/v1/auth/login", formData, {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
  });

  return resp.data;
}

export async function fetchCurrentUser<T>(): Promise<T> {
  const resp = await apiClient.get<T>("/api/v1/auth/me");
  return resp.data;
}
