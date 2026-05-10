use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use std::sync::Mutex;

const MAX_QUEUE_SIZE: usize = 1000;

/// 会议会话状态
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum SessionState {
    Idle,
    Recording,
    Paused,
    Stopped,
}

/// 会议会话信息
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MeetingSession {
    pub state: SessionState,
    pub meeting_id: Option<u32>,
    pub meeting_title: String,
    pub started_at: Option<String>,
    pub stopped_at: Option<String>,
    pub transcript_count: u32,
    pub queued_count: u32,
    pub error: Option<String>,
}

impl Default for MeetingSession {
    fn default() -> Self {
        Self {
            state: SessionState::Idle,
            meeting_id: None,
            meeting_title: String::new(),
            started_at: None,
            stopped_at: None,
            transcript_count: 0,
            queued_count: 0,
            error: None,
        }
    }
}

/// 离线转写队列（基于本地 SQLite）
pub struct OfflineQueue {
    conn: std::sync::Mutex<rusqlite::Connection>,
}

impl OfflineQueue {
    pub fn new(data_dir: &PathBuf) -> Self {
        let db_path = data_dir.join("offline_queue.db");
        let conn = rusqlite::Connection::open(&db_path)
            .expect("无法创建离线队列数据库");
        conn.execute_batch(
            "CREATE TABLE IF NOT EXISTS pending_transcripts (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                meeting_id  INTEGER NOT NULL,
                text        TEXT NOT NULL,
                speaker     TEXT,
                start_time  REAL,
                end_time    REAL,
                created_at  TEXT NOT NULL DEFAULT (datetime('now'))
            );",
        ).expect("无法创建离线队列表");
        Self { conn: std::sync::Mutex::new(conn) }
    }

    /// 入队一条转写记录
    pub fn enqueue(&self, meeting_id: u32, text: &str, speaker: Option<&str>, start_time: Option<f64>, end_time: Option<f64>) {
        let conn = self.conn.lock().unwrap();
        // 超出上限时删除最旧的
        let count: usize = conn
            .query_row("SELECT COUNT(*) FROM pending_transcripts", [], |r| r.get(0))
            .unwrap_or(0);
        if count >= MAX_QUEUE_SIZE {
            conn.execute(
                "DELETE FROM pending_transcripts WHERE id IN (SELECT id FROM pending_transcripts ORDER BY id ASC LIMIT ?)",
                [count - MAX_QUEUE_SIZE + 1],
            ).ok();
        }
        conn.execute(
            "INSERT INTO pending_transcripts (meeting_id, text, speaker, start_time, end_time) VALUES (?1, ?2, ?3, ?4, ?5)",
            rusqlite::params![meeting_id, text, speaker, start_time, end_time],
        ).ok();
    }

    /// 获取队列中指定会议的待发送记录
    pub fn pending_for_meeting(&self, meeting_id: u32) -> Vec<PendingTranscript> {
        let conn = self.conn.lock().unwrap();
        let mut stmt = conn
            .prepare("SELECT id, meeting_id, text, speaker, start_time, end_time FROM pending_transcripts WHERE meeting_id = ?1 ORDER BY id ASC")
            .unwrap();
        let rows = stmt
            .query_map([meeting_id], |row| {
                Ok(PendingTranscript {
                    id: row.get(0)?,
                    meeting_id: row.get(1)?,
                    text: row.get(2)?,
                    speaker: row.get(3)?,
                    start_time: row.get(4)?,
                    end_time: row.get(5)?,
                })
            })
            .unwrap();
        rows.filter_map(|r| r.ok()).collect()
    }

    /// 删除已成功同步的记录
    pub fn remove(&self, id: u32) {
        let conn = self.conn.lock().unwrap();
        conn.execute("DELETE FROM pending_transcripts WHERE id = ?1", [id]).ok();
    }

    /// 队列中的记录数
    pub fn count(&self) -> u32 {
        let conn = self.conn.lock().unwrap();
        conn.query_row("SELECT COUNT(*) FROM pending_transcripts", [], |r| r.get(0))
            .unwrap_or(0)
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PendingTranscript {
    pub id: u32,
    pub meeting_id: u32,
    pub text: String,
    pub speaker: Option<String>,
    pub start_time: Option<f64>,
    pub end_time: Option<f64>,
}

/// 会议会话管理器
pub struct MeetingSessionManager {
    pub session: Mutex<MeetingSession>,
    pub server_url: Mutex<String>,
    pub auth_token: Mutex<String>,
    pub offline_queue: OfflineQueue,
}

impl MeetingSessionManager {
    pub fn new(data_dir: PathBuf) -> Self {
        Self {
            session: Mutex::new(MeetingSession::default()),
            server_url: Mutex::new("http://127.0.0.1:8000".to_string()),
            auth_token: Mutex::new(String::new()),
            offline_queue: OfflineQueue::new(&data_dir),
        }
    }
}

/// 创建会议请求
#[derive(Serialize)]
struct CreateMeetingRequest {
    title: String,
    status: String,
}

/// 创建会议响应
#[derive(Deserialize)]
struct CreateMeetingResponse {
    id: u32,
    title: String,
}

/// 转写数据
#[derive(Serialize)]
struct TranscriptPayload {
    text: String,
    speaker: Option<String>,
    start_time: Option<f64>,
    end_time: Option<f64>,
}

fn auth_header(token: &str) -> String {
    format!("Bearer {}", token)
}

/// 尝试发送一条转写到服务器
async fn send_transcript(
    server_url: &str,
    auth_token: &str,
    meeting_id: u32,
    payload: &TranscriptPayload,
) -> Result<(), String> {
    let client = reqwest::Client::new();
    let response = client
        .post(format!(
            "{}/api/v1/meetings/{}/transcripts",
            server_url, meeting_id
        ))
        .header("Authorization", auth_header(auth_token))
        .json(payload)
        .send()
        .await
        .map_err(|e| format!("网络错误: {}", e))?;

    if !response.status().is_success() {
        let status = response.status();
        let body = response.text().await.unwrap_or_default();
        return Err(format!("服务器返回 {}: {}", status, body));
    }
    Ok(())
}

/// 刷新离线队列：将队列中的转写逐条发送到服务器
async fn flush_queue(manager: &MeetingSessionManager) -> u32 {
    let (server_url, auth_token, meeting_id) = {
        let session = manager.session.lock().unwrap();
        let mid = match session.meeting_id {
            Some(id) => id,
            None => return 0,
        };
        let url = manager.server_url.lock().unwrap().clone();
        let token = manager.auth_token.lock().unwrap().clone();
        (url, token, mid)
    };

    let pending = manager.offline_queue.pending_for_meeting(meeting_id);
    let mut flushed = 0u32;

    for item in pending {
        let payload = TranscriptPayload {
            text: item.text.clone(),
            speaker: item.speaker.clone(),
            start_time: item.start_time,
            end_time: item.end_time,
        };
        if send_transcript(&server_url, &auth_token, meeting_id, &payload)
            .await
            .is_ok()
        {
            manager.offline_queue.remove(item.id);
            flushed += 1;
        } else {
            // 服务器仍然不可达，停止刷新
            break;
        }
    }

    if flushed > 0 {
        let mut session = manager.session.lock().unwrap();
        session.transcript_count += flushed;
        session.queued_count = manager.offline_queue.count();
    }

    flushed
}

/// 开始会议会话
pub async fn start_session(
    manager: &MeetingSessionManager,
    title: String,
) -> Result<u32, String> {
    let (server_url, auth_token) = {
        let url = manager.server_url.lock().unwrap().clone();
        let token = manager.auth_token.lock().unwrap().clone();
        (url, token)
    };

    // 尝试刷新上次遗留的离线队列
    flush_queue(manager).await;

    // 在服务器端创建会议
    let client = reqwest::Client::new();
    let response = client
        .post(format!("{}/api/v1/meetings", server_url))
        .header("Authorization", auth_header(&auth_token))
        .json(&CreateMeetingRequest {
            title: title.clone(),
            status: "ongoing".to_string(),
        })
        .send()
        .await
        .map_err(|e| format!("创建会议失败: {}", e))?;

    if !response.status().is_success() {
        let status = response.status();
        let body = response.text().await.unwrap_or_default();
        return Err(format!("创建会议返回错误 {}: {}", status, body));
    }

    let meeting: CreateMeetingResponse = response
        .json()
        .await
        .map_err(|e| format!("解析会议响应失败: {}", e))?;

    // 更新会话状态
    let mut session = manager.session.lock().unwrap();
    session.state = SessionState::Recording;
    session.meeting_id = Some(meeting.id);
    session.meeting_title = meeting.title;
    session.started_at = Some(chrono::Utc::now().to_rfc3339());
    session.stopped_at = None;
    session.transcript_count = 0;
    session.queued_count = 0;
    session.error = None;

    Ok(meeting.id)
}

/// 同步转写文本到服务器（失败时入队离线队列）
pub async fn sync_transcript(
    manager: &MeetingSessionManager,
    text: String,
    speaker: Option<String>,
    start_time: Option<f64>,
    end_time: Option<f64>,
) -> Result<(), String> {
    let (meeting_id, server_url, auth_token) = {
        let session = manager.session.lock().unwrap();
        let meeting_id = session.meeting_id.ok_or("会议未开始")?;
        let url = manager.server_url.lock().unwrap().clone();
        let token = manager.auth_token.lock().unwrap().clone();
        (meeting_id, url, token)
    };

    let payload = TranscriptPayload {
        text: text.clone(),
        speaker: speaker.clone(),
        start_time,
        end_time,
    };

    // 先尝试发送
    match send_transcript(&server_url, &auth_token, meeting_id, &payload).await {
        Ok(()) => {
            {
                let mut session = manager.session.lock().unwrap();
                session.transcript_count += 1;
            }
            // 发送成功后，尝试刷新队列中更早的记录
            flush_queue(manager).await;
            Ok(())
        }
        Err(_) => {
            // 服务器不可达，存入离线队列
            manager.offline_queue.enqueue(
                meeting_id,
                &text,
                speaker.as_deref(),
                start_time,
                end_time,
            );
            {
                let mut session = manager.session.lock().unwrap();
                session.queued_count = manager.offline_queue.count();
            }
            Ok(()) // 不报错，静默入队
        }
    }
}

/// 停止会议会话
pub async fn stop_session(
    manager: &MeetingSessionManager,
) -> Result<(), String> {
    // 停止前先尝试刷新队列
    flush_queue(manager).await;

    let (meeting_id, server_url, auth_token) = {
        let session = manager.session.lock().unwrap();
        let meeting_id = session.meeting_id.ok_or("会议未开始")?;
        let url = manager.server_url.lock().unwrap().clone();
        let token = manager.auth_token.lock().unwrap().clone();
        (meeting_id, url, token)
    };

    // 更新会议状态为已完成
    let client = reqwest::Client::new();
    let response = client
        .patch(format!("{}/api/v1/meetings/{}", server_url, meeting_id))
        .header("Authorization", auth_header(&auth_token))
        .json(&serde_json::json!({
            "status": "done"
        }))
        .send()
        .await
        .map_err(|e| format!("停止会议失败: {}", e))?;

    if !response.status().is_success() {
        let status = response.status();
        let body = response.text().await.unwrap_or_default();
        return Err(format!("停止会议返回错误 {}: {}", status, body));
    }

    // 更新会话状态
    let mut session = manager.session.lock().unwrap();
    session.state = SessionState::Stopped;
    session.stopped_at = Some(chrono::Utc::now().to_rfc3339());

    Ok(())
}

/// 获取当前会话状态
pub fn get_session_status(manager: &MeetingSessionManager) -> MeetingSession {
    manager.session.lock().unwrap().clone()
}
