import { defineStore } from "pinia";

import { getApiErrorMessage } from "../api/client";
import { fetchCurrentUser, login, type LoginResponse } from "../api/auth";
import type { UserItem } from "../api/types";

interface AuthState {
  token: string | null;
  currentUser: UserItem | null;
  loading: boolean;
  error: string | null;
}

const STORAGE_KEY = "smartmeeting_access_token";

export const useAuthStore = defineStore("auth", {
  state: (): AuthState => ({
    token: localStorage.getItem(STORAGE_KEY),
    currentUser: null,
    loading: false,
    error: null,
  }),
  actions: {
    setToken(token: string | null) {
      this.token = token;
      if (token) {
        localStorage.setItem(STORAGE_KEY, token);
      } else {
        localStorage.removeItem(STORAGE_KEY);
      }
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
        this.currentUser = null;
        throw error;
      }
    },
    signOut() {
      this.currentUser = null;
      this.setToken(null);
    },
  },
});
