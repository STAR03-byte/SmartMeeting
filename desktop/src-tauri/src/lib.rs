#[cfg(feature = "audio-capture")]
mod audio_capture;
mod transcription;

use std::sync::Mutex;
use tauri::State;
use transcription::{TranscriptResult, WhisperConfig};

/// 应用状态
pub struct AppState {
    pub whisper_config: Mutex<WhisperConfig>,
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

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let app_state = AppState {
        whisper_config: Mutex::new(WhisperConfig::default()),
    };

    tauri::Builder::default()
        .manage(app_state)
        .invoke_handler(tauri::generate_handler![
            transcribe_segment,
            transcribe_all_segments,
            update_whisper_config,
            get_whisper_config,
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
