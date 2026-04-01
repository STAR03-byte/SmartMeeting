<template>
  <section class="detail-page" v-loading="store.loading">
    <el-page-header @back="goBack" content="会议工作台" />

    <AppErrorAlert :error="store.error" :closable="false" />

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

      <el-card class="base-card">
        <template #header>
          <div class="panel-header">
            <span>参与者</span>
            <el-button text @click="refreshParticipants">刷新</el-button>
          </div>
        </template>

        <div class="participant-create-row">
          <el-select
            v-model="participantForm.user_id"
            filterable
            clearable
            placeholder="选择用户"
            style="min-width: 220px"
          >
            <el-option
              v-for="user in availableUsers"
              :key="user.id"
              :label="`${user.full_name} (${user.username})`"
              :value="user.id"
            />
          </el-select>
          <el-select v-model="participantForm.participant_role" style="width: 140px">
            <el-option label="必须" value="required" />
            <el-option label="可选" value="optional" />
            <el-option label="旁听" value="observer" />
          </el-select>
          <el-button type="primary" :loading="creatingParticipant" @click="addParticipant">添加</el-button>
        </div>

        <el-empty v-if="participants.length === 0" description="暂无参与者" />
        <ul v-else class="plain-list" v-loading="participantsLoading">
          <li v-for="participant in participants" :key="participant.id" class="participant-row">
            <div class="participant-main">
              <strong>{{ resolveParticipantName(participant.user_id, participant.email) }}</strong>
              <el-tag size="small" type="info">{{ participant.email || "无邮箱" }}</el-tag>
              <el-tag size="small" :type="attendanceTag(participant.attendance_status)">
                {{ attendanceLabel(participant.attendance_status) }}
              </el-tag>
            </div>
            <div class="participant-actions">
              <el-select
                :model-value="participant.participant_role"
                size="small"
                style="width: 120px"
                @change="(role: string) => changeParticipantRole(participant.id, role)"
              >
                <el-option label="必须" value="required" />
                <el-option label="可选" value="optional" />
                <el-option label="旁听" value="observer" />
              </el-select>
              <el-popconfirm title="确认移除该参与者？" @confirm="removeParticipant(participant.id)">
                <template #reference>
                  <el-button size="small" type="danger" plain>移除</el-button>
                </template>
              </el-popconfirm>
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

import AppErrorAlert from "../components/AppErrorAlert.vue";
import { createMeetingShareLink } from "../api/meetings";
import {
  createMeetingParticipant,
  deleteMeetingParticipant,
  getMeetingParticipants,
  updateMeetingParticipant,
} from "../api/participants";
import { getUsers, type UserItem } from "../api/users";
import { useAuthStore } from "../stores/authStore";
import { useMeetingStore } from "../stores/meetingStore";
import type { MeetingParticipantOut, TaskCreatePayload } from "../api/types";
import type { TaskStatus } from "../api/tasks";
import { copyShareLinkToClipboard } from "../utils/share-link";
import { buildEmailShareDraft, openEmailShareDraft } from "../utils/email-share";
import { notifyApiError } from "../utils/notify";
import { buildRecordingFile, pickRecordingMimeType } from "../utils/recorder";

type TaskStatusValue = TaskStatus;

const store = useMeetingStore();
const authStore = useAuthStore();
const route = useRoute();
const router = useRouter();
const meetingId = Number(route.params.id);

const showTaskDialog = ref(false);
const creatingTask = ref(false);
const creatingParticipant = ref(false);
const participantsLoading = ref(false);
const taskFormRef = ref<FormInstance>();
const recordingState = ref<"idle" | "recording" | "paused" | "processing" | "streaming">("idle");
const recordingMimeType = ref("audio/webm");
const realtimeTranscript = ref("");
const realtimeChunks: BlobPart[] = [];
let realtimeTimer: number | null = null;

let mediaStream: MediaStream | null = null;
let mediaRecorder: MediaRecorder | null = null;
let recordedChunks: BlobPart[] = [];

const participants = ref<MeetingParticipantOut[]>([]);
const users = ref<UserItem[]>([]);

const participantForm = reactive<{ user_id: number | null; participant_role: string }>({
  user_id: null,
  participant_role: "required",
});

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
const availableUsers = computed(() => {
  const existingUserIds = new Set(participants.value.map((item) => item.user_id));
  return users.value.filter((user) => !existingUserIds.has(user.id));
});
const recordingStateLabel = computed(() => {
  const map: Record<typeof recordingState.value, string> = {
    idle: "未录音",
    recording: "录音中",
    paused: "已暂停",
    processing: "处理中",
    streaming: "实时转写中",
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
  await Promise.all([refreshParticipants(), refreshUsers()]);
});

onBeforeUnmount(() => {
  cleanupRecorder();
});

async function reloadMeeting() {
  await store.fetchMeetingDetail(meetingId);
  await refreshParticipants();
}

async function refreshParticipants() {
  participantsLoading.value = true;
  try {
    participants.value = await getMeetingParticipants(meetingId);
  } catch (err) {
    notifyApiError(err);
  } finally {
    participantsLoading.value = false;
  }
}

async function refreshUsers() {
  try {
    users.value = await getUsers();
  } catch (err) {
    notifyApiError(err);
  }
}

async function addParticipant() {
  if (!participantForm.user_id) {
    ElMessage.warning("请先选择用户");
    return;
  }
  creatingParticipant.value = true;
  try {
    await createMeetingParticipant({
      meeting_id: meetingId,
      user_id: participantForm.user_id,
      participant_role: participantForm.participant_role,
    });
    participantForm.user_id = null;
    participantForm.participant_role = "required";
    ElMessage.success("参与者已添加");
    await refreshParticipants();
  } catch (err) {
    notifyApiError(err);
  } finally {
    creatingParticipant.value = false;
  }
}

async function changeParticipantRole(participantId: number, role: string) {
  try {
    await updateMeetingParticipant(participantId, { participant_role: role });
    ElMessage.success("参与者角色已更新");
    await refreshParticipants();
  } catch (err) {
    notifyApiError(err);
  }
}

async function removeParticipant(participantId: number) {
  try {
    await deleteMeetingParticipant(participantId);
    ElMessage.success("参与者已移除");
    await refreshParticipants();
  } catch (err) {
    notifyApiError(err);
  }
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
  } catch (err) {
    notifyApiError(err);
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
  } catch (err) {
    notifyApiError(err);
  }
}

async function runPostprocess() {
  try {
    await store.runPostprocess(meetingId);
    ElMessage.success("已生成会议纪要与任务");
  } catch (err) {
    notifyApiError(err);
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
  } catch (err) {
    notifyApiError(err);
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
    realtimeChunks.length = 0;
    realtimeTranscript.value = "";

    mediaRecorder.addEventListener("dataavailable", (event: BlobEvent) => {
      if (event.data.size > 0) {
        recordedChunks.push(event.data);
        realtimeChunks.push(event.data);
      }
    });

    mediaRecorder.start();
    recordingState.value = "recording";
    startRealtimePolling();
    ElMessage.success("已开始录音");
  } catch (err) {
    cleanupRecorder();
    notifyApiError(err);
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
  stopRealtimePolling();

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
  } catch (err) {
    notifyApiError(err);
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
  stopRealtimePolling();
}

function startRealtimePolling() {
  stopRealtimePolling();
  realtimeTimer = window.setInterval(async () => {
    if (recordingState.value !== "recording" && recordingState.value !== "paused") {
      return;
    }
    if (realtimeChunks.length === 0) {
      return;
    }
    const chunk = new Blob(realtimeChunks, { type: recordingMimeType.value });
    realtimeChunks.length = 0;
    const chunkFile = buildRecordingFile([chunk], recordingMimeType.value, meetingId, "realtime-chunk");
    try {
      const transcript = await store.appendRealtimeTranscript(meetingId, chunkFile);
      realtimeTranscript.value = `${realtimeTranscript.value}${realtimeTranscript.value ? "\n" : ""}${transcript.content}`;
      recordingState.value = "streaming";
    } catch (err) {
      recordingState.value = "recording";
      notifyApiError(err);
    }
  }, 3000);
}

function stopRealtimePolling() {
  if (realtimeTimer !== null) {
    window.clearInterval(realtimeTimer);
    realtimeTimer = null;
  }
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
  } catch (err) {
    notifyApiError(err);
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
  } catch (err) {
    notifyApiError(err);
  }
}

async function copySummary() {
  const summary = store.currentMeeting?.summary;
  if (!summary) return;
  try {
    await navigator.clipboard.writeText(summary);
    ElMessage.success("摘要已复制");
  } catch (err) {
    notifyApiError(err);
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

function resolveParticipantName(userId: number, email: string | null): string {
  const user = users.value.find((item) => item.id === userId);
  if (user) {
    return `${user.full_name} (${user.username})`;
  }
  return email ?? `用户 #${userId}`;
}

function attendanceLabel(status: string): string {
  const map: Record<string, string> = {
    invited: "待确认",
    accepted: "已接受",
    declined: "已拒绝",
    attended: "已参会",
  };
  return map[status] ?? status;
}

function attendanceTag(status: string): string {
  const map: Record<string, string> = {
    invited: "info",
    accepted: "success",
    declined: "danger",
    attended: "warning",
  };
  return map[status] ?? "info";
}
</script>

<style scoped>
.detail-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 8px;
}

.base-card {
  border-radius: 16px;
  border: none;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.base-card :deep(.el-card__header) {
  padding: 20px 24px;
  border-bottom: 1px solid #f0f0f0;
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
  font-size: 26px;
  font-weight: 700;
  color: #303133;
  margin: 0 0 8px 0;
}

.header-row p {
  color: #606266;
  margin: 4px 0;
}

.summary-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.summary-actions :deep(.el-button) {
  border-radius: 10px;
  font-weight: 500;
}

.summary-actions :deep(.el-button--primary) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
}

.stats-row {
  margin-top: 16px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 12px;
}

.stats-row :deep(.el-col) {
  text-align: center;
}

.panel-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.panel-grid :deep(.el-card) {
  border-radius: 16px;
  border: none;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.action-row {
  display: flex;
  gap: 10px;
  margin: 16px 0;
  flex-wrap: wrap;
  padding: 16px;
  background: linear-gradient(135deg, #f5f7fa 0%, #ffffff 100%);
  border-radius: 12px;
}

.action-row :deep(.el-button) {
  border-radius: 10px;
  font-weight: 500;
}

.organizer-line {
  margin: 8px 0 0;
  color: #909399;
  font-size: 14px;
}

.summary-block {
  margin: 0;
  padding: 16px;
  background: linear-gradient(135deg, #f5f7fa 0%, #ffffff 100%);
  border-radius: 12px;
  border: 1px solid #ebeef5;
  white-space: pre-wrap;
  line-height: 1.8;
}

.summary-block.empty {
  color: #c0c4cc;
  font-style: italic;
}

.recording-status {
  margin-bottom: 12px;
  padding: 8px 16px;
  border-radius: 8px;
  font-weight: 500;
  display: inline-block;
}

.recording-status.recording {
  background: #fee;
  color: #f56c6c;
}

.recording-status.paused {
  background: #fef0e6;
  color: #e6a23c;
}

.recording-status.processing {
  background: #e6f7ff;
  color: #409eff;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
  color: #303133;
  font-size: 16px;
}

.plain-list {
  margin: 0;
  padding-left: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.transcript-row,
.task-row {
  padding: 14px 16px;
  background: #fafafa;
  border-radius: 12px;
  border: 1px solid #f0f0f0;
  transition: all 0.3s;
}

.transcript-row:hover,
.task-row:hover {
  background: #fff;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.transcript-meta {
  display: flex;
  gap: 12px;
  align-items: center;
  color: #606266;
  font-size: 13px;
}

.transcript-meta strong {
  color: #667eea;
}

.transcript-row p {
  margin: 10px 0 0;
  line-height: 1.7;
  color: #303133;
}

.task-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.task-info {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
}

.task-title {
  font-weight: 600;
  color: #303133;
}

.task-title.done {
  text-decoration: line-through;
  color: #c0c4cc;
}

.task-actions {
  flex-shrink: 0;
}

.participant-create-row {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 16px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 12px;
}

.participant-create-row :deep(.el-select) {
  min-width: 180px;
}

.participant-row {
  padding: 14px 16px;
  background: #fafafa;
  border-radius: 12px;
  border: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  transition: all 0.3s;
}

.participant-row:hover {
  background: #fff;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.participant-main {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  flex-wrap: wrap;
}

.participant-main strong {
  font-weight: 600;
  color: #303133;
}

.participant-actions {
  display: flex;
  align-items: center;
  gap: 8px;
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
