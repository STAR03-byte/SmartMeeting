<script setup lang="ts">
import { ref, onMounted, onUnmounted } from "vue";
import { invoke } from "@tauri-apps/api/core";

const isRecording = ref(false);
const isPaused = ref(false);
const meetingTitle = ref("");
const duration = ref(0);
const transcriptCount = ref(0);
const error = ref("");
let timer: ReturnType<typeof setInterval> | null = null;

interface SessionStatus {
  state: string;
  meeting_id: number | null;
  meeting_title: string;
  started_at: string | null;
  stopped_at: string | null;
  transcript_count: number;
  error: string | null;
}

async function startRecording() {
  if (!meetingTitle.value.trim()) {
    error.value = "请输入会议标题";
    return;
  }

  try {
    error.value = "";
    const meetingId = await invoke<number>("start_meeting_session", {
      title: meetingTitle.value.trim(),
    });
    isRecording.value = true;
    isPaused.value = false;
    duration.value = 0;
    transcriptCount.value = 0;
    startTimer();
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  }
}

async function stopRecording() {
  try {
    await invoke("stop_meeting_session");
    isRecording.value = false;
    isPaused.value = false;
    stopTimer();
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  }
}

function togglePause() {
  isPaused.value = !isPaused.value;
  if (isPaused.value) {
    stopTimer();
  } else {
    startTimer();
  }
}

function startTimer() {
  timer = setInterval(() => {
    duration.value++;
  }, 1000);
}

function stopTimer() {
  if (timer) {
    clearInterval(timer);
    timer = null;
  }
}

function formatDuration(seconds: number): string {
  const hrs = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  if (hrs > 0) {
    return `${hrs}:${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  }
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

async function refreshStatus() {
  try {
    const status = await invoke<SessionStatus>("get_meeting_session_status");
    if (status.state === "Recording") {
      isRecording.value = true;
      transcriptCount.value = status.transcript_count;
    }
  } catch {
    // 忽略
  }
}

onMounted(() => {
  refreshStatus();
});

onUnmounted(() => {
  stopTimer();
});
</script>

<template>
  <div class="recording-controls">
    <div v-if="error" class="error-banner">{{ error }}</div>

    <div v-if="!isRecording" class="start-section">
      <input
        v-model="meetingTitle"
        type="text"
        placeholder="输入会议标题..."
        class="title-input"
        @keyup.enter="startRecording"
      />
      <button class="btn-start" @click="startRecording">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
          <circle cx="12" cy="12" r="10" />
        </svg>
        开始录制
      </button>
    </div>

    <div v-else class="recording-section">
      <div class="recording-info">
        <div class="recording-indicator" :class="{ paused: isPaused }">
          <span class="dot"></span>
          {{ isPaused ? "已暂停" : "录制中" }}
        </div>
        <div class="meeting-title">{{ meetingTitle }}</div>
        <div class="stats">
          <span class="duration">{{ formatDuration(duration) }}</span>
          <span class="transcripts">{{ transcriptCount }} 条转写</span>
        </div>
      </div>

      <div class="controls">
        <button class="btn-pause" @click="togglePause">
          {{ isPaused ? "继续" : "暂停" }}
        </button>
        <button class="btn-stop" @click="stopRecording">
          停止录制
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.recording-controls {
  padding: 24px;
  background: var(--el-bg-color);
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.error-banner {
  padding: 12px;
  background: #fef2f2;
  color: #dc2626;
  border-radius: 8px;
  margin-bottom: 16px;
  font-size: 14px;
}

.start-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.title-input {
  padding: 14px 16px;
  border: 2px solid var(--el-border-color);
  border-radius: 8px;
  font-size: 16px;
  outline: none;
  transition: border-color 0.2s;
}

.title-input:focus {
  border-color: var(--el-color-primary);
}

.btn-start {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 16px;
  background: #dc2626;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-start:hover {
  background: #b91c1c;
}

.recording-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.recording-info {
  text-align: center;
}

.recording-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
  color: #dc2626;
  margin-bottom: 8px;
}

.recording-indicator.paused {
  color: #f59e0b;
}

.dot {
  width: 12px;
  height: 12px;
  background: #dc2626;
  border-radius: 50%;
  animation: pulse 1.5s infinite;
}

.recording-indicator.paused .dot {
  background: #f59e0b;
  animation: none;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.meeting-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  margin-bottom: 12px;
}

.stats {
  display: flex;
  justify-content: center;
  gap: 24px;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.duration {
  font-family: monospace;
  font-size: 16px;
}

.controls {
  display: flex;
  gap: 12px;
}

.btn-pause,
.btn-stop {
  flex: 1;
  padding: 14px;
  border: none;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-pause {
  background: #f59e0b;
  color: white;
}

.btn-pause:hover {
  background: #d97706;
}

.btn-stop {
  background: #6b7280;
  color: white;
}

.btn-stop:hover {
  background: #4b5563;
}
</style>
