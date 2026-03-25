import { defineStore } from "pinia";
import {
  createTask,
  createMeeting,
  deleteMeeting,
  getMeeting,
  getMeetings,
  getMeetingTranscripts,
  getTasksByMeeting,
  exportMeetingSummary,
  transcribeMeetingAudio,
  triggerPostprocess,
  uploadMeetingAudio,
  type Meeting,
  type MeetingCreatePayload,
  type MeetingDetail,
  type MeetingListParams,
  type TaskCreatePayload,
  type TaskItem,
  type Transcript,
} from "../api/meetings";
import { updateTaskStatus, type TaskStatus } from "../api/tasks";
import { getApiErrorMessage } from "../api/client";

interface MeetingState {
  meetings: Meeting[];
  currentMeeting: MeetingDetail | null;
  transcripts: Transcript[];
  tasks: TaskItem[];
  loading: boolean;
  error: string | null;
}

export const useMeetingStore = defineStore("meeting", {
  state: (): MeetingState => ({
    meetings: [],
    currentMeeting: null,
    transcripts: [],
    tasks: [],
    loading: false,
    error: null,
  }),
  actions: {
    async fetchMeetings(params?: MeetingListParams) {
      this.loading = true;
      this.error = null;
      try {
        this.meetings = await getMeetings(params);
      } catch (error) {
        this.error = getApiErrorMessage(error);
        throw error;
      } finally {
        this.loading = false;
      }
    },
    async createMeeting(payload: MeetingCreatePayload) {
      this.error = null;
      try {
        const meeting = await createMeeting(payload);
        this.meetings.unshift(meeting);
        return meeting;
      } catch (error) {
        this.error = getApiErrorMessage(error);
        throw error;
      }
    },
    async removeMeeting(meetingId: number) {
      this.error = null;
      try {
        await deleteMeeting(meetingId);
        this.meetings = this.meetings.filter((m) => m.id !== meetingId);
      } catch (error) {
        this.error = getApiErrorMessage(error);
        throw error;
      }
    },
    async fetchMeetingDetail(meetingId: number) {
      this.loading = true;
      this.error = null;
      try {
        this.currentMeeting = await getMeeting(meetingId);
        this.transcripts = await getMeetingTranscripts(meetingId);
        this.tasks = await getTasksByMeeting(meetingId);
      } catch (error) {
        this.error = getApiErrorMessage(error);
        throw error;
      } finally {
        this.loading = false;
      }
    },
    async uploadAudioAndTranscribe(meetingId: number, file: File) {
      this.loading = true;
      this.error = null;
      try {
        await uploadMeetingAudio(meetingId, file);
        await transcribeMeetingAudio(meetingId);
        await this.fetchMeetingDetail(meetingId);
      } catch (error) {
        this.error = getApiErrorMessage(error);
        throw error;
      } finally {
        this.loading = false;
      }
    },
    async runPostprocess(meetingId: number) {
      this.loading = true;
      this.error = null;
      try {
        await triggerPostprocess(meetingId);
        await this.fetchMeetingDetail(meetingId);
      } catch (error) {
        this.error = getApiErrorMessage(error);
        throw error;
      } finally {
        this.loading = false;
      }
    },
    async exportMeetingSummary(meetingId: number) {
      this.loading = true;
      this.error = null;
      try {
        return await exportMeetingSummary(meetingId);
      } catch (error) {
        this.error = getApiErrorMessage(error);
        throw error;
      } finally {
        this.loading = false;
      }
    },
    async changeTaskStatus(taskId: number, newStatus: TaskStatus) {
      this.error = null;
      try {
        const updated = await updateTaskStatus(taskId, newStatus);
        const idx = this.tasks.findIndex((t) => t.id === taskId);
        if (idx !== -1) this.tasks[idx] = updated;
        return updated;
      } catch (error) {
        this.error = getApiErrorMessage(error);
        throw error;
      }
    },
    async createMeetingTask(payload: TaskCreatePayload) {
      this.error = null;
      try {
        const task = await createTask(payload);
        this.tasks.unshift(task);
        return task;
      } catch (error) {
        this.error = getApiErrorMessage(error);
        throw error;
      }
    },
  },
});
