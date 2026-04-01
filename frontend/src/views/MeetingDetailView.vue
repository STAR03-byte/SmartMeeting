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
            <div style="display: flex; gap: 12px; align-items: flex-start;">
              <el-skeleton-item variant="button" style="width: 64px;" />
              <el-skeleton-item variant="button" style="width: 112px;" />
              <el-skeleton-item variant="button" style="width: 88px;" />
              <el-skeleton-item variant="button" style="width: 88px;" />
            </div>
          </div>
          <div style="display: flex; gap: 12px; margin-bottom: 24px; padding: 20px; background: var(--el-fill-color-light); border-radius: var(--el-border-radius-small);">
            <el-skeleton-item variant="rect" style="flex: 1; height: 60px; border-radius: var(--el-border-radius-small);" />
            <el-skeleton-item variant="rect" style="flex: 1; height: 60px; border-radius: var(--el-border-radius-small);" />
            <el-skeleton-item variant="rect" style="flex: 1; height: 60px; border-radius: var(--el-border-radius-small);" />
          </div>
          <div style="display: flex; gap: 12px; margin-bottom: 24px; padding: 20px; border: 1px solid var(--el-border-color-lighter); border-radius: var(--el-border-radius-small);">
            <el-skeleton-item variant="button" style="width: 120px;" />
            <el-skeleton-item variant="button" style="width: 88px;" />
            <el-skeleton-item variant="button" style="width: 88px;" />
            <el-skeleton-item variant="button" style="width: 104px;" />
            <el-skeleton-item variant="button" style="width: 120px;" />
          </div>
          <el-skeleton-item variant="text" style="width: 120px; height: 20px; margin-bottom: 16px;" />
          <el-skeleton-item variant="rect" style="width: 100%; height: 120px; border-radius: var(--el-border-radius-small);" />
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

          <div class="summary-container" ref="summaryBlockRef">
            <div
              class="summary-block"
              :class="{ empty: !store.currentMeeting.summary, 'is-clamped': showExpandBtn && !isExpanded }"
            >
              {{ store.currentMeeting.summary || "暂无会议摘要" }}
            </div>
            <transition name="expand-btn">
              <div class="expand-action" v-if="showExpandBtn">
                <el-button text type="primary" @click="isExpanded = !isExpanded">
                  {{ isExpanded ? "折叠摘要" : "展开全文" }}
                  <span class="expand-arrow" :class="{ 'is-rotated': isExpanded }">▼</span>
                </el-button>
              </div>
            </transition>
          </div>
        </el-card>
      </template>
    </el-skeleton>

    <div class="panel-grid">
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
              <div v-for="i in 3" :key="i" class="transcript-row" style="background: var(--el-fill-color-lighter); border-radius: var(--el-border-radius-small);">
                <div style="display: flex; gap: 12px; margin-bottom: 12px;">
                  <el-skeleton-item variant="text" style="width: 24px;" />
                  <el-skeleton-item variant="text" style="width: 64px;" />
                </div>
                <el-skeleton-item variant="text" style="width: 100%; margin-bottom: 8px;" />
                <el-skeleton-item variant="text" style="width: 80%;" />
              </div>
            </div>
          </el-card>
        </template>
        <template #default>
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
        </template>
      </el-skeleton>

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
        </template>
      </el-skeleton>

      <el-skeleton animated :loading="participantsLoading">
        <template #template>
          <el-card class="base-card">
            <template #header>
              <div class="panel-header">
                <el-skeleton-item variant="text" style="width: 48px; height: 24px;" />
                <el-skeleton-item variant="text" style="width: 32px; height: 24px;" />
              </div>
            </template>
            <div class="participant-create-row" style="background: var(--el-fill-color-light);">
              <el-skeleton-item variant="rect" style="width: 220px; height: 32px; border-radius: 4px;" />
              <el-skeleton-item variant="rect" style="width: 140px; height: 32px; border-radius: 4px;" />
              <el-skeleton-item variant="button" style="width: 64px; height: 32px;" />
            </div>
            <div class="plain-list">
              <div v-for="i in 3" :key="i" class="participant-row" style="background: var(--el-fill-color-lighter); border-radius: var(--el-border-radius-small);">
                <div style="display: flex; align-items: center; gap: 12px; flex: 1;">
                  <el-skeleton-item variant="text" style="width: 100px;" />
                  <el-skeleton-item variant="rect" style="width: 120px; height: 24px; border-radius: 4px;" />
                </div>
                <div style="display: flex; gap: 12px;">
                  <el-skeleton-item variant="rect" style="width: 120px; height: 32px; border-radius: 4px;" />
                  <el-skeleton-item variant="button" style="width: 56px; height: 32px;" />
                </div>
              </div>
            </div>
          </el-card>
        </template>
        <template #default>
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
            <ul v-else class="plain-list">
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
        </template>
      </el-skeleton>
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
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import type { FormInstance, FormRules } from "element-plus";
import { ElMessage } from "element-plus";
import { useRoute, useRouter } from "vue-router";
// @ts-ignore
import { prepare, layout } from "@chenglou/pretext";

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

// === Pretext & Truncation State ===
const maxClampLines = ref(4);
const totalLineCount = ref(0);

const summaryBlockRef = ref<HTMLElement | null>(null);
const summaryWidth = ref(0);
const isExpanded = ref(false);
const showExpandBtn = ref(false);
let resizeObserver: ResizeObserver | null = null;

// Caching variables for pretext
let cachedSummaryText = "";
let cachedPrepared: any = null;
let cachedWidth = -1;

watch(() => store.currentMeeting?.summary, () => {
  measureSummary();
});

function measureSummary() {
  const summaryText = store.currentMeeting?.summary;
  if (!summaryText || summaryWidth.value <= 0) {
    showExpandBtn.value = false;
    return;
  }

  // 动态响应移动端 (宽度小于 768px 显示 3 行，否则 4 行)
  maxClampLines.value = window.innerWidth <= 768 ? 3 : 4;

  try {
    // 缓存 prepare 结果
    if (summaryText !== cachedSummaryText || !cachedPrepared) {
      cachedSummaryText = summaryText;
      cachedPrepared = prepare(summaryText, "15px sans-serif", { whiteSpace: "pre-wrap" });
    }

    // 只有宽度变化超过 2px 且非初始状态，或者还没有 totalLineCount 时，才重新 layout
    if (Math.abs(cachedWidth - summaryWidth.value) > 2 || totalLineCount.value === 0) {
      const { lineCount } = layout(cachedPrepared, summaryWidth.value, 27);
      totalLineCount.value = lineCount;
      cachedWidth = summaryWidth.value;
    }

    showExpandBtn.value = totalLineCount.value > maxClampLines.value;
  } catch (err) {
    console.error("Pretext measure error", err);
  }
}
// ==================================

onMounted(async () => {
  if (!Number.isFinite(meetingId)) {
    ElMessage.error("会议ID无效");
    router.push("/");
    return;
  }
  await reloadMeeting();
  await Promise.all([refreshParticipants(), refreshUsers()]);

  resizeObserver = new ResizeObserver((entries) => {
    for (let entry of entries) {
      if (entry.contentBoxSize) {
        summaryWidth.value = entry.contentBoxSize[0].inlineSize;
      } else {
        summaryWidth.value = entry.contentRect.width;
      }
      measureSummary();
    }
  });
  if (summaryBlockRef.value) {
    resizeObserver.observe(summaryBlockRef.value);
  }
});

onBeforeUnmount(() => {
  cleanupRecorder();
  if (resizeObserver) {
    resizeObserver.disconnect();
  }
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
    attended: "已参加",
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

.stats-row {
  margin-top: 24px;
  padding: 20px;
  background: var(--el-fill-color-light);
  border-radius: var(--el-border-radius-small);
}

.stats-row :deep(.el-col) {
  text-align: center;
}

.panel-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.action-row {
  display: flex;
  gap: 12px;
  margin: 24px 0;
  flex-wrap: wrap;
  padding: 20px;
  background: var(--el-fill-color-lighter);
  border-radius: var(--el-border-radius-small);
  border: 1px solid var(--el-border-color-lighter);
}

.organizer-line {
  margin: 12px 0 0 !important;
  color: var(--el-text-color-secondary) !important;
  font-size: 14px !important;
}

.summary-container {
  margin-top: 24px;
}

/* === 过渡与截断样式 === */
.summary-block {
  margin: 0;
  padding: 24px;
  background: var(--el-fill-color-lighter);
  border-radius: var(--el-border-radius-small);
  border: 1px solid var(--el-border-color-lighter);
  white-space: pre-wrap;
  line-height: 27px; /* 与 js 计算逻辑同步 */
  font-size: 15px;
  color: var(--el-text-color-primary);
  
  /* 动画核心: max-height 与 padding */
  transition: max-height 0.4s cubic-bezier(0.4, 0, 0.2, 1), padding 0.4s ease;
  max-height: calc(v-bind('totalLineCount') * 27px + 48px);
  overflow: hidden;
}

.summary-block.empty {
  color: var(--el-text-color-placeholder);
  font-style: italic;
  text-align: center;
  padding: 40px;
  max-height: unset;
}

.summary-block.is-clamped {
  max-height: calc(v-bind('maxClampLines') * 27px + 48px);
  display: -webkit-box;
  -webkit-line-clamp: v-bind('maxClampLines');
  -webkit-box-orient: vertical;
}

.expand-action {
  text-align: center;
  margin-top: 8px;
}

.expand-btn-enter-active,
.expand-btn-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.expand-btn-enter-from,
.expand-btn-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.expand-arrow {
  display: inline-block;
  margin-left: 4px;
  transition: transform 0.3s ease;
  font-size: 12px;
}

.expand-arrow.is-rotated {
  transform: rotate(180deg);
}
/* =================== */

.recording-status {
  margin-bottom: 16px;
  padding: 10px 16px;
  border-radius: var(--el-border-radius-small);
  font-weight: 500;
  display: inline-block;
  font-size: 14px;
}

.recording-status.recording {
  background: var(--el-color-danger-light-9);
  color: var(--el-color-danger);
}

.recording-status.paused {
  background: var(--el-color-warning-light-9);
  color: var(--el-color-warning);
}

.recording-status.processing {
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
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

.transcript-row,
.task-row {
  padding: 16px 20px;
  background: var(--el-fill-color-lighter);
  border-radius: var(--el-border-radius-small);
  border: 1px solid transparent;
  transition: all 0.2s ease;
}

.transcript-row:hover,
.task-row:hover {
  background: var(--el-color-primary-light-9);
  border-color: var(--el-color-primary-light-7);
}

.transcript-meta {
  display: flex;
  gap: 12px;
  align-items: center;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.transcript-meta strong {
  color: var(--el-color-primary);
}

.transcript-row p {
  margin: 12px 0 0;
  line-height: 1.7;
  color: var(--el-text-color-primary);
  font-size: 14px;
}

.task-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
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

.participant-create-row {
  display: flex;
  gap: 16px;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 20px;
  padding: 20px;
  background: var(--el-fill-color-light);
  border-radius: var(--el-border-radius-small);
}

.participant-row {
  padding: 16px 20px;
  background: var(--el-fill-color-lighter);
  border-radius: var(--el-border-radius-small);
  border: 1px solid transparent;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  transition: all 0.2s ease;
}

.participant-row:hover {
  background: var(--el-color-primary-light-9);
  border-color: var(--el-color-primary-light-7);
}

.participant-main {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
  flex-wrap: wrap;
}

.participant-main strong {
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.participant-actions {
  display: flex;
  align-items: center;
  gap: 12px;
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
