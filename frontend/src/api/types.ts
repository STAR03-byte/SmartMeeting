export type UserRole = "admin" | "member";
export type TaskPriority = "high" | "medium" | "low";
export type TaskStatus = "todo" | "in_progress" | "done";
export type MeetingStatus = "planned" | "ongoing" | "done" | "cancelled";

export interface UserItem {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Meeting {
  id: number;
  title: string;
  description: string | null;
  organizer_id: number;
  scheduled_start_at: string | null;
  scheduled_end_at: string | null;
  actual_start_at: string | null;
  actual_end_at: string | null;
  location: string | null;
  status: MeetingStatus;
  summary: string | null;
  postprocessed_at: string | null;
  postprocess_version: string | null;
  share_token: string | null;
  shared_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface MeetingCreatePayload {
  title: string;
  description?: string | null;
  organizer_id: number;
  scheduled_start_at?: string | null;
  scheduled_end_at?: string | null;
  location?: string | null;
}

export interface MeetingListParams {
  status?: MeetingStatus;
  organizer_id?: number;
  keyword?: string;
  limit?: number;
  offset?: number;
}

export interface MeetingDetail extends Meeting {
  organizer: UserItem;
}

export interface MeetingShareCreateResult {
  meeting_id: number;
  share_token: string;
  share_path: string;
  created_now: boolean;
  shared_at: string;
}

export interface Transcript {
  id: number;
  meeting_id: number;
  speaker_user_id: number | null;
  speaker_name: string | null;
  segment_index: number;
  start_time_sec: number | null;
  end_time_sec: number | null;
  language_code: string;
  source: string;
  content: string;
  created_at: string;
  updated_at: string;
}

export interface SharedMeetingDetail {
  meeting: MeetingDetail;
  transcripts: Transcript[];
  tasks: TaskItem[];
}

export interface TaskItem {
  id: number;
  meeting_id: number;
  transcript_id: number | null;
  title: string;
  description: string | null;
  assignee_id: number | null;
  reporter_id: number | null;
  priority: TaskPriority;
  status: TaskStatus;
  due_at: string | null;
  completed_at: string | null;
  is_overdue: boolean;
  is_due_soon: boolean;
  created_at: string;
  updated_at: string;
}

export interface MeetingAudio {
  id: number;
  meeting_id: number;
  filename: string;
  storage_path: string;
  content_type: string;
  size_bytes: number;
  uploaded_at: string;
}

export interface MeetingPostprocessResult {
  meeting_id: number;
  summary: string;
  tasks: TaskItem[];
}

export interface TaskCreatePayload {
  meeting_id: number;
  transcript_id?: number | null;
  title: string;
  description?: string | null;
  assignee_id?: number | null;
  reporter_id?: number | null;
  priority?: TaskPriority;
  status?: TaskStatus;
  due_at?: string | null;
}
