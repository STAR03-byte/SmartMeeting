<template>
  <div class="action-row">
    <el-upload
      :auto-upload="false"
      :show-file-list="false"
      accept="audio/*"
      :on-change="onFilePicked"
      :disabled="recordingState !== 'idle' || jobProgress.isActive.value"
    >
      <el-button type="primary">{{ $t('transcript.uploadAndTranscribe') }}</el-button>
    </el-upload>
    <el-button
      type="primary"
      plain
      :disabled="recordingState === 'recording' || recordingState === 'paused' || jobProgress.isActive.value"
      @click="startRecording"
    >
      {{ $t('transcript.startRecord') }}
    </el-button>
    <el-button
      :disabled="recordingState !== 'recording'"
      @click="pauseRecording"
    >
      {{ $t('transcript.pauseRecord') }}
    </el-button>
    <el-button
      :disabled="recordingState !== 'paused'"
      @click="resumeRecording"
    >
      {{ $t('transcript.resumeRecord') }}
    </el-button>
    <el-button
      type="danger"
      :loading="recordingState === 'processing'"
      :disabled="recordingState !== 'recording' && recordingState !== 'paused'"
      @click="stopRecordingAndRefresh"
    >
      {{ $t('transcript.stopAndTranscribe') }}
    </el-button>
    <el-button type="success" @click="runPostprocess">{{ $t('transcript.generateSummary') }}</el-button>
    <el-button @click="downloadSummary" :disabled="!store.currentMeeting?.summary">{{ $t('transcript.exportSummary') }}</el-button>
    <el-button @click="copySummary" :disabled="summaryDisplayText === $t('summary.emptySummary')">{{ $t('transcript.copySummary') }}</el-button>
  </div>
  <ProcessingProgress
    :visible="jobProgress.isActive.value || jobProgress.isCompleted.value || jobProgress.isFailed.value"
    :status="jobProgress.jobStatus.value"
    :progress="jobProgress.jobProgress.value"
    :message="jobProgress.jobMessage.value"
    :error="jobProgress.jobError.value"
    :formatted-elapsed="jobProgress.formattedElapsed.value"
    :label="jobProgress.activeJobType.value === 'postprocess' ? '后处理' : '音频转写'"
    @cancel="jobProgress.cancel()"
  />
  <div v-if="!jobProgress.isActive.value" class="recording-status" :class="recordingState">
    录音状态：{{ recordingStateLabel }}
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';
const { t } = useI18n();
import { useMeetingStore } from "../../stores/meetingStore";
import { useRecording } from "../../composables/useRecording";
import { useTranscription } from "../../composables/useTranscription";
import { useSummary } from "../../composables/useSummary";
import { watch, onBeforeUnmount } from "vue";
import ProcessingProgress from "./ProcessingProgress.vue";

const props = defineProps<{ meetingId: number }>();
const emit = defineEmits<{ (e: "processed"): void }>();
const store = useMeetingStore();

const {
  recordingState,
  recordingStateLabel,
  startRecording,
  pauseRecording,
  resumeRecording,
  stopRecording: finishRecording,
  cleanupRecorder,
} = useRecording(props.meetingId);

const {
  onFilePickedAsync: transcribePickedFile,
  runPostprocessAsync: generatePostprocess,
  onJobCompleted,
  jobProgress,
} = useTranscription(props.meetingId);

const { summaryDisplayText, downloadSummary, copySummary } = useSummary(props.meetingId);

watch(() => jobProgress.isCompleted.value, (completed) => {
  if (completed) {
    onJobCompleted(jobProgress.activeJobType.value);
    emit("processed");
  }
});

onBeforeUnmount(() => {
  cleanupRecorder();
});

async function onFilePicked(file: { raw?: File }) {
  await transcribePickedFile(file);
}

async function runPostprocess() {
  await generatePostprocess();
}

async function stopRecordingAndRefresh() {
  await finishRecording();
  emit("processed");
}
</script>

<style scoped>
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
</style>
