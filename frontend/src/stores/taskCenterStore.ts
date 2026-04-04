import { defineStore } from "pinia";

import { getTasks, type TaskItem, type TaskListParams, type TaskListResult } from "../api/tasks";
import { getApiErrorMessage } from "../api/client";

interface TaskCenterState {
  tasks: TaskItem[];
  total: number;
  loading: boolean;
  error: string | null;
}

export const useTaskCenterStore = defineStore("task-center", {
  state: (): TaskCenterState => ({
    tasks: [],
    total: 0,
    loading: false,
    error: null,
  }),
  actions: {
    async fetchTasks(params: TaskListParams = {}) {
      this.loading = true;
      this.error = null;
      try {
        const result: TaskListResult = await getTasks(params);
        this.tasks = result.items;
        this.total = result.total;
      } catch (error) {
        this.error = getApiErrorMessage(error);
        throw error;
      } finally {
        this.loading = false;
      }
    },
    clearAllState() {
      this.tasks = [];
      this.total = 0;
      this.loading = false;
      this.error = null;
    },
  },
});
