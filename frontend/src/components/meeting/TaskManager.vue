<template>
  <el-skeleton animated :loading="store.loading">
    <template #template>
      <el-card class="base-card">
        <template #header>
          <div class="panel-header">
            <el-skeleton-item variant="text" style="width: 64px; height: 24px;" />
            <el-skeleton-item variant="text" style="width: 32px; height: 24px;" />
          </div>
        </template>
        <div class="plain-list">
          <div v-for="i in 3" :key="i" class="task-row" style="background: var(--el-fill-color-lighter); border-radius: var(--el-border-radius-small);">
            <div style="display: flex; align-items: center; gap: 12px; flex: 1;">
              <el-skeleton-item variant="text" style="width: 120px;" />
              <el-skeleton-item variant="rect" style="width: 32px; height: 24px; border-radius: 4px;" />
            </div>
            <el-skeleton-item variant="rect" style="width: 110px; height: 32px; border-radius: 4px;" />
          </div>
        </div>
      </el-card>
    </template>
    <template #default>
      <el-card class="base-card">
        <template #header>
          <div class="panel-header">
            <span>任务列表</span>
            <el-button text @click="$emit('reload')">刷新</el-button>
          </div>
        </template>

        <el-empty v-if="store.tasks.length === 0" description="暂无任务" />
        <ul v-else class="plain-list">
          <li v-for="task in store.tasks" :key="task.id" class="task-row">
            <div class="task-info">
              <span class="task-title" :class="{ done: task.status === 'done' }">{{ task.title }}</span>
              <el-tag size="small" :type="priorityTag(task.priority)">{{ priorityLabel(task.priority) }}</el-tag>
              <el-tag v-if="task.is_overdue" size="small" type="danger">已逾期</el-tag>
              <el-tag v-else-if="task.is_due_soon" size="small" type="warning">即将到期</el-tag>
            </div>
            <div class="task-actions">
              <el-select
                :model-value="task.status"
                size="small"
                style="width: 110px"
                @change="(val: string) => handleStatusChange(task.id, val as TaskStatus)"
              >
                <el-option label="待办" value="todo" />
                <el-option label="进行中" value="in_progress" />
                <el-option label="已完成" value="done" />
              </el-select>
            </div>
          </li>
        </ul>
      </el-card>
    </template>
  </el-skeleton>
</template>

<script setup lang="ts">
import { useMeetingStore } from "../../stores/meetingStore";
import { ElMessage } from "element-plus";
import { notifyApiError } from "../../utils/notify";
import type { TaskStatus } from "../../api/tasks";

defineProps<{ meetingId: number }>();
defineEmits<{ (e: 'reload'): void }>();

const store = useMeetingStore();

function openCreateDialog() {
  ElMessage.info("当前页面仅支持任务状态管理，请前往任务中心创建任务");
}

async function handleStatusChange(taskId: number, newStatus: TaskStatus) {
  try {
    await store.changeTaskStatus(taskId, newStatus);
    ElMessage.success("状态已更新");
  } catch (err) {
    notifyApiError(err);
  }
}

function priorityLabel(p: string): string {
  const map: Record<string, string> = { high: "高", medium: "中", low: "低" };
  return map[p] ?? p;
}

function priorityTag(p: string): string {
  const map: Record<string, string> = { high: "danger", medium: "warning", low: "info" };
  return map[p] ?? "";
}

defineExpose({
  openCreateDialog,
});
</script>

<style scoped>
.base-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  margin: 0;
  flex: 1;
  border-radius: var(--el-border-radius-base);
  border: none;
  box-shadow: var(--el-box-shadow-light) !important;
  background: var(--el-bg-color);
}

.base-card :deep(.el-card__header) {
  padding: 20px 24px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.base-card :deep(.el-card__body) {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
  color: var(--el-text-color-primary);
  font-size: 16px;
}

.plain-list {
  margin: 0;
  padding-left: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.task-row {
  padding: 16px 20px;
  background: var(--el-fill-color-lighter);
  border-radius: var(--el-border-radius-small);
  border: 1px solid transparent;
  transition: all 0.2s ease;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.task-row:hover {
  background: var(--el-color-primary-light-9);
  border-color: var(--el-color-primary-light-7);
}

.task-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.task-title {
  font-weight: 500;
  color: var(--el-text-color-primary);
  font-size: 15px;
}

.task-title.done {
  text-decoration: line-through;
  color: var(--el-text-color-placeholder);
}

.task-actions {
  flex-shrink: 0;
}
</style>
