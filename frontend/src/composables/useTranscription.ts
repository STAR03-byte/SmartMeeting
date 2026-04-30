import { ref, computed } from "vue";
import { ElMessage } from "element-plus";
import { useMeetingStore } from "../stores/meetingStore";
import { updateMeeting } from "../api/meetings";
import { notifyApiError } from "../utils/notify";
import { useJobProgress } from "./useJobProgress";
import type { ProcessingJobType } from "../api/types";

export function useTranscription(meetingId: number) {
  const store = useMeetingStore();
  const jobProgress = useJobProgress();

  async function onFilePicked(file: { raw?: File }) {
    if (!file.raw) {
      return;
    }
    try {
      await store.uploadAudioAndTranscribe(meetingId, file.raw);
      await updateMeeting(meetingId, {
        actual_start_at: store.currentMeeting?.actual_start_at ?? new Date().toISOString(),
        status: "ongoing",
      });
      await store.fetchMeetingDetail(meetingId);
      await store.fetchMeetings();
      ElMessage.success("音频上传并转写完成");
    } catch (err) {
      notifyApiError(err);
    }
  }

  async function onFilePickedAsync(file: { raw?: File }) {
    if (!file.raw) {
      return;
    }
    try {
      const job = await store.uploadAudioAndTranscribeAsync(meetingId, file.raw);
      await updateMeeting(meetingId, {
        actual_start_at: store.currentMeeting?.actual_start_at ?? new Date().toISOString(),
        status: "ongoing",
      });
      jobProgress.connect(job.job_id, "transcribe");
    } catch (err) {
      notifyApiError(err);
    }
  }

  async function onJobCompleted(jobType?: ProcessingJobType | null) {
    await store.fetchMeetingDetail(meetingId);
    await store.fetchMeetings();
    if (jobType === "postprocess") {
      ElMessage.success("已生成会议纪要与任务");
    } else {
      ElMessage.success("音频转写完成");
    }
    jobProgress.cleanup();
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

  async function runPostprocessAsync() {
    try {
      const job = await store.runPostprocessAsync(meetingId);
      jobProgress.connect(job.job_id, "postprocess");
    } catch (err) {
      notifyApiError(err);
    }
  }

  return {
    onFilePicked,
    onFilePickedAsync,
    onJobCompleted,
    removeTranscript,
    runPostprocess,
    runPostprocessAsync,
    jobProgress,
  };
}
