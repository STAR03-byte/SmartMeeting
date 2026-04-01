<template>
  <section class="tasks-page">
    <header class="hero-header">
      <div>
        <h1>任务中心</h1>
        <p>集中查看全部会议行动项，并支持手动调整负责人与优先级。</p>
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
      <div class="category-hint">
        <el-tag size="small" effect="plain" type="warning">AI行动项：由转写自动识别</el-tag>
        <el-tag size="small" effect="plain" type="info">手动任务：会议中人工创建</el-tag>
        <el-tag size="small" effect="plain" type="danger">逾期：已超过截止时间</el-tag>
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
        <el-table-column label="任务分类" width="240">
          <template #default="{ row }">
            <div class="category-tags">
              <el-tag size="small" :type="row.transcript_id ? 'warning' : 'info'">
                {{ row.transcript_id ? "AI行动项" : "手动任务" }}
              </el-tag>
              <el-tag v-if="row.is_overdue" size="small" type="danger">逾期</el-tag>
              <el-tag v-else-if="row.is_due_soon" size="small" type="warning">即将到期</el-tag>
              <el-tag v-else-if="row.priority === 'high'" size="small" type="danger">高优先级</el-tag>
              <el-tag v-if="!row.assignee_id" size="small" type="info">未分配</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="负责人" width="160">
          <template #default="{ row }">
            {{ resolveAssigneeName(row.assignee_id) }}
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
        <el-table-column label="操作" width="100">
          <template #default="scope">
            <el-button size="small" @click="openEditDialog(scope.row)">编辑</el-button>
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

    <el-dialog v-model="editDialogVisible" title="编辑任务" width="520px">
      <el-form label-width="80px">
        <el-form-item label="标题">
          <el-input v-model="editForm.title" placeholder="请输入任务标题" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="editForm.description" type="textarea" :rows="3" placeholder="可选" />
        </el-form-item>
        <el-form-item label="负责人">
          <el-select v-model="editForm.assignee_id" clearable placeholder="请选择负责人" style="width: 100%">
            <el-option
              v-for="user in users"
              :key="user.id"
              :label="`${user.full_name}（${user.username}）`"
              :value="user.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="editForm.priority" style="width: 160px">
            <el-option label="高" value="high" />
            <el-option label="中" value="medium" />
            <el-option label="低" value="low" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingEdit" @click="saveTaskEdit">保存</el-button>
      </template>
    </el-dialog>
  </section>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";

import AppErrorAlert from "../components/AppErrorAlert.vue";
import { notifyApiError } from "../utils/notify";
import {
  getTasks,
  updateTask,
  updateTaskStatus,
  type TaskListParams,
  type TaskListResult,
  type TaskItem,
  type TaskPriority,
  type TaskStatus,
} from "../api/tasks";
import { getUsers, type UserItem } from "../api/users";

const tasks = ref<TaskItem[]>([]);
const users = ref<UserItem[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);
const editDialogVisible = ref(false);
const editingTask = ref<TaskItem | null>(null);
const savingEdit = ref(false);

const editForm = reactive<{
  title: string;
  description: string;
  assignee_id: number | null;
  priority: TaskPriority;
}>({
  title: "",
  description: "",
  assignee_id: null,
  priority: "medium",
});

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
    error.value = notifyApiError(err, { prefix: "加载任务失败" });
  } finally {
    loading.value = false;
  }
}

async function refreshUsers() {
  try {
    users.value = await getUsers();
  } catch (err) {
    notifyApiError(err, { prefix: "加载用户失败" });
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

function openEditDialog(task: TaskItem) {
  editingTask.value = task;
  editForm.title = task.title;
  editForm.description = task.description ?? "";
  editForm.assignee_id = task.assignee_id;
  editForm.priority = task.priority;
  editDialogVisible.value = true;
}

async function saveTaskEdit() {
  if (!editingTask.value) return;
  const trimmedTitle = editForm.title.trim();
  if (!trimmedTitle) {
    ElMessage.warning("任务标题不能为空");
    return;
  }

  savingEdit.value = true;
  try {
    const updated = await updateTask(editingTask.value.id, {
      title: trimmedTitle,
      description: editForm.description.trim() || null,
      assignee_id: editForm.assignee_id,
      priority: editForm.priority,
    });
    const index = tasks.value.findIndex((item) => item.id === updated.id);
    if (index >= 0) {
      tasks.value[index] = updated;
    }
    ElMessage.success("任务已更新");
    editDialogVisible.value = false;
  } catch (err) {
    notifyApiError(err, { prefix: "更新任务失败" });
  } finally {
    savingEdit.value = false;
  }
}

onMounted(async () => {
  await refreshUsers();
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

function resolveAssigneeName(assigneeId: number | null): string {
  if (!assigneeId) return "未分配";
  const user = users.value.find((item) => item.id === assigneeId);
  return user ? `${user.full_name}（${user.username}）` : `用户 #${assigneeId}`;
}
</script>

<style scoped>
.tasks-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.hero-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  background: linear-gradient(135deg, var(--el-color-primary-light-9) 0%, var(--el-color-primary-light-8) 100%);
  border-radius: var(--el-border-radius-base);
  padding: 32px 40px;
  box-shadow: var(--el-box-shadow-light);
}

.hero-header h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  color: var(--el-color-primary-dark-2);
  letter-spacing: -0.5px;
}

.hero-header p {
  margin: 12px 0 0;
  color: var(--el-color-primary);
  font-size: 16px;
}

.base-card {
  border-radius: var(--el-border-radius-base);
  border: none;
  box-shadow: var(--el-box-shadow-light) !important;
}

.filter-card {
  background: var(--el-bg-color);
}

.filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: center;
}

.category-hint {
  margin-top: 12px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.category-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.muted-text {
  color: var(--el-text-color-placeholder);
}

.task-done {
  text-decoration: line-through;
  color: var(--el-text-color-secondary);
}

.meeting-link {
  color: var(--el-color-primary);
  text-decoration: none;
  font-weight: 600;
  padding: 4px 8px;
  background: var(--el-color-primary-light-9);
  border-radius: var(--el-border-radius-small);
  transition: all 0.2s ease;
}

.meeting-link:hover {
  background: var(--el-color-primary-light-8);
  color: var(--el-color-primary-dark-2);
}

.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

/* Custom Table Styles */
:deep(.el-table) {
  --el-table-border-color: var(--el-border-color-lighter);
  --el-table-header-bg-color: var(--el-fill-color-light);
  --el-table-row-hover-bg-color: var(--el-color-primary-light-9);
}

:deep(.el-table__header-wrapper th) {
  height: 56px;
  font-weight: 600;
  color: var(--el-text-color-regular);
  border-bottom: none;
}

:deep(.el-table__body-wrapper td) {
  padding: 16px 0;
}
</style>
