<script setup lang="ts">
import { ref, onMounted } from "vue";
import { invoke } from "@tauri-apps/api/core";

const serverUrl = ref("http://127.0.0.1:8000");
const authToken = ref("");
const whisperApiUrl = ref("https://api.groq.com/openai/v1/audio/transcriptions");
const whisperApiKey = ref("");
const whisperModel = ref("whisper-large-v3");
const whisperLanguage = ref("zh");
const saved = ref(false);

interface WhisperConfig {
  api_url: string;
  api_key: string;
  model: string;
  language: string | null;
}

async function loadSettings() {
  try {
    const config = await invoke<WhisperConfig>("get_whisper_config");
    whisperApiUrl.value = config.api_url;
    whisperApiKey.value = config.api_key;
    whisperModel.value = config.model;
    whisperLanguage.value = config.language || "zh";
  } catch {
    // 使用默认值
  }
}

async function saveSettings() {
  try {
    // 保存服务器配置
    await invoke("set_server_config", {
      serverUrl: serverUrl.value,
      authToken: authToken.value,
    });

    // 保存 Whisper 配置
    await invoke("update_whisper_config", {
      apiUrl: whisperApiUrl.value,
      apiKey: whisperApiKey.value,
      model: whisperModel.value,
      language: whisperLanguage.value,
    });

    saved.value = true;
    setTimeout(() => (saved.value = false), 2000);
  } catch (e) {
    console.error("保存设置失败:", e);
  }
}

onMounted(loadSettings);
</script>

<template>
  <div class="settings-view">
    <h2>设置</h2>

    <div class="settings-section">
      <h3>服务器连接</h3>
      <div class="form-group">
        <label>服务器地址</label>
        <input v-model="serverUrl" type="text" placeholder="http://127.0.0.1:8000" />
      </div>
      <div class="form-group">
        <label>认证令牌</label>
        <input v-model="authToken" type="password" placeholder="JWT Token" />
      </div>
    </div>

    <div class="settings-section">
      <h3>Whisper 转写服务</h3>
      <div class="form-group">
        <label>API 地址</label>
        <input v-model="whisperApiUrl" type="text" placeholder="https://api.groq.com/openai/v1/audio/transcriptions" />
      </div>
      <div class="form-group">
        <label>API 密钥</label>
        <input v-model="whisperApiKey" type="password" placeholder="sk-..." />
      </div>
      <div class="form-group">
        <label>模型</label>
        <select v-model="whisperModel">
          <option value="whisper-large-v3">whisper-large-v3</option>
          <option value="whisper-large-v3-turbo">whisper-large-v3-turbo</option>
          <option value="whisper-small">whisper-small</option>
        </select>
      </div>
      <div class="form-group">
        <label>语言</label>
        <select v-model="whisperLanguage">
          <option value="zh">中文</option>
          <option value="en">英文</option>
          <option value="ja">日文</option>
          <option value="ko">韩文</option>
        </select>
      </div>
    </div>

    <div class="actions">
      <button class="btn-save" @click="saveSettings">
        {{ saved ? "已保存 ✓" : "保存设置" }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.settings-view {
  padding: 24px;
  max-width: 600px;
}

h2 {
  margin: 0 0 24px;
  font-size: 24px;
  font-weight: 700;
  color: var(--el-text-color-primary);
}

.settings-section {
  margin-bottom: 32px;
  padding: 20px;
  background: var(--el-fill-color-lighter);
  border-radius: 12px;
}

h3 {
  margin: 0 0 16px;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.form-group {
  margin-bottom: 16px;
}

.form-group:last-child {
  margin-bottom: 0;
}

label {
  display: block;
  margin-bottom: 6px;
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-regular);
}

input,
select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

input:focus,
select:focus {
  border-color: var(--el-color-primary);
}

.actions {
  display: flex;
  justify-content: flex-end;
}

.btn-save {
  padding: 12px 24px;
  background: var(--el-color-primary);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
  min-width: 120px;
}

.btn-save:hover {
  background: var(--el-color-primary-light-3);
}
</style>
