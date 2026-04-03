<template>
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
    <el-button @click="downloadSummary" :disabled="!store.currentMeeting?.summary">导出纪要</el-button>
    <el-button @click="copySummary" :disabled="summaryDisplayText === '暂无会议摘要'">复制摘要</el-button>
  </div>
  <div class="recording-status" :class="recordingState">
    录音状态：{{ recordingStateLabel }}
  </div>
</template>

<script setup lang="ts">
import { useMeetingStore } from "../../stores/meetingStore";
import { useRecording } from "../../composables/useRecording";
import { useTranscription } from "../../composables/useTranscription";
import { useSummary } from "../../composables/useSummary";
import { onBeforeUnmount } from "vue";

const props = defineProps<{ meetingId: number }>();
const store = useMeetingStore();

const {
  recordingState,
  recordingStateLabel,
  startRecording,
  pauseRecording,
  resumeRecording,
  stopRecording,
  cleanupRecorder,
} = useRecording(props.meetingId);

const { onFilePicked, runPostprocess } = useTranscription(props.meetingId);

const { summaryDisplayText, downloadSummary, copySummary } = useSummary(props.meetingId);

onBeforeUnmount(() => {
  cleanupRecorder();
});
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