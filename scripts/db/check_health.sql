-- SmartMeeting 数据库健康检查脚本

USE smartmeeting;

SELECT '=== TABLES ===' AS section;
SHOW TABLES;

SELECT '=== VIEWS ===' AS section;
SHOW FULL TABLES WHERE TABLE_TYPE = 'VIEW';

SELECT '=== TRIGGERS ===' AS section;
SHOW TRIGGERS;

SELECT '=== PROCEDURES ===' AS section;
SHOW PROCEDURE STATUS WHERE Db = 'smartmeeting';

SELECT '=== INDEX USERS ===' AS section;
SHOW INDEX FROM users;

SELECT '=== INDEX MEETINGS ===' AS section;
SHOW INDEX FROM meetings;

SELECT '=== INDEX MEETING_TRANSCRIPTS ===' AS section;
SHOW INDEX FROM meeting_transcripts;

SELECT '=== INDEX TASKS ===' AS section;
SHOW INDEX FROM tasks;

SELECT '=== SAMPLE VIEW DATA ===' AS section;
SELECT * FROM v_meeting_overview LIMIT 5;

SELECT '=== TASK PROC SAMPLE ===' AS section;
CALL sp_list_tasks_by_user(4002, NULL);
