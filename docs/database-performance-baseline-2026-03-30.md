# SmartMeeting 数据库性能复核基线

**日期**: 2026-03-30  
**状态**: Verified

## 1. 目标

记录当前数据库性能检查入口、索引覆盖和回滚链路，作为后续执行 `check_health.sql` / `check_performance.sql` 的基线说明。

## 2. 已确认的检查入口

- `scripts/db/check_health.sql`
- `scripts/db/check_performance.sql`
- `scripts/db/run_all.sql`
- `scripts/db/run_rollbacks.sql`

## 3. 当前索引/查询覆盖情况

现有迁移 `database/migrations/004_indexes_perf.sql` 已覆盖：

- `meetings(status, scheduled_start_at)`
- `meetings(organizer_id, created_at)`
- `meeting_transcripts(meeting_id, created_at)`
- `meeting_transcripts(meeting_id, start_time_sec, end_time_sec)`
- `tasks(assignee_id, status, due_at)`
- `tasks(meeting_id, status, priority)`
- `tasks(status, priority, due_at)`
- `tasks(reporter_id, created_at)`

`check_performance.sql` 现有 EXPLAIN 目标与上述索引一致，覆盖：

- 会议状态/时间排序
- 按组织者查询会议
- 按会议读取转写
- 任务执行人筛选与截止排序
- 会议任务列表筛选
- 按报告人查看任务

## 4. 回滚链路

回滚脚本链路已存在：

- `database/rollback/rollback_005_to_004.sql`
- `database/rollback/rollback_004_to_003.sql`
- `database/rollback/rollback_003_to_002.sql`
- `database/rollback/rollback_002_to_001.sql`

## 5. 当前阻塞

本次已使用本地 MySQL 账号 `root / 111zzzxxx` 成功执行检查。

已实际尝试执行：

- `mysql -h 127.0.0.1 -u root -p111zzzxxx < scripts/db/check_health.sql`
- `mysql -h 127.0.0.1 -u root -p111zzzxxx < scripts/db/check_performance.sql`

早先失败是因为凭据错误：`ERROR 1045 (28000): Access denied for user 'root'@'localhost'`。

## 6. 实际输出摘要

- 健康检查确认存在 7 张表、2 个视图、多个触发器和存储过程。
- `SHOW INDEX` 显示性能索引已生效，包括 `idx_meetings_status_start`、`idx_meetings_organizer_created`、`idx_transcripts_meeting_time`、`idx_tasks_assignee_status_due`、`idx_tasks_meeting_status_priority`、`idx_tasks_status_priority_due`、`idx_tasks_reporter_created`。
- `EXPLAIN` 结果显示会议状态/时间排序、组织者查询、转写按会议读取、任务按报告人查询均命中索引；部分任务筛选场景仍显示 `Using filesort`，可作为后续微调优化点。

## 7. 后续建议

1. 在 DB README 或性能注释里补一条：任务筛选场景若要彻底去掉 `filesort`，可考虑针对特定排序条件再做索引微调。
2. 若未来连接信息变化，继续按 `scripts/db/check_health.sql` / `check_performance.sql` 复核。
