<template>
  <section class="detail-page" v-loading="store.loading">
    <el-page-header @back="goBack" content="会议详情" />

    <el-card v-if="store.currentMeeting" class="base-card">
      <h2>{{ store.currentMeeting.title }}</h2>
      <p>{{ store.currentMeeting.description || "暂无描述" }}</p>
      <p class="organizer-line">
        组织者：{{ store.currentMeeting.organizer.full_name }} · 状态：{{ store.currentMeeting.status }}
      </p>
      <div class="action-row">
        <el-upload
          :auto-upload="false"
          :show-file-list="false"
          accept="audio/*"
          :on-change="onFilePicked"
        >
          <el-button type="primary">上传音频并转写</el-button>
        </el-upload>
        <el-button type="success" @click="runPostprocess">生成纪要与任务</el-button>
      </div>
      <p class="summary-block">{{ store.currentMeeting.summary || "暂无会议摘要" }}</p>
    </el-card>

    <el-alert
      v-if="store.error"
      :title="store.error"
      type="error"
      show-icon
      :closable="false"
    />

    <div class="panel-grid">
      <el-card class="base-card">
        <template #header>转写片段</template>
        <ul class="plain-list">
          <li v-for="item in store.transcripts" :key="item.id">
            #{{ item.segment_index }} {{ item.content }}
          </li>
        </ul>
      </el-card>

      <el-card class="base-card">
        <template #header>任务列表</template>
        <ul class="plain-list">
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
                @change="(val: string) => handleStatusChange(task.id, val as TaskStatusValue)"
              >
                <el-option label="待办" value="todo" />
                <el-option label="进行中" value="in_progress" />
                <el-option label="已完成" value="done" />
              </el-select>
            </div>
          </li>
          <li v-if="store.tasks.length === 0" class="empty-hint">暂无任务</li>
        </ul>
      </el-card>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";

import { useMeetingStore } from "../stores/meetingStore";
import type { TaskStatus } from "../api/tasks";

type TaskStatusValue = TaskStatus;

const store = useMeetingStore();
const route = useRoute();
const router = useRouter();
const meetingId = Number(route.params.id);

onMounted(async () => {
  if (!Number.isFinite(meetingId)) {
    ElMessage.error("会议ID无效");
    router.push("/");
    return;
  }
  await store.fetchMeetingDetail(meetingId);
});

function goBack() {
  router.push("/");
}

async function onFilePicked(file: { raw?: File }) {
  if (!file.raw) {
    return;
  }
  try {
    await store.uploadAudioAndTranscribe(meetingId, file.raw);
    ElMessage.success("音频上传并转写完成");
  } catch {
    ElMessage.error(store.error || "音频处理失败");
  }
}

async function runPostprocess() {
  try {
    await store.runPostprocess(meetingId);
    ElMessage.success("已生成会议纪要与任务");
  } catch {
    ElMessage.error(store.error || "会议后处理失败");
  }
}

async function handleStatusChange(taskId: number, newStatus: TaskStatusValue) {
  try {
    await store.changeTaskStatus(taskId, newStatus);
    ElMessage.success("状态已更新");
  } catch {
    ElMessage.error(store.error || "更新失败");
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
</script>

<style scoped>
.detail-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.base-card {
  border-radius: 12px;
}

.panel-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.action-row {
  display: flex;
  gap: 10px;
  margin: 14px 0;
}

.organizer-line {
  margin: 0;
  color: #486078;
}

.summary-block {
  margin: 0;
  padding: 10px;
  background: #f7fbff;
  border-radius: 8px;
  border: 1px solid #d7e6f5;
}

.plain-list {
  margin: 0;
  padding-left: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.task-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #f8fafc;
  border-radius: 8px;
}

.task-info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.task-title {
  font-weight: 500;
  color: #1d2f45;
}

.task-title.done {
  text-decoration: line-through;
  color: #94a3b8;
}

.task-actions {
  flex-shrink: 0;
}

.empty-hint {
  color: #94a3b8;
  text-align: center;
  padding: 16px;
}

@media (max-width: 900px) {
  .panel-grid {
    grid-template-columns: 1fr;
  }
}
</style>
