import { defineStore } from "pinia";
import {
  createTask,
  createMeeting,
  deleteMeeting,
  getMeeting,
  getMeetings,
  getMeetingTranscripts,
  getTasksByMeeting,
  deleteTranscript,
  exportMeetingSummary,
  transcribeMeetingAudio,
  triggerPostprocess,
  uploadMeetingAudio,
  type Meeting,
  type MeetingCreatePayload,
  type MeetingDetail,
  type MeetingListParams,
  type MeetingListResult,
  type TaskCreatePayload,
  type TaskItem,
  type Transcript,
} from "../api/meetings";
import { updateTaskStatus, type TaskStatus } from "../api/tasks";
import { getApiErrorMessage } from "../api/client";
import type { Speaker, DiarizationSegment } from "../api/types";

interface MeetingState {
  meetings: Meeting[];
  meetingsTotal: number;
  currentMeeting: MeetingDetail | null;
  transcripts: Transcript[];
  tasks: TaskItem[];
  speakers: Speaker[];
  diarizationSegments: DiarizationSegment[];
  loading: boolean;
  error: string | null;
}

export const useMeetingStore = defineStore("meeting", {
  state: (): MeetingState => ({
    meetings: [],
    meetingsTotal: 0,
    currentMeeting: null,
    transcripts: [],
    tasks: [],
    speakers: [],
    diarizationSegments: [],
    loading: false,
    error: null,
  }),
  actions: {
    async fetchMeetings(params?: MeetingListParams) {
      this.loading = true;
      this.error = null;
      try {
        const result: MeetingListResult = await getMeetings(params);
        this.meetings = result.items;
        this.meetingsTotal = result.total;
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
        const taskResult = await getTasksByMeeting(meetingId);
        this.tasks = taskResult.items;
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
    async appendRealtimeTranscript(meetingId: number, file: File) {
      this.error = null;
      try {
        await uploadMeetingAudio(meetingId, file);
        const transcript = await transcribeMeetingAudio(meetingId);
        this.transcripts.push(transcript);
        return transcript;
      } catch (error) {
        this.error = getApiErrorMessage(error);
        throw error;
      }
    },
    async removeTranscript(meetingId: number, transcriptId: number) {
      this.error = null;
      try {
        await deleteTranscript(transcriptId);
        this.transcripts = this.transcripts.filter((item) => item.id !== transcriptId);
        await this.fetchMeetingDetail(meetingId);
      } catch (error) {
        this.error = getApiErrorMessage(error);
        throw error;
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
    setSpeakers(speakers: Speaker[]) {
      this.speakers = speakers;
    },
    setDiarizationSegments(segments: DiarizationSegment[]) {
      this.diarizationSegments = segments;
    },
    updateSpeakerName(speakerId: string, newName: string) {
      const speaker = this.speakers.find((s) => s.id === speakerId);
      if (speaker) {
        speaker.name = newName;
      }
      this.diarizationSegments.forEach((segment) => {
        if (segment.speaker_id === speakerId) {
          segment.speaker_name = newName;
        }
      });
    },
    clearDiarizationData() {
      this.speakers = [];
      this.diarizationSegments = [];
    },
    clearAllState() {
      this.meetings = [];
      this.meetingsTotal = 0;
      this.currentMeeting = null;
      this.transcripts = [];
      this.tasks = [];
      this.speakers = [];
      this.diarizationSegments = [];
      this.loading = false;
      this.error = null;
    },
  },
});
