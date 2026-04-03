import { ref, computed } from "vue";
import { ElMessage } from "element-plus";
import { useMeetingStore } from "../stores/meetingStore";
import { notifyApiError } from "../utils/notify";

export function useTranscription(meetingId: number) {
  const store = useMeetingStore();

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

  async function removeTranscript(transcriptId: number) {
    try {
      await store.removeTranscript(meetingId, transcriptId);
      ElMessage.success("转写片段已删除");
    } catch (err) {
      notifyApiError(err, { prefix: "删除转写失败" });
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

  return {
    onFilePicked,
    removeTranscript,
    runPostprocess,
  };
}