<template>
  <section class="tasks-page">
    <header class="hero-header">
      <div>
        <h1>任务中心</h1>
        <p>查看会议行动项，并快速推进任务状态。</p>
      </div>
      <el-button @click="refreshTasks">刷新</el-button>
    </header>

    <el-alert v-if="error" :title="error" type="error" show-icon :closable="false" />

    <el-card class="base-card filter-card">
      <div class="filter-row">
        <el-select v-model="filters.status" placeholder="状态" clearable style="width: 140px" @change="refreshTasks">
          <el-option label="待办" value="todo" />
          <el-option label="进行中" value="in_progress" />
          <el-option label="已完成" value="done" />
        </el-select>

        <el-select
          v-model="filters.priority"
          placeholder="优先级"
          clearable
          style="width: 140px"
          @change="refreshTasks"
        >
          <el-option label="高" value="high" />
          <el-option label="中" value="medium" />
          <el-option label="低" value="low" />
        </el-select>

        <el-input
          v-model="filters.keyword"
          placeholder="搜索任务标题"
          clearable
          style="max-width: 280px"
          @keyup.enter="refreshTasks"
          @clear="refreshTasks"
        />

        <el-button type="primary" @click="refreshTasks">应用筛选</el-button>
      </div>
    </el-card>

    <el-card class="base-card" v-loading="loading">
      <el-table :data="tasks" stripe>
        <el-table-column prop="title" label="任务" min-width="240" />
        <el-table-column prop="meeting_id" label="会议ID" width="100" />
        <el-table-column prop="priority" label="优先级" width="120" />
        <el-table-column label="提醒" width="120">
          <template #default="scope">
            <el-tag v-if="scope.row.is_overdue" type="danger">已逾期</el-tag>
            <el-tag v-else-if="scope.row.is_due_soon" type="warning">即将到期</el-tag>
            <span v-else class="muted-text">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="160">
          <template #default="scope">
            <el-select
              :model-value="scope.row.status"
              size="small"
              @change="(value: TaskStatus) => changeStatus(scope.row.id, value)"
            >
              <el-option label="待办" value="todo" />
              <el-option label="进行中" value="in_progress" />
              <el-option label="已完成" value="done" />
            </el-select>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </section>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";

import { getApiErrorMessage } from "../api/client";
import {
  getTasks,
  updateTaskStatus,
  type ListTasksParams,
  type TaskItem,
  type TaskPriority,
  type TaskStatus,
} from "../api/tasks";

const tasks = ref<TaskItem[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);
const filters = reactive<{
  status: TaskStatus | undefined;
  priority: TaskPriority | undefined;
  keyword: string;
}>({
  status: undefined,
  priority: undefined,
  keyword: "",
});

async function refreshTasks() {
  loading.value = true;
  error.value = null;
  try {
    const params: ListTasksParams = {};
    if (filters.status) {
      params.status = filters.status;
    }
    if (filters.priority) {
      params.priority = filters.priority;
    }
    const normalizedKeyword = filters.keyword.trim();
    if (normalizedKeyword.length > 0) {
      params.keyword = normalizedKeyword;
    }
    tasks.value = await getTasks(params);
  } catch (err) {
    error.value = getApiErrorMessage(err);
  } finally {
    loading.value = false;
  }
}

async function changeStatus(taskId: number, status: TaskStatus) {
  try {
    const updated = await updateTaskStatus(taskId, status);
    const index = tasks.value.findIndex((item) => item.id === taskId);
    if (index >= 0) {
      tasks.value[index] = updated;
    }
    ElMessage.success("任务状态已更新");
  } catch (err) {
    ElMessage.error(getApiErrorMessage(err));
    await refreshTasks();
  }
}

onMounted(async () => {
  await refreshTasks();
});
</script>

<style scoped>
.tasks-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.hero-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  background: linear-gradient(120deg, #eef8ff 0%, #f8f6ff 100%);
  border: 1px solid #dce8f4;
  border-radius: 18px;
  padding: 24px;
}

.hero-header h1 {
  margin: 0;
  font-size: 30px;
  color: #1d2f45;
}

.hero-header p {
  margin: 8px 0 0;
  color: #4b6077;
}

.base-card {
  border-radius: 12px;
}

.filter-card {
  padding-bottom: 0;
}

.filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.muted-text {
  color: #8aa0b8;
}
</style>
