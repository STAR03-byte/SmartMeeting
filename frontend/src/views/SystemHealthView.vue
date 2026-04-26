<template>
  <section class="health-page">
    <header class="page-header">
      <div>
        <h1>系统健康</h1>
        <p>私有化部署运行状态</p>
      </div>
      <el-button type="primary" :loading="loading" @click="loadStatus">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
    </header>

    <el-alert
      v-if="error"
      :title="error"
      type="error"
      show-icon
      :closable="false"
    />

    <section class="status-band">
      <div class="status-summary">
        <span class="status-label">总体状态</span>
        <strong>{{ statusLabel }}</strong>
      </div>
      <el-tag :type="statusTagType" size="large">{{ statusTagText }}</el-tag>
    </section>

    <section class="check-grid">
      <div
        v-for="item in checkItems"
        :key="item.key"
        class="check-item"
      >
        <span class="check-title">{{ item.label }}</span>
        <el-tag :type="item.ok ? 'success' : 'warning'">{{ item.ok ? '正常' : '需处理' }}</el-tag>
        <p>{{ item.detail }}</p>
      </div>
    </section>

    <section class="detail-grid">
      <el-card class="base-card">
        <template #header>
          <span>基础服务</span>
        </template>
        <dl class="detail-list">
          <div>
            <dt>存活检查</dt>
            <dd>{{ liveStatus || '-' }}</dd>
          </div>
          <div>
            <dt>就绪检查</dt>
            <dd>{{ readyStatus || '-' }}</dd>
          </div>
          <div>
            <dt>数据库后端</dt>
            <dd>{{ preflight?.database.backend || '-' }}</dd>
          </div>
          <div v-if="preflight?.database.error">
            <dt>数据库错误</dt>
            <dd>{{ preflight.database.error }}</dd>
          </div>
        </dl>
      </el-card>

      <el-card class="base-card">
        <template #header>
          <span>AI 与转写</span>
        </template>
        <dl class="detail-list">
          <div>
            <dt>LLM Provider</dt>
            <dd>{{ deployment?.llm_provider || '-' }}</dd>
          </div>
          <div>
            <dt>LLM 配置</dt>
            <dd>{{ deployment?.llm_configured ? '已配置' : '未配置' }}</dd>
          </div>
          <div>
            <dt>FFmpeg</dt>
            <dd>{{ deployment?.ffmpeg_available ? '可用' : '未检测到' }}</dd>
          </div>
          <div>
            <dt>模拟转写 fallback</dt>
            <dd>{{ deployment?.whisper_allow_mock_fallback ? '允许' : '关闭' }}</dd>
          </div>
        </dl>
      </el-card>

      <el-card class="base-card">
        <template #header>
          <span>部署配置</span>
        </template>
        <dl class="detail-list">
          <div>
            <dt>JWT Secret</dt>
            <dd>{{ deployment?.jwt_secret_configured ? '已替换默认值' : '仍是默认值' }}</dd>
          </div>
          <div>
            <dt>存储目录</dt>
            <dd>{{ deployment?.storage_dir || '-' }}</dd>
          </div>
          <div>
            <dt>目录存在</dt>
            <dd>{{ deployment?.storage_dir_exists ? '是' : '否' }}</dd>
          </div>
          <div>
            <dt>目录可写</dt>
            <dd>{{ deployment?.storage_dir_writable ? '是' : '否' }}</dd>
          </div>
        </dl>
      </el-card>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { Refresh } from "@element-plus/icons-vue";

import { getLivenessStatus, getPreflightStatus, getReadinessStatus } from "../api/health";
import type { PreflightStatus } from "../api/health";
import { getApiErrorMessage } from "../api/client";

const preflight = ref<PreflightStatus | null>(null);
const liveStatus = ref("");
const readyStatus = ref("");
const loading = ref(false);
const error = ref("");

const deployment = computed(() => preflight.value?.private_deployment ?? null);

const statusLabel = computed(() => {
  if (!preflight.value) return "等待检查";
  return preflight.value.status === "ok" ? "可以投入使用" : "需要处理配置项";
});

const statusTagType = computed(() => (preflight.value?.status === "ok" ? "success" : "warning"));
const statusTagText = computed(() => (preflight.value?.status === "ok" ? "OK" : "DEGRADED"));

const checkItems = computed(() => {
  const checks = preflight.value?.checks;
  const privateDeployment = preflight.value?.private_deployment;
  return [
    {
      key: "database",
      label: "数据库连接",
      ok: Boolean(checks?.database),
      detail: checks?.database ? "数据库连接正常。" : "无法连接数据库，请检查 DB 配置和服务状态。",
    },
    {
      key: "jwt",
      label: "JWT Secret",
      ok: Boolean(checks?.jwt_secret),
      detail: checks?.jwt_secret ? "JWT_SECRET_KEY 已设置为非默认值。" : "请在生产环境替换默认 JWT_SECRET_KEY。",
    },
    {
      key: "ffmpeg",
      label: "FFmpeg",
      ok: Boolean(checks?.ffmpeg),
      detail: checks?.ffmpeg ? "系统 PATH 中可检测到 ffmpeg。" : "音频处理需要 ffmpeg，请确认 PATH 或容器镜像。",
    },
    {
      key: "storage",
      label: "音频存储",
      ok: Boolean(checks?.storage),
      detail: privateDeployment?.storage_dir
        ? `目录：${privateDeployment.storage_dir}`
        : "请确认音频存储目录存在且可写。",
    },
  ];
});

async function loadStatus() {
  loading.value = true;
  error.value = "";
  try {
    const [preflightResult, liveResult, readyResult] = await Promise.all([
      getPreflightStatus(),
      getLivenessStatus(),
      getReadinessStatus(),
    ]);
    preflight.value = preflightResult;
    liveStatus.value = liveResult.status;
    readyStatus.value = readyResult.status;
  } catch (err) {
    error.value = getApiErrorMessage(err);
  } finally {
    loading.value = false;
  }
}

onMounted(loadStatus);
</script>

<style scoped>
.health-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.page-header,
.status-band {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.page-header h1 {
  margin: 0 0 8px;
  font-size: 28px;
  color: var(--el-text-color-primary);
}

.page-header p {
  margin: 0;
  color: var(--el-text-color-secondary);
}

.status-band {
  padding: 20px 24px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: var(--el-border-radius-small);
  background: var(--el-bg-color);
}

.status-summary {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.status-label {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.status-summary strong {
  color: var(--el-text-color-primary);
  font-size: 20px;
}

.check-grid,
.detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
}

.check-item {
  min-height: 132px;
  padding: 18px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: var(--el-border-radius-small);
  background: var(--el-bg-color);
}

.check-title {
  display: block;
  margin-bottom: 10px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.check-item p {
  margin: 12px 0 0;
  color: var(--el-text-color-secondary);
  line-height: 1.6;
}

.base-card {
  border-radius: var(--el-border-radius-small);
}

.detail-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin: 0;
}

.detail-list div {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}

.detail-list dt {
  color: var(--el-text-color-secondary);
}

.detail-list dd {
  margin: 0;
  color: var(--el-text-color-primary);
  text-align: right;
  word-break: break-word;
}

@media (max-width: 720px) {
  .page-header,
  .status-band {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
