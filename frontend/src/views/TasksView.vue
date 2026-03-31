<template>
  <section class="tasks-page">
    <header class="hero-header">
      <div>
        <h1>任务中心</h1>
        <p>查看会议行动项，并快速推进任务状态。</p>
      </div>
      <el-button @click="refreshTasks">刷新</el-button>
    </header>

    <AppErrorAlert :error="error" :closable="false" />

    <el-card class="base-card filter-card">
      <div class="filter-row">
        <el-select v-model="filters.status" placeholder="状态" clearable style="width: 140px" @change="applyFiltersAndRefresh">
          <el-option label="待办" value="todo" />
          <el-option label="进行中" value="in_progress" />
          <el-option label="已完成" value="done" />
        </el-select>

        <el-select
          v-model="filters.priority"
          placeholder="优先级"
          clearable
          style="width: 140px"
          @change="applyFiltersAndRefresh"
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
          @keyup.enter="applyFiltersAndRefresh"
          @clear="applyFiltersAndRefresh"
        />

        <el-select v-model="sortBy" placeholder="排序" style="width: 180px" @change="handleSortChange">
          <el-option label="按创建时间（新→旧）" value="id_desc" />
          <el-option label="按截止时间（近→远）" value="due_at_asc" />
          <el-option label="按截止时间（远→近）" value="due_at_desc" />
        </el-select>

        <el-button type="primary" @click="applyFiltersAndRefresh">应用筛选</el-button>
      </div>
    </el-card>

    <el-card class="base-card" v-loading="loading">
      <el-table :data="tasks" stripe>
        <el-table-column prop="title" label="任务" min-width="240">
          <template #default="{ row }">
            <span :class="{ 'task-done': row.status === 'done' }">{{ row.title }}</span>
          </template>
        </el-table-column>
        <el-table-column label="所属会议" width="120">
          <template #default="{ row }">
            <router-link v-if="row.meeting_id" :to="`/meetings/${row.meeting_id}`" class="meeting-link">
              #{{ row.meeting_id }}
            </router-link>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="优先级" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="priorityTag(row.priority)">{{ priorityLabel(row.priority) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="截止时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.due_at) }}
          </template>
        </el-table-column>
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

    <el-pagination
      v-if="totalCount > pageSize"
      class="pagination"
      layout="prev, pager, next"
      :total="totalCount"
      :page-size="pageSize"
      :current-page="currentPage"
      @current-change="handlePageChange"
    />
  </section>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";

import { getApiErrorMessage } from "../api/client";
import AppErrorAlert from "../components/AppErrorAlert.vue";
import { notifyApiError } from "../utils/notify";
import {
  getTasks,
  updateTaskStatus,
  type TaskListParams,
  type TaskListResult,
  type TaskItem,
  type TaskPriority,
  type TaskStatus,
} from "../api/tasks";

const tasks = ref<TaskItem[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);

const currentPage = ref(1);
const pageSize = 20;
const totalCount = ref(0);
const sortBy = ref("id_desc");

const filters = reactive<{
  status: TaskStatus | undefined;
  priority: TaskPriority | undefined;
  keyword: string;
}>({
  status: undefined,
  priority: undefined,
  keyword: "",
});

function applyFiltersAndRefresh() {
  currentPage.value = 1;
  refreshTasks();
}

async function refreshTasks() {
  loading.value = true;
  error.value = null;
  totalCount.value = 0;
  try {
    const params: TaskListParams = {
      limit: pageSize,
      offset: (currentPage.value - 1) * pageSize,
      sort_by: sortBy.value,
    };
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
    const result: TaskListResult = await getTasks(params);
    tasks.value = result.items;
    totalCount.value = result.total;
  } catch (err) {
    error.value = getApiErrorMessage(err);
  } finally {
    loading.value = false;
  }
}

function handlePageChange(page: number) {
  currentPage.value = page;
  refreshTasks();
}

function handleSortChange() {
  currentPage.value = 1;
  refreshTasks();
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
    notifyApiError(err);
    await refreshTasks();
  }
}

onMounted(async () => {
  await refreshTasks();
});

function priorityLabel(p: string): string {
  const map: Record<string, string> = { high: "高", medium: "中", low: "低" };
  return map[p] ?? p;
}

function priorityTag(p: string): string {
  const map: Record<string, string> = { high: "danger", medium: "warning", low: "info" };
  return map[p] ?? "";
}

function formatDate(iso: string | null): string {
  if (!iso) return "-";
  return new Date(iso).toLocaleString("zh-CN");
}
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

.task-done {
  text-decoration: line-through;
  color: #94a3b8;
}

.meeting-link {
  color: #0c4a84;
  text-decoration: none;
  font-weight: 500;
}

.meeting-link:hover {
  text-decoration: underline;
}

.pagination {
  margin-top: 8px;
  display: flex;
  justify-content: flex-end;
}
</style>
