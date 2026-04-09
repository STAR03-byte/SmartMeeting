import { ref, computed } from "vue";
import { ElMessage } from "element-plus";
import { useMeetingStore } from "../stores/meetingStore";
import { updateMeeting } from "../api/meetings";
import { notifyApiError } from "../utils/notify";
import { buildRecordingFile, pickRecordingMimeType } from "../utils/recorder";

export function useRecording(meetingId: number) {
  const store = useMeetingStore();
  
  const recordingState = ref<"idle" | "recording" | "paused" | "processing" | "streaming">("idle");
  const recordingMimeType = ref("audio/webm");
  const realtimeTranscript = ref("");
  const realtimeChunks: BlobPart[] = [];
  let realtimeTimer: number | null = null;

  let mediaStream: MediaStream | null = null;
  let mediaRecorder: MediaRecorder | null = null;
  let recordedChunks: BlobPart[] = [];

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
      await updateMeeting(meetingId, {
        actual_start_at: new Date().toISOString(),
        status: "ongoing",
      });
      if (store.currentMeeting?.id === meetingId) {
        store.currentMeeting.status = "ongoing";
      }
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
      await updateMeeting(meetingId, {
        actual_end_at: new Date().toISOString(),
        status: "done",
      });
      await store.fetchMeetingDetail(meetingId);
      await store.fetchMeetings();
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

  return {
    recordingState,
    recordingStateLabel,
    realtimeTranscript,
    startRecording,
    pauseRecording,
    resumeRecording,
    stopRecording,
    cleanupRecorder
  };
}
