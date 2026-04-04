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
            <span>{{ $t('task.listTitle') }}</span>
            <el-button text @click="$emit('reload')">{{ $t('common.refresh') }}</el-button>
          </div>
        </template>

        <el-empty v-if="store.tasks.length === 0" :description="$t('task.empty')" />
        <ul v-else class="plain-list">
          <li v-for="task in store.tasks" :key="task.id" class="task-row">
            <div class="task-info">
              <span class="task-title" :class="{ done: task.status === 'done' }">{{ task.title }}</span>
              <span class="assignee-text">负责人：{{ assigneeLabel(task.assignee_id) }}</span>
              <el-tag size="small" :type="priorityTag(task.priority)">{{ priorityLabel(task.priority) }}</el-tag>
              <el-tag v-if="task.is_overdue" size="small" type="danger">{{ $t('task.overdue') }}</el-tag>
              <el-tag v-else-if="task.is_due_soon" size="small" type="warning">{{ $t('task.dueSoon') }}</el-tag>
            </div>
            <div class="task-actions">
              <el-select
                :model-value="task.status"
                size="small"
                style="width: 110px"
                @change="(val: string) => handleStatusChange(task.id, val as TaskStatus)"
              >
                <el-option :label="$t('task.statusTodo')" value="todo" />
                <el-option :label="$t('task.statusInProgress')" value="in_progress" />
                <el-option :label="$t('task.statusDone')" value="done" />
              </el-select>
              <el-button size="small" @click="openEditDialog(task)">编辑</el-button>
            </div>
          </li>
        </ul>
      </el-card>

      <el-dialog v-model="editDialogVisible" title="编辑任务" width="560px">
        <el-form ref="editFormRef" :model="editForm" label-width="92px">
          <el-form-item label="任务标题" prop="title" :rules="[{ required: true, message: '请输入任务标题', trigger: 'blur' }]">
            <el-input v-model="editForm.title" maxlength="200" show-word-limit />
          </el-form-item>
          <el-form-item label="任务描述" prop="description">
            <el-input v-model="editForm.description" type="textarea" :rows="3" />
          </el-form-item>
          <el-form-item label="负责人" prop="assignee_id">
            <el-select v-model="editForm.assignee_id" clearable placeholder="请选择负责人" style="width: 100%">
              <el-option label="未指派" :value="null" />
              <el-option
                v-for="option in assigneeOptions"
                :key="option.user_id"
                :label="option.username"
                :value="option.user_id"
              />
            </el-select>
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="editDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="savingEdit" @click="submitEdit">保存</el-button>
        </template>
      </el-dialog>
    </template>
  </el-skeleton>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';
const { t } = useI18n();
import { computed, onMounted, reactive, ref } from "vue";
import type { FormInstance } from "element-plus";
import { useMeetingStore } from "../../stores/meetingStore";
import { ElMessage } from "element-plus";
import { notifyApiError } from "../../utils/notify";
import { updateTask, type TaskItem, type TaskStatus } from "../../api/tasks";
import { getMeetingParticipants, type MeetingParticipantOut } from "../../api/participants";

const props = defineProps<{ meetingId: number }>();
defineEmits<{ (e: 'reload'): void }>();

const store = useMeetingStore();
const editDialogVisible = ref(false);
const savingEdit = ref(false);
const editingTaskId = ref<number | null>(null);
const editFormRef = ref<FormInstance>();
const assigneeOptions = ref<MeetingParticipantOut[]>([]);
const editForm = reactive({
  title: "",
  description: "",
  assignee_id: null as number | null,
});

const assigneeLabelMap = computed(() => {
  const map = new Map<number, string>();
  for (const p of assigneeOptions.value) {
    map.set(p.user_id, p.username);
  }
  return map;
});

function assigneeLabel(assigneeId: number | null): string {
  if (assigneeId == null) return "未指派";
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
  ElMessage.info(t('task.statusManageOnly'));
}

function openEditDialog(task: TaskItem) {
  editingTaskId.value = task.id;
  editForm.title = task.title;
  editForm.description = task.description || "";
  editForm.assignee_id = task.assignee_id;
  editDialogVisible.value = true;
}

async function submitEdit() {
  if (!editingTaskId.value) return;
  if (!editFormRef.value) return;
  const valid = await editFormRef.value.validate().catch(() => false);
  if (!valid) return;

  savingEdit.value = true;
  try {
    const updated = await updateTask(editingTaskId.value, {
      title: editForm.title.trim(),
      description: editForm.description.trim() || null,
      assignee_id: editForm.assignee_id,
    });
    const index = store.tasks.findIndex((item) => item.id === updated.id);
    if (index >= 0) {
      store.tasks[index] = updated;
    }
    ElMessage.success("任务已更新");
    editDialogVisible.value = false;
    window.dispatchEvent(new Event('tasks-updated'));
  } catch (err) {
    notifyApiError(err);
  } finally {
    savingEdit.value = false;
  }
}

async function handleStatusChange(taskId: number, newStatus: TaskStatus) {
  try {
    await store.changeTaskStatus(taskId, newStatus);
    ElMessage.success(t('task.statusUpdateSuccess'));
    window.dispatchEvent(new Event('tasks-updated'));
  } catch (err) {
    notifyApiError(err);
  }
}

function priorityLabel(p: string): string {
  const map: Record<string, string> = { high: t('task.priorityHigh'), medium: t('task.priorityMedium'), low: t('task.priorityLow') };
  return map[p] ?? p;
}

function priorityTag(p: string): string {
  const map: Record<string, string> = { high: "danger", medium: "warning", low: "info" };
  return map[p] ?? "";
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

.assignee-text {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.task-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}
</style>
