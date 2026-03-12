import { defineStore } from "pinia";
import {
  getMeeting,
  getMeetings,
  getMeetingTranscripts,
  getTasksByAssignee,
  transcribeMeetingAudio,
  triggerPostprocess,
  uploadMeetingAudio,
  type Meeting,
  type TaskItem,
  type Transcript,
} from "../api/meetings";

interface MeetingState {
  meetings: Meeting[];
  currentMeeting: Meeting | null;
  transcripts: Transcript[];
  tasks: TaskItem[];
  loading: boolean;
}

export const useMeetingStore = defineStore("meeting", {
  state: (): MeetingState => ({
    meetings: [],
    currentMeeting: null,
    transcripts: [],
    tasks: [],
    loading: false,
  }),
  actions: {
    async fetchMeetings() {
      this.loading = true;
      try {
        this.meetings = await getMeetings();
      } finally {
        this.loading = false;
      }
    },
    async fetchMeetingDetail(meetingId: number) {
      this.loading = true;
      try {
        this.currentMeeting = await getMeeting(meetingId);
        this.transcripts = await getMeetingTranscripts(meetingId);
        this.tasks = await getTasksByAssignee(this.currentMeeting.organizer_id);
      } finally {
        this.loading = false;
      }
    },
    async uploadAudioAndTranscribe(meetingId: number, file: File) {
      this.loading = true;
      try {
        await uploadMeetingAudio(meetingId, file);
        await transcribeMeetingAudio(meetingId);
        await this.fetchMeetingDetail(meetingId);
      } finally {
        this.loading = false;
      }
    },
    async runPostprocess(meetingId: number) {
      this.loading = true;
      try {
        await triggerPostprocess(meetingId);
        await this.fetchMeetingDetail(meetingId);
      } finally {
        this.loading = false;
      }
    },
  },
});
