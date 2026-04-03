<template>
  <section class="detail-page">
    <el-page-header @back="goBack" content="会议工作台" />

    <AppErrorAlert :error="store.error" :closable="false" />

    <el-skeleton animated :loading="store.loading">
      <template #template>
        <el-card class="base-card">
          <div class="header-row" style="margin-bottom: 24px;">
            <div style="flex: 1;">
              <el-skeleton-item variant="h1" style="width: 40%; margin-bottom: 16px;" />
              <el-skeleton-item variant="text" style="width: 60%; margin-bottom: 12px;" />
              <el-skeleton-item variant="text" style="width: 30%;" />
            </div>
          </div>
          <div style="margin-bottom: 24px;">
            <el-skeleton-item variant="rect" style="width: 100%; height: 120px;" />
          </div>
        </el-card>
      </template>
      <template #default>
        <el-card v-if="store.currentMeeting" class="base-card">
          <div class="header-row">
            <div>
              <h2>{{ store.currentMeeting.title }}</h2>
              <p>{{ store.currentMeeting.description || "暂无描述" }}</p>
              <p class="organizer-line">
                组织者：{{ store.currentMeeting.organizer.full_name }} · 状态：{{ statusLabel(store.currentMeeting.status) }}
              </p>
            </div>
            <div class="summary-actions">
              <el-button @click="reloadMeeting">刷新</el-button>
              <el-button type="primary" plain :disabled="!store.currentMeeting.summary" @click="copyShareLink">生成分享链接</el-button>
              <el-button type="primary" plain :disabled="!store.currentMeeting.summary" @click="distributeByEmail">邮件分发</el-button>
              <el-button type="primary" @click="openTaskDialog">新建任务</el-button>
            </div>
          </div>

          <StatsOverview />
          <AudioRecorder :meetingId="meetingId" />
          <SummaryPanel :meetingId="meetingId" />
        </el-card>
      </template>
    </el-skeleton>

    <div class="panel-container">
      <splitpanes class="default-theme">
        <pane size="50" min-size="20">
          <TranscriptPanel :meetingId="meetingId" @reload="reloadMeeting" />
        </pane>
        <pane size="50" min-size="20">
          <splitpanes horizontal class="default-theme">
            <pane size="50" min-size="20">
              <TaskManager :meetingId="meetingId" @reload="reloadMeeting" ref="taskManagerRef" />
            </pane>
            <pane size="50" min-size="20">
              <ParticipantManager :meetingId="meetingId" ref="participantManagerRef" />
            </pane>
          </splitpanes>
        </pane>
      </splitpanes>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import type { FormInstance, FormRules } from "element-plus";
import { ElMessage } from "element-plus";
import { useRoute, useRouter } from "vue-router";
import { Splitpanes, Pane } from "splitpanes";
import "splitpanes/dist/splitpanes.css";

import AppErrorAlert from "../components/AppErrorAlert.vue";
import StatsOverview from "../components/meeting/StatsOverview.vue";
import AudioRecorder from "../components/meeting/AudioRecorder.vue";
import SummaryPanel from "../components/meeting/SummaryPanel.vue";
import TranscriptPanel from "../components/meeting/TranscriptPanel.vue";
import TaskManager from "../components/meeting/TaskManager.vue";
import ParticipantManager from "../components/meeting/ParticipantManager.vue";

import { createMeetingShareLink } from "../api/meetings";
import { getMeetingParticipants } from "../api/participants";
import { useAuthStore } from "../stores/authStore";
import { useMeetingStore } from "../stores/meetingStore";
import type { TaskCreatePayload } from "../api/types";
import { copyShareLinkToClipboard } from "../utils/share-link";
import { buildEmailShareDraft, openEmailShareDraft } from "../utils/email-share";
import { notifyApiError } from "../utils/notify";

const store = useMeetingStore();
const route = useRoute();
const router = useRouter();
const meetingId = Number(route.params.id);

const taskManagerRef = ref<InstanceType<typeof TaskManager> | null>(null);
const participantManagerRef = ref<InstanceType<typeof ParticipantManager> | null>(null);

onMounted(async () => {
  if (!Number.isFinite(meetingId)) {
    ElMessage.error("会议ID无效");
    router.push("/");
    return;
  }
  await reloadMeeting();
});

async function reloadMeeting() {
  await store.fetchMeetingDetail(meetingId);
}

function openTaskDialog() {
  taskManagerRef.value?.openCreateDialog();
}

async function copyShareLink() {
  try {
    const result = await createMeetingShareLink(meetingId);
    await copyShareLinkToClipboard(window.location.origin, result.share_path);
    ElMessage.success(result.created_now ? "分享链接已生成并复制" : "分享链接已复制");
  } catch (err) {
    notifyApiError(err);
  }
}

async function distributeByEmail() {
  try {
    const shareResult = await createMeetingShareLink(meetingId);
    const parts = await getMeetingParticipants(meetingId);
    const summaryLines = (store.currentMeeting?.summary ?? "")
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter(Boolean)
      .slice(0, 2);
    const draft = buildEmailShareDraft({
      title: store.currentMeeting?.title ?? "会议纪要",
      summaryLines,
      shareLink: `${window.location.origin}${shareResult.share_path}`,
      recipientEmails: parts.map((p) => p.email ?? ""),
    });
    openEmailShareDraft(draft);
    ElMessage.success("已打开邮件客户端");
  } catch (err) {
    notifyApiError(err);
  }
}

function goBack() {
  router.push("/");
}

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    planned: "计划中",
    ongoing: "进行中",
    done: "已结束",
    cancelled: "已取消",
  };
  return map[status] ?? status;
}
</script>

<style scoped>
.detail-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.base-card {
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
  padding: 24px;
}

.header-row {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  align-items: flex-start;
}

.header-row h2 {
  font-size: 28px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  margin: 0 0 12px 0;
  letter-spacing: -0.5px;
}

.header-row p {
  color: var(--el-text-color-regular);
  margin: 4px 0;
  font-size: 15px;
  line-height: 1.6;
}

.summary-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.panel-container {
  height: 700px;
  min-height: 500px;
}

.panel-container :deep(.splitpanes__pane) {
  background-color: transparent !important;
  display: flex;
  flex-direction: column;
}

.panel-container :deep(.splitpanes__splitter) {
  background-color: var(--el-border-color-lighter) !important;
  width: 6px;
  transition: background-color 0.2s ease;
}

.panel-container :deep(.splitpanes__splitter:hover) {
  background-color: var(--el-color-primary-light-5) !important;
}

.panel-container :deep(.splitpanes--horizontal > .splitpanes__splitter) {
  height: 6px;
  width: auto;
}

.organizer-line {
  margin: 12px 0 0 !important;
  color: var(--el-text-color-secondary) !important;
  font-size: 14px !important;
}

@media (max-width: 900px) {
  .panel-container {
    height: auto;
    min-height: 800px;
  }
  .panel-container :deep(.splitpanes.default-theme) {
    flex-direction: column !important;
  }
  .panel-container :deep(.splitpanes--horizontal) {
    flex-direction: column !important;
  }
  .panel-container :deep(.splitpanes__splitter) {
    height: 12px !important;
    width: auto !important;
  }

  .header-row {
    flex-direction: column;
  }
}
</style>