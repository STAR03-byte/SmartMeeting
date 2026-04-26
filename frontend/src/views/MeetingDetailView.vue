<template>
  <section class="detail-page">
    <el-page-header @back="goBack" :content="$t('meeting.workbench')" />

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
              <p>{{ store.currentMeeting.description || $t('team.noDescription') }}</p>
              <p class="organizer-line">
                {{ $t('meeting.organizerColon') }}{{ store.currentMeeting.organizer.full_name }} · {{ $t('meeting.statusColon') }}{{ statusLabel(store.currentMeeting.status) }}
              </p>
            </div>
            <div class="summary-actions">
              <el-button @click="reloadMeeting">{{ $t('common.refresh') }}</el-button>
              <el-button type="danger" plain @click="clearDialogVisible = true">{{ $t('meeting.clearContent') }}</el-button>
              <el-select
                v-model="shareExpiryMode"
                class="share-expiry-select"
                :disabled="!store.currentMeeting.summary"
                placeholder="分享有效期"
              >
                <el-option label="永久有效" value="never" />
                <el-option label="1 天" value="1d" />
                <el-option label="7 天" value="7d" />
                <el-option label="30 天" value="30d" />
              </el-select>
              <el-button type="primary" plain :disabled="!store.currentMeeting.summary" @click="copyShareLink">{{ $t('meeting.generateShareLink') }}</el-button>
              <el-button type="warning" plain :disabled="!canRevokeShare" @click="revokeShareLink">撤销分享</el-button>
              <el-button type="primary" plain :disabled="!store.currentMeeting.summary" @click="distributeByEmail">{{ $t('meeting.emailDistribute') }}</el-button>
              <el-button type="primary" plain :disabled="!store.currentMeeting.summary" @click="exportMarkdown">导出 MD</el-button>
              <el-button v-if="canCreateTask" type="primary" @click="openTaskDialog">{{ $t('meeting.newTask') }}</el-button>
            </div>
          </div>

          <div class="workflow-strip">
            <div class="workflow-heading">
              <span>会议流程</span>
              <el-tag :type="workflowTagType">{{ workflowCurrentLabel }}</el-tag>
            </div>
            <el-steps :active="workflowActiveStep" finish-status="success" align-center>
              <el-step
                v-for="step in workflowSteps"
                :key="step.key"
                :title="step.title"
                :description="step.description"
                :status="step.status"
              />
            </el-steps>
          </div>

          <StatsOverview />
          <AudioFiles :meeting-id="meetingId" />
          <AudioRecorder :meetingId="meetingId" @processed="reloadMeeting" />
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

    <el-dialog v-model="clearDialogVisible" :title="$t('meeting.clearContentSelectiveTitle')" width="460px">
      <el-checkbox-group v-model="selectedClearOptions" class="clear-options">
        <el-checkbox label="transcripts">{{ $t('meeting.clearTranscripts') }}</el-checkbox>
        <el-checkbox label="tasks">{{ $t('meeting.clearTasks') }}</el-checkbox>
        <el-checkbox label="summary">{{ $t('meeting.clearSummary') }}</el-checkbox>
        <el-checkbox label="audios">{{ $t('meeting.clearAudios') }}</el-checkbox>
        <el-checkbox label="resetStatus">{{ $t('meeting.resetStatus') }}</el-checkbox>
      </el-checkbox-group>
      <template #footer>
        <el-button @click="clearDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="danger" @click="handleClearContent">{{ $t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
  </section>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';
const { t } = useI18n();
import { computed, onMounted, reactive, ref } from "vue";
import type { FormInstance, FormRules } from "element-plus";
import { ElMessage, ElMessageBox } from "element-plus";
import { useRoute, useRouter } from "vue-router";
import { Splitpanes, Pane } from "splitpanes";
import "splitpanes/dist/splitpanes.css";

import AppErrorAlert from "../components/AppErrorAlert.vue";
import StatsOverview from "../components/meeting/StatsOverview.vue";
import AudioFiles from "../components/meeting/AudioFiles.vue";
import AudioRecorder from "../components/meeting/AudioRecorder.vue";
import SummaryPanel from "../components/meeting/SummaryPanel.vue";
import TranscriptPanel from "../components/meeting/TranscriptPanel.vue";
import TaskManager from "../components/meeting/TaskManager.vue";
import ParticipantManager from "../components/meeting/ParticipantManager.vue";

import { createMeetingShareLink, exportMeetingSummary, listMeetingAudios, revokeMeetingShareLink } from "../api/meetings";
import { getMeetingParticipants } from "../api/participants";
import { useAuthStore } from "../stores/authStore";
import { useMeetingStore } from "../stores/meetingStore";
import type { TaskCreatePayload } from "../api/types";
import { copyShareLinkToClipboard } from "../utils/share-link";
import { buildEmailShareDraft, openEmailShareDraft } from "../utils/email-share";
import { notifyApiError } from "../utils/notify";

const store = useMeetingStore();
const authStore = useAuthStore();
const route = useRoute();
const router = useRouter();
const meetingId = Number(route.params.id);

const taskManagerRef = ref<InstanceType<typeof TaskManager> | null>(null);
const participantManagerRef = ref<InstanceType<typeof ParticipantManager> | null>(null);
const audioCount = ref(0);
const shareExpiryMode = ref<"never" | "1d" | "7d" | "30d">("7d");
const clearDialogVisible = ref(false);
const selectedClearOptions = ref<Array<'transcripts' | 'tasks' | 'summary' | 'audios' | 'resetStatus'>>([
  'transcripts',
  'tasks',
  'summary',
  'audios',
  'resetStatus',
]);

const canCreateTask = computed(() => {
  const currentUser = authStore.currentUser;
  const meeting = store.currentMeeting;
  if (!currentUser || !meeting) {
    return false;
  }
  return currentUser.role === "admin" || currentUser.id === meeting.organizer_id;
});

const canRevokeShare = computed(() => {
  const meeting = store.currentMeeting;
  return Boolean(meeting?.share_token && !meeting.share_revoked_at);
});

type WorkflowStep = {
  key: string;
  title: string;
  description: string;
  done: boolean;
  status?: "success" | "process" | "wait" | "error" | "finish";
};

const draftTaskCount = computed(() => store.tasks.filter((task) => task.status === "draft").length);
const confirmedTaskCount = computed(() => store.tasks.filter((task) => task.status !== "draft").length);

const workflowSteps = computed<WorkflowStep[]>(() => {
  const hasMeeting = Boolean(store.currentMeeting);
  const hasAudio = audioCount.value > 0;
  const hasTranscripts = store.transcripts.length > 0;
  const hasSummary = Boolean(store.currentMeeting?.summary);
  const hasConfirmedTasks = confirmedTaskCount.value > 0;
  const hasDraftTasks = draftTaskCount.value > 0;

  const steps: WorkflowStep[] = [
    {
      key: "meeting",
      title: "创建会议",
      description: hasMeeting ? "基础信息已就绪" : "等待创建",
      done: hasMeeting,
    },
    {
      key: "audio",
      title: "上传/录音",
      description: hasAudio ? `${audioCount.value} 个音频文件` : "等待音频",
      done: hasAudio,
    },
    {
      key: "transcript",
      title: "转写",
      description: hasTranscripts ? `${store.transcripts.length} 段转写` : "等待转写",
      done: hasTranscripts,
    },
    {
      key: "summary",
      title: "结构化纪要",
      description: hasSummary ? "纪要已生成" : "等待后处理",
      done: hasSummary,
    },
    {
      key: "tasks",
      title: "行动项确认",
      description: hasDraftTasks ? `${draftTaskCount.value} 个待确认` : `${confirmedTaskCount.value} 个正式任务`,
      done: hasSummary && !hasDraftTasks && hasConfirmedTasks,
      status: hasDraftTasks ? "process" : undefined,
    },
  ];

  const activeIndex = steps.findIndex((step) => !step.done);
  return steps.map((step, index) => {
    if (step.status) return step;
    if (step.done) return { ...step, status: "success" };
    if (index === activeIndex) return { ...step, status: "process" };
    return { ...step, status: "wait" };
  });
});

const workflowActiveStep = computed(() => {
  const firstIncomplete = workflowSteps.value.findIndex((step) => step.status !== "success");
  return firstIncomplete === -1 ? workflowSteps.value.length : firstIncomplete;
});

const workflowCurrentLabel = computed(() => {
  const current = workflowSteps.value.find((step) => step.status === "process");
  if (current) return current.title;
  return "已完成";
});

const workflowTagType = computed(() => {
  if (draftTaskCount.value > 0) return "warning";
  return workflowActiveStep.value >= workflowSteps.value.length ? "success" : "primary";
});

onMounted(async () => {
  if (!Number.isFinite(meetingId)) {
    ElMessage.error(t('meeting.invalidMeetingId'));
    router.push("/");
    return;
  }
  await reloadMeeting();
});

async function reloadMeeting() {
  await store.fetchMeetingDetail(meetingId);
  await refreshAudioCount();
}

async function refreshAudioCount() {
  try {
    const audios = await listMeetingAudios(meetingId);
    audioCount.value = audios.length;
  } catch {
    audioCount.value = 0;
  }
}

function openTaskDialog() {
  taskManagerRef.value?.openCreateDialog();
}

async function copyShareLink() {
  try {
    const result = await createMeetingShareLink(meetingId, buildSharePayload());
    await copyShareLinkToClipboard(window.location.origin, result.share_path);
    await reloadMeeting();
    ElMessage.success(result.created_now ? t('meeting.shareLinkGenerated') : t('meeting.shareLinkCopied'));
  } catch (err) {
    notifyApiError(err);
  }
}

async function distributeByEmail() {
  try {
    const shareResult = await createMeetingShareLink(meetingId, buildSharePayload());
    await reloadMeeting();
    const parts = await getMeetingParticipants(meetingId);
    const summaryLines = (store.currentMeeting?.summary ?? "")
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter(Boolean)
      .slice(0, 2);
    const draft = buildEmailShareDraft({
      title: store.currentMeeting?.title ?? t('meeting.meetingSummary'),
      summaryLines,
      shareLink: `${window.location.origin}${shareResult.share_path}`,
      recipientEmails: parts.map((p) => p.email ?? ""),
    });
    openEmailShareDraft(draft);
    ElMessage.success(t('meeting.emailClientOpened'));
  } catch (err) {
    notifyApiError(err);
  }
}

function buildSharePayload() {
  if (shareExpiryMode.value === "never") {
    return { expires_at: null };
  }
  const daysByMode: Record<"1d" | "7d" | "30d", number> = {
    "1d": 1,
    "7d": 7,
    "30d": 30,
  };
  const days = daysByMode[shareExpiryMode.value];
  const expiresAt = new Date(Date.now() + days * 24 * 60 * 60 * 1000);
  return { expires_at: expiresAt.toISOString() };
}

async function revokeShareLink() {
  try {
    await ElMessageBox.confirm("撤销后，已有分享链接将无法继续访问。", "撤销分享", {
      type: "warning",
      confirmButtonText: "撤销",
      cancelButtonText: t('common.cancel'),
    });
    await revokeMeetingShareLink(meetingId);
    await reloadMeeting();
    ElMessage.success("分享链接已撤销");
  } catch (err) {
    if (err !== "cancel") {
      notifyApiError(err);
    }
  }
}

async function exportMarkdown() {
  try {
    const result = await exportMeetingSummary(meetingId, { format: "md" });
    const blob = new Blob([result.content], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = result.filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    ElMessage.success("Markdown 已导出");
  } catch (err) {
    notifyApiError(err);
  }
}

async function handleClearContent() {
  try {
    if (selectedClearOptions.value.length === 0) {
      ElMessage.warning(t('meeting.clearContentSelectAtLeastOne'));
      return;
    }

    await store.clearMeetingContentSelective(meetingId, {
      clear_transcripts: selectedClearOptions.value.includes('transcripts'),
      clear_tasks: selectedClearOptions.value.includes('tasks'),
      clear_summary: selectedClearOptions.value.includes('summary'),
      clear_audios: selectedClearOptions.value.includes('audios'),
      reset_status: selectedClearOptions.value.includes('resetStatus'),
    });

    await reloadMeeting();
    clearDialogVisible.value = false;
    ElMessage.success(t('meeting.clearContentSuccess'));
  } catch (err) {
    notifyApiError(err);
  }
}

function goBack() {
  router.push("/");
}

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    planned: t('meeting.statusPlanned'),
    ongoing: t('task.statusInProgress'),
    done: t('meeting.statusDone'),
    cancelled: t('meeting.statusCancelled'),
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

.share-expiry-select {
  width: 120px;
}

.clear-options {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.workflow-strip {
  margin-top: 24px;
  padding: 18px 20px;
  background: var(--el-fill-color-light);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: var(--el-border-radius-small);
}

.workflow-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.workflow-strip :deep(.el-step__title) {
  font-size: 14px;
}

.workflow-strip :deep(.el-step__description) {
  margin-top: 4px;
  font-size: 12px;
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

@media (max-width: 767px) {
  .summary-actions {
    justify-content: flex-start;
    width: 100%;
    margin-top: 16px;
    gap: 8px;
  }
  .summary-actions .el-button {
    margin-left: 0 !important;
    width: 100%;
  }
  .share-expiry-select {
    width: 100%;
  }
  .base-card :deep(.el-card__body) {
    padding: 16px;
  }
  .header-row h2 {
    font-size: 24px;
  }
}
</style>
