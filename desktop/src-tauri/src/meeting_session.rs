use serde::{Deserialize, Serialize};
use std::sync::Mutex;

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
            error: None,
        }
    }
}

/// 会议会话管理器
pub struct MeetingSessionManager {
    pub session: Mutex<MeetingSession>,
    pub server_url: Mutex<String>,
    pub auth_token: Mutex<String>,
}

impl MeetingSessionManager {
    pub fn new() -> Self {
        Self {
            session: Mutex::new(MeetingSession::default()),
            server_url: Mutex::new("http://127.0.0.1:8000".to_string()),
            auth_token: Mutex::new(String::new()),
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

    // 在服务器端创建会议
    let client = reqwest::Client::new();
    let response = client
        .post(format!("{}/api/v1/meetings", server_url))
        .header("Authorization", format!("Bearer {}", auth_token))
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
    session.error = None;

    Ok(meeting.id)
}

/// 同步转写文本到服务器
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

    let client = reqwest::Client::new();
    let response = client
        .post(format!(
            "{}/api/v1/meetings/{}/transcripts",
            server_url, meeting_id
        ))
        .header("Authorization", format!("Bearer {}", auth_token))
        .json(&TranscriptPayload {
            text,
            speaker,
            start_time,
            end_time,
        })
        .send()
        .await
        .map_err(|e| format!("同步转写失败: {}", e))?;

    if !response.status().is_success() {
        let status = response.status();
        let body = response.text().await.unwrap_or_default();
        return Err(format!("同步转写返回错误 {}: {}", status, body));
    }

    // 更新转写计数
    let mut session = manager.session.lock().unwrap();
    session.transcript_count += 1;

    Ok(())
}

/// 停止会议会话
pub async fn stop_session(
    manager: &MeetingSessionManager,
) -> Result<(), String> {
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
        .header("Authorization", format!("Bearer {}", auth_token))
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
