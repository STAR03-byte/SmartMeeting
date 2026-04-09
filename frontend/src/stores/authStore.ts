import { defineStore } from "pinia";
import { useMeetingStore } from "./meetingStore";
import { useTaskCenterStore } from "./taskCenterStore";

import { getApiErrorMessage } from "../api/client";
import { fetchCurrentUser, login, type LoginResponse } from "../api/auth";
import type { UserItem } from "../api/types";
import { notifyApiError } from "../utils/notify";

interface AuthState {
  token: string | null;
  currentUser: UserItem | null;
  loading: boolean;
  error: string | null;
}

const STORAGE_KEY = "smartmeeting_access_token";

function hasBrowserStorage(): boolean {
  return typeof window !== "undefined";
}

function getStoredToken(): string | null {
  if (!hasBrowserStorage()) {
    return null;
  }
  const sessionToken = sessionStorage.getItem(STORAGE_KEY);
  if (sessionToken) {
    return sessionToken;
  }
  return localStorage.getItem(STORAGE_KEY);
}

function setStoredToken(token: string | null): void {
  if (!hasBrowserStorage()) {
    return;
  }
  if (token) {
    sessionStorage.setItem(STORAGE_KEY, token);
    localStorage.removeItem(STORAGE_KEY);
    return;
  }
  sessionStorage.removeItem(STORAGE_KEY);
  localStorage.removeItem(STORAGE_KEY);
}

export const useAuthStore = defineStore("auth", {
  state: (): AuthState => ({
    token: getStoredToken(),
    currentUser: null,
    loading: false,
    error: null,
  }),
  actions: {
    setToken(token: string | null) {
      this.token = token;
      setStoredToken(token);
    },
    async signIn(username: string, password: string) {
      this.loading = true;
      this.error = null;
      try {
        const resp: LoginResponse = await login(username, password);
        this.setToken(resp.access_token);
        await this.loadCurrentUser();
      } catch (error) {
        this.error = getApiErrorMessage(error);
        notifyApiError(error, { prefix: "登录失败" });
        throw error;
      } finally {
        this.loading = false;
      }
    },
    async loadCurrentUser() {
      if (!this.token) {
        this.currentUser = null;
        return;
      }

      this.error = null;
      try {
        this.currentUser = await fetchCurrentUser<UserItem>();
      } catch (error) {
        this.error = getApiErrorMessage(error);
        notifyApiError(error, { prefix: "加载当前用户失败" });
        this.currentUser = null;
        throw error;
      }
    },
    signOut() {
      const meetingStore = useMeetingStore();
      const taskCenterStore = useTaskCenterStore();
      meetingStore.clearAllState();
      taskCenterStore.clearAllState();
      this.currentUser = null;
      this.setToken(null);
    },
  },
});
