use serde::{Deserialize, Serialize};

/// 转写结果
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TranscriptResult {
    pub segment_index: u32,
    pub text: String,
    pub language: Option<String>,
    pub duration_secs: f64,
}

/// Whisper API 配置
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WhisperConfig {
    pub api_url: String,
    pub api_key: String,
    pub model: String,
    pub language: Option<String>,
}

impl Default for WhisperConfig {
    fn default() -> Self {
        Self {
            api_url: "https://api.groq.com/openai/v1/audio/transcriptions".to_string(),
            api_key: String::new(),
            model: "whisper-large-v3".to_string(),
            language: Some("zh".to_string()),
        }
    }
}

/// 将音频段落保存为临时 WAV 文件
#[cfg(feature = "audio-capture")]
fn segment_to_wav(
    segment: &crate::audio_capture::AudioSegment,
    path: &std::path::PathBuf,
) -> Result<(), String> {
    use hound::WavSpec;

    let spec = WavSpec {
        channels: segment.channels,
        sample_rate: segment.sample_rate,
        bits_per_sample: 16,
        sample_format: hound::SampleFormat::Int,
    };

    let mut writer =
        hound::WavWriter::create(path, spec).map_err(|e| format!("创建 WAV 文件失败: {}", e))?;

    for &sample in &segment.samples {
        let sample_i16 = (sample * i16::MAX as f32) as i16;
        writer
            .write_sample(sample_i16)
            .map_err(|e| format!("写入 WAV 数据失败: {}", e))?;
    }

    writer
        .finalize()
        .map_err(|e| format!("完成 WAV 文件失败: {}", e))?;

    Ok(())
}

/// 调用 Whisper API 转写音频段落
#[cfg(feature = "audio-capture")]
pub async fn transcribe_segment(
    segment: &crate::audio_capture::AudioSegment,
    config: &WhisperConfig,
) -> Result<TranscriptResult, String> {
    // 保存为临时 WAV 文件
    let temp_dir = std::env::temp_dir().join("smartmeeting");
    std::fs::create_dir_all(&temp_dir).map_err(|e| format!("创建临时目录失败: {}", e))?;

    let wav_path = temp_dir.join(format!("segment_{}.wav", segment.index));
    segment_to_wav(segment, &wav_path)?;

    // 构建 multipart 请求
    let file_bytes =
        std::fs::read(&wav_path).map_err(|e| format!("读取 WAV 文件失败: {}", e))?;

    let client = reqwest::Client::new();
    let form = reqwest::multipart::Form::new()
        .part(
            "file",
            reqwest::multipart::Part::bytes(file_bytes)
                .file_name(format!("segment_{}.wav", segment.index))
                .mime_str("audio/wav")
                .map_err(|e| format!("设置 MIME 类型失败: {}", e))?,
        )
        .text("model", config.model.clone());

    let form = if let Some(ref lang) = config.language {
        form.text("language", lang.clone())
    } else {
        form
    };

    let response = client
        .post(&config.api_url)
        .header("Authorization", format!("Bearer {}", config.api_key))
        .multipart(form)
        .send()
        .await
        .map_err(|e| format!("Whisper API 请求失败: {}", e))?;

    if !response.status().is_success() {
        let status = response.status();
        let body = response.text().await.unwrap_or_default();
        return Err(format!("Whisper API 返回错误 {}: {}", status, body));
    }

    let result: serde_json::Value = response
        .json()
        .await
        .map_err(|e| format!("解析 Whisper API 响应失败: {}", e))?;

    let text = result["text"]
        .as_str()
        .ok_or("Whisper API 响应中没有 text 字段")?
        .to_string();

    // 清理临时文件
    let _ = std::fs::remove_file(&wav_path);

    Ok(TranscriptResult {
        segment_index: segment.index,
        text,
        language: result["language"].as_str().map(|s| s.to_string()),
        duration_secs: segment.duration_secs,
    })
}

/// 批量转写多个音频段落
#[cfg(feature = "audio-capture")]
pub async fn transcribe_segments(
    segments: &[crate::audio_capture::AudioSegment],
    config: &WhisperConfig,
) -> Vec<Result<TranscriptResult, String>> {
    let mut results = Vec::new();

    for segment in segments {
        let result = transcribe_segment(segment, config).await;
        results.push(result);
    }

    results
}
