use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use cpal::{Device, Host, SampleFormat, StreamConfig};
use std::sync::{Arc, Mutex};
use std::thread;

/// 音频采集状态
#[derive(Debug, Clone, serde::Serialize)]
pub struct CaptureStatus {
    pub is_recording: bool,
    pub device_name: String,
    pub sample_rate: u32,
    pub channels: u16,
    pub duration_secs: f64,
}

/// 音频段落（30 秒一段）
#[derive(Debug, Clone, serde::Serialize)]
pub struct AudioSegment {
    pub index: u32,
    pub samples: Vec<f32>,
    pub sample_rate: u32,
    pub channels: u16,
    pub duration_secs: f64,
}

/// 共享的录音状态
pub struct RecordingState {
    pub is_recording: bool,
    pub buffer: Vec<f32>,
    pub sample_rate: u32,
    pub channels: u16,
    pub segment_index: u32,
    pub segments: Vec<AudioSegment>,
    pub device_name: String,
}

impl RecordingState {
    pub fn new() -> Self {
        Self {
            is_recording: false,
            buffer: Vec::new(),
            sample_rate: 44100,
            channels: 2,
            segment_index: 0,
            segments: Vec::new(),
            device_name: String::new(),
        }
    }
}

/// 获取系统音频输入设备（loopback/麦克风）
pub fn get_audio_device(host: &Host) -> Option<Device> {
    // 优先尝试获取 loopback 设备（系统音频输出）
    #[cfg(target_os = "linux")]
    {
        if let Ok(devices) = host.input_devices() {
            for device in devices {
                if let Ok(name) = device.name() {
                    if name.to_lowercase().contains("monitor")
                        || name.to_lowercase().contains("loopback")
                    {
                        return Some(device);
                    }
                }
            }
        }
    }

    // macOS: 使用 ScreenCaptureKit 或默认输入
    #[cfg(target_os = "macos")]
    {
        // macOS 系统音频采集需要 ScreenCaptureKit
        // 这里先使用默认输入设备作为 fallback
    }

    // Windows: WASAPI loopback
    #[cfg(target_os = "windows")]
    {
        // cpal 在 Windows 上支持 WASAPI loopback
        // 需要通过 output device 的 loopback 获取
    }

    // Fallback: 使用默认输入设备（麦克风）
    host.default_input_device()
}

/// 获取设备支持的录音配置
pub fn get_stream_config(device: &Device) -> Option<StreamConfig> {
    if let Ok(config) = device.default_input_config() {
        Some(StreamConfig {
            channels: config.channels(),
            sample_rate: config.sample_rate(),
            buffer_size: cpal::BufferSize::Default,
        })
    } else {
        None
    }
}

/// 开始录音
pub fn start_recording(state: Arc<Mutex<RecordingState>>) -> Result<String, String> {
    let host = cpal::default_host();
    let device = get_audio_device(&host).ok_or("未找到音频输入设备")?;
    let device_name = device.name().unwrap_or_else(|_| "Unknown".to_string());
    let config = get_stream_config(&device).ok_or("无法获取设备配置")?;

    let sample_rate = config.sample_rate.0;
    let channels = config.channels;
    let sample_format = device
        .default_input_config()
        .map(|c| c.sample_format())
        .unwrap_or(SampleFormat::F32);

    {
        let mut s = state.lock().unwrap();
        s.is_recording = true;
        s.sample_rate = sample_rate;
        s.channels = channels;
        s.device_name = device_name.clone();
        s.buffer.clear();
        s.segment_index = 0;
        s.segments.clear();
    }

    let state_clone = state.clone();
    let segment_duration_secs = 30.0;
    let segment_samples = (sample_rate as f64 * channels as f64 * segment_duration_secs) as usize;

    let stream = match sample_format {
        SampleFormat::F32 => device
            .build_input_stream(
                &config,
                move |data: &[f32], _: &cpal::InputCallbackInfo| {
                    let mut s = state_clone.lock().unwrap();
                    if !s.is_recording {
                        return;
                    }
                    s.buffer.extend_from_slice(data);

                    // 每 30 秒切一段
                    if s.buffer.len() >= segment_samples {
                        let segment = AudioSegment {
                            index: s.segment_index,
                            samples: s.buffer[..segment_samples].to_vec(),
                            sample_rate: s.sample_rate,
                            channels: s.channels,
                            duration_secs: segment_duration_secs,
                        };
                        s.segments.push(segment);
                        s.buffer = s.buffer[segment_samples..].to_vec();
                        s.segment_index += 1;
                    }
                },
                |err| log::error!("音频采集错误: {}", err),
                None,
            )
            .map_err(|e| format!("创建音频流失败: {}", e))?,
        SampleFormat::I16 => {
            let state_clone2 = state.clone();
            device
                .build_input_stream(
                    &config,
                    move |data: &[i16], _: &cpal::InputCallbackInfo| {
                        let float_data: Vec<f32> =
                            data.iter().map(|&s| s as f32 / i16::MAX as f32).collect();
                        let mut s = state_clone2.lock().unwrap();
                        if !s.is_recording {
                            return;
                        }
                        s.buffer.extend_from_slice(&float_data);

                        if s.buffer.len() >= segment_samples {
                            let segment = AudioSegment {
                                index: s.segment_index,
                                samples: s.buffer[..segment_samples].to_vec(),
                                sample_rate: s.sample_rate,
                                channels: s.channels,
                                duration_secs: segment_duration_secs,
                            };
                            s.segments.push(segment);
                            s.buffer = s.buffer[segment_samples..].to_vec();
                            s.segment_index += 1;
                        }
                    },
                    |err| log::error!("音频采集错误: {}", err),
                    None,
                )
                .map_err(|e| format!("创建音频流失败: {}", e))?
        }
        _ => return Err(format!("不支持的采样格式: {:?}", sample_format)),
    };

    stream
        .play()
        .map_err(|e| format!("启动音频流失败: {}", e))?;

    // 保持 stream 存活（在后台线程中）
    thread::spawn(move || {
        // stream 在此线程生命周期内保持活跃
        let _stream = stream;
        loop {
            std::thread::sleep(std::time::Duration::from_millis(100));
            let s = state.lock().unwrap();
            if !s.is_recording {
                break;
            }
        }
    });

    Ok(device_name)
}

/// 停止录音并返回所有段落
pub fn stop_recording(state: Arc<Mutex<RecordingState>>) -> Vec<AudioSegment> {
    let mut s = state.lock().unwrap();
    s.is_recording = false;

    // 将剩余的 buffer 作为最后一段
    if !s.buffer.is_empty() {
        let segment = AudioSegment {
            index: s.segment_index,
            samples: s.buffer.clone(),
            sample_rate: s.sample_rate,
            channels: s.channels,
            duration_secs: s.buffer.len() as f64 / (s.sample_rate as f64 * s.channels as f64),
        };
        s.segments.push(segment);
        s.buffer.clear();
    }

    s.segments.clone()
}

/// 获取当前录音状态
pub fn get_status(state: &RecordingState) -> CaptureStatus {
    CaptureStatus {
        is_recording: state.is_recording,
        device_name: state.device_name.clone(),
        sample_rate: state.sample_rate,
        channels: state.channels,
        duration_secs: state.buffer.len() as f64
            / (state.sample_rate as f64 * state.channels as f64),
    }
}
