/**
 * Zod validation schemas for API requests and responses.
 * These schemas provide runtime validation and type inference for all API payloads.
 */

import { z } from 'zod'

// ============================================
// Enums
// ============================================

export const UserRoleSchema = z.enum(['admin', 'member'])
export const TaskPrioritySchema = z.enum(['high', 'medium', 'low'])
export const TaskStatusSchema = z.enum(['todo', 'in_progress', 'done'])
export const MeetingStatusSchema = z.enum(['planned', 'ongoing', 'done', 'cancelled'])

// ============================================
// User Schemas
// ============================================

export const UserItemSchema = z.object({
  id: z.number(),
  username: z.string(),
  email: z.string().email(),
  full_name: z.string(),
  role: UserRoleSchema,
  is_active: z.boolean(),
  created_at: z.string(),
  updated_at: z.string(),
})

export const UserCreateSchema = z.object({
  username: z.string().min(1).max(50),
  email: z.string().email(),
  password_hash: z.string().min(1),
  full_name: z.string().min(1).max(100),
  role: UserRoleSchema.optional().default('member'),
})

export const UserUpdateSchema = z.object({
  username: z.string().min(1).max(50).optional(),
  email: z.string().email().optional(),
  full_name: z.string().min(1).max(100).optional(),
  role: UserRoleSchema.optional(),
  is_active: z.boolean().optional(),
})

// ============================================
// Auth Schemas
// ============================================

export const LoginRequestSchema = z.object({
  username: z.string().min(1),
  password: z.string().min(1),
})

export const LoginResponseSchema = z.object({
  access_token: z.string(),
  token_type: z.string(),
})

export const CurrentUserSchema = UserItemSchema

// ============================================
// Meeting Schemas
// ============================================

export const MeetingCreateSchema = z.object({
  title: z.string().min(1).max(200),
  description: z.string().max(1000).nullable().optional(),
  organizer_id: z.number(),
  scheduled_start_at: z.string().datetime().nullable().optional(),
  scheduled_end_at: z.string().datetime().nullable().optional(),
  location: z.string().max(255).nullable().optional(),
})

export const MeetingUpdateSchema = z.object({
  title: z.string().min(1).max(200).optional(),
  description: z.string().max(1000).nullable().optional(),
  scheduled_start_at: z.string().datetime().nullable().optional(),
  scheduled_end_at: z.string().datetime().nullable().optional(),
  location: z.string().max(255).nullable().optional(),
  status: MeetingStatusSchema.optional(),
})

export const MeetingListParamsSchema = z.object({
  status: MeetingStatusSchema.optional(),
  organizer_id: z.number().optional(),
  keyword: z.string().optional(),
  sort_by: z.string().optional(),
  limit: z.number().min(1).max(100).optional(),
  offset: z.number().min(0).optional(),
})

export const MeetingSchema = z.object({
  id: z.number(),
  title: z.string(),
  description: z.string().nullable(),
  organizer_id: z.number(),
  scheduled_start_at: z.string().datetime().nullable(),
  scheduled_end_at: z.string().datetime().nullable(),
  actual_start_at: z.string().datetime().nullable(),
  actual_end_at: z.string().datetime().nullable(),
  location: z.string().nullable(),
  status: MeetingStatusSchema,
  summary: z.string().nullable(),
  postprocessed_at: z.string().datetime().nullable(),
  postprocess_version: z.string().nullable(),
  share_token: z.string().nullable(),
  shared_at: z.string().datetime().nullable(),
  created_at: z.string().datetime(),
  updated_at: z.string().datetime(),
})

export const MeetingDetailSchema = MeetingSchema.extend({
  organizer: UserItemSchema,
})

export const MeetingListResultSchema = z.object({
  items: z.array(MeetingSchema),
  total: z.number(),
})

export const MeetingShareCreateResultSchema = z.object({
  meeting_id: z.number(),
  share_token: z.string(),
  share_path: z.string(),
  created_now: z.boolean(),
  shared_at: z.string().datetime(),
})

// ============================================
// Transcript Schemas
// ============================================

export const TranscriptSchema = z.object({
  id: z.number(),
  meeting_id: z.number(),
  speaker_user_id: z.number().nullable(),
  speaker_name: z.string().nullable(),
  segment_index: z.number(),
  start_time_sec: z.number().nullable(),
  end_time_sec: z.number().nullable(),
  language_code: z.string(),
  source: z.string(),
  content: z.string(),
  created_at: z.string().datetime(),
  updated_at: z.string().datetime(),
})

export const TranscriptCreateSchema = z.object({
  meeting_id: z.number(),
  speaker_user_id: z.number().nullable().optional(),
  speaker_name: z.string().max(100).optional(),
  segment_index: z.number(),
  content: z.string().min(1),
  start_time_sec: z.number().nullable().optional(),
  end_time_sec: z.number().nullable().optional(),
  language_code: z.string().optional().default('zh-CN'),
  source: z.string().optional().default('manual'),
})

// ============================================
// Task Schemas
// ============================================

export const TaskCreateSchema = z.object({
  meeting_id: z.number(),
  transcript_id: z.number().nullable().optional(),
  title: z.string().min(1).max(200),
  description: z.string().max(1000).nullable().optional(),
  assignee_id: z.number().nullable().optional(),
  reporter_id: z.number().nullable().optional(),
  priority: TaskPrioritySchema.optional().default('medium'),
  status: TaskStatusSchema.optional().default('todo'),
  due_at: z.string().datetime().nullable().optional(),
})

export const TaskUpdateSchema = z.object({
  title: z.string().min(1).max(200).optional(),
  description: z.string().max(1000).nullable().optional(),
  assignee_id: z.number().nullable().optional(),
  reporter_id: z.number().nullable().optional(),
  priority: TaskPrioritySchema.optional(),
  status: TaskStatusSchema.optional(),
  progress_note: z.string().max(1000).nullable().optional(),
  due_at: z.string().datetime().nullable().optional(),
})

export const TaskItemSchema = z.object({
  id: z.number(),
  meeting_id: z.number(),
  transcript_id: z.number().nullable(),
  title: z.string(),
  description: z.string().nullable(),
  assignee_id: z.number().nullable(),
  reporter_id: z.number().nullable(),
  priority: TaskPrioritySchema,
  status: TaskStatusSchema,
  progress_note: z.string().nullable(),
  due_at: z.string().datetime().nullable(),
  completed_at: z.string().datetime().nullable(),
  is_overdue: z.boolean(),
  is_due_soon: z.boolean(),
  created_at: z.string().datetime(),
  updated_at: z.string().datetime(),
})

export const TaskListParamsSchema = z.object({
  assignee_id: z.number().optional(),
  meeting_id: z.number().optional(),
  status: TaskStatusSchema.optional(),
  priority: TaskPrioritySchema.optional(),
  keyword: z.string().optional(),
  sort_by: z.string().optional(),
  limit: z.number().min(1).max(100).optional(),
  offset: z.number().min(0).optional(),
})

export const TaskListResultSchema = z.object({
  items: z.array(TaskItemSchema),
  total: z.number(),
})

// ============================================
// Participant Schemas
// ============================================

export const MeetingParticipantOutSchema = z.object({
  id: z.number(),
  meeting_id: z.number(),
  user_id: z.number(),
  email: z.string().email().nullable(),
  participant_role: z.string(),
  attendance_status: z.string(),
  joined_at: z.string().datetime().nullable(),
  left_at: z.string().datetime().nullable(),
  created_at: z.string().datetime(),
  updated_at: z.string().datetime(),
})

export const ParticipantAddSchema = z.object({
  user_id: z.number(),
  participant_role: z.string().optional().default('attendee'),
  attendance_status: z.string().optional().default('invited'),
})

// ============================================
// Audio Schemas
// ============================================

export const MeetingAudioSchema = z.object({
  id: z.number(),
  meeting_id: z.number(),
  filename: z.string(),
  storage_path: z.string(),
  content_type: z.string(),
  size_bytes: z.number(),
  uploaded_at: z.string().datetime(),
})

// ============================================
// Structured Summary Schemas
// ============================================

export const AgendaItemSchema = z.object({
  topic: z.string().min(1).max(500),
  speaker: z.string().max(100).nullable().optional(),
  key_points: z.array(z.string()).optional().default([]),
})

export const ResolutionSchema = z.object({
  decision: z.string().min(1).max(500),
  proposer: z.string().max(100).nullable().optional(),
  context: z.string().max(1000).nullable().optional(),
})

export const TodoItemSchema = z.object({
  title: z.string().min(1).max(200),
  description: z.string().max(1000).nullable().optional(),
  assignee: z.string().max(100).nullable().optional(),
  due_date: z.string().max(100).nullable().optional(),
  priority: TaskPrioritySchema.optional().default('medium'),
})

export const StructuredSummarySchema = z.object({
  agenda: z.array(AgendaItemSchema).optional().default([]),
  resolutions: z.array(ResolutionSchema).optional().default([]),
  todos: z.array(TodoItemSchema).optional().default([]),
  raw_summary: z.string().nullable().optional(),
})

export const MeetingStructuredSummaryResultSchema = z.object({
  meeting_id: z.number(),
  structured_summary: StructuredSummarySchema,
  has_structured_data: z.boolean(),
})

// ============================================
// Shared Meeting Schemas
// ============================================

export const SharedMeetingDetailSchema = z.object({
  meeting: MeetingDetailSchema,
  transcripts: z.array(TranscriptSchema),
  tasks: z.array(TaskItemSchema),
})

// ============================================
// Hotword Schemas
// ============================================

export const HotwordItemSchema = z.object({
  id: z.number(),
  user_id: z.number(),
  word: z.string().min(1).max(100),
  created_at: z.string().datetime(),
})

export const HotwordCreateSchema = z.object({
  word: z.string().min(1).max(100),
})

// ============================================
// Postprocess Result Schema
// ============================================

export const MeetingPostprocessResultSchema = z.object({
  meeting_id: z.number(),
  summary: z.string(),
  tasks: z.array(TaskItemSchema),
})

// ============================================
// Type exports (inferred from schemas)
// ============================================

export type UserItemType = z.infer<typeof UserItemSchema>
export type UserCreateType = z.infer<typeof UserCreateSchema>
export type UserUpdateType = z.infer<typeof UserUpdateSchema>
export type LoginRequestType = z.infer<typeof LoginRequestSchema>
export type LoginResponseType = z.infer<typeof LoginResponseSchema>
export type MeetingCreateType = z.infer<typeof MeetingCreateSchema>
export type MeetingUpdateType = z.infer<typeof MeetingUpdateSchema>
export type MeetingType = z.infer<typeof MeetingSchema>
export type MeetingDetailType = z.infer<typeof MeetingDetailSchema>
export type MeetingListParamsType = z.infer<typeof MeetingListParamsSchema>
export type MeetingListResultType = z.infer<typeof MeetingListResultSchema>
export type TranscriptType = z.infer<typeof TranscriptSchema>
export type TranscriptCreateType = z.infer<typeof TranscriptCreateSchema>
export type TaskCreateType = z.infer<typeof TaskCreateSchema>
export type TaskUpdateType = z.infer<typeof TaskUpdateSchema>
export type TaskItemType = z.infer<typeof TaskItemSchema>
export type TaskListParamsType = z.infer<typeof TaskListParamsSchema>
export type TaskListResultType = z.infer<typeof TaskListResultSchema>
export type MeetingParticipantOutType = z.infer<typeof MeetingParticipantOutSchema>
export type ParticipantAddType = z.infer<typeof ParticipantAddSchema>
export type MeetingAudioType = z.infer<typeof MeetingAudioSchema>
export type StructuredSummaryType = z.infer<typeof StructuredSummarySchema>
export type MeetingStructuredSummaryResultType = z.infer<typeof MeetingStructuredSummaryResultSchema>
export type SharedMeetingDetailType = z.infer<typeof SharedMeetingDetailSchema>
export type HotwordItemType = z.infer<typeof HotwordItemSchema>
export type HotwordCreateType = z.infer<typeof HotwordCreateSchema>
export type MeetingPostprocessResultType = z.infer<typeof MeetingPostprocessResultSchema>