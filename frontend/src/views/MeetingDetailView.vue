<template>
  <section class="detail-page" v-loading="store.loading">
    <el-page-header @back="goBack" content="会议工作台" />

    <el-alert
      v-if="store.error"
      :title="store.error"
      type="error"
      show-icon
      :closable="false"
    />

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
          <el-button type="primary" @click="showTaskDialog = true">新建任务</el-button>
        </div>
      </div>

      <el-row :gutter="12" class="stats-row">
        <el-col :span="8"><el-statistic title="转写片段" :value="store.transcripts.length" /></el-col>
        <el-col :span="8"><el-statistic title="任务数" :value="store.tasks.length" /></el-col>
        <el-col :span="8"><el-statistic title="已完成任务" :value="doneTaskCount" /></el-col>
      </el-row>

      <div class="action-row">
        <el-upload
          :auto-upload="false"
          :show-file-list="false"
          accept="audio/*"
          :on-change="onFilePicked"
          :disabled="recordingState !== 'idle'"
        >
          <el-button type="primary">上传音频并转写</el-button>
        </el-upload>
        <el-button
          type="primary"
          plain
          :disabled="recordingState === 'recording' || recordingState === 'paused'"
          @click="startRecording"
        >
          开始录音
        </el-button>
        <el-button
          :disabled="recordingState !== 'recording'"
          @click="pauseRecording"
        >
          暂停录音
        </el-button>
        <el-button
          :disabled="recordingState !== 'paused'"
          @click="resumeRecording"
        >
          继续录音
        </el-button>
        <el-button
          type="danger"
          :loading="recordingState === 'processing'"
          :disabled="recordingState !== 'recording' && recordingState !== 'paused'"
          @click="stopRecording"
        >
          停止并转写
        </el-button>
        <el-button type="success" @click="runPostprocess">生成纪要与任务</el-button>
        <el-button @click="downloadSummary" :disabled="!store.currentMeeting.summary">导出纪要</el-button>
        <el-button @click="copySummary" :disabled="!store.currentMeeting.summary">复制摘要</el-button>
      </div>

      <div class="recording-status" :class="recordingState">
        录音状态：{{ recordingStateLabel }}
      </div>

      <div class="summary-block" :class="{ empty: !store.currentMeeting.summary }">
        {{ store.currentMeeting.summary || "暂无会议摘要" }}
      </div>
    </el-card>

    <div class="panel-grid">
      <el-card class="base-card">
        <template #header>
          <div class="panel-header">
            <span>转写片段</span>
            <el-button text @click="reloadMeeting">刷新</el-button>
          </div>
        </template>

        <el-empty v-if="store.transcripts.length === 0" description="暂无转写内容" />
        <ul v-else class="plain-list">
          <li v-for="item in store.transcripts" :key="item.id" class="transcript-row">
            <div class="transcript-meta">
              <strong>#{{ item.segment_index }}</strong>
              <span>{{ item.speaker_name || item.source }}</span>
            </div>
            <p>{{ item.content }}</p>
          </li>
        </ul>
      </el-card>

      <el-card class="base-card">
        <template #header>
          <div class="panel-header">
            <span>任务列表</span>
            <el-button text @click="reloadMeeting">刷新</el-button>
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
                @change="(val: string) => handleStatusChange(task.id, val as TaskStatusValue)"
              >
                <el-option label="待办" value="todo" />
                <el-option label="进行中" value="in_progress" />
                <el-option label="已完成" value="done" />
              </el-select>
            </div>
          </li>
        </ul>
      </el-card>
    </div>

    <el-dialog v-model="showTaskDialog" title="新建任务" width="520px" @closed="resetTaskForm">
      <el-form ref="taskFormRef" :model="taskForm" :rules="taskRules" label-width="90px">
        <el-form-item label="标题" prop="title">
          <el-input v-model="taskForm.title" placeholder="请输入任务标题" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="taskForm.description" type="textarea" :rows="3" placeholder="可选" />
        </el-form-item>
        <el-form-item label="负责人ID">
          <el-input-number v-model="taskForm.assignee_id" :min="1" />
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="taskForm.priority" style="width: 160px">
            <el-option label="高" value="high" />
            <el-option label="中" value="medium" />
            <el-option label="低" value="low" />
          </el-select>
        </el-form-item>
        <el-form-item label="截止时间">
          <el-date-picker v-model="taskForm.due_at" type="datetime" placeholder="可选" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showTaskDialog = false">取消</el-button>
        <el-button type="primary" :loading="creatingTask" @click="createTask">创建</el-button>
      </template>
    </el-dialog>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref } from "vue";
import type { FormInstance, FormRules } from "element-plus";
import { ElMessage } from "element-plus";
import { useRoute, useRouter } from "vue-router";

import { createMeetingShareLink } from "../api/meetings";
import { getMeetingParticipants } from "../api/participants";
import { useAuthStore } from "../stores/authStore";
import { useMeetingStore } from "../stores/meetingStore";
import type { TaskCreatePayload } from "../api/types";
import type { TaskStatus } from "../api/tasks";
import { copyShareLinkToClipboard } from "../utils/share-link";
import { buildEmailShareDraft, openEmailShareDraft } from "../utils/email-share";
import { buildRecordingFile, pickRecordingMimeType } from "../utils/recorder";

type TaskStatusValue = TaskStatus;

const store = useMeetingStore();
const authStore = useAuthStore();
const route = useRoute();
const router = useRouter();
const meetingId = Number(route.params.id);

const showTaskDialog = ref(false);
const creatingTask = ref(false);
const taskFormRef = ref<FormInstance>();
const recordingState = ref<"idle" | "recording" | "paused" | "processing">("idle");
const recordingMimeType = ref("audio/webm");

let mediaStream: MediaStream | null = null;
let mediaRecorder: MediaRecorder | null = null;
let recordedChunks: BlobPart[] = [];

const taskForm = reactive<TaskCreatePayload>({
  meeting_id: meetingId,
  title: "",
  description: null,
  assignee_id: authStore.currentUser?.id ?? null,
  reporter_id: authStore.currentUser?.id ?? null,
  priority: "medium",
  status: "todo",
  due_at: null,
});

const taskRules: FormRules = {
  title: [{ required: true, message: "请输入任务标题", trigger: "blur" }],
};

const doneTaskCount = computed(() => store.tasks.filter((task) => task.status === "done").length);
const recordingStateLabel = computed(() => {
  const map: Record<typeof recordingState.value, string> = {
    idle: "未录音",
    recording: "录音中",
    paused: "已暂停",
    processing: "处理中",
  };
  return map[recordingState.value];
});

onMounted(async () => {
  if (!Number.isFinite(meetingId)) {
    ElMessage.error("会议ID无效");
    router.push("/");
    return;
  }
  await reloadMeeting();
});

onBeforeUnmount(() => {
  cleanupRecorder();
});

async function reloadMeeting() {
  await store.fetchMeetingDetail(meetingId);
}

async function copyShareLink() {
  try {
    const result = await createMeetingShareLink(meetingId);
    await copyShareLinkToClipboard(window.location.origin, result.share_path);
    ElMessage.success(result.created_now ? "分享链接已生成并复制" : "分享链接已复制");
  } catch {
    ElMessage.error("分享链接生成失败，请重试");
  }
}

async function distributeByEmail() {
  try {
    const shareResult = await createMeetingShareLink(meetingId);
    const participants = await getMeetingParticipants(meetingId);
    const summaryLines = (store.currentMeeting?.summary ?? "")
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter(Boolean)
      .slice(0, 2);
    const draft = buildEmailShareDraft({
      title: store.currentMeeting?.title ?? "会议纪要",
      summaryLines,
      shareLink: `${window.location.origin}${shareResult.share_path}`,
      recipientEmails: participants.map((participant) => participant.email ?? ""),
    });
    openEmailShareDraft(draft);
    ElMessage.success("已打开邮件客户端");
  } catch {
    ElMessage.error("邮件分发失败，请重试");
  }
}

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

async function downloadSummary() {
  try {
    const result = await store.exportMeetingSummary(meetingId);
    const blob = new Blob([result.content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = result.filename;
    link.click();
    URL.revokeObjectURL(url);
    ElMessage.success("纪要已导出");
  } catch {
    ElMessage.error(store.error || "纪要导出失败");
  }
}

async function startRecording() {
  if (!Number.isFinite(meetingId)) {
    ElMessage.error("会议ID无效");
    return;
  }

  if (!navigator.mediaDevices?.getUserMedia) {
    ElMessage.error("当前浏览器不支持麦克风录音");
    return;
  }

  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    recordingMimeType.value = pickRecordingMimeType((mime) => MediaRecorder.isTypeSupported(mime));
    mediaRecorder = new MediaRecorder(mediaStream, { mimeType: recordingMimeType.value });
    recordedChunks = [];

    mediaRecorder.addEventListener("dataavailable", (event: BlobEvent) => {
      if (event.data.size > 0) {
        recordedChunks.push(event.data);
      }
    });

    mediaRecorder.start();
    recordingState.value = "recording";
    ElMessage.success("已开始录音");
  } catch {
    cleanupRecorder();
    ElMessage.error("无法访问麦克风，请检查浏览器权限");
  }
}

function pauseRecording() {
  if (!mediaRecorder || mediaRecorder.state !== "recording") {
    return;
  }
  mediaRecorder.pause();
  recordingState.value = "paused";
  ElMessage.info("录音已暂停");
}

function resumeRecording() {
  if (!mediaRecorder || mediaRecorder.state !== "paused") {
    return;
  }
  mediaRecorder.resume();
  recordingState.value = "recording";
  ElMessage.success("录音已继续");
}

async function stopRecording() {
  if (!mediaRecorder || (mediaRecorder.state !== "recording" && mediaRecorder.state !== "paused")) {
    return;
  }

  recordingState.value = "processing";

  await new Promise<void>((resolve) => {
    if (!mediaRecorder) {
      resolve();
      return;
    }
    mediaRecorder.requestData();
    mediaRecorder.addEventListener(
      "stop",
      () => {
        resolve();
      },
      { once: true },
    );
    mediaRecorder.stop();
  });

  try {
    if (recordedChunks.length === 0) {
      throw new Error("empty recording");
    }
    const file = buildRecordingFile(recordedChunks, recordingMimeType.value, meetingId, "online-recording");
    await store.uploadAudioAndTranscribe(meetingId, file);
    ElMessage.success("录音上传并转写完成");
  } catch {
    ElMessage.error(store.error || "录音处理失败");
  } finally {
    cleanupRecorder();
    recordingState.value = "idle";
  }
}

function cleanupRecorder() {
  if (mediaStream) {
    for (const track of mediaStream.getTracks()) {
      track.stop();
    }
  }
  mediaStream = null;
  mediaRecorder = null;
  recordedChunks = [];
}

async function createTask() {
  const valid = await taskFormRef.value?.validate().catch(() => false);
  if (!valid) return;

  creatingTask.value = true;
  try {
    await store.createMeetingTask({
      ...taskForm,
      due_at: taskForm.due_at ? new Date(taskForm.due_at).toISOString() : null,
    });
    showTaskDialog.value = false;
    ElMessage.success("任务创建成功");
  } catch {
    ElMessage.error(store.error || "任务创建失败");
  } finally {
    creatingTask.value = false;
  }
}

function resetTaskForm() {
  taskForm.title = "";
  taskForm.description = null;
  taskForm.assignee_id = authStore.currentUser?.id ?? null;
  taskForm.reporter_id = authStore.currentUser?.id ?? null;
  taskForm.priority = "medium";
  taskForm.status = "todo";
  taskForm.due_at = null;
  taskFormRef.value?.resetFields();
}

async function handleStatusChange(taskId: number, newStatus: TaskStatusValue) {
  try {
    await store.changeTaskStatus(taskId, newStatus);
    ElMessage.success("状态已更新");
  } catch {
    ElMessage.error(store.error || "更新失败");
  }
}

async function copySummary() {
  const summary = store.currentMeeting?.summary;
  if (!summary) return;
  try {
    await navigator.clipboard.writeText(summary);
    ElMessage.success("摘要已复制");
  } catch {
    ElMessage.error("摘要复制失败，请重试");
  }
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

.header-row {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
}

.summary-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.stats-row {
  margin-top: 12px;
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
  flex-wrap: wrap;
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
  white-space: pre-wrap;
}

.summary-block.empty {
  color: #94a3b8;
}

.recording-status {
  margin-bottom: 12px;
  color: #486078;
}

.recording-status.recording {
  color: #dc2626;
  font-weight: 600;
}

.recording-status.paused {
  color: #d97706;
  font-weight: 600;
}

.recording-status.processing {
  color: #1d4ed8;
  font-weight: 600;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.plain-list {
  margin: 0;
  padding-left: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.transcript-row,
.task-row {
  padding: 10px 12px;
  background: #f8fafc;
  border-radius: 8px;
}

.transcript-meta {
  display: flex;
  gap: 8px;
  align-items: center;
  color: #486078;
}

.transcript-row p {
  margin: 8px 0 0;
  line-height: 1.6;
}

.task-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
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

@media (max-width: 900px) {
  .panel-grid {
    grid-template-columns: 1fr;
  }

  .header-row {
    flex-direction: column;
  }
}
</style>
