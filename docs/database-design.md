# SmartMeeting 数据库设计说明

## 1. 设计目标

- 支持会议全生命周期: 创建、组织、记录、会后执行。
- 支持 AI 产物落库: 转写文本、任务提取结果。
- 支持业务审计: 关键实体变更可追溯。
- 支持性能扩展: 针对高频查询提供复合索引。

## 2. 核心表关系

- `users` 1 --- n `meetings`（组织者）
- `meetings` 1 --- n `meeting_transcripts`
- `meetings` 1 --- n `tasks`
- `meeting_transcripts` 1 --- n `tasks`（可选关联来源片段）
- `users` n --- n `meetings` 通过 `meeting_participants`

## 3. 功能映射

- 会议管理: `meetings`, `meeting_participants`
- 会议文本记录: `meeting_transcripts`
- 任务提取: `tasks.transcript_id` 关联转写来源
- 任务管理: `tasks`（状态、优先级、截止时间、执行人）
- 用户系统: `users`
- 审计跟踪: `audit_logs`

## 4. 增强能力

- 视图:
  - `v_meeting_overview`: 会议维度统计视图
  - `v_task_detail`: 任务详情联查视图
- 存储过程:
  - `sp_list_tasks_by_user`: 按用户和状态查询任务
- 触发器:
  - `trg_tasks_set_completed_at`: 任务完成时间自动维护
  - `trg_audit_meetings_*`: 会议增删改审计
  - `trg_audit_tasks_*`: 任务增删改审计

## 5. 迁移与回滚

- 迁移目录: `database/migrations/`
- 回滚目录: `database/rollback/`
- 一键初始化: `scripts/db/run_all.sql`
- 一键回滚: `scripts/db/run_rollbacks.sql`

## 6. 校验脚本

- 健康检查: `scripts/db/check_health.sql`
- 性能检查: `scripts/db/check_performance.sql`
