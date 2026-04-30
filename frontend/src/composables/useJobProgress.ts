import { ref, computed, onUnmounted } from "vue";
import { subscribeJobEvents, cancelJob } from "../api/jobs";
import type { ProcessingJobStatus, ProcessingJobType } from "../api/types";

export function useJobProgress() {
  const activeJobId = ref<string | null>(null);
  const activeJobType = ref<ProcessingJobType | null>(null);
  const jobStatus = ref<ProcessingJobStatus | null>(null);
  const jobProgress = ref(0);
  const jobMessage = ref("");
  const jobError = ref<string | null>(null);
  const elapsedSeconds = ref(0);

  let eventSource: EventSource | null = null;
  let elapsedTimer: ReturnType<typeof setInterval> | null = null;

  const isActive = computed(() =>
    activeJobId.value != null &&
    jobStatus.value != null &&
    !["completed", "failed", "interrupted"].includes(jobStatus.value),
  );

  const isCompleted = computed(() => jobStatus.value === "completed");
  const isFailed = computed(() => jobStatus.value === "failed" || jobStatus.value === "interrupted");

  const formattedElapsed = computed(() => {
    const s = elapsedSeconds.value;
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return m > 0 ? `${m}分${sec}秒` : `${sec}秒`;
  });

  function startElapsedTimer() {
    elapsedSeconds.value = 0;
    elapsedTimer = setInterval(() => {
      elapsedSeconds.value++;
    }, 1000);
  }

  function stopElapsedTimer() {
    if (elapsedTimer != null) {
      clearInterval(elapsedTimer);
      elapsedTimer = null;
    }
  }

  function resetState() {
    jobStatus.value = null;
    jobProgress.value = 0;
    jobMessage.value = "";
    jobError.value = null;
    elapsedSeconds.value = 0;
    activeJobType.value = null;
  }

  function connect(jobId: string, jobType?: ProcessingJobType) {
    cleanup();
    resetState();
    activeJobId.value = jobId;
    activeJobType.value = jobType ?? null;
    startElapsedTimer();

    eventSource = subscribeJobEvents(jobId);

    eventSource.onmessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data) as {
          type: string;
          status?: ProcessingJobStatus;
          progress?: number;
          message?: string;
          error?: string;
        };

        if (data.status) {
          jobStatus.value = data.status;
        }
        if (typeof data.progress === "number") {
          jobProgress.value = data.progress;
        }
        if (data.message) {
          jobMessage.value = data.message;
        }
        if (data.type === "error" || data.error) {
          jobError.value = data.error ?? "未知错误";
        }
        if (data.type === "completed" || data.type === "error" || data.type === "cancelled") {
          stopElapsedTimer();
          eventSource?.close();
          eventSource = null;
        }
      } catch {
        // 忽略解析错误的 keepalive 消息
      }
    };

    eventSource.onerror = () => {
      stopElapsedTimer();
      if (isActive.value) {
        jobError.value = "连接中断";
        jobStatus.value = "failed";
      }
      eventSource?.close();
      eventSource = null;
    };
  }

  async function cancel() {
    if (activeJobId.value) {
      try {
        await cancelJob(activeJobId.value);
      } catch {
        // 忽略取消失败
      }
    }
    cleanup();
  }

  function cleanup() {
    stopElapsedTimer();
    if (eventSource) {
      eventSource.close();
      eventSource = null;
    }
  }

  onUnmounted(cleanup);

  return {
    activeJobId,
    activeJobType,
    jobStatus,
    jobProgress,
    jobMessage,
    jobError,
    elapsedSeconds,
    formattedElapsed,
    isActive,
    isCompleted,
    isFailed,
    connect,
    cancel,
    cleanup,
  };
}
