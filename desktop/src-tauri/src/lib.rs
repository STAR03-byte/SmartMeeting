#[cfg(feature = "audio-capture")]
mod audio_capture;
mod meeting_session;
mod transcription;

use meeting_session::{MeetingSession, MeetingSessionManager};
use std::path::PathBuf;
use std::sync::Mutex;
use tauri::State;
use transcription::{TranscriptResult, WhisperConfig};

/// 应用状态
pub struct AppState {
    pub whisper_config: Mutex<WhisperConfig>,
    pub session_manager: MeetingSessionManager,
}

/// 转写指定段落
#[tauri::command]
async fn transcribe_segment(
    segment_index: u32,
    _state: State<'_, AppState>,
) -> Result<TranscriptResult, String> {
    Err(format!("段落 {} 不存在（音频采集功能未启用）", segment_index))
}

/// 转写所有段落
#[tauri::command]
async fn transcribe_all_segments(
    _state: State<'_, AppState>,
) -> Result<Vec<TranscriptResult>, String> {
    Err("音频采集功能未启用。请使用 --features audio-capture 编译。".to_string())
}

/// 更新 Whisper 配置
#[tauri::command]
fn update_whisper_config(
    api_url: Option<String>,
    api_key: Option<String>,
    model: Option<String>,
    language: Option<String>,
    state: State<'_, AppState>,
) -> Result<(), String> {
    let mut config = state.whisper_config.lock().unwrap();
    if let Some(url) = api_url {
        config.api_url = url;
    }
    if let Some(key) = api_key {
        config.api_key = key;
    }
    if let Some(m) = model {
        config.model = m;
    }
    if let Some(lang) = language {
        config.language = Some(lang);
    }
    Ok(())
}

/// 获取当前 Whisper 配置
#[tauri::command]
fn get_whisper_config(state: State<'_, AppState>) -> WhisperConfig {
    state.whisper_config.lock().unwrap().clone()
}

/// 开始会议会话
#[tauri::command]
async fn start_meeting_session(
    title: String,
    state: State<'_, AppState>,
) -> Result<u32, String> {
    meeting_session::start_session(&state.session_manager, title).await
}

/// 同步转写文本
#[tauri::command]
async fn sync_transcript(
    text: String,
    speaker: Option<String>,
    start_time: Option<f64>,
    end_time: Option<f64>,
    state: State<'_, AppState>,
) -> Result<(), String> {
    meeting_session::sync_transcript(&state.session_manager, text, speaker, start_time, end_time)
        .await
}

/// 停止会议会话
#[tauri::command]
async fn stop_meeting_session(
    state: State<'_, AppState>,
) -> Result<(), String> {
    meeting_session::stop_session(&state.session_manager).await
}

/// 获取会议会话状态
#[tauri::command]
fn get_meeting_session_status(
    state: State<'_, AppState>,
) -> MeetingSession {
    meeting_session::get_session_status(&state.session_manager)
}

/// 设置服务器配置
#[tauri::command]
fn set_server_config(
    server_url: String,
    auth_token: String,
    state: State<'_, AppState>,
) -> Result<(), String> {
    *state.session_manager.server_url.lock().unwrap() = server_url;
    *state.session_manager.auth_token.lock().unwrap() = auth_token;
    Ok(())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    // 初始使用临时路径，setup 中会更新为 Tauri app data 目录
    let data_dir = std::env::current_dir()
        .unwrap_or_else(|_| PathBuf::from("."))
        .join(".smartmeeting");
    let app_state = AppState {
        whisper_config: Mutex::new(WhisperConfig::default()),
        session_manager: MeetingSessionManager::new(data_dir),
    };

    tauri::Builder::default()
        .manage(app_state)
        .invoke_handler(tauri::generate_handler![
            transcribe_segment,
            transcribe_all_segments,
            update_whisper_config,
            get_whisper_config,
            start_meeting_session,
            sync_transcript,
            stop_meeting_session,
            get_meeting_session_status,
            set_server_config,
        ])
        .setup(|app| {
            if cfg!(debug_assertions) {
                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Info)
                        .build(),
                )?;
            }
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
