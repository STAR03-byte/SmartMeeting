import { defineStore } from "pinia";
import {
  getMeeting,
  getMeetings,
  getMeetingTranscripts,
  getTasksByMeeting,
  transcribeMeetingAudio,
  triggerPostprocess,
  uploadMeetingAudio,
  type Meeting,
  type MeetingDetail,
  type TaskItem,
  type Transcript,
} from "../api/meetings";
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
    async fetchMeetings() {
      this.loading = true;
      this.error = null;
      try {
        this.meetings = await getMeetings();
      } catch (error) {
        this.error = getApiErrorMessage(error);
        throw error;
      } finally {
        this.loading = false;
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
  },
});
