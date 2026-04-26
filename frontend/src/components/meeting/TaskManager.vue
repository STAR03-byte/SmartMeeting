<template>
  <el-skeleton animated :loading="store.loading">
    <template #template>
      <el-card class="base-card">
        <template #header>
          <div class="panel-header">
            <el-skeleton-item variant="text" style="width: 64px; height: 24px" />
            <el-skeleton-item variant="text" style="width: 32px; height: 24px" />
          </div>
        </template>
        <div class="plain-list">
          <div v-for="i in 3" :key="i" class="task-row skeleton-row">
            <div class="skeleton-main">
              <el-skeleton-item variant="text" style="width: 120px" />
              <el-skeleton-item variant="rect" style="width: 32px; height: 24px; border-radius: 4px" />
            </div>
            <el-skeleton-item variant="rect" style="width: 110px; height: 32px; border-radius: 4px" />
          </div>
        </div>
      </el-card>
    </template>

    <template #default>
      <el-card class="base-card">
        <template #header>
          <div class="panel-header">
            <span>{{ $t("task.listTitle") }}</span>
            <div class="header-actions">
              <el-button text @click="openCreateDialog">{{ $t("meeting.newTask") }}</el-button>
              <el-button text @click="$emit('reload')">{{ $t("common.refresh") }}</el-button>
            </div>
          </div>
        </template>

        <el-empty v-if="store.tasks.length === 0" :description="$t('task.empty')" />
        <div v-else class="task-sections">
          <section v-if="draftTasks.length > 0" class="draft-section">
            <div class="section-title">
              <span>待确认行动项</span>
              <el-tag size="small" type="warning">{{ draftTasks.length }}</el-tag>
            </div>
            <ul class="plain-list">
              <li v-for="task in draftTasks" :key="task.id" class="task-row draft-row">
                <div class="task-info">
                  <span class="task-title">{{ task.title }}</span>
                  <span class="assignee-text">负责人：{{ assigneeLabel(task.assignee_id) }}</span>
                  <span class="due-text">{{ $t("task.dueDateLabel") }}：{{ formatDate(task.due_at) }}</span>
                  <el-tag size="small" type="warning">AI 草稿</el-tag>
                  <el-tag size="small" :type="priorityTag(task.priority)">{{ priorityLabel(task.priority) }}</el-tag>
                </div>
                <div class="task-actions">
                  <el-button size="small" type="primary" :disabled="!task.can_manage" @click="confirmDraftTask(task.id)">
                    确认
                  </el-button>
                  <el-button size="small" :disabled="!task.can_manage" @click="openEditDialog(task)">编辑</el-button>
                  <el-button
                    size="small"
                    type="danger"
                    plain
                    :disabled="!task.can_manage"
                    @click="cancelDraftTask(task.id)"
                  >
                    取消
                  </el-button>
                </div>
              </li>
            </ul>
          </section>

          <section>
            <div v-if="draftTasks.length > 0" class="section-title">
              <span>正式任务</span>
              <el-tag size="small" type="info">{{ confirmedTasks.length }}</el-tag>
            </div>
            <el-empty v-if="confirmedTasks.length === 0" description="暂无正式任务" />
            <ul v-else class="plain-list">
              <li v-for="task in confirmedTasks" :key="task.id" class="task-row">
                <div class="task-info">
                  <span class="task-title" :class="{ done: task.status === 'done' }">{{ task.title }}</span>
                  <span class="assignee-text">负责人：{{ assigneeLabel(task.assignee_id) }}</span>
                  <span class="due-text">{{ $t("task.dueDateLabel") }}：{{ formatDate(task.due_at) }}</span>
                  <span class="due-text">{{ $t("task.reminder") }}：{{ formatDate(task.reminder_at) }}</span>
                  <el-tag size="small" :type="priorityTag(task.priority)">{{ priorityLabel(task.priority) }}</el-tag>
                  <el-tag v-if="task.status === 'cancelled'" size="small" type="info">已取消</el-tag>
                  <el-tag v-if="task.is_overdue" size="small" type="danger">{{ $t("task.overdue") }}</el-tag>
                  <el-tag v-else-if="task.is_due_soon" size="small" type="warning">{{ $t("task.dueSoon") }}</el-tag>
                </div>
                <div class="task-actions">
                  <el-select
                    :model-value="task.status"
                    size="small"
                    style="width: 112px"
                    :disabled="!task.can_manage || task.status === 'cancelled'"
                    @change="(val: string) => handleStatusChange(task.id, val as TaskStatus)"
                  >
                    <el-option :label="$t('task.statusTodo')" value="todo" />
                    <el-option :label="$t('task.statusInProgress')" value="in_progress" />
                    <el-option :label="$t('task.statusDone')" value="done" />
                    <el-option label="已取消" value="cancelled" disabled />
                  </el-select>
                  <el-button
                    size="small"
                    :disabled="!task.can_manage || task.status === 'cancelled'"
                    @click="openEditDialog(task)"
                  >
                    编辑
                  </el-button>
                </div>
              </li>
            </ul>
          </section>
        </div>
      </el-card>

      <el-dialog v-model="editDialogVisible" title="编辑任务" width="600px">
        <TaskFormWithSuggestions
          :key="editingTaskId ?? 0"
          :meeting-id="meetingId"
          :participants="assigneeOptions"
          :initial-data="editFormData"
          :is-edit="true"
          @submit="handleEditFormSubmit"
          @cancel="editDialogVisible = false"
        />
      </el-dialog>

      <el-dialog v-model="createDialogVisible" title="新建任务" width="600px">
        <TaskFormWithSuggestions
          :meeting-id="meetingId"
          :participants="assigneeOptions"
          @submit="handleTaskFormSubmit"
          @cancel="createDialogVisible = false"
        />
      </el-dialog>
    </template>
  </el-skeleton>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import { ElMessage } from "element-plus";

import { getMeetingParticipants, type MeetingParticipantOut } from "../../api/participants";
import { updateTask, type TaskItem, type TaskStatus } from "../../api/tasks";
import type { TaskPriority } from "../../api/types";
import { useMeetingStore } from "../../stores/meetingStore";
import { notifyApiError } from "../../utils/notify";
import TaskFormWithSuggestions from "./TaskFormWithSuggestions.vue";

type TaskFormSubmitPayload = {
  title: string;
  description: string;
  due_at: Date | null;
  priority: TaskPriority;
  assignee_id: number | null;
  meeting_id: number;
  reminder_at?: Date | null;
};

const props = defineProps<{ meetingId: number }>();
defineEmits<{ (e: "reload"): void }>();

const { t } = useI18n();
const store = useMeetingStore();

const createDialogVisible = ref(false);
const editDialogVisible = ref(false);
const editingTaskId = ref<number | null>(null);
const assigneeOptions = ref<MeetingParticipantOut[]>([]);
const editForm = ref({
  title: "",
  description: "",
  assignee_id: null as number | null,
  priority: "medium" as TaskPriority,
  due_at: null as string | null,
  reminder_at: null as string | null,
});

const draftTasks = computed(() => store.tasks.filter((task) => task.status === "draft"));
const confirmedTasks = computed(() => store.tasks.filter((task) => task.status !== "draft"));

const editFormData = computed(() => ({
  title: editForm.value.title,
  description: editForm.value.description,
  due_at: editForm.value.due_at ? new Date(editForm.value.due_at) : null,
  priority: editForm.value.priority,
  assignee_id: editForm.value.assignee_id,
  reminder_at: editForm.value.reminder_at ? new Date(editForm.value.reminder_at) : null,
}));

const assigneeLabelMap = computed(() => {
  const map = new Map<number, string>();
  for (const participant of assigneeOptions.value) {
    map.set(participant.user_id, participant.full_name || participant.username);
  }
  return map;
});

function assigneeLabel(assigneeId: number | null): string {
  if (assigneeId == null) return "未指定";
  return assigneeLabelMap.value.get(assigneeId) || "已删除用户";
}

async function loadAssigneeOptions() {
  try {
    assigneeOptions.value = await getMeetingParticipants(props.meetingId);
  } catch {
    assigneeOptions.value = [];
  }
}

function openCreateDialog() {
  createDialogVisible.value = true;
}

function openEditDialog(task: TaskItem) {
  editingTaskId.value = task.id;
  editForm.value = {
    title: task.title,
    description: task.description || "",
    assignee_id: task.assignee_id,
    priority: task.priority,
    due_at: task.due_at ? task.due_at.replace("T", " ").slice(0, 19) : null,
    reminder_at: task.reminder_at ? task.reminder_at.replace("T", " ").slice(0, 19) : null,
  };
  editDialogVisible.value = true;
}

function formatDateToString(date: Date | string): string {
  if (typeof date === "string") return date;
  return new Date(date).toISOString().slice(0, 19).replace("T", " ");
}

function upsertTask(updated: TaskItem) {
  const index = store.tasks.findIndex((item) => item.id === updated.id);
  if (index >= 0) {
    store.tasks[index] = updated;
  }
}

async function handleTaskFormSubmit(formData: TaskFormSubmitPayload) {
  try {
    await store.createMeetingTask({
      meeting_id: props.meetingId,
      title: formData.title.trim(),
      description: formData.description?.trim() || null,
      assignee_id: formData.assignee_id,
      priority: formData.priority,
      due_at: formData.due_at ? formatDateToString(formData.due_at) : null,
      reminder_at: null,
    });
    ElMessage.success("任务创建成功");
    createDialogVisible.value = false;
    window.dispatchEvent(new Event("tasks-updated"));
  } catch (err) {
    notifyApiError(err);
  }
}

async function handleEditFormSubmit(formData: TaskFormSubmitPayload) {
  if (!editingTaskId.value) return;
  try {
    const updated = await updateTask(editingTaskId.value, {
      title: formData.title.trim(),
      description: formData.description?.trim() || null,
      assignee_id: formData.assignee_id,
      priority: formData.priority,
      due_at: formData.due_at ? formatDateToString(formData.due_at) : null,
      reminder_at: formData.reminder_at ? formatDateToString(formData.reminder_at) : null,
    });
    upsertTask(updated);
    ElMessage.success("任务已更新");
    editDialogVisible.value = false;
    window.dispatchEvent(new Event("tasks-updated"));
  } catch (err) {
    notifyApiError(err);
  }
}

async function handleStatusChange(taskId: number, newStatus: TaskStatus) {
  try {
    await store.changeTaskStatus(taskId, newStatus);
    ElMessage.success(t("task.statusUpdateSuccess"));
    window.dispatchEvent(new Event("tasks-updated"));
  } catch (err) {
    notifyApiError(err);
  }
}

async function confirmDraftTask(taskId: number) {
  await handleStatusChange(taskId, "todo");
}

async function cancelDraftTask(taskId: number) {
  await handleStatusChange(taskId, "cancelled");
}

function priorityLabel(priority: string): string {
  const map: Record<string, string> = {
    high: t("task.priorityHigh"),
    medium: t("task.priorityMedium"),
    low: t("task.priorityLow"),
  };
  return map[priority] ?? priority;
}

function priorityTag(priority: string): string {
  const map: Record<string, string> = { high: "danger", medium: "warning", low: "info" };
  return map[priority] ?? "";
}

function formatDate(iso: string | null): string {
  if (!iso) return "-";
  return new Date(iso).toLocaleString("zh-CN");
}

onMounted(() => {
  loadAssigneeOptions();
});

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

.panel-header,
.section-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
  color: var(--el-text-color-primary);
  font-size: 16px;
}

.task-sections {
  display: flex;
  flex-direction: column;
  gap: 22px;
}

.draft-section {
  padding-bottom: 18px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.section-title {
  margin-bottom: 12px;
}

.plain-list {
  margin: 0;
  padding-left: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.task-row {
  padding: 14px 16px;
  background: var(--el-fill-color-lighter);
  border-radius: var(--el-border-radius-small);
  border: 1px solid transparent;
  transition: all 0.2s ease;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.task-row:hover {
  background: var(--el-color-primary-light-9);
  border-color: var(--el-color-primary-light-7);
}

.draft-row {
  background: var(--el-color-warning-light-9);
  border-color: var(--el-color-warning-light-7);
}

.skeleton-row {
  background: var(--el-fill-color-lighter);
}

.skeleton-main {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.task-info {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
  flex-wrap: wrap;
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

.header-actions,
.task-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.assignee-text,
.due-text {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

@media (max-width: 900px) {
  .task-row {
    align-items: flex-start;
    flex-direction: column;
  }

  .task-actions {
    width: 100%;
    justify-content: flex-start;
    flex-wrap: wrap;
  }
}
</style>
