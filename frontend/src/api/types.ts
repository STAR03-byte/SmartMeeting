export type UserRole = "admin" | "member";
export type TaskPriority = "high" | "medium" | "low";
export type TaskStatus = "draft" | "todo" | "in_progress" | "done" | "cancelled";
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

export interface HotwordItem {
  id: number;
  user_id: number;
  word: string;
  created_at: string;
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
  share_expires_at: string | null;
  share_revoked_at: string | null;
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
  team_id?: number | null;
}

export interface MeetingListParams {
  status?: MeetingStatus;
  organizer_id?: number;
  keyword?: string;
  sort_by?: string;
  limit?: number;
  offset?: number;
}

export interface MeetingListResult {
  items: Meeting[];
  total: number;
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
  expires_at: string | null;
  revoked_at: string | null;
}

export interface MeetingShareCreatePayload {
  expires_at?: string | null;
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
  progress_note: string | null;
  can_manage: boolean;
  due_at: string | null;
  reminder_at: string | null;
  completed_at: string | null;
  is_overdue: boolean;
  is_due_soon: boolean;
  created_at: string;
  updated_at: string;
}

export interface TaskListParams {
  assignee_id?: number;
  meeting_id?: number;
  team_id?: number;
  status?: TaskStatus;
  priority?: TaskPriority;
  keyword?: string;
  sort_by?: string;
  limit?: number;
  offset?: number;
}

export interface TaskListResult {
  items: TaskItem[];
  total: number;
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
  reminder_at?: string | null;
}

export interface MeetingParticipantOut {
  id: number;
  meeting_id: number;
  user_id: number;
  username: string;
  full_name: string;
  email: string | null;
  participant_role: string;
  attendance_status: string;
  joined_at: string | null;
  left_at: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * ˵������Ϣ
 * ����˵���˷��빦�ܣ���ʶÿ��˵���˵Ļ�����Ϣ
 */
export interface Speaker {
  id: string;
  name: string;
  color: string;
  segment_count: number;
  total_duration_sec: number;
}

/**
 * ˵���˷���Ƭ��
 * ����˵���˱�ʶ��ʱ�䷶Χ���ı�����
 */
export interface DiarizationSegment {
  speaker_id: string;
  speaker_name: string;
  start_time_sec: number;
  end_time_sec: number;
  content: string;
}

/**
 * ˵��������������
 */
export interface SpeakerRenamePayload {
  speaker_id: string;
  new_name: string;
}
export interface AgendaItem {
  topic: string;
  speaker: string | null;
  key_points: string[];
}

export interface Resolution {
  decision: string;
  proposer: string | null;
  context: string | null;
}

export interface TodoItem {
  title: string;
  description: string | null;
  assignee: string | null;
  due_date: string | null;
  priority: "high" | "medium" | "low";
}

export interface StructuredSummary {
  agenda: AgendaItem[];
  resolutions: Resolution[];
  todos: TodoItem[];
  raw_summary: string | null;
}

export interface MeetingStructuredSummaryResult {
  meeting_id: number;
  structured_summary: StructuredSummary;
  has_structured_data: boolean;
}

// AI 助理相关类型

export type TaskPriorityLevel = "high" | "medium" | "low";
export type ChatChunkType = "chunk" | "end" | "error";
export type ConversationRole = "user" | "assistant";

export interface SuggestedTask {
  title: string;
  description?: string | null;
  assigneeName?: string | null;
  priority?: TaskPriorityLevel;
  dueHint?: string | null;
}

export interface RelatedTaskInfo {
  id: number;
  title: string;
}

export interface TaskSuggestions {
  steps: string[];
  risks: string[];
  suggestedRoles: string[];
  relatedTasks: RelatedTaskInfo[];
}

export interface TaskSuggestionRequest {
  title: string;
  description?: string;
  meetingId?: number;
  meeting_id?: number;
}

export interface Conversation {
  id: number;
  title: string;
  createdAt: string;
  updatedAt: string;
  created_at?: string;
  updated_at?: string;
}

export interface ConversationMessage {
  id: number;
  conversationId: number;
  role: ConversationRole;
  content: string;
  createdAt: string;
  taskId?: number;
  conversation_id?: number;
  created_at?: string;
}

export interface ChatContext {
  meetingId?: number;
  taskId?: number;
  taskIds?: number[];
  meeting_id?: number;
  task_ids?: number[];
}

export interface ChatChunk {
  type: ChatChunkType;
  content?: string;
  taskDraft?: TaskDraft;
  task_draft?: TaskDraft;
}

export interface TaskDraft {
  id: number;
  title: string;
  description?: string | null;
  meetingId: number;
  dueDate?: string | null;
  priority: TaskPriorityLevel;
  assigneeId?: number | null;
  status: string;
  meeting_id?: number;
  due_date?: string | null;
  assignee_id?: number | null;
}

export interface CreateConversationRequest {
  title?: string;
}

export interface SendMessageRequest {
  conversationId?: number;
  conversation_id?: number;
  message: string;
  context?: ChatContext;
}

export type TaskSuggestionResponse = TaskSuggestions;
export type ChatStreamContext = ChatContext;
export type CreateTaskDraftPayload = {
  meeting_id: number;
  title: string;
  description: string;
  due_date: string | Date;
  priority?: TaskPriorityLevel;
  assignee_id: number;
};

export interface KnowledgeSource {
  meeting_id: number;
  meeting_title: string;
  source_type: "meeting" | "summary" | "transcript" | "task" | "participant";
  snippet: string;
  created_at: string | null;
}

export interface KnowledgeQueryRequest {
  question: string;
  team_id?: number | null;
  limit?: number;
}

export interface KnowledgeQueryResponse {
  answer: string;
  sources: KnowledgeSource[];
  used_llm: boolean;
}
