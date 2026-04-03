import { ref, computed, watch, onBeforeUnmount } from "vue";
import { ElMessage } from "element-plus";
import { useMeetingStore } from "../stores/meetingStore";
import { notifyApiError } from "../utils/notify";
// @ts-ignore
import { prepare, layout } from "@chenglou/pretext";

export function useSummary(meetingId: number) {
  const store = useMeetingStore();

  const maxClampLines = ref(4);
  const totalLineCount = ref(0);

  const summaryBlockRef = ref<HTMLElement | null>(null);
  const summaryWidth = ref(0);
  const isExpanded = ref(false);
  const showExpandBtn = ref(false);
  let resizeObserver: ResizeObserver | null = null;

  let cachedSummaryText = "";
  let cachedPrepared: any = null;
  let cachedWidth = -1;

  function formatSummaryForDisplay(raw: string | null | undefined): string {
    if (!raw) {
      return "暂无会议摘要";
    }

    let cleaned = raw;
    cleaned = cleaned.replace(/^[\s\u00A0·•]+/gm, "");
    cleaned = cleaned.replace(/^\s*#{1,6}\s*/gm, "");
    cleaned = cleaned.replace(/^\s*[-*+]\s+/gm, "• ");
    cleaned = cleaned.replace(/\*{3,}/g, "");
    cleaned = cleaned.replace(/\*\*(.*?)\*\*/g, "$1");
    cleaned = cleaned.replace(/\*(.*?)\*/g, "$1");
    cleaned = cleaned.replace(/\n{3,}/g, "\n\n");
    cleaned = cleaned
      .split(/\r?\n/)
      .map((line) => line.trimEnd())
      .join("\n")
      .trim();
    return cleaned || "暂无会议摘要";
  }

  const summaryDisplayText = computed(() => formatSummaryForDisplay(store.currentMeeting?.summary));

  watch(() => store.currentMeeting?.summary, () => {
    measureSummary();
  });

  function measureSummary() {
    if (summaryWidth.value <= 0) {
      showExpandBtn.value = false;
      return;
    }
    const summaryText = summaryDisplayText.value;
    if (!summaryText || summaryText === "暂无会议摘要") {
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

  function initResizeObserver() {
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
  }

  function cleanupObserver() {
    if (resizeObserver) {
      resizeObserver.disconnect();
    }
  }

  onBeforeUnmount(() => {
    cleanupObserver();
  });

  async function copySummary() {
    const summary = summaryDisplayText.value;
    if (!summary) return;
    try {
      await navigator.clipboard.writeText(summary);
      ElMessage.success("摘要已复制");
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

  return {
    maxClampLines,
    totalLineCount,
    summaryBlockRef,
    summaryWidth,
    isExpanded,
    showExpandBtn,
    summaryDisplayText,
    copySummary,
    downloadSummary,
    initResizeObserver
  };
}