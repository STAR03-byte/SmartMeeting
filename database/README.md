# SmartMeeting 数据库模块说明

本目录用于管理 SmartMeeting 的 MySQL 数据库结构、种子数据和后续迁移。

## 目录说明

- `migrations/`: 建表与结构演进脚本
- `seeds/`: 初始化测试数据脚本
- `rollback/`: 回滚脚本（按版本逆向回退）
- `backups/`: 备份文件目录（不建议提交大体积备份）

## 初始化顺序

按以下顺序执行：

1. `database/migrations/001_init_smartmeeting.sql`
2. `database/migrations/002_enhance_smartmeeting.sql`
3. `database/migrations/003_sp_task_query.sql`
4. `database/migrations/004_indexes_perf.sql`
5. `database/migrations/005_audit_and_participants.sql`
6. `database/migrations/006_collaboration_share_fields.sql`
7. `database/migrations/006_meeting_share_links.sql`
8. `database/migrations/007_fix_meeting_audio_cascade.sql`
9. `database/migrations/008_participant_unique_guard.sql`
10. `database/migrations/009_extend_audit_logs_for_auth_events.sql`
11. `database/seeds/001_seed_basic_data.sql`（可选）
12. `database/seeds/002_seed_participants.sql`（可选）

也可直接一键执行:

- `scripts/db/run_all.sql`

## 执行命令示例

```bash
mysql -u <user> -p < database/migrations/001_init_smartmeeting.sql
mysql -u <user> -p < database/migrations/002_enhance_smartmeeting.sql
mysql -u <user> -p < database/migrations/003_sp_task_query.sql
mysql -u <user> -p < database/migrations/004_indexes_perf.sql
mysql -u <user> -p < database/migrations/005_audit_and_participants.sql
mysql -u <user> -p < database/migrations/006_collaboration_share_fields.sql
mysql -u <user> -p < database/migrations/006_meeting_share_links.sql
mysql -u <user> -p < database/migrations/007_fix_meeting_audio_cascade.sql
mysql -u <user> -p < database/migrations/008_participant_unique_guard.sql
mysql -u <user> -p < database/migrations/009_extend_audit_logs_for_auth_events.sql
mysql -u <user> -p < database/seeds/001_seed_basic_data.sql
mysql -u <user> -p < database/seeds/002_seed_participants.sql
```

或使用 SOURCE 一键执行:

```bash
mysql -u <user> -p < scripts/db/run_all.sql
```

## 校验建议

```sql
USE smartmeeting;

SHOW TABLES;
SHOW FULL TABLES WHERE TABLE_TYPE = 'VIEW';
SHOW TRIGGERS LIKE 'tasks';
SHOW PROCEDURE STATUS WHERE Db = 'smartmeeting';

SELECT COUNT(*) AS audit_log_count FROM audit_logs;
SELECT COUNT(*) AS participant_count FROM meeting_participants;

SHOW INDEX FROM users;
SHOW INDEX FROM meetings;
SHOW INDEX FROM meeting_transcripts;
SHOW INDEX FROM tasks;

SELECT * FROM v_meeting_overview LIMIT 10;
CALL sp_list_tasks_by_user(4002, NULL);

EXPLAIN SELECT * FROM meetings
WHERE status = 'planned'
ORDER BY scheduled_start_at DESC
LIMIT 20;

EXPLAIN SELECT * FROM tasks
WHERE assignee_id = 4002 AND status IN ('todo', 'in_progress')
ORDER BY due_at ASC;

EXPLAIN SELECT * FROM meeting_transcripts
WHERE meeting_id = 3001
ORDER BY start_time_sec ASC;
```

也可直接执行:

- `scripts/db/check_health.sql`
- `scripts/db/check_performance.sql`

## 回滚说明

回滚脚本位于 `database/rollback/`，建议按以下顺序执行:

1. `rollback_009_to_008.sql`
2. `rollback_008_to_007.sql`
3. `rollback_007_to_006.sql`
4. `rollback_006_to_005.sql`
5. `rollback_005_to_004.sql`
6. `rollback_004_to_003.sql`
7. `rollback_003_to_002.sql`
8. `rollback_002_to_001.sql`

可直接执行:

```bash
mysql -u <user> -p < scripts/db/run_rollbacks.sql
```
