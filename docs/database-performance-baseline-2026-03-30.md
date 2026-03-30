# SmartMeeting 数据库性能复核基线

**日期**: 2026-03-30  
**状态**: Blocked

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

本地 MySQL 默认账号 `root/root` 与 `smartmeeting/smartmeeting` 均无法直接连接，暂无法在当前环境跑 `check_health.sql` / `check_performance.sql` 获取真实输出。

已实际尝试执行：

- `mysql -u root -proot < scripts/db/check_health.sql`
- `mysql -u root -proot < scripts/db/check_performance.sql`

结果均为 `ERROR 1045 (28000): Access denied for user 'root'@'localhost'`。

## 6. 后续建议

1. 在可用的 MySQL 环境中执行：
   - `mysql -u <user> -p < scripts/db/check_health.sql`
   - `mysql -u <user> -p < scripts/db/check_performance.sql`
2. 将 EXPLAIN 输出整理进本文件或 DB README。
3. 如发现全表扫描，再补索引迁移。
