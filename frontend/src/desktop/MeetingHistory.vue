<script setup lang="ts">
import { ref, onMounted } from "vue";
import { invoke } from "@tauri-apps/api/core";

interface Meeting {
  id: number;
  title: string;
  status: string;
  created_at: string;
  scheduled_start_at: string | null;
}

const meetings = ref<Meeting[]>([]);
const loading = ref(false);
const error = ref("");

const statusLabel: Record<string, string> = {
  planned: "计划中",
  ongoing: "进行中",
  done: "已完成",
  cancelled: "已取消",
};

const statusClass: Record<string, string> = {
  planned: "status-planned",
  ongoing: "status-ongoing",
  done: "status-done",
  cancelled: "status-cancelled",
};

async function loadMeetings() {
  loading.value = true;
  error.value = "";
  try {
    // 这里需要调用后端 API 获取会议列表
    // 暂时使用模拟数据
    meetings.value = [
      {
        id: 1,
        title: "产品需求评审会",
        status: "done",
        created_at: new Date().toISOString(),
        scheduled_start_at: null,
      },
      {
        id: 2,
        title: "技术方案讨论",
        status: "done",
        created_at: new Date(Date.now() - 86400000).toISOString(),
        scheduled_start_at: null,
      },
    ];
  } catch (e) {
    error.value = e instanceof Error ? e.message : "加载失败";
  } finally {
    loading.value = false;
  }
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString("zh-CN");
}

onMounted(loadMeetings);
</script>

<template>
  <div class="meeting-history">
    <div class="header">
      <h2>会议历史</h2>
      <button class="btn-refresh" @click="loadMeetings">刷新</button>
    </div>

    <div v-if="error" class="error">{{ error }}</div>

    <div v-if="loading" class="loading">加载中...</div>

    <div v-else-if="meetings.length === 0" class="empty">
      暂无会议记录
    </div>

    <div v-else class="meeting-list">
      <div v-for="meeting in meetings" :key="meeting.id" class="meeting-card">
        <div class="meeting-header">
          <h3>{{ meeting.title }}</h3>
          <span :class="['status', statusClass[meeting.status]]">
            {{ statusLabel[meeting.status] || meeting.status }}
          </span>
        </div>
        <div class="meeting-meta">
          <span>{{ formatDate(meeting.created_at) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.meeting-history {
  padding: 24px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  color: var(--el-text-color-primary);
}

.btn-refresh {
  padding: 8px 16px;
  background: var(--el-fill-color-lighter);
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-refresh:hover {
  background: var(--el-fill-color-light);
  border-color: var(--el-color-primary);
}

.error {
  padding: 12px;
  background: #fef2f2;
  color: #dc2626;
  border-radius: 8px;
  font-size: 14px;
}

.loading,
.empty {
  text-align: center;
  padding: 48px;
  color: var(--el-text-color-secondary);
  font-size: 16px;
}

.meeting-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.meeting-card {
  padding: 16px 20px;
  background: var(--el-fill-color-lighter);
  border-radius: 10px;
  transition: all 0.2s;
  cursor: pointer;
}

.meeting-card:hover {
  background: var(--el-color-primary-light-9);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.meeting-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.status {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.status-planned {
  background: #e0f2fe;
  color: #0369a1;
}

.status-ongoing {
  background: #dcfce7;
  color: #16a34a;
}

.status-done {
  background: #f3f4f6;
  color: #6b7280;
}

.status-cancelled {
  background: #fef2f2;
  color: #dc2626;
}

.meeting-meta {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}
</style>
